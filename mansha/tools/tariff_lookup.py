"""Tariff lookup tool. Pure code, no LLM.

Turns the Intake output (HS code and/or product description) into a shortlist
of candidate tariff lines from the knowledge base. It does NOT pick the final
line: the Researcher chooses from this shortlist only, and cites the record ID.

HS codes are harmonised only to 6 digits; digits 7-8 are national. A UAE
exporter's 8-digit code may mean something else in India's tariff, so a given
code is matched on its 6-digit (or 4-digit) prefix, with exact 8-digit hits
flagged rather than trusted alone.
"""

from __future__ import annotations

import copy
import re
from dataclasses import asdict, dataclass, field

from mansha.kb import load_corridor

TOOL_ID = "TOOL:tariff_lookup"
MAX_CANDIDATES = 5
CORRIDOR_CODES = {"india": "IN"}
CORRIDOR_NAMES = {"india": "India"}

# Words too common in tariff descriptions to say anything about the product.
STOPWORDS = {
    "and", "the", "for", "with", "other", "others", "their", "thereof",
    "not", "whether", "including", "made", "parts", "article", "type",
    "used", "kind", "etc", "our", "make", "product", "from",
}
SPELLING = {"aluminum": "aluminium", "jewelry": "jewellery", "color": "colour"}


@dataclass
class TariffLookupResult:
    tool_id: str
    status: str  # CANDIDATES | NOT_FOUND
    method: str | None  # hs_code | keywords | None
    query: dict
    candidates: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    # Notes about the user's own code that code prints in the report word for word (problem 98); each is
    # also in `notes`. The other notes are for the Researcher only (they name IDs or give instructions).
    report_notes: list[str] = field(default_factory=list)
    # Keyword path: the best candidates tie and each matches different words of the description, so no
    # line describes the product as a whole (problem 100; the Researcher must then write a gap).
    split_match: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


# ---------- text matching ----------

def _singular(w: str) -> str:
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"  # batteries -> battery
    if w.endswith(("sses", "shes", "ches", "xes")):
        return w[:-2]  # boxes -> box, glasses -> glass
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]  # chargers -> charger
    return w


def tokens(text: str) -> set[str]:
    out = set()
    for w in re.findall(r"[a-z]+", (text or "").lower()):
        w = SPELLING.get(w, w)
        w = _singular(w)
        w = SPELLING.get(w, w)
        if len(w) > 2 and w not in STOPWORDS:
            out.add(w)
    return out


def _line_tokens(line: dict) -> set[str]:
    t = tokens(line["description"])
    for kw in line["keywords"]:
        t |= tokens(kw)
    return t


def keyword_score(query_tokens: set[str], line: dict) -> int:
    score = len(query_tokens & _line_tokens(line))
    for kw in line["keywords"]:
        kw_t = tokens(kw)
        if len(kw_t) > 1 and kw_t <= query_tokens:
            score += 1  # whole multi-word keyword present, e.g. "sweet biscuits"
    return score


# ---------- candidate records ----------

def _line_candidate(line: dict, sources: dict, excluded: dict, match: str, score: int | None = None) -> dict:
    c = copy.deepcopy(line)  # the KB is cached: never mutate it
    c.pop("keywords", None)
    c["kind"] = "tariff_line"
    c["match"] = match
    if score is not None:
        c["score"] = score
    keys = sorted({k for part in ("mfn", "cepa", "staging") for k in line[part]["source_keys"]})
    c["sources"] = {k: sources[k]["url"] for k in keys}
    c["in_excluded_heading"] = line["tariff_line"][:4] in excluded
    return c


def _exclusion_candidate(exc: dict, sources: dict, prefix: str) -> dict:
    return {
        "kind": "heading_exclusion",
        "id": f"EXC-{prefix}-{exc['heading']}",
        "heading": exc["heading"],
        "cepa": {"status": "EXCLUDED", "rate_pct": None},
        "evidence": exc.get("evidence", ""),
        "match": "hs_heading",
        "sources": {k: sources[k]["url"] for k in exc["source_keys"]},
        "note": "Whole heading excluded: no CEPA preference, MFN applies. MFN rate for this exact line is not loaded.",
    }


# ---------- main entry point ----------

