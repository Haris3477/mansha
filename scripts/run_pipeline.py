"""Run the full Mansha pipeline live (Step 9.4). Needs the router running.

Run (from the project root):
    python -m scripts.run_pipeline                    # all 6 dev cases
    python -m scripts.run_pipeline windows chargers   # named dev cases
    python -m scripts.run_pipeline --message "We make ... and export to India." [--bom samples/windows_qualifies]

Each run is saved in runs/pipeline/<YYYYMMDD-HHMMSS>_<case>/ (message, intake, evidence,
researcher_N, qa_N, builder, report.md or notice.md, phase_log.json and phase_log.md).
Dev cases also check the status and verdict against the expected ones. Every report also
goes through the automatic report check (mansha/report_check.py); its problems are printed
and make the exit code 1, but they never replace reading the report.
"""

import argparse
import logging
import sys
import time
from pathlib import Path

from mansha.llm_client import call_llm
from mansha.orchestrator import run_pipeline
from scripts.pipeline_cases import PIPELINE_CASES

RUNS_ROOT = Path("runs/pipeline")


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s | %(message)s", datefmt="%H:%M:%S")
    for noisy in ("httpx", "httpx2", "openai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def run_one(name: str, message: str, folder: str | None, *, llm, runs_root: Path) -> dict:
    out = runs_root / f"{time.strftime('%Y%m%d-%H%M%S')}_{name}"
    print(f"\n{'=' * 70}\n{name}: {message}\n{'=' * 70}")
    res = run_pipeline(message, case_folder=folder, llm=llm, out_dir=out)
    print()
    for i, p in enumerate(res.phases, 1):
        print(f"  {i}. {p.name:<22} {p.status:<8} {p.seconds:>6.1f}s  {p.summary}")
    for w in res.warnings:
        print(f"  WARNING: {w}")
    print(f"  -> {res.status}{f' ({res.verdict})' if res.verdict else ''} in {res.seconds:.1f}s")
    print(f"  saved: {out}/  (read {'report.md' if res.status == 'REPORT' else 'notice.md'} "
          "and phase_log.md)")
    builder = next((p for p in res.phases if p.name == "Document Builder"), None)
    check = next((p for p in res.phases if p.name == "Report check"), None)
    if check:
        for x in check.problems:
            print(f"  REPORT CHECK problem: {x}")
        for x in check.warnings:
            print(f"  REPORT CHECK warning: {x}")
    return {"case": name, "status": res.status, "verdict": res.verdict, "seconds": res.seconds,
            "fallback": bool(builder and builder.status == "FALLBACK"), "out": out,
            "check": (len(check.problems), len(check.warnings)) if check else None}


def check_text(r: dict) -> str:
    if r["check"] is None:
        return "check -"
    p, w = r["check"]
    return f"check {p}P/{w}W"


def main(argv: list[str] | None = None, *, llm=call_llm, runs_root: Path = RUNS_ROOT) -> int:
    parser = argparse.ArgumentParser(description="Run the full Mansha pipeline.")
    parser.add_argument("cases", nargs="*", help=f"dev cases: {', '.join(PIPELINE_CASES)} (default: all)")
    parser.add_argument("--message", help="a free user message instead of the dev cases")
    parser.add_argument("--bom", help="folder with bom.csv and declaration.json (with --message)")
    args = parser.parse_args(argv)

    if args.message:
        if args.cases:
            parser.error("give either dev case names or --message, not both")
        r = run_one("msg", args.message, args.bom, llm=llm, runs_root=runs_root)
        return 1 if r["check"] and r["check"][0] else 0
    if args.bom:
        parser.error("--bom only works with --message (dev cases have their own folder)")

    names = args.cases or list(PIPELINE_CASES)
    unknown = [n for n in names if n not in PIPELINE_CASES]
    if unknown:
        parser.error(f"unknown case(s) {unknown}; choose from {list(PIPELINE_CASES)}")

    rows = []
    for name in names:
        message, folder, want_status, want_verdict = PIPELINE_CASES[name]
        r = run_one(name, message, folder, llm=llm, runs_root=runs_root)
        r["ok"] = r["status"] == want_status and r["verdict"] == want_verdict
        r["expected"] = want_status + (f" ({want_verdict})" if want_verdict else "")
        rows.append(r)

    print("\n================ SUMMARY ================")
    for r in rows:
        got = r["status"] + (f" ({r['verdict']})" if r["verdict"] else "")
        print(f"{'OK  ' if r['ok'] else 'FAIL'} {r['case']:<15} expected {r['expected']:<26} got {got:<26} "
              f"{r['seconds']:>6.1f}s  {check_text(r)}{'  [Builder fallback]' if r['fallback'] else ''}")
    print("\nOK/FAIL checks the status and verdict only; 'check NP/NW' is the automatic report check "
          "(problems/warnings, flag only).\nRead each report.md and phase_log.md before calling a run good.")
    flagged = any(r["check"] and r["check"][0] for r in rows)
    return 0 if all(r["ok"] for r in rows) and not flagged else 1


if __name__ == "__main__":
    setup_logging()
    sys.exit(main())
