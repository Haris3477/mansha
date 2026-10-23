"""Offline tests for Step 7.6g (gap G39, problems 81-82): gaps carry a source, and code checks
QA's corrections against the KB before the Researcher sees them. Fake LLMs, no router.

1. Gaps: {text, source_id}; old plain strings read as source null; a gap citing a passage with
   KB notes is moved into `caveats` (or dropped when it repeats one); shape and ID checks.
2. KB shield replays: the 14 QA corrections from the live windows_nodata runs of 23 Oct
   (samples/qa_replays/), each with the result the shield must give.
3. Re-judge (Haris, 23 Oct, option iii, fallback i): every correction overruled -> one re-judge
   with the KB notes shown; still overruled -> OVERRULED; some kept -> REJECTED with those only.
4. Corrections name their record as a source_id to cite, never glued to the fix text.

Run: python -m scripts.test_kb_shield
"""

import copy
import json
import sys
from pathlib import Path

from mansha.evidence import build_evidence
from mansha.llm_client import LLMResult
from mansha.qa import (
    QA_APPROVED,
    QA_OVERRULED,
    QA_REJECTED,
    Part,
    _review,
    correction_text,
    kb_shield,
    rejudge_problems,
)
from mansha.researcher import (
    build_messages as researcher_messages,
    check_researcher,
    move_note_gaps,
    normalize_gaps,
    record_notes,
    run_researcher,
)
from scripts.pipeline_cases import DEV_INTAKES

FIXTURES = Path("samples/researcher_outputs")
REPLAYS = Path("samples/qa_replays/2026-10-23_windows_nodata.json")
failures: list[str] = []


def check(name: str, cond: bool, detail="") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def fixture(case: str) -> dict:
    return json.loads((FIXTURES / f"{case}.json").read_text(encoding="utf-8"))["output"]


intake, folder, _ = DEV_INTAKES["windows_nodata"]
pack = build_evidence(intake, folder)
notes = record_notes(pack)
LABOUR = next(n for n in notes["P-AGR-3.2.2-VA"] if "labour" in n)

# ---------------------------------------------------------------- 1
print("1. Gaps carry a source (Step 7.6g)")
check("record_notes reads each record's notes verbatim",
      LABOUR == "'Direct labour cost' and 'direct overhead cost' are not defined in the agreement."
      and len(notes["P-AGR-3.2.2-VA"]) == 2 and notes["P-UAE-ISSUER"][0].startswith("No official page"), notes.get("P-AGR-3.2.2-VA"))
check("tool records' notes are read too", "TOOL:duty:76101000" in notes)

d = {"gaps": ["Old plain gap.", {"text": "New gap.", "source_id": None}]}
ch = normalize_gaps(d)
check("plain-string gaps read as {text, source_id: null}, one change logged",
      d["gaps"] == [{"text": "Old plain gap.", "source_id": None}, {"text": "New gap.", "source_id": None}]
      and len(ch) == 1 and "gaps[0]" in ch[0], (d, ch))
check("nothing to normalize: no change", normalize_gaps({"gaps": [{"text": "x", "source_id": None}]}) == [])

base = fixture("windows_nodata")
issuer_caveats = [c for c in base["caveats"] if c["source_id"] == "P-UAE-ISSUER"]
d = copy.deepcopy(base)
d["caveats"] = [c for c in d["caveats"] if c["source_id"] != "P-AGR-3.2.2-VA"]  # no note from it yet
n_cav = len(d["caveats"])
d["gaps"] = [
    {"text": "The agreement does not define 'direct labour cost' and 'direct overhead cost' for the "
             "build-up method.", "source_id": "P-AGR-3.2.2-VA"},                       # 19:05 gaps[0]
    {"text": "No official source confirms that the Ministry of Foreign Trade is the issuing authority.",
     "source_id": "P-UAE-ISSUER"},                                                      # 19:05 gaps[1]
    {"text": "The shipment value is needed to estimate the saving.", "source_id": "TOOL:duty:76101000"},
    {"text": "Nothing in the evidence covers X.", "source_id": None},
    {"text": "Ex-Works basis lowers the threshold.", "source_id": "PSR-GEN-EXW"},       # a rule, no notes
]
ch = move_note_gaps(d, pack)
moved = d["caveats"][n_cav:]
check("a gap citing a passage with KB notes moves to caveats, with its source",
      len(moved) == 1 and moved[0]["source_id"] == "P-AGR-3.2.2-VA" and "direct labour cost" in moved[0]["note"],
      moved)
check("issuer gap when the issuer note exists: dropped (code writes that note from the KB)",
      issuer_caveats and not any("issuing authority" in g["text"] for g in d["gaps"])
      and any("dropped, already a note from P-UAE-ISSUER" in c for c in ch), ch)
check("gaps citing a tool result, no record, or a rule without notes stay gaps",
      [g["source_id"] for g in d["gaps"]] == ["TOOL:duty:76101000", None, "PSR-GEN-EXW"], d["gaps"])
check("each move and drop logged", len(ch) == 2 and ch[0].startswith("gaps[0]: moved to caveats[") , ch)

