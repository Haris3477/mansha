"""Rule lookup tool. Pure code, no LLM.

For one tariff line, returns the product-specific rule of origin (PSR) from the
knowledge base, plus the general rules that change how it is applied. The most
specific row wins (lookup_order in psr_rules.json). There is NO default rule:
no match means a gap, never an assumed 'VA 40%'.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field

from mansha.kb import load_corridor

TOOL_PREFIX = "TOOL:rule_lookup"
FINE_LEVELS = {"subheading", "heading", "heading_range"}


@dataclass
class RuleLookupResult:
    tool_id: str
    status: str  # RULE_FOUND | RULE_NOT_LOADED | NO_RULE_MATCH
    tariff_line: str
    level: str | None
    rules: list[dict] = field(default_factory=list)
    general_rules: list[dict] = field(default_factory=list)
    interpretations: list[str] = field(default_factory=list)
    sources: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------- pure matching logic (tested with fake rules) ----------

def _is_digits(s, n: int) -> bool:
    return isinstance(s, str) and s.isdigit() and len(s) == n


def scope_matches(scope: dict, codes: list[str]) -> bool:
    """codes: the line's code(s) to try, e.g. [HS-2022 line, HS-2017 code]."""
    t = scope.get("type")
    if t == "subheading":
        s = scope.get("subheading")
        return _is_digits(s, 6) and any(c.startswith(s) for c in codes)
    if t == "heading":
        h = scope.get("heading")
        return _is_digits(h, 4) and any(c[:4] == h for c in codes)
    if t == "heading_range":
        lo, hi = scope.get("from"), scope.get("to")
        return _is_digits(lo, 4) and _is_digits(hi, 4) and any(lo <= c[:4] <= hi for c in codes)
    if t in ("ex_chapter", "chapter"):
        ch = scope.get("chapter")
        return _is_digits(ch, 2) and any(c[:2] == ch for c in codes)
    return False


def find_rule(codes: list[str], rules: list[dict], order: list[str]) -> tuple[str | None, list[dict]]:
    """Return (level, matching rules) for the most specific level with a match."""
    for level in order:
        hits = [r for r in rules if r.get("scope", {}).get("type") == level and scope_matches(r["scope"], codes)]
        if hits:
            return level, hits
    return None, []


# ---------- main entry point ----------

def rule_lookup(tariff_line: str, corridor: str = "india") -> RuleLookupResult:
    if not _is_digits(tariff_line, 8):
        raise ValueError(f"tariff_line must be 8 digits, got {tariff_line!r}")

    kb = load_corridor(corridor)
    psr = kb["psr"]
    meta = psr.get("metadata", {})
    checked = set(meta.get("chapters_fully_checked", []))
    order = meta.get("lookup_order", ["subheading", "heading", "heading_range", "ex_chapter", "chapter"])
    chapter = tariff_line[:2]

    line = next((l for l in kb["tariff"]["lines"] if l["tariff_line"] == tariff_line), None)
    hs17 = line.get("hs2017_code") if line else None
    codes = [tariff_line] + ([hs17] if hs17 and hs17 != tariff_line else [])

    result = RuleLookupResult(tool_id=f"{TOOL_PREFIX}:{tariff_line}", status="NO_RULE_MATCH",
                              tariff_line=tariff_line, level=None)

    level, hits = find_rule(codes, psr.get("rules", []), order)
    if hits:
        result.status = "RULE_FOUND"
        result.level = level
        result.rules = copy.deepcopy(hits)  # the KB is cached: never mutate it
        if len(hits) > 1:
            result.notes.append(f"{len(hits)} rules match at level '{level}'; which one applies depends on the exact product.")
        if level == "ex_chapter":
            result.notes.append("Ex-chapter rule: applies only to part of the chapter. Confirm the product falls in it.")
        if level in FINE_LEVELS and not hs17:
            result.notes.append("PSR rows use HS 2017 codes; this line has no HS 2017 code recorded. "
                                "Confirm the code did not change between HS 2017 and HS 2022.")
        if chapter not in checked:
            result.notes.append(f"Chapter {chapter} is not fully checked: a more specific row may exist "
                                "that is not loaded.")
        if any("+" in r.get("rule_text", "") for r in hits):
            result.interpretations = list(meta.get("interpretations", []))
    elif chapter not in checked:
        result.status = "RULE_NOT_LOADED"
        result.notes.append(f"REGULATORY_GAP_DETECTED: the rule of origin for chapter {chapter} is not "
                            "loaded in the knowledge base (rule not loaded, not 'no rule').")
    else:
        result.notes.append(f"REGULATORY_GAP_DETECTED: no product-specific rule matches {tariff_line}. "
                            "The agreement has no default rule.")

    # General rules always travel with a found rule; mark which apply to this line.
    if result.status == "RULE_FOUND":
        fob_only = set()
        for g in psr.get("general_rules", []):
            fob_only |= set((g.get("params") or {}).get("fob_only_chapters", []))
        for g in psr.get("general_rules", []):
            g2 = copy.deepcopy(g)
            params = g.get("params") or {}
            if "fob_only_chapters" in params:
                g2["applies_to_this_line"] = chapter in params["fob_only_chapters"]
            elif "exworks_reduction_pts" in params:
                g2["applies_to_this_line"] = chapter not in fob_only
            else:
                g2["applies_to_this_line"] = True
            result.general_rules.append(g2)

    keys = {r["source_key"] for r in result.rules} | {g["source_key"] for g in result.general_rules}
    result.sources = {k: kb["sources"][k]["url"] for k in sorted(keys)}
    return result