"""Offline tests for the QA Evaluator's code (Step 7.3): fake LLM, no router.

These test the MECHANICS: what QA is sent, how its answer is validated, how the status
is decided, the retry, and failures. Whether a real model judges well is tested live
in Step 7.4 (scripts/eval_qa.py, seeded mistakes).

Run: python -m scripts.test_qa
"""

import copy
import csv
import json
import sys
from pathlib import Path

from mansha.evidence import build_evidence
from mansha.llm_client import LLMCallError, LLMResult
from mansha.qa import (
    QA_APPROVED,
    QA_CHAIN,
    QA_ERROR,
    QA_REJECTED,
    build_messages,
    check_qa,
    correction_text,
    run_qa,
)
from mansha.researcher import ResearcherResult, number_keys
from scripts.pipeline_cases import DEV_INTAKES

FIXTURES = Path("samples/researcher_outputs")
failures: list[str] = []


def check(name: str, cond: bool, detail="") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def fixture(case: str) -> dict:
    return json.loads((FIXTURES / f"{case}.json").read_text(encoding="utf-8"))["output"]


class FakeLLM:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls: list[tuple[str, str, list[dict], dict]] = []

    def __call__(self, agent, chain, messages, **kwargs):
        self.calls.append((agent, chain, messages, kwargs))
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return LLMResult(text=json.dumps(r), data=copy.deepcopy(r), routed_via="fake/judge",
                         finish_reason="stop", latency_s=0.1, attempts=[{"attempt": 1, "ok": True}])


def answer(warnings=(), corrections=(), f=1, c=1, s=1, **extra):
    a = {"warnings": [{"id": w, "judgement": j, "reason": "r"} for w, j in warnings],
         "corrections": list(corrections),
         "scores": {"factuality": f, "completeness": c, "formatting_safety": s}}
    a.update(extra)
    return a


FIX = {"field": "follow_up_questions[0]", "problem": "Asks for a bill of materials already given.",
       "fix": "Remove the question.", "source_id": "TOOL:origin:85044030"}

intake, folder, _ = DEV_INTAKES["chargers"]
pack = build_evidence(intake, folder)
data = fixture("chargers")
data["follow_up_questions"] = ["Provide a bill of materials so the tests can be re-checked."]  # problem 55
WARNS = ["origin_result: number(s) ['3', '4'] not found in TOOL:origin:85044030",
         "procedure[0]: names 'Ministry of Economy', which P-X does not"]
research = ResearcherResult(data=data, problems=[], warnings=list(WARNS))

# ---------------------------------------------------------------- 1
print("1. What QA is sent")
msgs = build_messages(intake, pack, data, WARNS)
system, user = msgs[0]["content"], msgs[1]["content"]
check("system prompt: shared rules + the QA prompt",
      "You are one component of Mansha" in system and "You judge MEANING" in system)
check("warnings numbered W1, W2", f"W1: {WARNS[0]}" in user and f"W2: {WARNS[1]}" in user)
check("no warnings -> 'none'", "CODE WARNINGS:\nnone" in build_messages(intake, pack, data, [])[1]["content"])
check("compact evidence, not the full block", "=== CHOSEN LINE: TOOL RESULTS ===" in user
      and "=== TOOL RESULTS PER CANDIDATE ===" not in user)
check("Researcher JSON without code-filled verdict", '"verdict"' not in user.split("RESEARCHER JSON:")[1])
check("the intake is included", '"product_description": "battery chargers"' in user)
rows = list(csv.DictReader((Path(folder) / "bom.csv").open(encoding="utf-8")))
everything = system + user
check("no supplier name in QA's prompt", not [r for r in rows if r["supplier"].split(" (")[0] in everything])
check("no individual input value in QA's prompt",
      not ({v for r in rows for v in number_keys(r["value"])} & number_keys(everything)))

# ---------------------------------------------------------------- 2
print("\n2. Validation of QA's answer (check_qa)")
ok_reject = answer([("W1", "NOISE"), ("W2", "REAL")], [FIX], f=0, c=0)
check("a valid rejection passes", check_qa(ok_reject, data, WARNS, pack.allowed_ids) == [],
      check_qa(ok_reject, data, WARNS, pack.allowed_ids))
check("a valid approval passes",
      check_qa(answer([("W1", "NOISE"), ("W2", "NOISE")]), data, WARNS, pack.allowed_ids) == [])


def problems_for(a, warns=WARNS):
    return check_qa(a, data, warns, pack.allowed_ids)


def caught(name, a, needle, warns=WARNS):
    p = problems_for(a, warns)
    check(f"caught: {name}", any(needle in x for x in p), p)


caught("score 2", answer([("W1", "NOISE"), ("W2", "NOISE")], f=2), "must be 0 or 1")
caught("missing metric", {**answer([("W1", "NOISE"), ("W2", "NOISE")]), "scores": {"factuality": 1}},
       "exactly these keys")