d2 = copy.deepcopy(base)
d2["caveats"].append({"note": LABOUR, "source_id": "P-AGR-3.2.2-VA"})
d2["gaps"] = [{"text": "Direct labour cost and direct overhead cost are not defined in the agreement.",
               "source_id": "P-AGR-3.2.2-VA"}]
n2 = len(d2["caveats"])
ch2 = move_note_gaps(d2, pack)
check("a gap repeating a same-source caveat is dropped, not duplicated",
      d2["gaps"] == [] and len(d2["caveats"]) == n2 and "dropped, already a note" in ch2[0], ch2)

d4 = copy.deepcopy(base)
d4["caveats"] = [c for c in d4["caveats"] if c["source_id"] != "P-AGR-3.2.2-VA"] + [
    {"note": LABOUR, "source_id": "P-AGR-3.2.2-VA"}]          # only the first of its two notes
d4["gaps"] = [{"text": "The agreement does not state whether the build-down and build-up methods use the "
                       "same threshold.", "source_id": "P-AGR-3.2.2-VA"}]  # the other note
ch4 = move_note_gaps(d4, pack)
check("same record, the OTHER note: moved, not dropped as a duplicate",
      d4["gaps"] == [] and d4["caveats"][-1]["note"].startswith("The agreement does not state whether")
      and "moved to caveats" in ch4[0], ch4)

d3 = copy.deepcopy(base)
d3["gaps"] = [{"text": "", "source_id": None}]
p3, _, _ = check_researcher(d3, pack)
check("a gap without text is a problem", any("`gaps[0]` must be an object with a `text`" in p for p in p3), p3)
d3["gaps"] = [{"text": "A gap.", "source_id": "P-NOT-THERE"}]
p3, _, _ = check_researcher(d3, pack)
check("a gap with an unknown source_id is a problem",
      any("gaps[0].source_id 'P-NOT-THERE' is not an ID in the evidence" in p for p in p3), p3)
d3["gaps"] = [{"text": "As P-MOET-COO-INDIA says, ...", "source_id": None}]
p3, _, _ = check_researcher(d3, pack)
check("a record ID in a gap's text is a problem (exporter text)",
      any(p.startswith("gaps[0].text contains 'P-MOET-COO-INDIA") for p in p3), p3)


def fake_llm(output):
    def llm(agent, chain, messages, **kwargs):
        return LLMResult(text=json.dumps(output), data=copy.deepcopy(output), routed_via="fake/long",
                         finish_reason="stop", latency_s=0.1, attempts=[{"attempt": 1, "ok": True}])
    return llm


out = copy.deepcopy(base)
out["caveats"] = [c for c in out["caveats"] if c["source_id"] != "P-AGR-3.2.2-VA"]
out["gaps"] = [{"text": "The agreement does not define 'direct labour cost' and 'direct overhead cost'.",
                "source_id": "[P-AGR-3.2.2-VA]"},
               "No official confirmation is available that a free-zone factory cannot obtain Factory "
               "Registration."]
res = run_researcher(intake, pack, llm=fake_llm(out))
check("run_researcher: bracketed gap ID fixed, note-gap moved, plain gap kept as source null; passes",
      res.passed and res.data["gaps"] == [{"text": out["gaps"][1], "source_id": None}]
      and any(c["source_id"] == "P-AGR-3.2.2-VA" and "direct labour" in c["note"] for c in res.data["caveats"])
      and any("moved to caveats" in c for c in res.changes) and any("square brackets" in c for c in res.changes),
      (res.problems, res.data["gaps"], res.changes))
sysmsg = researcher_messages(intake, pack)[0]["content"]
check("Researcher prompt: gap schema with source_id, notes go to caveats",
      '"gaps": [{ "text": "string", "source_id": "string | null" }]' in sysmsg
      and "A record's `notes`" in sysmsg and "put it in `source_id`, never in the text" in sysmsg)

# ---------------------------------------------------------------- 2
print("\n2. KB shield replays (14 live corrections, 23 Oct)")
replays = json.loads(REPLAYS.read_text(encoding="utf-8"))["cases"]
check("14 replay cases", len(replays) == 14, len(replays))
results = []
for c in replays:
    name, idx = c["field"].split(".")[0][:-1].split("[")
    research = {name: [None] * int(idx) + [c["item"]]}
    kept, over = kb_shield([c["correction"]], research, notes)
    got = "overruled" if over else "kept"
    results.append((c, got))
    check(f"{c['run'][9:15]} r{c['round']} {c['field']} ({c['kb_verdict']}): {c['expect']}",
          got == c["expect"], f"{got}: {c['why']}")
right_dropped = [c for c, g in results if c["kb_verdict"] == "right" and g == "overruled"]
wrong = [c for c, _ in results if c["kb_verdict"] == "wrong"]
wrong_caught = [c for c, g in results if c["kb_verdict"] == "wrong" and g == "overruled"]
check("no right correction overruled", not right_dropped, [c["field"] for c in right_dropped])
check("5 of the 6 wrong corrections overruled (incl. both 'MoFT confirmed' fixes)",
      len(wrong) == 6 and len(wrong_caught) == 5
      and sum("MoFT" in c["why"] or "Ministry of Foreign Trade" in c["correction"]["fix"] for c in wrong_caught) >= 2,
      (len(wrong), len(wrong_caught)))
