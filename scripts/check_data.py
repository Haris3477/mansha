"""Validate the knowledge-base files and print a summary.

Run from the project root:  python -m scripts.check_data
"""

import re
import sys

from mansha.kb import CORRIDORS, KBError, corridor_for, load_corridor


def check_corridors() -> list[str]:
    """Every registered corridor loads, and destination names map as expected."""
    problems = []
    for country, folder in CORRIDORS.items():
        try:
            load_corridor(folder)
        except KBError as e:
            problems.append(f"corridor {country} -> {folder}: {e}")
    expected = {"India": "india", " india ": "india", "INDIA": "india",
                "Türkiye": None, "Brazil": None, "": None, None: None}
    for destination, want in expected.items():
        got = corridor_for(destination)
        if got != want:
            problems.append(f"corridor_for({destination!r}) = {got!r}, expected {want!r}")
    return problems


# KB batch (27 Oct, item 4 + leftovers): notes printed word for word reach the exporter, so no raw
# "Inference:" or "Interpretation:" label;
# the reworded notes must keep a qualifier that check 10 (SOURCE_QUALIFIER_RE) and the KB shield
# (SHIELD_QUALIFIER_RE) both recognise, or a model dropping it would go unnoticed.
QUALIFIED_NOTES = {"P-MOET-FACTORY-REG": 1, "P-IN-DUTY-SCOPE": 2, "P-AGR-3.4-DEMINIMIS": 1}


def check_note_wording(kb: dict) -> list[str]:
    from mansha.qa import SHIELD_QUALIFIER_RE
    from mansha.researcher import SOURCE_QUALIFIER_RE
    problems = []
    by_id = {p["id"]: p for p in kb["passages"]["passages"]}
    for p in by_id.values():
        for text in [p.get("summary", "")] + p.get("notes", []):
            if re.search(r"\b(?:Inference|Interpretation):", text):
                problems.append(f"{p['id']}: raw 'Inference:'/'Interpretation:' label in {text[:60]!r}")
    for pid, n in QUALIFIED_NOTES.items():
        notes = by_id.get(pid, {}).get("notes", [])
        if len(notes) != n:
            problems.append(f"{pid}: expected {n} qualified note(s), found {len(notes)}")
        for note in notes:
            if not (SOURCE_QUALIFIER_RE.search(note) and SHIELD_QUALIFIER_RE.search(note)):
                problems.append(f"{pid}: note lost its qualifier: {note[:60]!r}")
    return problems


# Step shield (S3, 28 Oct): code prints each claim step's KB text word for word in the checklist, so every
# listed record has the text in English and Arabic, no evidence IDs, and no number its summary lacks
# (a later summary edit cannot leave a step stale unnoticed).
def check_steps(kb: dict, corridor: str = "india") -> list[str]:
    from mansha.researcher import CLAIM_STEPS, EVIDENCE_ID_RE, PROCEDURE_TOOL_IDS, number_keys
    problems = []
    by_id = {p["id"]: p for p in kb["passages"]["passages"]}
    for pid in CLAIM_STEPS[corridor]:
        if pid in PROCEDURE_TOOL_IDS:
            continue
        p = by_id.get(pid)
        if p is None:
            problems.append(f"{pid}: claim step record missing from passages")
            continue
        for lang in ("en", "ar"):
            text = (p.get("step") or {}).get(lang, "")
            if not text.strip():
                problems.append(f"{pid}: no {lang} step text")
                continue
            if EVIDENCE_ID_RE.search(text):
                problems.append(f"{pid}: evidence ID in the {lang} step text")
            extra = number_keys(text) - number_keys(p.get("summary", ""))
            if extra:
                problems.append(f"{pid}: {lang} step has number(s) {sorted(extra)} not in its summary")
    return problems


def main() -> int:
    try:
        kb = load_corridor("india")
    except KBError as e:
        print(f"FAILED\n{e}")
        return 1
    problems = check_corridors() + check_note_wording(kb) + check_steps(kb)
    if problems:
        print("FAILED\n- " + "\n- ".join(problems))
        return 1

    lines = kb["tariff"]["lines"]
    preferential = sum(1 for l in lines if l["cepa"]["status"] == "PREFERENTIAL")
    exclusions = [e["heading"] for e in kb["tariff"]["heading_exclusions"]]
    rules = kb["psr"]["rules"]

    print(f"sources:            {len(kb['sources'])}")
    print(f"tariff lines:       {len(lines)} ({preferential} preferential, {len(lines) - preferential} excluded)")
    print(f"heading exclusions: {', '.join(exclusions)}")
    print(f"PSR rules:          {len(rules)} (chapters {', '.join(r['scope']['chapter'] for r in rules)})")
    print(f"PSR general notes:  {len(kb['psr']['general_rules'])}")
    print(f"passages:           {len(kb['passages']['passages'])}")
    print(f"corridors:          {', '.join(f'{c} -> data/{f}' for c, f in CORRIDORS.items())}")
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())