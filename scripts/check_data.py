"""Validate the knowledge-base files and print a summary.

Run from the project root:  python -m scripts.check_data
"""

import sys

from mansha.kb import KBError, load_corridor


def main() -> int:
    try:
        kb = load_corridor("india")
    except KBError as e:
        print(f"FAILED\n{e}")
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
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())