"""Try a candidate router chain on the Document Builder, without touching the pipeline chains.

Use it to test a new model before it goes into `long` (or later, a paid model).
1. In the FreeLLMAPI dashboard, create a chain (e.g. "trial") holding only the candidate model.
2. Run: python -m scripts.try_chain trial                 # all 4 dev cases
        python -m scripts.try_chain trial chargers        # one case
Reads the latest runs/<case>/researcher_N.json, like scripts.run_document_builder, and saves
runs/<case>/try_<chain>/report.md and builder.json. The pipeline's own reports are not touched.
The chain gets the same token budget as auto:long, in this process only.
"""

import json
import sys
from pathlib import Path

import mansha.llm_client as lc
from mansha.document_builder import run_document_builder
from mansha.evidence import build_evidence
from scripts.run_document_builder import latest_research  # also sets up logging
from scripts.run_researcher import CASES


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: python -m scripts.try_chain <chain-name> [case ...]")
    short = sys.argv[1].removeprefix("auto:")
    chain = f"auto:{short}"
    names = sys.argv[2:] or list(CASES)
    unknown = [n for n in names if n not in CASES]
    if unknown:
        sys.exit(f"Unknown case(s): {unknown}. Choose from {list(CASES)}")

    lc.CHAIN_LIMITS.setdefault(chain, dict(lc.CHAIN_LIMITS["auto:long"]))

    def llm(agent, _pipeline_chain, messages, **kwargs):
        return lc.call_llm(agent, chain, messages, **kwargs)

    rows = []
    for name in names:
        intake, case_folder, _ = CASES[name]
        src, research = latest_research(Path("runs") / name)
        pack = build_evidence(intake, case_folder)
        res = run_document_builder(research, intake, pack.id_sources, llm=llm)

        out = Path("runs") / name / f"try_{short}"
        out.mkdir(parents=True, exist_ok=True)
        (out / "report.md").write_text(res.markdown, encoding="utf-8")
        calls = [{"served_by": c.routed_via, "latency_s": c.latency_s, "attempts": c.attempts}
                 for c in res.llm_calls]
        record = {"chain": chain, "researcher_file": str(src), "calls": calls,
                  "used_fallback": res.used_fallback, "problems_left": res.problems,
                  "prose": res.prose, "notes": res.notes}
        (out / "builder.json").write_text(json.dumps(record, indent=2, ensure_ascii=False),
                                          encoding="utf-8")
        rows.append((name, research["verdict"], len(calls), res.used_fallback,
                     calls[-1]["served_by"] if calls else "-",
                     sum(c["latency_s"] for c in calls)))
        print(f"saved     : {out / 'report.md'}")

    print(f"\n================ {chain} ================")
    for name, verdict, n, fb, by, secs in rows:
        print(f"{'FALLBACK' if fb else 'OK      '} {name:<15} verdict {verdict:<16} "
              f"calls {n}  {secs:6.1f}s  by {by}")


if __name__ == "__main__":
    main()
