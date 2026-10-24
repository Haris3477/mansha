"""Live evaluation of the QA Evaluator alone (Step 7.4). Needs the router running.

Concept: an evaluation set for a judge. We feed QA Researcher outputs whose answer we
already know: CLEAN ones (the 4 saved outputs, read in Steps 8-9) that it should approve,
and SEEDED ones, each with ONE planted mistake taken from a real problem, that it should
reject with a correction on the right field. A miss and a false rejection both count:
a judge that rejects good work wastes the only revision and can turn a correct answer
into CHECKS_FAILED.

Run (from the project root):
    python -m scripts.eval_qa                      # every case once, on auto:judge
    python -m scripts.eval_qa --repeat 2           # twice (free models are not deterministic)
    python -m scripts.eval_qa --chain trial        # QA on a trial chain (one candidate model)
    python -m scripts.eval_qa merged_step clean_windows
    python -m scripts.eval_qa --chain trial --pause 65   # one call a minute (Groq: 8,000 tokens/min)

Each answer is saved in runs/eval_qa/<YYYYMMDD-HHMMSS>[_<chain>]/<case>_<n>.json. Read the
corrections and reasons, not just the score: a "false rejection" can be a real mistake
in a clean output, and a "catch" can be right for the wrong reason.
Exit code 0 only if every seeded case is caught on its field and every clean case approved.
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import mansha.llm_client as lc
from mansha.evidence import build_evidence
from mansha.qa import QA_APPROVED, QA_CHAIN, QA_REJECTED, build_messages, run_qa
from mansha.researcher import ResearcherResult, check_researcher
from scripts.pipeline_cases import DEV_INTAKES

FIXTURES = Path("samples/researcher_outputs")
RUNS_ROOT = Path("runs/eval_qa")
_sleep = time.sleep  # replaced in tests


def fixture(case: str) -> dict:
    return json.loads((FIXTURES / f"{case}.json").read_text(encoding="utf-8"))["output"]


# ---------- the seeds: one planted mistake each, from a real problem ----------

def flip_failed_check(d):      # problem 30: a check's meaning reversed
    d["origin_result"]["basis"] = d["origin_result"]["basis"].replace(
        "Final manufacture did not take place in the UAE.", "Final manufacture took place in the UAE.")


def merged_step(d):            # G8: a fact from another passage in a step (P-AGR-COO-RULES)
    d["procedure"][0]["step"] += " The certificate is then issued within five working days of export."


def dropped_qualifier(d):      # problem 6: "reportedly" dropped
    d["procedure"][5]["step"] = d["procedure"][5]["step"].replace("are reportedly uploaded", "are uploaded")


def invented_timeline(d):      # a number the record does not give (code warns; QA must judge it REAL)
    d["procedure"][1]["step"] += " Processing takes 14 working days."


def bom_already_given(d):      # problem 55: asks for a bill of materials the check already used
    d["follow_up_questions"] = [("Provide a bill of materials with the origin, HS code and value of each "
                                 "input so the origin tests can be re-checked.")]


def irrelevant_caveat(d):      # G12: a note that does not apply to this product
    d["caveats"].append({"note": "For products under HS 71 (such as gold jewellery), value addition is "
                                 "calculated on a different basis.", "source_id": "PSR-GEN-HS71"})


def useless_gap(d):            # 17 Oct 16:59 chargers run (Dots3): a gap that cannot change a failed result
    d["gaps"] = [{"text": ("The build-up value addition percentage is not available, so the value-addition "
                           "test could only be assessed using the build-down method."),
                  "source_id": None}]   # Step 7.6g: gaps are {text, source_id}


def nodata_dropped_qualifier(d):   # problem 6 inside a big (split) review
    note = d["caveats"][11]["note"]
    d["caveats"][11]["note"] = note.replace(
        "are reportedly accepted and uploaded to e-Sanchit (unconfirmed, seen only in secondary sources).",
        "are accepted and uploaded to e-Sanchit.")


def nodata_merged_step(d):     # G8 inside a big (split) review: a fact from P-AGR-3.17-APPLICATION
    d["procedure"][4]["step"] += " The issuing authority may also visit the factory before issuing it."


@dataclass
class Case:
    name: str
    base: str                  # DEV_INTAKES / fixture case
    seed: object = None        # function that plants the mistake (None = clean)
    fields: tuple = ()         # correction fields that count as a catch (a ".step"/".note" suffix is fine)
    note: str = ""
    code_catches: bool = False  # Step 7.8: the Researcher's code checks stop it; no QA call


CASES = [
    Case("clean_windows", "windows", note="ELIGIBLE, 7 steps"),
    Case("clean_chargers", "chargers", note="NOT_ELIGIBLE"),
    Case("clean_windows_nodata", "windows_nodata", note="NEEDS_MORE_DATA, 13 caveats"),
    Case("clean_plastic", "plastic", note="NO_PREFERENCE"),
    Case("flip_failed_check", "chargers", flip_failed_check, ("origin_result", "origin_result.basis"), "problem 30"),
    Case("merged_step", "windows", merged_step, ("procedure[0]", "procedure"), "G8"),
    Case("dropped_qualifier", "windows", dropped_qualifier, ("procedure[5]", "procedure"), "problem 6"),
    Case("invented_timeline", "windows", invented_timeline, ("procedure[1]", "procedure"), "code warning"),
    Case("bom_already_given", "chargers", bom_already_given, ("follow_up_questions", "follow_up_questions[0]"), "problem 55"),
    Case("irrelevant_caveat", "chargers", irrelevant_caveat, ("caveats", "caveats[6]"), "G12"),
    Case("useless_gap", "chargers", useless_gap, ("gaps", "gaps[0]"), "17 Oct live run"),
    Case("nodata_dropped_qualifier", "windows_nodata", nodata_dropped_qualifier,
         ("caveats[11]", "caveats"), "problem 6, split review; code since 7.8", code_catches=True),
    Case("nodata_merged_step", "windows_nodata", nodata_merged_step,
         ("procedure[4]", "procedure"), "G8, split review"),
]
BY_NAME = {c.name: c for c in CASES}


def prepare(case: Case):
    """(intake, pack, ResearcherResult) for a case: seeded data, warnings from the real code checks."""
    intake, folder, _ = DEV_INTAKES[case.base]
    pack = build_evidence(intake, folder)
    data = copy.deepcopy(fixture(case.base))
    if case.seed:
        case.seed(data)
    problems, warnings, verdict = check_researcher(copy.deepcopy(data), pack)
    data["verdict"] = verdict
    return intake, pack, ResearcherResult(data=data, problems=problems, warnings=warnings)


def judge(case: Case, q) -> str:
    """CAUGHT / WRONG FIELD / MISSED for seeds; APPROVED / FALSE REJECTION for clean; ERROR."""
    if q.status not in (QA_APPROVED, QA_REJECTED):
        return "ERROR"
    if case.seed is None:
        return "APPROVED" if q.status == QA_APPROVED else "FALSE REJECTION"
    if q.status == QA_APPROVED:
        return "MISSED"
    fields = [c.split(":", 1)[0].strip() for c in q.corrections]
    hit = any(f == want or f.startswith(want + ".") for f in fields for want in case.fields)
    return "CAUGHT" if hit else "WRONG FIELD"


GOOD = {"CAUGHT", "CAUGHT BY CODE", "APPROVED"}


def main(argv: list[str] | None = None, *, llm=lc.call_llm, runs_root: Path = RUNS_ROOT) -> int:
    parser = argparse.ArgumentParser(description="Evaluate the QA Evaluator on clean and seeded cases.")
    parser.add_argument("cases", nargs="*", help=f"cases (default: all): {', '.join(BY_NAME)}")
    parser.add_argument("--chain", help="run QA on this chain instead of auto:judge (e.g. trial)")
    parser.add_argument("--repeat", type=int, default=1, help="runs per case (default 1)")
    parser.add_argument("--pause", type=float, default=0.0,
                        help="seconds to wait between QA calls (Groq's free tier fits ~1 QA call a minute)")
    args = parser.parse_args(argv)
    unknown = [n for n in args.cases if n not in BY_NAME]
    if unknown:
        parser.error(f"unknown case(s) {unknown}")
    cases = [BY_NAME[n] for n in args.cases] if args.cases else CASES

    chain = QA_CHAIN
    if args.chain:
        chain = "auto:" + args.chain.removeprefix("auto:")
        if chain in ("auto:long", "auto:qa", "auto:auto"):
            parser.error(f"{args.chain!r}: QA must not run on a pipeline chain shared with other agents")
        # The trial chain gets QA's own budget, so the model is tested under the real limits.
        lc.CHAIN_LIMITS.setdefault(chain, dict(lc.CHAIN_LIMITS[QA_CHAIN]))

    def qa_llm(agent, _chain, messages, **kwargs):
        return llm(agent, chain, messages, **kwargs)

    out = runs_root / (time.strftime("%Y%m%d-%H%M%S") + (f"_{chain.removeprefix('auto:')}" if args.chain else ""))
    out.mkdir(parents=True, exist_ok=True)
    print(f"QA on {chain}; answers saved in {out}/")
    rows = []
    for case in cases:
        intake, pack, research = prepare(case)
        if case.code_catches:      # Step 7.8: the Researcher's code checks stop it; no QA call
            result = "CAUGHT BY CODE" if research.problems else "SETUP ERROR"
            rows.append((case, 1, result, None, 0.0))
            (out / f"{case.name}_1.json").write_text(json.dumps({
                "case": case.name, "base": case.base, "note": case.note, "result": result,
                "expected_fields": list(case.fields), "code_problems": research.problems},
                indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  {result:<16} {case.name:<22} (no QA call)")
            for pr in research.problems:
                print(f"      - {pr[:160]}")
            continue
        if research.problems:      # a seed must get past the code checks, or it tests code, not QA
            print(f"  SETUP ERROR {case.name}: code checks catch it: {research.problems}")
            rows.append((case, 0, "SETUP ERROR", None, 0.0))
            continue
        chars = sum(len(m["content"]) for m in build_messages(intake, pack, research.data, research.warnings))
        for n in range(1, args.repeat + 1):
            if args.pause and any(r[2] not in ("SETUP ERROR", "CAUGHT BY CODE") for r in rows):
                _sleep(args.pause)
            t = time.monotonic()
            q = run_qa(intake, pack, research, llm=qa_llm)
            secs = round(time.monotonic() - t, 1)
            result = judge(case, q)
            who = q.llm.routed_via if q.llm else None
            rows.append((case, n, result, who, secs))
            (out / f"{case.name}_{n}.json").write_text(json.dumps({
                "case": case.name, "base": case.base, "note": case.note, "result": result,
                "expected_fields": list(case.fields), "status": q.status, "scores": q.scores,
                "corrections": q.corrections, "warning_judgements": q.judgements,
                "code_warnings": research.warnings, "answer_problems": q.output_problems,
                "served_by": who, "seconds": secs, "prompt_chars": chars,
                "attempts": [a for c in q.llm_calls for a in (c.attempts or [])] or q.failed_attempts,
                "qa_note": q.note, "parts": q.parts}, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
            print(f"  {result:<16} {case.name:<22} #{n} {secs:>5}s  {who or '-'}  (~{chars // 4} tokens in)")
            for c in q.corrections:
                print(f"      - {c[:160]}")

    print("\n================ SUMMARY ================")
    seeded = [r for r in rows if r[0].seed]
    clean = [r for r in rows if not r[0].seed]
    judged = [r for r in seeded if r[2] != "CAUGHT BY CODE"]
    print(f"seeded caught on the right field: {sum(r[2] == 'CAUGHT' for r in judged)}/{len(judged)}")
    print(f"seeded stopped by code (no call): {len(seeded) - len(judged)}")
    print(f"clean approved:                   {sum(r[2] == 'APPROVED' for r in clean)}/{len(clean)}")
    print(f"errors (not reviewed):            {sum(r[2] in ('ERROR', 'SETUP ERROR') for r in rows)}")
    times = sorted(r[4] for r in rows if r[2] not in ("ERROR", "SETUP ERROR"))
    if times:
        print(f"time per QA call: median {times[len(times) // 2]}s, max {times[-1]}s")
    models = sorted({r[3] for r in rows if r[3]})
    print(f"served by: {', '.join(models) or '-'}")
    print("\nRead the saved answers before trusting these numbers: a false rejection may be a real catch.")
    return 0 if all(r[2] in GOOD for r in rows) else 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s | %(message)s", datefmt="%H:%M:%S")
    for noisy in ("httpx", "httpx2", "openai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    sys.exit(main())
