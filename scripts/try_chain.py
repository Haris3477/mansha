"""Try a candidate router chain on the FULL pipeline, without touching the pipeline chains.

Use it to test a new model before it goes into `long` (later: a paid model, G16), `qa` or
`judge` (the QA Evaluator's chain, Step 7).
1. In the FreeLLMAPI dashboard, create a chain (e.g. "trial") holding only the candidate model.
2. Run (router running):
     python -m scripts.try_chain trial                      # all 6 dev cases
     python -m scripts.try_chain trial windows chargers     # named dev cases
     python -m scripts.try_chain trial --message "..." [--bom samples/windows_qualifies]
     python -m scripts.try_chain trial --agents researcher  # only the Researcher on the trial chain
     python -m scripts.try_chain trial --agents qa          # only the QA Evaluator (Step 7.4)
By default the agents on `auto:long` (Researcher, Document Builder) use the trial chain; the
others keep their own chain. Everything else is scripts.run_pipeline: same cases, same report
check, same summary; runs are saved in runs/try_<chain>/<timestamp>_<case>/, apart from the
pipeline's own runs. Each switched agent keeps the token budget of its own chain (QA: 3000,
Researcher: 16000), so a model is tested under the limits it will really get.

Since Step 9.6c this runs the whole pipeline (it used to run the Builder alone on old
runs/<case>/researcher_N.json files): the Researcher is the slow, demanding call, so a new
model is judged on it too.
"""

import argparse
import sys
from pathlib import Path

import mansha.llm_client as lc
from scripts.run_pipeline import main as run_pipeline_main
from scripts.run_pipeline import setup_logging

LONG_AGENTS = ("researcher", "document_builder")


def main(argv: list[str] | None = None, *, llm=lc.call_llm, runs_root: Path = Path("runs")) -> int:
    parser = argparse.ArgumentParser(description="Run the pipeline with some agents on a trial chain.",
                                     epilog="Other arguments go to scripts.run_pipeline.")
    parser.add_argument("chain", help="the trial chain's name, e.g. trial (or auto:trial)")
    parser.add_argument("--agents", nargs="+", default=list(LONG_AGENTS),
                        help=f"agents switched to the trial chain (default: {' '.join(LONG_AGENTS)})")
    args, rest = parser.parse_known_args(argv)

    short = args.chain.removeprefix("auto:")
    chain = f"auto:{short}"
    if chain in ("auto:long", "auto:qa", "auto:judge", "auto:auto") or not short:
        parser.error(f"{args.chain!r} is a pipeline chain (or empty): give a separate trial chain")
    top = max(v["ceiling"] for v in lc.CHAIN_LIMITS.values())
    lc.CHAIN_LIMITS.setdefault(chain, {"default": top, "ceiling": top})

    def trial_llm(agent, pipeline_chain, messages, **kwargs):
        if agent not in args.agents:
            return llm(agent, pipeline_chain, messages, **kwargs)
        # The budget the agent gets on its own chain (QA must stay inside Groq's limits).
        kwargs.setdefault("max_tokens", lc.CHAIN_LIMITS[pipeline_chain]["default"])
        return llm(agent, chain, messages, **kwargs)

    print(f"Trial chain {chain} for: {', '.join(args.agents)}")
    return run_pipeline_main(rest, llm=trial_llm, runs_root=runs_root / f"try_{short}")


if __name__ == "__main__":
    setup_logging()
    sys.exit(main())
