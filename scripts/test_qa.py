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
import tempfile
from pathlib import Path

import scripts.eval_qa as ev
from mansha.evidence import build_evidence
from mansha.llm_client import CHAIN_LIMITS, LLMCallError, LLMResult
from mansha.qa import (
    PART_BUDGET,
    PLAN_BUDGET,
    QA_APPROVED,
    QA_CHAIN,
    QA_ERROR,
    QA_REJECTED,
    SPLIT_LIMIT,
    build_messages,
    check_qa,
    correction_text,
    estimate_tokens,
    QA_SETTLED,
    QAOutcome,
    plan_parts,
    run_qa,
    settle_round_2,
)
from mansha.qa_evidence import item_keys
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
facts = user.split("CHECKED BY CODE (correct; never correct these):\n")[1].split("\n\nCODE WARNINGS")[0]
check("checked facts: verdict, origin status, rule, saving", "verdict: NOT_ELIGIBLE" in facts
      and "origin result status: DOES_NOT_QUALIFY" in facts and "CTH + VA 40%" in facts
      and "duty saving status: NOT_APPLICABLE" in facts, facts)
check("checked facts: what the user gave (value and bill of materials)",
      "shipment value 50000 AED" in facts and "bill of materials and declaration: GIVEN" in facts, facts)
ni, nf, _ = DEV_INTAKES["windows_nodata"]
nmsg = build_messages(ni, build_evidence(ni, nf), fixture("windows_nodata"), [])[1]["content"]
check("checked facts, nothing given: value and bill of materials NOT given",
      "shipment value: NOT given" in nmsg and "NOT given or incomplete" in nmsg)
check("code-verified fields not shown as JSON fields",
      '"estimated_saving"' not in user and '"origin_rule"' not in user)
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
for owned in ("estimated_saving", "estimated_saving.amount", "origin_result.status", "origin_rule.rule",
              "verdict"):
    caught(f"correction on code-checked {owned}", answer([("W1", "NOISE"), ("W2", "NOISE")],
           [{**FIX, "field": owned}], f=0), "checked by code")
check("origin_result.basis is still QA's to correct", problems_for(answer(
      [("W1", "NOISE"), ("W2", "NOISE")], [{**FIX, "field": "origin_result.basis"}], f=0)) == [])
caught("correction without a fix", answer([("W1", "NOISE"), ("W2", "NOISE")], [{**FIX, "fix": ""}], c=0),
       "needs a `fix`")
check("field forms accepted: 'classification', 'caveats', 'origin_result.basis'",
      problems_for(answer([("W1", "NOISE"), ("W2", "NOISE")],
                          [{**FIX, "field": f} for f in ("classification", "caveats", "origin_result.basis")],
                          f=0)) == [])
check("source_id null accepted", problems_for(answer([("W1", "NOISE"), ("W2", "NOISE")],
                                                      [{**FIX, "source_id": None}], c=0)) == [])
# Step 7.6j: the confidence is not QA's to correct; code-fixed sources get no "cite" advice.
LIVE_0359 = {"field": "classification.confidence", "problem": "Confidence level is not supported by any cited "
             "evidence.", "fix": "Remove the confidence field or set it to null.", "source_id": None}
caught("7.6j replay 03:59: correction on classification.confidence refused",
       answer([("W1", "NOISE"), ("W2", "NOISE")], [LIVE_0359], f=0), "own judgement")
check("7.6j: a correction on the classification itself is still allowed", problems_for(answer(
      [("W1", "NOISE"), ("W2", "NOISE")], [{**FIX, "field": "classification"}], f=0)) == [])
LIVE_0409 = {"field": "origin_result.basis", "problem": "The statement includes a 40% value-addition requirement.",
             "fix": "The origin check could not be completed because the required information was not provided.",
             "source_id": "TOOL:rule_lookup:76101000"}
t = correction_text(LIVE_0409)
check("7.6j replay 04:09: no 'cite the rule lookup' for origin_result; keep its source",
      "Cite" not in t and "TOOL:rule_lookup" not in t and t.endswith("Keep this field's source_id as it is."), t)
for f in ("classification", "tariff.mfn_rate", "origin_rule", "estimated_saving"):
    check(f"7.6j: no cite advice for {f}", "Cite" not in correction_text({**LIVE_0409, "field": f}))
