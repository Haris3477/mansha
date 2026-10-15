"""Live Document Builder runs on the 4 dev cases (Step 8.4). Needs the router running.

Run: python -m scripts.run_document_builder              # all 4 cases
     python -m scripts.run_document_builder windows      # one case
Reads the latest runs/<case>/researcher_N.json (from scripts.run_researcher),
rebuilds the evidence (pure code, for the source URLs), calls the Document Builder
and saves runs/<case>/report.md and runs/<case>/builder.json.
"""

import json
import logging
import sys
from pathlib import Path

from mansha.document_builder import run_document_builder
from mansha.evidence import build_evidence
from scripts.run_researcher import CASES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s | %(message)s", datefmt="%H:%M:%S")
for noisy in ("httpx", "httpx2", "openai"):
    logging.getLogger(noisy).setLevel(logging.WARNING)


def latest_research(folder: Path) -> tuple[Path, dict]:
    """The last Researcher round saved for this case (researcher_2.json beats researcher_1.json)."""
    files = sorted(folder.glob("researcher_*.json"))
    if not files:
        sys.exit(f"No researcher_*.json in {folder}. Run: python -m scripts.run_researcher {folder.name}")
    path = files[-1]
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("problems"):
        print(f"WARNING: {path} still has code-check problems; the report may carry them.")
    return path, record["output"]


def run_case(name: str) -> dict:
    intake, case_folder, _ = CASES[name]
    out = Path("runs") / name
    src, research = latest_research(out)
    pack = build_evidence(intake, case_folder)

    res = run_document_builder(research, intake, pack.id_sources)

    (out / "report.md").write_text(res.markdown, encoding="utf-8")
    calls = [{"served_by": c.routed_via, "latency_s": c.latency_s, "attempts": len(c.attempts)}
             for c in res.llm_calls]
    record = {"researcher_file": str(src), "calls": calls, "used_fallback": res.used_fallback,
              "problems_left": res.problems, "prose": res.prose, "notes": res.notes}
    (out / "builder.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n--- {name} ---")
    print(f"input     : {src}")
    for i, c in enumerate(calls, 1):
        print(f"call {i}    : {c['served_by']} ({c['latency_s']:.1f}s, {c['attempts']} attempt(s))")
    print(f"notes     : {len(res.notes)} in -> {len(res.prose.get('notes', []))} out "
          f"({sum(n['mandatory'] for n in res.notes)} mandatory)")
    print(f"fallback  : {'YES (code-only report)' if res.used_fallback else 'no'}")
    for p in res.problems:
        print(f"  left    : {p}")
    print(f"saved     : {out / 'report.md'}")
    return {"case": name, "verdict": research["verdict"], "calls": len(calls),
            "fallback": res.used_fallback,
            "served_by": calls[-1]["served_by"] if calls else "-"}


if __name__ == "__main__":
    names = sys.argv[1:] or list(CASES)
    unknown = [n for n in names if n not in CASES]
    if unknown:
        sys.exit(f"Unknown case(s): {unknown}. Choose from {list(CASES)}")

    results = [run_case(n) for n in names]
    print("\n================ SUMMARY ================")
    for r in results:
        status = "FALLBACK" if r["fallback"] else "OK      "
        print(f"{status} {r['case']:<15} verdict {r['verdict']:<16} calls {r['calls']}  by {r['served_by']}")