"""Offline tests for the Builder prose check (Step 7.6): fake LLM, no router.

Run: python -m scripts.test_prose_qa
Checks: what the judge is sent (exactly the Builder's input, never mandatory notes, IDs or
bill-of-materials data), validation of its answer (each rule with a break test), status by
code, the retry, ERROR paths, the one-call size guard, that plan B's split code is never
used, the live-evaluation fixtures and seeds, and scripts/eval_prose_qa.py with fakes.
"""

import ast
import copy
import csv
import json
import sys
import tempfile
from pathlib import Path

import mansha.prose_qa as pq
import mansha.qa as qa_module
from mansha.document_builder import build_facts, check_prose
from mansha.llm_client import LLMCallError, LLMResult
from mansha.prose_qa import (
    ANSWER_BUDGET,
    PROSE_QA_CHAIN,
    build_messages,
    check_prose_qa,
    estimate_tokens,
    review_prose,
    sent_note_ids,
)
from mansha.researcher import EVIDENCE_ID_RE, number_keys
from scripts import eval_prose_qa as ev

TMP = Path(tempfile.mkdtemp(prefix="mansha_prose_qa_"))
failures: list[str] = []


def check(name: str, cond: bool, detail="") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def case_input(base: str):
    fx = ev.fixture(base)
    facts, notes = build_facts(fx["research"], fx["intake"])
    return facts, notes, copy.deepcopy(fx["prose"])


def fake_llm(*replies):
    """Returns the given dicts in order (or raises a given exception); records every call."""
    queue = list(replies)
    seen: list[dict] = []

    def llm(agent, chain, messages, **kwargs):
        seen.append({"agent": agent, "chain": chain, "messages": messages, **kwargs})
        r = queue.pop(0)
        if callable(r):
            r = r(messages)
        if isinstance(r, Exception):
            raise r
        return LLMResult(text=json.dumps(r), data=copy.deepcopy(r), routed_via="fake/judge",
                         finish_reason="stop", latency_s=0.2,
                         attempts=[{"attempt": 1, "ok": True, "routed_via": "fake/judge"}])
    llm.seen = seen
    return llm


APPROVE = {"corrections": [], "scores": {"factuality": 1, "completeness": 1}}
REJECT = {"corrections": [{"field": "notes[0].text", "problem": "'cannot obtain' drops 'likely'.",
                           "fix": "Say a producer in a free zone is likely not eligible.", "based_on": "N1"}],
          "scores": {"factuality": 0, "completeness": 1}}

facts, notes, prose = case_input("windows")

# ---------------------------------------------------------------- 1
print("\n1. What the judge is sent")
msgs = build_messages(facts, prose)
user = msgs[1]["content"]
check("system prompt: shared rules + the prose check's section",
      msgs[0]["content"].startswith("- You are one component of Mansha")
      and "You check the text that the Document Builder wrote" in msgs[0]["content"])
check("user message: the Builder's input exactly, then its JSON",
      user.startswith(facts + "\n\nBUILDER JSON:\n") and json.loads(user.split("BUILDER JSON:\n", 1)[1]) == prose)
mandatory = [n["text"] for n in notes if n["mandatory"]]
check("mandatory notes are never sent (the Builder never saw them)",
      mandatory and not any(t in user for t in mandatory), len(mandatory))
check("no evidence IDs in what is sent", not EVIDENCE_ID_RE.search(user),
      EVIDENCE_ID_RE.search(user) and EVIDENCE_ID_RE.search(user).group(0))
with Path("samples/windows_qualifies/bom.csv").open(encoding="utf-8") as fh:
    rows = list(csv.DictReader(fh))
check("no supplier name from the bill of materials",
      not any(r["supplier"].split(" (")[0] in user for r in rows))
check("no individual input value from the bill of materials",
      not ({v for r in rows for v in number_keys(r["value"])} & number_keys(user)))
retry = build_messages(facts, prose, previous=APPROVE, problems=["`scores` must have exactly these keys"])
check("retry: previous answer and its problems appended", len(retry) == 4
      and retry[2]["role"] == "assistant" and "Fix all of them" in retry[3]["content"])

print("\n   sent note numbers")
check("windows: N1", sent_note_ids(facts) == ["N1"], sent_note_ids(facts))
nd_facts = case_input("windows_nodata")[0]
check("windows_nodata: N1..N12", sent_note_ids(nd_facts) == [f"N{i}" for i in range(1, 13)],
      sent_note_ids(nd_facts))
check("no optional notes: none", sent_note_ids("FACTS:\nVERDICT: X\n\nNOTES: none (return an empty `notes` list)")
      == [])

# ---------------------------------------------------------------- 2
print("\n2. Validating the judge's answer (each rule with a break test)")
check("approve: valid", check_prose_qa(APPROVE, prose, ["N1"]) == [])
check("reject with a correction on notes[0].text: valid", check_prose_qa(REJECT, prose, ["N1"]) == [])