LIVE_1556 = {"field": "follow_up_questions[0]",   # 27 Oct 15:56, N10 (Dots3 then returned an object)
             "problem": "Asks for HS codes for other non-originating inputs not required by the cited record",
             "fix": "Provide the 6-digit HS code for Emollients (BOM row 2) as required by the origin rule.",
             "source_id": "TOOL:origin:33049990"}
t = correction_text(LIVE_1556)
check("1c replay 15:56: no 'cite in source_id' for a follow-up; keep it a plain string",
      "Cite" not in t and "TOOL:origin" not in t and t.endswith("Keep it a plain string, with no source_id."), t)
check("1c: also without an index", "Cite" not in correction_text({**LIVE_1556, "field": "follow_up_questions"}))
check("7.6j: a note still gets its record to cite",
      correction_text({**LIVE_0409, "field": "caveats[0].note"}).endswith(
          "Cite TOOL:rule_lookup:76101000 in source_id, not in the text."))

# ---------------------------------------------------------------- 3
print("\n3. run_qa: status, corrections, retry, failures")
llm = FakeLLM(ok_reject)
q = run_qa(intake, pack, research, llm=llm)
check("chain is auto:judge, JSON with required keys", llm.calls[0][1] == QA_CHAIN == "auto:judge"
      and llm.calls[0][3]["expect_json"] and set(llm.calls[0][3]["required_keys"]) ==
      {"warnings", "corrections", "scores"})
check("any 0 -> REJECTED (decided by code)", q.status == QA_REJECTED and q.scores == {
      "factuality": 0, "completeness": 0, "formatting_safety": 1})
check("correction for the Researcher: field, problem, fix (a follow-up has no source to cite, 1c)",
      q.corrections == [correction_text(FIX)] and q.corrections[0] ==
      "follow_up_questions[0]: Asks for a bill of materials already given. Fix: Remove the question. "
      "Keep it a plain string, with no source_id.", q.corrections)
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


# ---------------------------------------------------------------- 4
print("\n4. The live evaluation script (scripts.eval_qa) with a fake LLM")
for case in ev.CASES:
    _, _, r = ev.prepare(case)
    base = fixture(case.base)
    if case.code_catches:   # Step 7.8: a full qualifier drop is now a Researcher code problem
        check(f"{case.name}: caught by the Researcher's code checks",
              any("plain fact" in x for x in r.problems), r.problems)
    else:
        check(f"{case.name}: gets past the code checks", r.problems == [], r.problems)
    if case.seed:
        changed = {k for k in base if base[k] != r.data.get(k)} - {"verdict"}
        check(f"{case.name}: the seed changed exactly one part", len(changed) == 1, changed)
check("invented_timeline: code warns, QA must judge it",
      ev.prepare(ev.BY_NAME["invented_timeline"])[2].warnings ==
      ["procedure[1]: number(s) ['14'] not found in P-MOET-COO-INDIA"])


def spy(reply_for):
    seen = []

    def llm(agent, chain, messages, **kwargs):
        seen.append((agent, chain, kwargs.get("max_tokens")))
        r = reply_for(messages)
        return LLMResult(text=json.dumps(r), data=r, routed_via="fake/judge", finish_reason="stop",
                         latency_s=0.1, attempts=[{"attempt": 1, "ok": True}])
    return llm, seen


def approve_all(messages):
    ids = [ln.split(":")[0] for ln in messages[1]["content"].split("CODE WARNINGS:\n")[1].splitlines()
           if ln.startswith("W")]
    return answer([(w, "NOISE") for w in ids])


tmp = Path(tempfile.mkdtemp(prefix="mansha_evalqa_"))
llm, seen = spy(approve_all)
code = ev.main([], llm=llm, runs_root=tmp)
saved = {f.name: json.loads(f.read_text()) for d in tmp.iterdir() for f in d.iterdir()}
check("approve-everything judge: exit 1", code == 1, code)
check("clean cases APPROVED, seeded MISSED (CAUGHT BY CODE where code stops it)", all(
      v["result"] == ("APPROVED" if k.startswith("clean_") else "CAUGHT BY CODE"
                      if ev.BY_NAME[k.rsplit("_", 1)[0]].code_catches else "MISSED") for k, v in saved.items()),
      {k: v["result"] for k, v in saved.items()})