o = kb_shield([replays[7]["correction"]], {"gaps": [None, replays[7]["item"]]}, notes)[1][0]
check("an overruled correction keeps its record and KB note", o["record"] == "P-UAE-ISSUER"
      and o["kb_note"].startswith("No official page"), o)
check("re-judge message quotes the KB note and the record",
      "P-UAE-ISSUER" in rejudge_problems([o])[0] and o["kb_note"] in rejudge_problems([o])[0])
check("a hedge the KB note does not carry is not shielded (QA may remove it)",
      kb_shield([{"field": "caveats[0].note", "problem": "p", "fix": "CEPA rates reduce BCD only.",
                  "source_id": None}],
                {"caveats": [{"note": "CEPA rates reportedly reduce BCD only.", "source_id": "TOOL:duty:76101000"}]},
                notes)[1] == [])

# ---------------------------------------------------------------- 3
print("\n3. Re-judge with the KB notes, then OVERRULED")
data = copy.deepcopy(base)
data["caveats"].append({"note": LABOUR, "source_id": "P-AGR-3.2.2-VA"})
k = len(data["caveats"]) - 1
BAD = {"field": f"caveats[{k}].note", "problem": "Not supported by any cited record.",
       "fix": "The cited records do not provide information on these costs.", "source_id": None}
GOOD = {"field": "follow_up_questions[0]", "problem": "Asks for something unrelated.",
        "fix": "Remove the question.", "source_id": None}


def answer(corrections=(), f=1, c=1):
    return {"warnings": [], "corrections": list(corrections),
            "scores": {"factuality": f, "completeness": c, "formatting_safety": 1}}


class Script:
    def __init__(self, *replies):
        self.replies, self.seen = list(replies), []

    def __call__(self, agent, chain, messages, **kwargs):
        self.seen.append(messages)
        r = self.replies.pop(0)
        return LLMResult(text=json.dumps(r), data=copy.deepcopy(r), routed_via="fake/judge",
                         finish_reason="stop", latency_s=0.1, attempts=[{"attempt": 1, "ok": True}])


whole = Part("whole review", None, [])
llm = Script(answer([BAD], f=0), answer())
q = _review(intake, pack, data, whole, llm)
check("every correction overruled -> re-judge; the judge then approves -> APPROVED",
      q.status == QA_APPROVED and q.rejudged and len(llm.seen) == 2 and len(q.overruled) == 1
      and q.corrections == [], (q.status, q.rejudged, len(llm.seen)))
check("the re-judge shows the KB note and asks to rescore",
      LABOUR in llm.seen[1][-1]["content"] and "P-AGR-3.2.2-VA" in llm.seen[1][-1]["content"])
llm = Script(answer([BAD], f=0), answer([BAD], f=0))
q = _review(intake, pack, data, whole, llm)
check("still overruled after the re-judge -> OVERRULED, nothing sent to the Researcher (option i)",
      q.status == QA_OVERRULED and q.corrections == [] and len(q.overruled) == 2 and len(llm.seen) == 2, q.status)
llm = Script(answer([BAD, GOOD], f=0, c=0))
q = _review(intake, pack, data, whole, llm)
check("some corrections kept -> REJECTED with those only, no re-judge",
      q.status == QA_REJECTED and q.corrections == [correction_text(GOOD)] and len(q.overruled) == 1
      and not q.rejudged and len(llm.seen) == 1 and q.raw_corrections == [GOOD], q.corrections)
invalid = {"warnings": [], "corrections": [], "scores": {"factuality": 2}}
llm = Script(invalid, answer([BAD], f=0), answer())
q = _review(intake, pack, data, whole, llm)
check("a format retry and a re-judge are separate: 3 calls, then APPROVED",
      q.status == QA_APPROVED and q.rejudged and len(llm.seen) == 3 and q.output_problems, (q.status, len(llm.seen)))
llm = Script(answer([BAD], f=0), answer([GOOD], c=0))
q = _review(intake, pack, data, whole, llm)
check("re-judge finds a real mistake instead -> REJECTED with the new correction",
      q.status == QA_REJECTED and q.corrections == [correction_text(GOOD)], q.corrections)

# ---------------------------------------------------------------- 4
print("\n4. Correction text")
t = correction_text({"field": "gaps[1].text", "problem": "p.", "fix": "f.", "source_id": "P-UAE-ISSUER"})
check("the record goes in its own sentence as a source_id, not '(see ID)' after the fix",
      t == "gaps[1].text: p. Fix: f. Cite P-UAE-ISSUER in source_id, not in the text." and "(see" not in t, t)
check("no record: nothing added", correction_text({"field": "x", "problem": "p.", "fix": "f.",
                                                   "source_id": None}) == "x: p. Fix: f.")

print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")
sys.exit(1 if failures else 0)