caught("a warning not judged", answer([("W1", "NOISE")]), "missing W2")
caught("a warning judged twice", answer([("W1", "NOISE"), ("W1", "NOISE"), ("W2", "NOISE")]), "twice")
caught("unknown warning id", answer([("W1", "NOISE"), ("W2", "NOISE"), ("W9", "NOISE")]), "unknown id")
caught("judgement not REAL/NOISE", answer([("W1", "MAYBE"), ("W2", "NOISE")]), "REAL or NOISE")
caught("warnings judged when there are none", answer([("W1", "NOISE")]), "unknown id", warns=[])
caught("score 0 without a correction", answer([("W1", "NOISE"), ("W2", "NOISE")], c=0), "needs at least one")
caught("corrections with every score 1", answer([("W1", "NOISE"), ("W2", "NOISE")], [FIX]), "every score is 1")
caught("REAL warning with factuality 1", answer([("W1", "REAL"), ("W2", "NOISE")], [FIX], c=0),
       "factuality must be 0")
caught("field that does not exist", answer([("W1", "NOISE"), ("W2", "NOISE")],
       [{**FIX, "field": "summary"}], c=0), "not a field")
caught("index out of range", answer([("W1", "NOISE"), ("W2", "NOISE")],
       [{**FIX, "field": "procedure[3].step"}], c=0), "does not exist")
caught("source_id not in the evidence", answer([("W1", "NOISE"), ("W2", "NOISE")],
       [{**FIX, "source_id": "P-MADE-UP"}], c=0), "not an evidence ID")
caught("correction without a fix", answer([("W1", "NOISE"), ("W2", "NOISE")], [{**FIX, "fix": ""}], c=0),
       "needs a `fix`")
check("field forms accepted: 'classification', 'caveats', 'origin_result.basis'",
      problems_for(answer([("W1", "NOISE"), ("W2", "NOISE")],
                          [{**FIX, "field": f} for f in ("classification", "caveats", "origin_result.basis")],
                          f=0)) == [])
check("source_id null accepted", problems_for(answer([("W1", "NOISE"), ("W2", "NOISE")],
                                                      [{**FIX, "source_id": None}], c=0)) == [])

# ---------------------------------------------------------------- 3
print("\n3. run_qa: status, corrections, retry, failures")
llm = FakeLLM(ok_reject)
q = run_qa(intake, pack, research, llm=llm)
check("chain is auto:judge, JSON with required keys", llm.calls[0][1] == QA_CHAIN == "auto:judge"
      and llm.calls[0][3]["expect_json"] and set(llm.calls[0][3]["required_keys"]) ==
      {"warnings", "corrections", "scores"})
check("any 0 -> REJECTED (decided by code)", q.status == QA_REJECTED and q.scores == {
      "factuality": 0, "completeness": 0, "formatting_safety": 1})
check("correction for the Researcher: field, problem, fix and source",
      q.corrections == [correction_text(FIX)] and q.corrections[0] ==
      "follow_up_questions[0]: Asks for a bill of materials already given. Fix: Remove the question. "
      "(see TOOL:origin:85044030)", q.corrections)
check("judgements keep the warning text", q.judgements[1] == {
      "id": "W2", "warning": WARNS[1], "judgement": "REAL", "reason": "r"}, q.judgements)
check("note says what happened", q.note.startswith("REJECTED | factuality 0") and "2 (1 real)" in q.note)

q = run_qa(intake, pack, research,
           llm=FakeLLM(answer([("W1", "NOISE"), ("W2", "NOISE")], status="REJECTED")))
check("all 1 -> APPROVED, whatever 'status' the model writes", q.status == QA_APPROVED and not q.corrections)

bad = answer([("W1", "NOISE")])          # W2 not judged
llm = FakeLLM(bad, answer([("W1", "NOISE"), ("W2", "NOISE")]))
q = run_qa(intake, pack, research, llm=llm)
retry = llm.calls[1][2]
check("invalid answer -> one retry with the problems listed", len(llm.calls) == 2
      and retry[-2]["role"] == "assistant" and "missing W2" in retry[-1]["content"])
check("retry fixes it: APPROVED, both calls kept, first problems logged", q.status == QA_APPROVED
      and len(q.llm_calls) == 2 and any("missing W2" in p for p in q.output_problems))

q = run_qa(intake, pack, research, llm=FakeLLM(bad, bad))
check("still invalid after the retry -> ERROR (not reviewed), never APPROVED",
      q.status == QA_ERROR and "NOT reviewed" in q.note
      and any(p.startswith("after retry:") for p in q.output_problems))

err = LLMCallError("router down", [{"attempt": 1, "ok": False, "problem": "HTTP 502"}])
q = run_qa(intake, pack, research, llm=FakeLLM(err))
check("call fails -> ERROR with its attempts", q.status == QA_ERROR and q.failed_attempts == err.attempts
      and "NOT reviewed" in q.note)

q = run_qa(intake, pack, ResearcherResult(data=fixture("plastic"), problems=[], warnings=[]),
           llm=FakeLLM(answer()))
check("no code warnings: approval with an empty warnings list", q.status == QA_APPROVED and q.judgements == [])
check("the Researcher JSON is not changed by QA", research.data["verdict"] == "NOT_ELIGIBLE")

print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")
sys.exit(1 if failures else 0)