check("one answer file per case", len(saved) == len(ev.CASES), sorted(saved))
check("QA ran on auto:judge", {c for _, c, _ in seen} == {"auto:judge"})


def rejects_field(field):
    def reply(messages):
        a = approve_all(messages)
        a["corrections"] = [{**FIX, "field": field, "source_id": None}]
        a["scores"]["factuality"] = 0
        a["warnings"] = [{**w, "judgement": "REAL"} for w in a["warnings"]]
        return a
    return reply


llm, seen = spy(rejects_field("procedure[0].step"))
code = ev.main(["merged_step", "--chain", "trial"], llm=llm, runs_root=tmp)
check("right field: CAUGHT, exit 0", code == 0, code)
check("--chain trial: QA on auto:trial with QA's 3000-token budget",
      seen and all(c == "auto:trial" for _, c, _ in seen))
check("trial chain budget = judge budget", CHAIN_LIMITS["auto:trial"]["default"] == 3000)
llm, _ = spy(rejects_field("procedure[3].step"))
check("wrong step rejected: WRONG FIELD, exit 1", ev.main(["merged_step"], llm=llm, runs_root=tmp) == 1)
llm, _ = spy(rejects_field("caveats[0].note"))
check("clean case rejected: FALSE REJECTION, exit 1", ev.main(["clean_plastic"], llm=llm, runs_root=tmp) == 1)
slept = []
ev._sleep = slept.append
llm, _ = spy(approve_all)
ev.main(["clean_plastic", "clean_chargers", "--pause", "65"], llm=llm, runs_root=tmp)
check("--pause: waits between calls, not before the first", slept == [65.0], slept)
try:
    ev.main(["--chain", "long"], llm=llm, runs_root=tmp)
    check("refuses QA on the long chain", False)
except SystemExit as e:
    check("refuses QA on the long chain", e.code == 2)


# ---------------------------------------------------------------- 5
print("\n5. Plan B: big reviews split into parts that fit Groq (8,000 tokens a minute)")
for name, want in (("clean_chargers", 1), ("clean_plastic", 1), ("clean_windows", 2),
                   ("clean_windows_nodata", 3)):
    pi, pp, pr = ev.prepare(ev.BY_NAME[name])
    parts = plan_parts(pi, pp, pr.data, pr.warnings)
    check(f"{name}: {want} part(s)", len(parts) == want, [p.label for p in parts])
    if want == 1:
        check(f"{name}: one call keeps the whole review and the chain budget",
              parts[0].scope is None and parts[0].max_tokens is None)
        continue
    sizes = [estimate_tokens(build_messages(pi, pp, pr.data, None, part=p)) for p in parts]
    check(f"{name}: every part planned to fit (prompt + {PLAN_BUDGET} <= {SPLIT_LIMIT})",
          all(x + PLAN_BUDGET <= SPLIT_LIMIT for x in sizes), sizes)
    check(f"{name}: every part sent with the {PART_BUDGET}-token answer budget (7.6h)",
          PART_BUDGET == 3000 and all(p.max_tokens == PART_BUDGET for p in parts),
          [p.max_tokens for p in parts])
    keys = [k for p in parts for k in p.scope]
    check(f"{name}: findings first, every step and note in exactly one part, in order",
          keys == ["findings"] + item_keys(pr.data), keys)
    first = build_messages(pi, pp, pr.data, None, part=parts[0])[1]["content"]
    last = build_messages(pi, pp, pr.data, None, part=parts[-1])[1]["content"]
    check(f"{name}: part 1 has the candidates and the findings",
          first.startswith("REVIEW PART 1/") and "=== CANDIDATE TARIFF LINES ===" in first
          and '"classification"' in first)
    check(f"{name}: a later part has only its items, their records and the basis as context",
          "=== CANDIDATE TARIFF LINES ===" not in last and '"origin_basis_for_context"' in last
          and '"classification"' not in last and all(f'"{k}"' in last for k in parts[-1].scope))

