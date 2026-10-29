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
PASSAGE_KINDS = {"origin_rule", "procedure", "authority", "duty"}
QUOTE_STATUSES = {"V", "B"}  # only display-safe quotes may be stored
ACTOR_KINDS = {"procedure", "authority"}  # passages that say who acts; code copies actor into steps


# Destinations Mansha has data for: the Intake's canonical English country name -> data/<folder>.
# A destination missing here is NOT_COVERED by Mansha. That says nothing about whether
# the UAE has a CEPA with that country (it has CEPAs Mansha doesn't cover yet).
CORRIDORS = {"India": "india"}
# Arabic names of the covered destinations, for code-written Arabic messages (29 Oct: the Intake's
# English name was printed inside Arabic text). «الهند» is the word the checklist step text already uses.
CORRIDOR_NAMES_AR = {"India": "الهند"}


class KBError(Exception):
    """Raised when knowledge-base files are missing or invalid."""


def corridor_for(destination: str | None) -> str | None:
    """The corridor folder for a destination country, or None if Mansha doesn't cover it."""
    if not destination:
        return None
    wanted = destination.strip().casefold()
    for country, folder in CORRIDORS.items():
        if country.casefold() == wanted:
            return folder
    return None


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
        "passages": _read_json(folder / "passages.json"),
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


def _check_note_lists(kb: dict, problems: list[str]) -> None:
    """`notes` are facts the exporter may read; `dev_notes` are for the team and never rendered."""
    records = (kb["tariff"].get("lines", []) + kb["tariff"].get("heading_exclusions", [])
               + kb["psr"].get("rules", []) + kb["psr"].get("general_rules", [])
               + kb["passages"].get("passages", []))
    for rec in records:
        rid = rec.get("id") or rec.get("heading") or rec.get("rule_text") or "?"
        for key in ("notes", "dev_notes"):
            value = rec.get(key)
            if value is not None and not (isinstance(value, list) and all(isinstance(n, str) for n in value)):
                problems.append(f"{rid}: `{key}` must be a list of strings")


def validate(kb: dict) -> list[str]:
    """Return a list of problems (empty list = valid)."""
    problems: list[str] = []
    sources = kb["sources"]
    _check_note_lists(kb, problems)

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

    # passages.json
    seen_passage_ids = set()
    for p in kb["passages"].get("passages", []):
        pid = p.get("id", "<no id>")
        if not str(pid).startswith("P-"):
            problems.append(f"{pid}: passage id must start with 'P-'")
        if pid in seen_passage_ids:
            problems.append(f"{pid}: duplicate id")
        seen_passage_ids.add(pid)

        if not p.get("title"):
            problems.append(f"{pid}: missing title")
        if p.get("kind") not in PASSAGE_KINDS:
            problems.append(f"{pid}: kind must be one of {sorted(PASSAGE_KINDS)}")
        tags = p.get("tags")
        if not isinstance(tags, list) or not tags or not all(isinstance(t, str) for t in tags):
            problems.append(f"{pid}: tags must be a non-empty list of strings")
        _check_source_keys(p.get("source_keys"), pid, sources, problems)
        if not p.get("summary"):
            problems.append(f"{pid}: missing summary")
        actor = p.get("actor")
        if p.get("kind") in ACTOR_KINDS:
            if not isinstance(actor, str) or not actor.strip():
                problems.append(f"{pid}: a {p.get('kind')} passage needs a non-empty actor")
        elif actor is not None:
            problems.append(f"{pid}: only procedure and authority passages may have an actor")

        for field in ("quotes", "items"):
            for q_i, q in enumerate(p.get(field, [])):
                if not q.get("text"):
                    problems.append(f"{pid} {field}[{q_i}]: missing text")
                if q.get("status") not in QUOTE_STATUSES:
                    problems.append(f"{pid} {field}[{q_i}]: status must be V or B (display-safe quotes only)")

        bands = (p.get("params") or {}).get("fee_bands_aed")
        if bands is not None:
            prev = 0
            for b_i, band in enumerate(bands):
                last = b_i == len(bands) - 1
                mx = band.get("max_aed")
                if last:
                    if mx is not None:
                        problems.append(f"{pid}: last fee band must have max_aed = null")
                elif not _is_number(mx) or mx <= prev:
                    problems.append(f"{pid}: fee band {b_i} max_aed must be a number above {prev}")
                else:
                    prev = mx
                fee = band.get("fee_aed")
                if not _is_number(fee) or fee < 0:
                    problems.append(f"{pid}: fee band {b_i} fee_aed must be a non-negative number")

    return problems