def expect(label, answer, needle):
    problems = check_prose_qa(answer, prose, ["N1"])
    check(label, any(needle in p for p in problems), problems)


def with_correction(**kw):
    a = copy.deepcopy(REJECT)
    a["corrections"][0].update(kw)
    return a


expect("missing score key", {"corrections": [], "scores": {"factuality": 1}}, "exactly these keys")
expect("extra metric (formatting_safety is code's job)",
       {"corrections": [], "scores": {"factuality": 1, "completeness": 1, "formatting_safety": 1}},
       "exactly these keys")
expect("score not 0/1", {"corrections": [], "scores": {"factuality": 2, "completeness": 1}}, "must be 0 or 1")
expect("corrections not a list", {"corrections": "none", "scores": APPROVE["scores"]}, "must be a list")
expect("field outside the prose", with_correction(field="verdict"), "must be one of")
expect("note index that does not exist", with_correction(field="notes[3].text"), "does not exist")
check("notes[0] without .text is accepted", check_prose_qa(with_correction(field="notes[0]"), prose, ["N1"]) == [])
check("summary accepted", check_prose_qa(with_correction(field="summary", based_on="FACTS"), prose, ["N1"]) == [])
expect("missing problem", with_correction(problem=" "), "needs a `problem`")
expect("missing fix", with_correction(fix=""), "needs a `fix`")
expect("based_on a note not sent", with_correction(based_on="N7"), "based_on 'N7'")
expect("based_on an evidence ID (the judge never saw them)", with_correction(based_on="P-UAE-ISSUER"),
       "based_on 'P-UAE-ISSUER'")
check("based_on null accepted", check_prose_qa(with_correction(based_on=None), prose, ["N1"]) == [])
expect("a 0 without corrections", {"corrections": [], "scores": {"factuality": 0, "completeness": 1}},
       "needs at least one correction")
expect("corrections with all scores 1", dict(copy.deepcopy(REJECT), scores=APPROVE["scores"]),
       "every score is 1")

# ---------------------------------------------------------------- 3
print("\n3. review_prose with a fake LLM")
llm = fake_llm(APPROVE)
q = review_prose(facts, prose, llm=llm)
check("approve -> APPROVED, scores kept", q.status == "APPROVED"
      and q.scores == {"factuality": 1, "completeness": 1} and not q.corrections)
c = llm.seen[0]
check("one call: agent prose_qa, chain auto:judge, 2,000-token budget, JSON expected",
      len(llm.seen) == 1 and c["agent"] == "prose_qa" and c["chain"] == PROSE_QA_CHAIN == "auto:judge"
      and c["max_tokens"] == ANSWER_BUDGET == 2000 and c["expect_json"], c.get("max_tokens"))
check("served_by recorded", q.llm.routed_via == "fake/judge" and q.seconds == 0.2)

q = review_prose(facts, prose, llm=fake_llm(REJECT))
check("reject -> REJECTED, status by code", q.status == "REJECTED" and q.scores["factuality"] == 0)
EXPECTED_TEXT = ("notes[0].text: 'cannot obtain' drops 'likely'. Fix: Say a producer in a free zone is likely "
                 "not eligible. (see N1)")
check("correction text for the Builder", q.corrections == [EXPECTED_TEXT], q.corrections)

q = review_prose(facts, prose, llm=fake_llm(dict(APPROVE, status="REJECTED")))
check("a status written by the model is ignored", q.status == "APPROVED")

bad = {"corrections": [], "scores": {"factuality": 0, "completeness": 1}}
llm = fake_llm(bad, REJECT)
q = review_prose(facts, prose, llm=llm)
check("invalid then valid: one retry, then REJECTED", len(llm.seen) == 2 and q.status == "REJECTED"
      and len(q.llm_calls) == 2)
check("retry lists the problems", "needs at least one correction" in llm.seen[1]["messages"][-1]["content"])
check("first answer's problems kept for the phase log", q.output_problems
      and "needs at least one correction" in q.output_problems[0])

llm = fake_llm(bad, bad)
q = review_prose(facts, prose, llm=llm)
check("invalid twice -> ERROR (NOT reviewed), no third call", q.status == "ERROR" and len(llm.seen) == 2
      and "NOT reviewed" in q.note and any(p.startswith("after retry:") for p in q.output_problems))

attempts = [{"attempt": 1, "ok": False, "problem": "HTTP 429 tpd-limit", "latency_s": 0.4}]
q = review_prose(facts, prose, llm=fake_llm(LLMCallError("daily cap", attempts)))
check("call fails -> ERROR with the attempts", q.status == "ERROR" and q.failed_attempts == attempts
      and "NOT reviewed" in q.note)

