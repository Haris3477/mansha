"""Validate the knowledge-base files and print a summary.

Run from the project root:  python -m scripts.check_data
"""

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


def main() -> int:
    try:
        kb = load_corridor("india")
    except KBError as e:
        print(f"FAILED\n{e}")
        return 1
    problems = check_corridors()
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