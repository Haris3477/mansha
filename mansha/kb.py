"""Knowledge-base loader and validator. Pure code, no LLM.

Loads the structured data for one corridor (data/<corridor>/) and refuses to
return it if any record breaks the schema, so a typo fails loudly at startup
instead of producing a wrong duty figure later.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

TIERS = {"PRIMARY", "PRIMARY-COPY", "UNCONFIRMED"}
CEPA_STATUSES = {"PREFERENTIAL", "EXCLUDED"}
CEPA_TABLES = {"I", "II", "III"}
PSR_TESTS = {"CTH", "CTSH", "VA", "WO"}
SCOPE_TYPES = {"subheading", "heading", "heading_range", "ex_chapter", "chapter"}


class KBError(Exception):
    """Raised when knowledge-base files are missing or invalid."""


def _read_json(path: Path):
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise KBError(f"missing file: {path}") from e
    except json.JSONDecodeError as e:
        raise KBError(f"invalid JSON in {path}: {e}") from e


@cache
def load_corridor(corridor: str = "india") -> dict:
    """Load and validate one corridor. Cached: treat the result as read-only."""
    folder = DATA_DIR / corridor
    kb = {
        "sources": _read_json(folder / "sources.json"),
        "tariff": _read_json(folder / "tariff_lines.json"),
        "psr": _read_json(folder / "psr_rules.json"),
    }
    problems = validate(kb)
    if problems:
        raise KBError(f"{corridor}: {len(problems)} problem(s):\n- " + "\n- ".join(problems))
    return kb


# ---------- validation ----------

def _is_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _check_pct(value, where: str, problems: list[str]) -> None:
    if not _is_number(value) or not 0 <= value <= 100:
        problems.append(f"{where}: must be a number from 0 to 100, got {value!r}")


def _check_source_keys(keys, where: str, sources: dict, problems: list[str]) -> None:
    if not isinstance(keys, list) or not keys:
        problems.append(f"{where}: source_keys must be a non-empty list")
        return
    for key in keys:
        if key not in sources:
            problems.append(f"{where}: unknown source key {key!r}")


def _is_digits(s, length: int) -> bool:
    return isinstance(s, str) and s.isdigit() and len(s) == length


def validate(kb: dict) -> list[str]:
    """Return a list of problems (empty list = valid)."""
    problems: list[str] = []
    sources = kb["sources"]

    # sources.json
    for key, src in sources.items():
        for field in ("title", "url", "tier"):
            if not src.get(field):
                problems.append(f"source {key}: missing {field}")
        if not str(src.get("url", "")).startswith("https://"):
            problems.append(f"source {key}: url must start with https://")
        if src.get("tier") not in TIERS:
            problems.append(f"source {key}: tier must be one of {sorted(TIERS)}")

    # tariff_lines.json
    tariff = kb["tariff"]
    excluded_headings = set()
    for i, exc in enumerate(tariff.get("heading_exclusions", [])):
        where = f"heading_exclusions[{i}]"
        if not _is_digits(exc.get("heading"), 4):
            problems.append(f"{where}: heading must be 4 digits")
        else:
            excluded_headings.add(exc["heading"])
        _check_source_keys(exc.get("source_keys"), where, sources, problems)

    seen_ids, seen_lines = set(), set()
    for line in tariff.get("lines", []):
        rid = line.get("id", "<no id>")
        if rid in seen_ids:
            problems.append(f"{rid}: duplicate id")
        seen_ids.add(rid)

        code = line.get("tariff_line")
        if not _is_digits(code, 8):
            problems.append(f"{rid}: tariff_line must be 8 digits")
        elif code in seen_lines:
            problems.append(f"{rid}: duplicate tariff_line {code}")
        else:
            seen_lines.add(code)
            if rid != f"TL-IN-{code}":
                problems.append(f"{rid}: id should be TL-IN-{code}")

        if not line.get("description"):
            problems.append(f"{rid}: missing description")
        kws = line.get("keywords")
        if not isinstance(kws, list) or not kws or not all(isinstance(k, str) for k in kws):
            problems.append(f"{rid}: keywords must be a non-empty list of strings")

        mfn = line.get("mfn", {})
        _check_pct(mfn.get("tariff_rate_pct"), f"{rid} mfn.tariff_rate_pct", problems)
        _check_pct(mfn.get("effective_rate_pct"), f"{rid} mfn.effective_rate_pct", problems)
        _check_source_keys(mfn.get("source_keys"), f"{rid} mfn", sources, problems)

        cepa = line.get("cepa", {})
        status = cepa.get("status")
        if status not in CEPA_STATUSES:
            problems.append(f"{rid}: cepa.status must be one of {sorted(CEPA_STATUSES)}")
        elif status == "PREFERENTIAL":
            _check_pct(cepa.get("rate_pct"), f"{rid} cepa.rate_pct", problems)
            if cepa.get("table") not in CEPA_TABLES:
                problems.append(f"{rid}: cepa.table must be I, II or III")
            if not isinstance(cepa.get("s_no"), int):
                problems.append(f"{rid}: cepa.s_no must be an integer")
        else:  # EXCLUDED
            if cepa.get("rate_pct") is not None:
                problems.append(f"{rid}: an EXCLUDED line must have cepa.rate_pct = null")
        _check_source_keys(cepa.get("source_keys"), f"{rid} cepa", sources, problems)

        if isinstance(code, str) and code[:4] in excluded_headings and status != "EXCLUDED":
            problems.append(f"{rid}: heading {code[:4]} is excluded, so status must be EXCLUDED")

        staging = line.get("staging", {})
        if not staging.get("category"):
            problems.append(f"{rid}: missing staging.category")
        _check_source_keys(staging.get("source_keys"), f"{rid} staging", sources, problems)

        hs17 = line.get("hs2017_code")
        if hs17 is not None and not _is_digits(hs17, 8):
            problems.append(f"{rid}: hs2017_code must be 8 digits or null")
        if line.get("confidence") not in {"high", "medium", "low"}:
            problems.append(f"{rid}: confidence must be high, medium or low")

    # psr_rules.json
    psr = kb["psr"]
    checked = set(psr.get("metadata", {}).get("chapters_fully_checked", []))
    for g in psr.get("general_rules", []):
        if not g.get("id") or not g.get("text"):
            problems.append("general_rules: every entry needs id and text")
        _check_source_keys([g.get("source_key")], f"{g.get('id')}", sources, problems)

    seen_rule_ids = set()
    for rule in psr.get("rules", []):
        rid = rule.get("id", "<no id>")
        if rid in seen_rule_ids:
            problems.append(f"{rid}: duplicate id")
        seen_rule_ids.add(rid)

        scope = rule.get("scope", {})
        if scope.get("type") not in SCOPE_TYPES:
            problems.append(f"{rid}: scope.type must be one of {sorted(SCOPE_TYPES)}")
        if scope.get("type") == "chapter":
            ch = scope.get("chapter")
            if not _is_digits(ch, 2):
                problems.append(f"{rid}: scope.chapter must be 2 digits")
            elif ch not in checked:
                problems.append(f"{rid}: chapter {ch} not in chapters_fully_checked")

        if not rule.get("rule_text"):
            problems.append(f"{rid}: missing rule_text")
        alts = rule.get("alternatives")
        if not isinstance(alts, list) or not alts:
            problems.append(f"{rid}: alternatives must be a non-empty list")
        else:
            for a_i, alt in enumerate(alts):
                if not isinstance(alt, list) or not alt:
                    problems.append(f"{rid}: alternative {a_i} must be a non-empty list of tests")
                    continue
                for test in alt:
                    t = test.get("test")
                    if t not in PSR_TESTS:
                        problems.append(f"{rid}: unknown test {t!r}")
                    if t == "VA":
                        _check_pct(test.get("min_pct"), f"{rid} VA.min_pct", problems)
        _check_source_keys([rule.get("source_key")], rid, sources, problems)

    return problems