def tariff_lookup(product_description: str | None = None, hs_code_given: str | None = None,
                  corridor: str = "india") -> TariffLookupResult:
    kb = load_corridor(corridor)
    lines = kb["tariff"]["lines"]
    sources = kb["sources"]
    excluded = {e["heading"]: e for e in kb["tariff"].get("heading_exclusions", [])}
    prefix = CORRIDOR_CODES.get(corridor, corridor.upper())

    result = TariffLookupResult(
        tool_id=TOOL_ID, status="NOT_FOUND", method=None,
        query={"corridor": corridor, "product_description": product_description, "hs_code_given": hs_code_given},
    )
    code = re.sub(r"\D", "", hs_code_given or "")

    # 1) HS code path
    if code and len(code) < 4:
        result.notes.append(f"HS code '{code}' is shorter than 4 digits; ignored.")
    elif code:
        plen = 6 if len(code) >= 6 else 4
        exact = {l["tariff_line"] for l in lines
                 if len(code) >= 8 and code[:8] in (l["tariff_line"], l.get("hs2017_code"))}
        hits = [l for l in lines if l["tariff_line"] in exact or l["tariff_line"].startswith(code[:plen])]
        for l in sorted(hits, key=lambda l: (l["tariff_line"] not in exact, l["tariff_line"])):
            match = "hs_exact_8" if l["tariff_line"] in exact else f"hs_prefix_{plen}"
            result.candidates.append(_line_candidate(l, sources, excluded, match))

        heading = code[:4]
        if heading in excluded and not result.candidates:
            result.candidates.append(_exclusion_candidate(excluded[heading], sources, prefix))

        if result.candidates:
            result.method = "hs_code"
            country = CORRIDOR_NAMES.get(corridor, corridor.title())
            if len(code) >= 8 and not exact:
                result.report_notes.append(
                    f"The 8-digit code {code[:8]} you gave is not a line in {country}'s tariff; Mansha matched "
                    f"it on its first {plen} digits ({code[:plen]}). 8-digit codes are national and differ "
                    f"between the UAE and {country}."
                )
            # Problem 98 (N9, 25 Oct): an HS 2017 code matched exactly through the line's hs2017_code, so no
            # note was written and the report said nothing about the old code.
            for l in hits:
                if l["tariff_line"] in exact and l["tariff_line"] != code[:8]:
                    result.report_notes.append(
                        f"The code {code[:8]} you gave is {country}'s older HS 2017 code for this product; "
                        f"{country}'s current tariff line is {l['tariff_line']}."
                    )
            result.notes += result.report_notes
        else:
            result.notes.append(f"HS code {code} matches no line in the knowledge base; trying keywords.")

    # 2) Keyword path (no usable code, or code found nothing)
    q_tokens = tokens(product_description or "")
    if q_tokens:
        scored = sorted(((keyword_score(q_tokens, l), l) for l in lines),
                        key=lambda x: (-x[0], x[1]["tariff_line"]))
        top = [(s, l) for s, l in scored if s >= 1][:MAX_CANDIDATES]
        if not result.candidates:
            result.method = "keywords" if top else None
            result.candidates = [_line_candidate(l, sources, excluded, "keywords", s) for s, l in top]
            # Problem 100 (N13, 25 Oct): "wooden doors" matched aluminium doors on "door" and wooden
            # furniture on "wooden", 1 each; the Researcher picked furniture. A tie on different words
            # means no line describes the product as a whole.
            tied = [l for s, l in top if s == top[0][0]] if top else []
            matched = [sorted(q_tokens & _line_tokens(l)) for l in tied]
            if len(tied) > 1 and len({tuple(m) for m in matched}) > 1:
                result.split_match = True
                parts = ", ".join(f"{l['id']} matches only {' '.join(m)!r}" for l, m in zip(tied, matched))
                result.notes.append(
                    f"No candidate matches the whole description ({parts}). If none of them describes the "
                    f"product, the classification is REGULATORY_GAP_DETECTED."
                )
        else:
            # Both given: flag if the words point somewhere the code doesn't.
            code_ids = {c["id"] for c in result.candidates}
            if top and top[0][1]["id"] not in code_ids:
                result.notes.append(
                    f"The description best matches {top[0][1]['id']}, which the HS code does not point to. "
                    "Ask the user to confirm the product or the code."
                )

    if result.candidates:
        result.status = "CANDIDATES"
    else:
        result.notes.append("No matching tariff line in the knowledge base: REGULATORY_GAP_DETECTED.")
    return result