ti, tp, tr = ev.prepare(ev.BY_NAME["invented_timeline"])
tparts = plan_parts(ti, tp, tr.data, tr.warnings)
owner = [p for p in tparts if p.warnings]
check("a code warning goes to the part holding its field (procedure[1])",
      len(owner) == 1 and "procedure[1]" in owner[0].scope and owner[0].warnings[0][0] == "W1",
      [(p.label, p.warnings) for p in tparts])
wi, wp, wr = ev.prepare(ev.BY_NAME["clean_windows"])
wwarn = ["origin_result: number(s) ['3'] not found in TOOL:origin:76101000",
         "caveats[5]: number(s) ['9'] not found in P-MOET-FACTORY-REG"]
wparts = plan_parts(wi, wp, wr.data, wwarn)
check("warnings keep their global numbers: W1 (origin) in part 1, W2 (caveats[5]) where caveats[5] is",
      [w for w, _ in wparts[0].warnings] == ["W1"]
      and [w for p in wparts if "caveats[5]" in p.scope for w, _ in p.warnings][-1:] == ["W2"],
      [(p.label, p.warnings) for p in wparts])

later = wparts[-1]
item = next(k for k in later.scope if k != "findings")
judged_here = [(w, "NOISE") for w, _ in later.warnings]
ok = answer(judged_here, [{**FIX, "field": f"{item}.note" if item.startswith("caveats") else f"{item}.step",
                           "source_id": None}], c=0)
check("a part may correct its own items", check_qa(ok, wr.data, later.warnings, wp.allowed_ids,
                                                     allowed_fields=later.fields()) == [])
outside = answer(judged_here, [{**FIX, "field": "classification", "source_id": None}], f=0)
check("a part may not correct a field it does not show",
      any("not in this part" in x for x in check_qa(outside, wr.data, later.warnings, wp.allowed_ids,
                                                     allowed_fields=later.fields())))


def scripted(*replies):
    """A fake judge answering the parts in order."""
    queue = list(replies)

    def llm(agent, chain, messages, **kwargs):
        r = queue.pop(0)
        if isinstance(r, Exception):
            raise r
        return LLMResult(text=json.dumps(r), data=copy.deepcopy(r), routed_via="fake/judge",
                         finish_reason="stop", latency_s=0.1, attempts=[{"attempt": 1, "ok": True}])
    return llm


wres = ResearcherResult(data=wr.data, problems=[], warnings=[])
fix0 = {**FIX, "field": "procedure[0].step", "source_id": None}
q = run_qa(wi, wp, wres, llm=scripted(answer(), answer()))
check("merge: every part approves -> APPROVED, '2 parts' in the note, both parts logged",
      q.status == QA_APPROVED and "2 parts" in q.note and len(q.parts) == 2 and len(q.llm_calls) == 2, q.note)
q = run_qa(wi, wp, wres, llm=scripted(answer(corrections=[fix0], f=0), answer()))
check("merge: one part rejects -> REJECTED, its correction kept, lowest score wins",
      q.status == QA_REJECTED and q.corrections == [correction_text(fix0)] and q.scores["factuality"] == 0
      and q.scores["completeness"] == 1, (q.status, q.scores))
q = run_qa(wi, wp, wres, llm=scripted(err, answer()))
check("merge: a part fails, none rejects -> ERROR (NOT reviewed in full), attempts kept",
      q.status == QA_ERROR and "NOT reviewed by QA" in q.note and "part 1/2" in q.note
      and q.failed_attempts == err.attempts, q.note)
q = run_qa(wi, wp, wres, llm=scripted(err, answer(corrections=[{**FIX, "field": f"{item}.note"
                                                                 if item.startswith("caveats") else
                                                                 f"{item}.step", "source_id": None}],
                                                  c=0)))
check("merge: a part fails but another rejects -> REJECTED (a known mistake is still fixed)",
      q.status == QA_REJECTED and len(q.corrections) == 1, (q.status, q.corrections))


print("\n1d. Round 2: corrections on items round 1 passed and left unchanged are not counted")
R1 = {"origin_result": {"basis": "old basis"},
      "procedure": [{"step": "The importer: claims the rate.", "source_id": "P-IN-IMPORTER"},
                    {"step": "The exporter: keep origin records.", "source_id": "P-AGR-RECORDS-VERIFICATION"}],
      "caveats": [{"note": "n0", "source_id": "X"}, {"note": "n1", "source_id": "Y"}]}
