"""Live evaluation of the Builder prose check alone (Step 7.6). Needs the router running.

Same idea as scripts/eval_qa.py, for the Document Builder's text: CLEAN Builder outputs
(the 4 live outputs of 17 Oct in samples/builder_outputs/, read for meaning, with the
mistakes found by reading fixed and recorded in each file's "edits") that the check should
approve, and SEEDED ones, each with ONE planted mistake taken from a real problem, that it
should reject with a correction on the right field. Every seed passes the Builder's code
checks (otherwise it would test code, not the judge). A miss and a false rejection both
count: a false rejection costs the Builder's only retry and can turn good prose into the
plain code-only report.

Run (from the project root):
    python -m scripts.eval_prose_qa --dry-run           # cases and token estimate, no calls
    python -m scripts.eval_prose_qa                     # every case once, on auto:judge
    python -m scripts.eval_prose_qa minimal_ops_completed clean_windows
    python -m scripts.eval_prose_qa --pause 30          # wait between calls (Groq: 8,000 tokens/min)
    python -m scripts.eval_prose_qa --chain trial       # a candidate model on a trial chain

Each answer is saved in runs/eval_prose_qa/<YYYYMMDD-HHMMSS>[_<chain>]/<case>_<n>.json.
Read the corrections, not just the result: a "false rejection" can be a real mistake.
Exit code 0 only if every seed is caught on its field and every clean case approved.
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
from mansha.document_builder import build_facts, check_prose
from mansha.prose_qa import (
    ANSWER_BUDGET,
    PROSE_QA_CHAIN,
    QA_APPROVED,
    QA_REJECTED,
    build_messages,
    estimate_tokens,
    review_prose,
)

FIXTURES = Path("samples/builder_outputs")
RUNS_ROOT = Path("runs/eval_prose_qa")
_sleep = time.sleep  # replaced in tests


def fixture(case: str) -> dict:
    return json.loads((FIXTURES / f"{case}.json").read_text(encoding="utf-8"))


def _replace(prose: dict, key: str, old: str, new: str) -> None:
    if prose[key].count(old) != 1:
        raise ValueError(f"seed text not found once in `{key}`: {old[:60]!r}")
    prose[key] = prose[key].replace(old, new)


# ---------- the seeds: one planted mistake each, from a real problem ----------

# Problem 57 ("likely not eligible" -> "cannot obtain", 17 Oct) had the seed free_zone_cannot. Since
# Step 7.6e a note with a qualifier ("likely") is printed verbatim by code and never sent to the
# Builder, so that mistake cannot be made any more; test_document_builder checks it instead.


def eliminates_duty(p):          # problem 53: wider than TERMS (the CEPA rate cuts Basic Customs Duty only)
    _replace(p, "summary", "so the CEPA rate can be claimed.",
             "so the CEPA rate can be claimed, which eliminates your customs duty in India.")


def minimal_ops_completed(p):    # problem 30: a passed check's meaning reversed
    _replace(p, "origin", "the minimal operations check passed because the work goes beyond simple operations",
             "the minimal operations were completed")


def claims_qualifies(p):         # contradicts the verdict (NEEDS_MORE_DATA said as qualifying)
    _replace(p, "summary",
             "Mansha cannot confirm whether the aluminium window frames qualify for the preferential duty rate "
             "under the India-UAE CEPA because the required information is missing.",
             "The aluminium window frames qualify for the preferential duty rate under the India-UAE CEPA; "
             "the information below is needed only to file the claim.")


def missing_failed_checks(p):    # completeness: a not-eligible origin text naming 2 of the 4 failed checks
    start = p["origin"].index(" The change in tariff heading check failed")
    p["origin"] = p["origin"][:start]


def note_beyond_from(p):         # a fact from another note (e-Sanchit, without "reportedly") in an item citing N2
    p["notes"][0]["text"] += " Electronic certificates are accepted and uploaded to India's e-Sanchit system."


@dataclass
class Case:
    name: str
    base: str                  # fixture in samples/builder_outputs/
    seed: object = None        # function that plants the mistake (None = clean)
    fields: tuple = ()         # correction fields that count as a catch (a ".text" suffix is fine)
    note: str = ""
    code_catches: bool = False  # 7.6b: the Builder's code checks stop this seed before any judge call


CASES = [
    Case("clean_windows", "windows", note="ELIGIBLE (no optional notes since 7.6e)"),
    Case("clean_chargers", "chargers", note="NOT_ELIGIBLE"),
    Case("clean_windows_nodata", "windows_nodata", note="NEEDS_MORE_DATA, 9 optional notes, 2 items"),
    Case("clean_plastic", "plastic", note="NO_PREFERENCE"),
    Case("eliminates_duty", "windows", eliminates_duty, ("summary",), "problem 53; blocked by code since 7.6b",
         code_catches=True),
    Case("minimal_ops_completed", "windows", minimal_ops_completed, ("origin",), "problem 30"),
    Case("claims_qualifies", "windows_nodata", claims_qualifies, ("summary",), "verdict contradicted"),
    Case("missing_failed_checks", "chargers", missing_failed_checks, ("origin",), "completeness"),
    Case("note_beyond_from", "windows_nodata", note_beyond_from, ("notes[0]",), "fact from another note"),
]
BY_NAME = {c.name: c for c in CASES}


def prepare(case: Case) -> tuple[str, list[dict], dict, list[str]]:
    """(facts_text, notes, prose, code problems) for a case.

    Code problems must be empty, except for a seed marked `code_catches`, which must have them."""
    fx = fixture(case.base)
    facts_text, notes = build_facts(fx["research"], fx["intake"])
    prose = copy.deepcopy(fx["prose"])
    if case.seed:
        case.seed(prose)
    return facts_text, notes, prose, check_prose(prose, facts_text, notes)


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


def setup_problem(case: Case, problems: list[str]) -> str | None:
    """Why a case cannot run as set up, or None. A seed tests the judge only if code lets it through;
    a `code_catches` seed tests that code stops it (and is never sent to the judge)."""
    if case.code_catches:
        return None if problems else "the Builder's code checks should stop this seed but don't"
    return f"code checks catch it: {problems}" if problems else None


def main(argv: list[str] | None = None, *, llm=lc.call_llm, runs_root: Path = RUNS_ROOT) -> int:
    parser = argparse.ArgumentParser(description="Evaluate the Builder prose check on clean and seeded cases.")
    parser.add_argument("cases", nargs="*", help=f"cases (default: all): {', '.join(BY_NAME)}")
    parser.add_argument("--chain", help="run the check on this chain instead of auto:judge (e.g. trial)")
    parser.add_argument("--repeat", type=int, default=1, help="runs per case (default 1)")
    parser.add_argument("--pause", type=float, default=0.0, help="seconds to wait between calls")
    parser.add_argument("--dry-run", action="store_true",
                        help="list the cases with their estimated tokens; no LLM call")
    args = parser.parse_args(argv)
    unknown = [n for n in args.cases if n not in BY_NAME]
    if unknown:
        parser.error(f"unknown case(s) {unknown}")
    cases = [BY_NAME[n] for n in args.cases] if args.cases else CASES

    chain = PROSE_QA_CHAIN
    if args.chain:
        chain = "auto:" + args.chain.removeprefix("auto:")
        if chain in ("auto:long", "auto:qa", "auto:auto"):
            parser.error(f"{args.chain!r}: the check must not run on a pipeline chain shared with other agents")
        lc.CHAIN_LIMITS.setdefault(chain, dict(lc.CHAIN_LIMITS[PROSE_QA_CHAIN]))

    if args.dry_run:
        total, calls = 0, 0
        print(f"{'case':<24} {'est. prompt':>11} {'+ budget':>9}  code check")
        for case in cases:
            facts_text, _, prose, problems = prepare(case)
            est = estimate_tokens(build_messages(facts_text, prose))
            bad = setup_problem(case, problems)
            if case.code_catches and not bad:
                print(f"{case.name:<24} {'-':>11} {'-':>9}  CAUGHT BY CODE (no call)")
                continue
            total += est * args.repeat
            calls += args.repeat
            print(f"{case.name:<24} {est:>11} {est + ANSWER_BUDGET:>9}  "
                  f"{'OK' if not bad else 'SETUP ERROR: ' + bad}")
        print(f"\n{calls} call(s), estimated prompt tokens {total} (Groq counted ~10% less on "
              "17 Oct), plus each answer's real length incl. hidden reasoning (~300-900, a guess).")
        return 0

    def qa_llm(agent, _chain, messages, **kwargs):
        return llm(agent, chain, messages, **kwargs)

    out = runs_root / (time.strftime("%Y%m%d-%H%M%S") + (f"_{chain.removeprefix('auto:')}" if args.chain else ""))
    out.mkdir(parents=True, exist_ok=True)
    print(f"Prose check on {chain}; answers saved in {out}/")
    rows = []
    for case in cases:
        facts_text, _, prose, problems = prepare(case)
        bad = setup_problem(case, problems)
        if bad:           # a seed must get past the code checks, or it tests code, not the judge
            print(f"  SETUP ERROR {case.name}: {bad}")
            rows.append((case, 0, "SETUP ERROR", None, 0.0))
            continue
        if case.code_catches:   # 7.6b: stopped by the Builder's code checks; no judge call
            rows.append((case, 1, "CAUGHT BY CODE", None, 0.0))
            (out / f"{case.name}_1.json").write_text(json.dumps({
                "case": case.name, "base": case.base, "note": case.note, "result": "CAUGHT BY CODE",
                "expected_fields": list(case.fields), "code_problems": problems,
                "prose_reviewed": prose}, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  {'CAUGHT BY CODE':<16} {case.name:<24} (no judge call)")
            for pr in problems:
                print(f"      - {pr[:160]}")
            continue
        est = estimate_tokens(build_messages(facts_text, prose))
        for n in range(1, args.repeat + 1):
            if args.pause and any(r[2] != "SETUP ERROR" for r in rows):
                _sleep(args.pause)
            t = time.monotonic()
            q = review_prose(facts_text, prose, llm=qa_llm)
            secs = round(time.monotonic() - t, 1)
            result = judge(case, q)
            who = q.llm.routed_via if q.llm else None
            rows.append((case, n, result, who, secs))
            (out / f"{case.name}_{n}.json").write_text(json.dumps({
                "case": case.name, "base": case.base, "note": case.note, "result": result,
                "expected_fields": list(case.fields), "status": q.status, "scores": q.scores,
                "corrections": q.corrections, "answer_problems": q.output_problems,
                "served_by": who, "seconds": secs, "estimated_prompt_tokens": est,
                "prose_reviewed": prose,
                "answers": [c.data for c in q.llm_calls],
                "attempts": [a for c in q.llm_calls for a in (c.attempts or [])] or q.failed_attempts,
                "qa_note": q.note}, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
            print(f"  {result:<16} {case.name:<24} #{n} {secs:>5}s  {who or '-'}  (~{est} tokens in)")
            for c in q.corrections:
                print(f"      - {c[:160]}")

    print("\n================ SUMMARY ================")
    seeded = [r for r in rows if r[0].seed]
    clean = [r for r in rows if not r[0].seed]
    by_code = sum(r[2] == "CAUGHT BY CODE" for r in seeded)
    judged = [r for r in seeded if r[2] != "CAUGHT BY CODE"]
    print(f"seeded caught by the judge:       {sum(r[2] == 'CAUGHT' for r in judged)}/{len(judged)}")
    print(f"seeded stopped by code (no call): {by_code}")
    print(f"clean approved:                   {sum(r[2] == 'APPROVED' for r in clean)}/{len(clean)}")
    print(f"errors (not reviewed):            {sum(r[2] in ('ERROR', 'SETUP ERROR') for r in rows)}")
    times = sorted(r[4] for r in rows if r[2] not in ("ERROR", "SETUP ERROR"))
    if times:
        print(f"time per check: median {times[len(times) // 2]}s, max {times[-1]}s")
    models = sorted({r[3] for r in rows if r[3]})
    print(f"served by: {', '.join(models) or '-'}")
    print("\nRead the saved answers before trusting these numbers: a false rejection may be a real catch.")
    return 0 if all(r[2] in GOOD for r in rows) else 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s | %(message)s", datefmt="%H:%M:%S")
    for noisy in ("httpx", "httpx2", "openai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    sys.exit(main())