print("\n   size guard: one call or none, never a split")
old = pq.SIZE_LIMIT
pq.SIZE_LIMIT = 1000
llm = fake_llm(APPROVE)
q = review_prose(facts, prose, llm=llm)
pq.SIZE_LIMIT = old
check("too large -> ERROR without a call", q.status == "ERROR" and not llm.seen and "too large" in q.note, q.note)
sizes = {}
for base in ("windows", "chargers", "windows_nodata", "plastic"):
    f, _, p = case_input(base)
    sizes[base] = estimate_tokens(build_messages(f, p)) + ANSWER_BUDGET
check("every 17 Oct case fits one call with room to spare (< 6,000 of 7,600)",
      all(v < 6000 for v in sizes.values()), sizes)


def boom(*a, **k):
    raise AssertionError("plan B code used")


saved = (qa_module.plan_parts, qa_module._review, qa_module.build_messages)
qa_module.plan_parts = qa_module._review = qa_module.build_messages = boom
try:
    q = review_prose(nd_facts, case_input("windows_nodata")[2], llm=fake_llm(APPROVE))
    ok = q.status == "APPROVED"
except AssertionError:
    ok = False
qa_module.plan_parts, qa_module._review, qa_module.build_messages = saved
check("plan B's split code is never called (plan_parts, _review, build_messages patched to fail)", ok)
tree = ast.parse(Path(pq.__file__).read_text(encoding="utf-8"))
from_qa = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == "mansha.qa"
           for a in n.names}
check("from mansha.qa it imports only the chain name and status constants",
      from_qa == {"QA_CHAIN", "QA_APPROVED", "QA_REJECTED", "QA_ERROR"}, from_qa)

# ---------------------------------------------------------------- 4
print("\n4. Live-evaluation fixtures and seeds (samples/builder_outputs/)")
for base in ("windows", "chargers", "windows_nodata", "plastic"):
    fx = ev.fixture(base)
    f, n, p = case_input(base)
    check(f"clean {base}: passes the Builder's code checks", check_prose(p, f, n) == [], check_prose(p, f, n))
    check(f"clean {base}: read for meaning, edits recorded", fx.get("read_for_meaning")
          and isinstance(fx.get("edits"), list) and fx["source"].startswith("runs/pipeline/2026"))
check("clean windows: problem 57 fixed ('likely not eligible')",
      "likely not eligible" in ev.fixture("windows")["prose"]["notes"][0]["text"])
for case in ev.CASES:
    if not case.seed:
        continue
    f, n, seeded, problems = ev.prepare(case)
    clean = ev.fixture(case.base)["prose"]
    changed = [k for k in ("summary", "classification", "duty", "origin") if seeded[k] != clean[k]] + [
        f"notes[{i}]" for i, (a, b) in enumerate(zip(seeded["notes"], clean["notes"])) if a != b]
    check(f"seed {case.name}: invisible to the code checks", problems == [], problems)
    check(f"seed {case.name}: changes exactly its expected field", changed == list(case.fields), changed)

# ---------------------------------------------------------------- 5
print("\n5. scripts/eval_prose_qa.py with a fake judge")


def perfect_judge(messages):
    """Rejects a seed on the field its seed changed; approves clean prose."""
    sent = json.loads(messages[1]["content"].split("BUILDER JSON:\n", 1)[1])
    for case in ev.CASES:
        if case.seed and ev.prepare(case)[2] == sent:
            return {"corrections": [{"field": case.fields[0] + (".text" if case.fields[0].startswith("notes")
                                                                 else ""),
                                     "problem": "planted.", "fix": "fix it.", "based_on": "FACTS"}],
                    "scores": {"factuality": 0, "completeness": 1}}
    return APPROVE


def eval_llm(judge_fn):
    def llm(agent, chain, messages, **kwargs):
        return fake_llm(judge_fn)(agent, chain, messages, **kwargs)
    return llm


code = ev.main([], llm=eval_llm(perfect_judge), runs_root=TMP)
saved_files = sorted(p.name for d in TMP.iterdir() for p in d.iterdir())
check("a perfect judge: exit 0", code == 0, code)
check("one saved answer per case", len(saved_files) == len(ev.CASES), saved_files)
code = ev.main(["free_zone_cannot", "clean_plastic"], llm=eval_llm(lambda m: APPROVE), runs_root=TMP)
check("a judge that approves everything misses the seed: exit 1", code == 1, code)
code = ev.main(["clean_plastic"], llm=eval_llm(lambda m: REJECT), runs_root=TMP / "fr")
check("a false rejection: exit 1", code == 1, code)
calls = []
code = ev.main(["--dry-run"], llm=lambda *a, **k: calls.append(a), runs_root=TMP / "dry")
check("--dry-run: no call, nothing saved", code == 0 and not calls and not (TMP / "dry").exists())

print(f"\n(outputs in {TMP})")
print("\n" + ("ALL PASSED" if not failures else f"{len(failures)} FAILED: {failures}"))
sys.exit(1 if failures else 0)
