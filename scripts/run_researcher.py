"""Live Researcher runs on the 4 dev cases (Step 6.4). Needs the router running.

Run: python -m scripts.run_researcher              # all 4 cases
     python -m scripts.run_researcher windows      # one case
Saves runs/<case>/evidence.txt and researcher_1.json (+ researcher_2.json after a revision).
Intake JSONs are fixed here so this run tests the Researcher alone.
"""

import json
import logging
import sys
from pathlib import Path

from mansha.evidence import build_evidence
from mansha.llm_client import LLMCallError
from mansha.researcher import ResearcherResult, run_researcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s | %(message)s", datefmt="%H:%M:%S")
for noisy in ("httpx", "httpx2", "openai"):
    logging.getLogger(noisy).setLevel(logging.WARNING)


def intake(product, hs=None, role="manufacturer", processing=None, value=None):
    missing = [k for k, v in (("hs_code_given", hs), ("uae_processing", processing),
                              ("shipment_value", value)) if v is None]
    return {
        "product_description": product, "hs_code_given": hs, "destination_country": "India",
        "exporter_role": role, "uae_processing": processing, "shipment_value": value,
        "language": "en", "missing_fields": missing,
    }


AED_100K = {"amount": 100000, "currency": "AED"}
AED_50K = {"amount": 50000, "currency": "AED"}

# case name -> (intake JSON, case folder with bom.csv/declaration.json, expected verdict)
CASES = {
    "windows": (intake("aluminium window frames",
                       processing="cut and assembled from imported aluminium profiles", value=AED_100K),
                "samples/windows_qualifies", "ELIGIBLE"),
    "chargers": (intake("battery chargers", role="trader",
                        processing="repacked and relabelled only", value=AED_50K),
                 "samples/chargers_repacked", "NOT_ELIGIBLE"),
    "windows_nodata": (intake("aluminium window frames",
                              processing="cut and assembled from imported aluminium profiles"),
                       None, "NEEDS_MORE_DATA"),
    "plastic": (intake("plastic packing articles", hs="39239090", value=AED_50K),
                None, "NO_PREFERENCE"),
}


def save(path: Path, res: ResearcherResult) -> None:
    llm = res.llm
    record = {
        "served_by": llm.routed_via if llm else None,
        "latency_s": llm.latency_s if llm else None,
        "attempts": len(llm.attempts) if llm else None,
        "problems": res.problems,
        "warnings": res.warnings,
        "output": res.data,
    }
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def report(name: str, round_no: int, res: ResearcherResult) -> None:
    d = res.data
    print(f"\n--- {name}, round {round_no} ---")
    print(f"served by : {res.llm.routed_via} ({res.llm.latency_s:.1f}s, {len(res.llm.attempts)} attempt(s))")
    print(f"line      : {d['classification'].get('tariff_line')} "
          f"(confidence {d['classification'].get('confidence')})")
    print(f"origin    : {d['origin_result'].get('status')}   saving: {d['estimated_saving'].get('status')} "
          f"{d['estimated_saving'].get('amount') or ''} {d['estimated_saving'].get('currency') or ''}")
    print(f"verdict   : {d['verdict']}   procedure steps: {len(d['procedure'])}   "
          f"caveats: {len(d['caveats'])}   follow-ups: {len(d['follow_up_questions'])}")
    for p in res.problems:
        print(f"  PROBLEM : {p}")
    for w in res.warnings:
        print(f"  warning : {w}")


def run_case(name: str) -> dict:
    data, folder, expected = CASES[name]
    out = Path("runs") / name
    out.mkdir(parents=True, exist_ok=True)
    pack = build_evidence(data, folder)
    (out / "evidence.txt").write_text(pack.text, encoding="utf-8")

    try:
        res = run_researcher(data, pack)
        save(out / "researcher_1.json", res)
        report(name, 1, res)
        rounds = 1
        if res.problems:
            res = run_researcher(data, pack, previous=res.data, corrections=res.problems)
            save(out / "researcher_2.json", res)
            report(name, 2, res)
            rounds = 2
    except LLMCallError as exc:
        print(f"\n--- {name}: LLM call failed: {exc}")
        return {"case": name, "expected": expected, "got": "LLM_ERROR", "ok": False}

    got = res.data["verdict"]
    return {"case": name, "expected": expected, "got": got, "rounds": rounds,
            "problems": len(res.problems), "warnings": len(res.warnings),
            "served_by": res.llm.routed_via, "ok": res.passed and got == expected}


if __name__ == "__main__":
    names = sys.argv[1:] or list(CASES)
    unknown = [n for n in names if n not in CASES]
    if unknown:
        sys.exit(f"Unknown case(s): {unknown}. Choose from {list(CASES)}")

    results = [run_case(n) for n in names]
    print("\n================ SUMMARY ================")
    for r in results:
        print(f"{'OK  ' if r['ok'] else 'FAIL'} {r['case']:<15} expected {r['expected']:<16} "
              f"got {r['got']:<16} rounds {r.get('rounds', '-')}  problems {r.get('problems', '-')}  "
              f"warnings {r.get('warnings', '-')}  by {r.get('served_by', '-')}")