R2 = copy.deepcopy(R1)
R2["origin_result"]["basis"] = "new basis"           # changed after round 1's correction
R2["caveats"] = R2["caveats"][1:]                    # n0 removed: n1 moved from caveats[1] to caveats[0]
SC = {"factuality": 0, "completeness": 1, "formatting_safety": 1}
def corr(f):
    return {"field": f, "problem": "p.", "fix": "f.", "source_id": None}
def q1(*fields, status=QA_REJECTED, parts=None):
    return QAOutcome(status, [], dict(SC), raw_corrections=[corr(f) for f in fields], parts=parts or [])
def q2(*fields):
    return QAOutcome(QA_REJECTED, ["x"] * len(fields), dict(SC), note="REJECTED",
                     raw_corrections=[corr(f) for f in fields])
q = settle_round_2(q2("procedure[1].step"), R2, R1, q1("origin_result.basis"))
check("unchanged step round 1 passed -> SETTLED, no corrections, note says so",
      q.status == QA_SETTLED and q.corrections == [] and len(q.settled) == 1 and "not counted" in q.note, q)
q = settle_round_2(q2("procedure[1].step", "origin_result.basis"), R2, R1, q1("origin_result.basis"))
check("a changed field still counts: REJECTED with 1 correction, 1 settled",
      q.status == QA_REJECTED and len(q.raw_corrections) == 1 and len(q.settled) == 1
      and q.corrections == [correction_text(corr("origin_result.basis"))], q)
q = settle_round_2(q2("caveats[0].note"), R2, R1, q1("origin_result.basis"))
check("list items matched by text, not position (caveats[1] -> caveats[0])", q.status == QA_SETTLED, q)
q = settle_round_2(q2("caveats[0].note"), R2, R1, q1("caveats[1].note"))
check("an item round 1 flagged (and the Researcher kept) still counts", q.status == QA_REJECTED and not q.settled, q)
q = settle_round_2(q2("procedure[1].step"), R2, R1, q1("origin_result.basis", status="ERROR"))
check("round 1 not reviewed (ERROR): nothing settled", q.status == QA_REJECTED and not q.settled)
q = settle_round_2(q2("procedure[1].step"), R2, R1,
                   q1("origin_result.basis", parts=[{"status": "REJECTED"}, {"status": "ERROR"}]))
check("round 1 with a part NOT reviewed: nothing settled", q.status == QA_REJECTED and not q.settled)
q = settle_round_2(q2("caveats"), R2, R1, q1("origin_result.basis"))
check("a correction on a whole list (something missing) still counts", q.status == QA_REJECTED and not q.settled)
q = settle_round_2(q2("procedure[1].step"), R2, R1, None)
check("no round 1 (first review): unchanged", q.status == QA_REJECTED and not q.settled)
appr = QAOutcome(QA_APPROVED, [], {"factuality": 1, "completeness": 1, "formatting_safety": 1})
check("an approved round 2 is left alone", settle_round_2(appr, R2, R1, q1()).status == QA_APPROVED)
# Replay 27 Oct 16:36 N10 (git-ignored run folder: skipped if absent)
N10 = Path("runs/eval_set/20261027-163642/N10_cosmetics_missing_hs")
if (N10 / "qa_2.json").exists():
    def saved_q(f):
        j = json.loads((N10 / f).read_text())
        return QAOutcome(j["status"], list(j["corrections"]), j["scores"], note=j["note"], parts=j["parts"],
                         raw_corrections=j["raw_corrections"], overruled=j["overruled_by_kb"])
    out = lambda f: json.loads((N10 / f).read_text())["output"]
    q = settle_round_2(saved_q("qa_2.json"), out("researcher_2.json"), out("researcher_1.json"), saved_q("qa_1.json"))
    check("replay N10 16:36: both round-2 step rejections settled -> SETTLED",
          q.status == QA_SETTLED and [c["field"] for c in q.settled] == ["procedure[7].step", "procedure[8].step"],
          (q.status, q.settled))
else:
    print("  SKIP  replay N10 16:36 (run folder not on this machine)")

print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")
sys.exit(1 if failures else 0)
