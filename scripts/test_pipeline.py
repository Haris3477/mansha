"""Offline tests for the orchestrator (Step 9.3): fake LLM, no router.

Run: python -m scripts.test_pipeline
The fake LLM answers each agent with saved outputs (samples/researcher_outputs/) or
canned JSON, so every path of run_pipeline() is checked in about a second:
statuses, stops, the shared revision, the QA slot, the Builder prose check (Step 7.6),
LLM failures, saved files, and
that nothing from a bill of materials (supplier names, input values) reaches an LLM
or a saved file.
"""

import copy
import csv
import json
import logging
import re
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from mansha.document_builder import (
    CONDITION_TEXT,
    build_facts,
    fallback_prose,
    max_llm_notes,
)
from mansha.llm_client import LLMCallError, LLMResult
from mansha.orchestrator import (
    MOFT_CEPA_URL,
    ProseQAOutcome,
    QAOutcome,
    builder_vs_prose_qa_warning,
    msg_destination_not_covered,
    msg_product_not_covered,
    qa_passthrough,
    render_phase_log,
    run_pipeline,
    same_model_warning,
)
from mansha.researcher import number_keys
from scripts import run_pipeline as runner
from scripts.pipeline_cases import DEV_INTAKES as INTAKES
from scripts.pipeline_cases import PIPELINE_CASES
from scripts.run_pipeline import main as runner_main
from scripts.try_chain import main as try_chain_main

logging.basicConfig(level=logging.WARNING)
FIXTURES = Path("samples/researcher_outputs")
TMP = Path(tempfile.mkdtemp(prefix="mansha_pipeline_"))
failures: list[str] = []


def check(name: str, cond: bool, detail="") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def research_fixture(case: str) -> dict:
    return json.loads((FIXTURES / f"{case}.json").read_text(encoding="utf-8"))["output"]


def builder_prose(case: str) -> dict:
    """Prose that passes the Builder's checks (code fallback text, notes cut to the limit)."""
    research = research_fixture(case)
    _, notes = build_facts(research, INTAKES[case][0])
    prose = fallback_prose(research, notes)
    prose["notes"] = prose["notes"][:max_llm_notes(notes)]
    return prose


NULL_INTAKE = {"product_description": None, "hs_code_given": None, "destination_country": None,
               "exporter_role": None, "uae_processing": None, "shipment_value": None,
               "language": "en", "missing_fields": []}
EXTRA_INTAKES = {
    "vague": NULL_INTAKE,
    "brazil": dict(NULL_INTAKE, product_description="polyethylene shopping bags",
                   destination_country="Brazil", exporter_role="manufacturer"),
}


class FakeLLM:
    """Stands in for call_llm. Per agent, a queue of replies (dict, or an exception to raise)."""

    def __init__(self, **queues):
        self.queues = {k: list(v) for k, v in queues.items()}
        self.seen: list[tuple[str, list[dict]]] = []

    def __call__(self, agent, chain, messages, **kwargs):
        self.seen.append((agent, messages))
        r = self.queues[agent].pop(0)
        if callable(r):          # a reply built from the prompt (fake QA judging the warnings it got)
            r = r(messages)
        if isinstance(r, Exception):
            raise r
        return LLMResult(text=json.dumps(r), data=copy.deepcopy(r), routed_via=f"fake/{agent}",
                         finish_reason="stop", latency_s=0.1,
                         attempts=[{"attempt": 1, "chain": chain, "ok": True, "routed_via": f"fake/{agent}"}])

    def agents(self) -> list[str]:
        return [a for a, _ in self.seen]

    def sent_text(self) -> str:
        return "\n".join(m["content"] for _, msgs in self.seen for m in msgs)


def qa_approves(messages) -> dict:
    """A QA answer that approves and judges every code warning in the prompt as NOISE."""
    ids = re.findall(r"^(W\d+): ", messages[1]["content"], re.MULTILINE)
    return {"warnings": [{"id": w, "judgement": "NOISE", "reason": "fake"} for w in ids],
            "corrections": [], "scores": {"factuality": 1, "completeness": 1, "formatting_safety": 1}}


def qa_rejects(messages) -> dict:
    ans = qa_approves(messages)
    ans["corrections"] = [{"field": "follow_up_questions", "problem": "asks for data already given.",
                           "fix": "remove it.", "source_id": None}]
    ans["scores"]["completeness"] = 0
    return ans


PROSE_APPROVES = {"corrections": [], "scores": {"factuality": 1, "completeness": 1}}
PROSE_REJECTS = {"corrections": [{"field": "summary", "problem": "'eliminates your customs duty' is wider "
                                  "than the CEPA rate term.", "fix": "Say it cuts Basic Customs Duty only.",
                                  "based_on": "FACTS"}],
                 "scores": {"factuality": 0, "completeness": 1}}


def fake_for(case: str, **overrides) -> FakeLLM:
    queues = {"intake": [EXTRA_INTAKES.get(case) or INTAKES[case][0]]}
    if case in INTAKES:
        queues["researcher"] = [research_fixture(case)]
        queues["qa"] = [qa_approves] * 8   # windows splits into 2 QA parts, windows_nodata into 3
        queues["document_builder"] = [builder_prose(case)]
        queues["prose_qa"] = [PROSE_APPROVES] * 2   # Step 7.6: the Builder prose check, one per round
    queues.update(overrides)
    return FakeLLM(**queues)


def researcher_round2(llm: FakeLLM) -> str:
    """The last message of the Researcher's second call (its corrections)."""
    return [m for a, m in llm.seen if a == "researcher"][1][-1]["content"]


def run(case: str, llm: FakeLLM, **kwargs):
    message, folder, _, _ = PIPELINE_CASES[case]
    out = TMP / f"{case}_{len(list(TMP.iterdir()))}"
    return run_pipeline(message, case_folder=folder, llm=llm, out_dir=out, **kwargs)


def phase_names(res) -> list[str]:
    return [p.name for p in res.phases]


MISSING_PHASE = SimpleNamespace(name="(missing)", status="MISSING", summary="", calls=[], problems=[],
                                warnings=[], details={})


def phase(res, name: str):
    """The named phase, or a MISSING placeholder (so a missing phase fails a check, not the script)."""
    return next((p for p in res.phases if p.name == name), MISSING_PHASE)


ERR = LLMCallError("router down", [{"attempt": 1, "ok": False, "http_status": 502,
                                    "problem": "HTTP 502", "waited_before_retry_s": 30},
                                   {"attempt": 2, "ok": False, "problem": "empty reply"}])

# ---------------------------------------------------------------- 1
print("\n1. The six dev cases")
results = {}
for case, (_, _, status, verdict) in PIPELINE_CASES.items():
    llm = fake_for(case)
    res = run(case, llm)
    results[case] = (res, llm)
    check(f"{case}: status {status}", res.status == status, res.status)
    check(f"{case}: verdict {verdict}", res.verdict == verdict, res.verdict)

res, llm = results["windows"]
check("windows: phases in order", phase_names(res) == [
    "Intake", "Coverage check", "Tools + evidence", "Researcher (round 1)", "QA (round 1)",
    "Document Builder", "Prose QA (round 1)", "Report check"], phase_names(res))
check("windows: agents called intake -> researcher -> qa (2 parts) -> builder -> prose check",
      llm.agents() == ["intake", "researcher", "qa", "qa", "document_builder", "prose_qa"], llm.agents())
check("windows: QA split shown in phase_log.md (plan B)",
      "Review split into parts" in (res.out_dir / "phase_log.md").read_text()
      and "part 2/2: steps and notes: APPROVED" in (res.out_dir / "phase_log.md").read_text())
check("chargers: one QA call (fits Groq)", results["chargers"][1].agents().count("qa") == 1)
check("windows_nodata: three QA calls", results["windows_nodata"][1].agents().count("qa") == 3)
check("windows: QA approved by default (run_qa)", phase(res, "QA (round 1)").status == "OK"
      and phase(res, "QA (round 1)").summary.startswith("APPROVED"), phase(res, "QA (round 1)").summary)
check("windows: QA ran on the judge chain", "qa" in llm.agents())
check("windows: LLM prose used (no fallback)", phase(res, "Document Builder").status == "OK")
check("windows: prose check approved, on the judge chain (one call, no split)",
      phase(res, "Prose QA (round 1)").status == "OK" and llm.agents().count("prose_qa") == 1
      and "prose QA approved" in phase(res, "Document Builder").summary)
for case in ("chargers", "windows_nodata", "plastic"):
    check(f"{case}: one prose check, approved", results[case][1].agents().count("prose_qa") == 1
          and phase(results[case][0], "Prose QA (round 1)").status == "OK")
check("windows: every LLM phase records who served it",
      all(c.get("served_by") for p in res.phases for c in p.calls))
files = sorted(f.name for f in res.out_dir.iterdir())
check("windows: all phase files saved", files == sorted([
    "message.txt", "intake.json", "evidence.txt", "researcher_1.json", "qa_1.json",
    "builder.json", "prose_qa_1.json", "report.md", "phase_log.json", "phase_log.md"]), files)
check("windows: report.md is the report", (res.out_dir / "report.md").read_text() == res.output
      and res.output.startswith("#"))
# Problem 97 (fix round, 26 Oct): the origin tool's conditions reach the summary through the
# orchestrator, from the tool result itself (the windows fixture has no free-zone caveat at all).
fz_folder = TMP / "windows_freezone_case"
shutil.copytree(PIPELINE_CASES["windows"][1], fz_folder)
dec = json.loads((fz_folder / "declaration.json").read_text())
(fz_folder / "declaration.json").write_text(json.dumps(dict(dec, factory_in_free_zone=True)))
fz = run_pipeline(PIPELINE_CASES["windows"][0], case_folder=fz_folder, llm=fake_for("windows"),
                  out_dir=TMP / "windows_freezone_run")
fz_summary = fz.output.split("## Summary\n\n", 1)[1].split("\n## ", 1)[0]
check("free-zone factory: code caution in the summary (problem 97)",
      fz.verdict == "ELIGIBLE" and CONDITION_TEXT["FREE_ZONE"]["en"] in fz_summary, fz_summary[-200:])
check("free-zone factory: conditions in builder.json and the phase log",
      json.loads((fz.out_dir / "builder.json").read_text())["conditions"] == ["FREE_ZONE"]
      and "summary cautions (code): FREE_ZONE" in phase(fz, "Document Builder").summary,
      phase(fz, "Document Builder").summary)
check("windows (not in a free zone): no caution, conditions []",
      "Caution:" not in res.output
      and json.loads((res.out_dir / "builder.json").read_text())["conditions"] == [])

plog = json.loads((res.out_dir / "phase_log.json").read_text())
check("phase_log.json: status, verdict and 8 phases", plog["status"] == "REPORT"
      and plog["verdict"] == "ELIGIBLE" and len(plog["phases"]) == 8)
for case in ("windows", "chargers", "windows_nodata", "plastic"):
    rc = phase(results[case][0], "Report check")
    check(f"{case}: report check clean", rc.status == "OK" and not rc.problems and not rc.warnings,
          rc.problems + rc.warnings)
for case in ("vague", "brazil"):
    check(f"{case}: no report check for a stop", "Report check" not in phase_names(results[case][0]))

res, llm = results["windows_nodata"]
check("windows_nodata: no bill of materials noted", "bill of materials: not given" in res.phases[2].summary)

res, llm = results["vague"]
check("vague: only Intake called", llm.agents() == ["intake"])
check("vague: asks for product and destination", "What product" in res.output
      and "Which country" in res.output)
check("vague: notice.md, no report.md", (res.out_dir / "notice.md").exists()
      and not (res.out_dir / "report.md").exists())

res, llm = results["brazil"]
check("brazil: only Intake called", llm.agents() == ["intake"])
check("brazil: says Mansha doesn't cover it, not that there is no CEPA",
      "does not mean the UAE has no trade agreement with Brazil" in res.output
      and "no CEPA" not in res.output)
check("brazil: links the Ministry of Foreign Trade CEPA list", MOFT_CEPA_URL in res.output)

# ---------------------------------------------------------------- 2
print("\n2. Other stops")
msg = "We make quantum widgets in Dubai and want to export them to India."
llm = FakeLLM(intake=[dict(NULL_INTAKE, product_description="quantum widgets",
                           destination_country="India")])
res = run_pipeline(msg, llm=llm, out_dir=TMP / "widgets")
check("no matching tariff line: NOT_COVERED without calling the Researcher",
      res.status == "NOT_COVERED" and llm.agents() == ["intake"], (res.status, llm.agents()))
check("no matching tariff line: message names the product", '"quantum widgets"' in res.output)
check("no matching tariff line, no HS code: suggests giving one", "try again and include it" in res.output)
llm = FakeLLM(intake=[dict(NULL_INTAKE, product_description="quantum widgets", hs_code_given="99999999",
                           destination_country="India")])
res = run_pipeline(msg + " HS 99999999.", llm=llm)
check("HS code given but not loaded: names the code, doesn't ask for it again",
      res.status == "NOT_COVERED" and "(HS code 99999999)" in res.output
      and "try again" not in res.output and "Check the classification" in res.output, res.output)


# Arabic stop messages name countries and products in Arabic (29 Oct, PDF item 82): the Intake gives English
# names, which were printed inside the Arabic text.
LATIN_OUTSIDE = re.compile(r"[A-Za-z]")


def latin_outside_brackets(text: str) -> list[str]:
    """Latin letters left after removing bracketed parts and web addresses."""
    rest = re.sub(r"https?://\S+", "", re.sub(r"\([^)]*\)", "", text))
    return LATIN_OUTSIDE.findall(rest)


ar = msg_destination_not_covered("Türkiye", "ar")
check("ar, country not covered: covered list in Arabic (الهند), no 'India'", "إلى: الهند فقط" in ar and "India" not in ar, ar)
check("ar, country not covered: the country as «هذه الدولة (Türkiye)», agreement line names no country",
      "عن هذه الدولة (Türkiye)" in ar and "بين الإمارات وهذه الدولة." in ar, ar)
check("ar, country not covered: no English outside brackets and the link", not latin_outside_brackets(ar), ar)
for hs in ("94036000", None):
    ar = msg_product_not_covered("wooden doors", hs, "India", "ar")
    check(f"ar, product not covered (HS {hs}): «في الهند», product as «هذا المنتج (wooden doors…)»",
          "في الهند" in ar and "هذا المنتج (wooden doors" in ar and (hs is None or f"الرمز الجمركي {hs})" in ar), ar)
    check(f"ar, product not covered (HS {hs}): no English outside brackets", not latin_outside_brackets(ar.replace("(HS)", "")), ar)
check("en messages unchanged",
      msg_destination_not_covered("Türkiye", "en").startswith(
          "Mansha currently covers exports from the UAE to India only. It has no data for Türkiye, so it can't")
      and "trade agreement with Türkiye." in msg_destination_not_covered("Türkiye", "en")
      and msg_product_not_covered("wooden doors", "94036000", "India", "en").startswith(
          "Mansha's tariff data for India does not include a line matching \"wooden doors\" (HS code 94036000) yet"))
llm = FakeLLM(intake=[dict(NULL_INTAKE, product_description="polyethylene bags", destination_country="Türkiye",
                           language="ar")])
res = run_pipeline("نصنع أكياس البولي إيثيلين في عجمان ونريد تصديرها إلى تركيا.", llm=llm)
check("pipeline, Arabic Türkiye (S3): NOT_COVERED with the Arabic names",
      res.status == "NOT_COVERED" and "إلى: الهند فقط" in res.output and "(Türkiye)" in res.output, res.output)

llm = FakeLLM()
res = run_pipeline("   ", llm=llm)
check("empty message: NEEDS_INPUT, no LLM call", res.status == "NEEDS_INPUT" and not llm.seen)

llm = FakeLLM(intake=[dict(NULL_INTAKE, language="ar", destination_country="India")])
res = run_pipeline("أريد التصدير إلى الهند", llm=llm)
check("Arabic: asks in Arabic, only for the product", res.language == "ar"
      and "ما المنتج" in res.output and "إلى أي دولة" not in res.output)

# ---------------------------------------------------------------- 3
print("\n3. Researcher revision (code checks)")
bad = research_fixture("windows")
bad["origin_result"]["status"] = "DOES_NOT_QUALIFY"
llm = fake_for("windows", researcher=[bad, research_fixture("windows")])
res = run("windows", llm)
check("bad then good: REPORT after 2 rounds", res.status == "REPORT"
      and "Researcher (round 2)" in phase_names(res), phase_names(res))
sent = researcher_round2(llm)
check("round 2 receives the code corrections", "CORRECTIONS" in sent and "origin_result.status" in sent)
check("researcher_2.json and qa_2.json saved", (res.out_dir / "researcher_2.json").exists()
      and (res.out_dir / "qa_2.json").exists())

llm = fake_for("windows", researcher=[bad, bad])
res = run("windows", llm)
check("bad twice: CHECKS_FAILED", res.status == "CHECKS_FAILED", res.status)
check("bad twice: Builder never called", "document_builder" not in llm.agents())
check("bad twice: QA round 2 skipped", res.phases[-1].name == "QA (round 2)"
      and res.phases[-1].status == "SKIPPED")
check("bad twice: short notice, no report", "couldn't verify" in res.output
      and not (res.out_dir / "report.md").exists())

# ---------------------------------------------------------------- 4
print("\n4. The QA slot")
res = run("windows", fake_for("windows"), qa=qa_passthrough, prose_qa=None)   # no QA of any kind
qa_phase = res.phases[4]
check("pass-through: QA SKIPPED, not APPROVED", qa_phase.status == "SKIPPED"
      and "NOT reviewed by QA" in qa_phase.summary)
check("pass-through: nothing in the phase log says APPROVED",
      "APPROVED" not in (res.out_dir / "phase_log.json").read_text())

warn = research_fixture("windows")
# a number not in the cited record -> warning (S3: steps are code's; O1: origin-tool notes too, and D1 drops
# caveat 4, the rule lookup's copy of the origin tool's '+' note; so caveat 1, the duty estimate note, carries it)
o1 = research_fixture("windows")
o1["caveats"][3]["note"] += " It costs AED 777."
res = run("windows", fake_for("windows", researcher=[o1]), qa=qa_passthrough)
check("O1: a number added to an origin-tool note is gone (code writes the note), no warning",
      "777" not in (res.out_dir / "researcher_1.json").read_text().split('"output"')[1]
      and not any("not reviewed by QA" in w for w in res.warnings), res.warnings)
warn["caveats"][1]["note"] += " It costs AED 777."
res = run("windows", fake_for("windows", researcher=[warn]), qa=qa_passthrough)
check("code warnings with QA skipped: pipeline warns they were not reviewed",
      any("not reviewed by QA" in w for w in res.warnings), res.warnings)

print("\n4b. The real QA Evaluator (run_qa) with a fake LLM")
llm = fake_for("windows", researcher=[warn])
res = run("windows", llm)
qp = phase(res, "QA (round 1)")
qa_msgs = [m[1][1]["content"] for m in llm.seen if m[0] == "qa"]
check("code warning sent to QA as W1", any("W1: caveats[1]: number(s) ['777']" in m for m in qa_msgs),
      [m[:300] for m in qa_msgs])
check("QA judged it: shown in the phase log", "Code warnings judged by QA:" in
      (res.out_dir / "phase_log.md").read_text() and qp.details["warning_judgements"][0]["id"] == "W1")
check("judged warnings: no 'not reviewed' warning", not any("not reviewed" in w for w in res.warnings),
      res.warnings)
saved = json.loads((res.out_dir / "qa_1.json").read_text())
check("qa_1.json holds the judgements and the call", saved["warning_judgements"]
      and saved["calls"] and saved["served_by"] == "fake/qa")

llm = fake_for("windows", researcher=[research_fixture("windows")] * 2,
               qa=[qa_rejects, qa_approves, qa_approves, qa_approves])
res = run("windows", llm)
check("QA rejects: phase REJECTED, revision, then REPORT", phase(res, "QA (round 1)").status == "REJECTED"
      and phase(res, "QA (round 2)").status == "OK" and res.status == "REPORT", phase_names(res))
check("QA's correction reaches the Researcher", "QA: follow_up_questions: asks for data already given."
      in researcher_round2(llm))

llm = fake_for("windows", qa=[ERR, qa_approves])
res = run("windows", llm)
check("QA call fails: run goes on to a REPORT (D5 A)", res.status == "REPORT"
      and "document_builder" in llm.agents())
check("QA call fails: phase FAILED, attempts kept", phase(res, "QA (round 1)").status == "FAILED"
      and any(c.get("attempts") == ERR.attempts for c in phase(res, "QA (round 1)").calls))
check("QA call fails: pipeline warns NOT reviewed", any("NOT reviewed by QA" in w for w in res.warnings),
      res.warnings)

llm = fake_for("windows", qa=[{"warnings": [], "corrections": [], "scores": {"factuality": 2}}] * 2
               + [qa_approves])
res = run("windows", llm)
check("QA answer invalid twice: ERROR, run goes on, problems logged", res.status == "REPORT"
      and phase(res, "QA (round 1)").status == "FAILED"
      and phase(res, "QA (round 1)").details.get("qa_answer_problems"), phase(res, "QA (round 1)"))


def qa_script(*outcomes):
    queue = list(outcomes)

    def qa(intake, pack, research, *, llm):
        return queue.pop(0)
    return qa


def qa_llm(model):
    return LLMResult(text="{}", data={}, routed_via=model, finish_reason="stop", latency_s=0.1)


rejected = QAOutcome("REJECTED", ["classification not justified by the description"],
                     {"factuality": 0, "completeness": 1, "formatting_safety": 1}, qa_llm("fake/qa"))
approved = QAOutcome("APPROVED", [], {"factuality": 1, "completeness": 1, "formatting_safety": 1},
                     qa_llm("fake/qa"))
llm = fake_for("windows", researcher=[research_fixture("windows")] * 2)
res = run("windows", llm, qa=qa_script(rejected, approved))
check("QA rejects then approves: REPORT after the revision", res.status == "REPORT"
      and "Researcher (round 2)" in phase_names(res))
check("QA corrections go to the Researcher", "QA: classification not justified"
      in llm.seen[2][1][-1]["content"])
check("QA phase OK after approval", phase(res, "QA (round 2)").status == "OK")

llm = fake_for("windows", researcher=[research_fixture("windows")] * 2)
res = run("windows", llm, qa=qa_script(rejected, rejected))
check("QA rejects twice: CHECKS_FAILED", res.status == "CHECKS_FAILED"
      and "document_builder" not in llm.agents())

# 1d (27 Oct, N10 16:36): round 2 may not reject an item round 1 reviewed without a correction and that
# is unchanged since; a correction on an item round 1 flagged still counts
CLS = {"field": "classification", "problem": "classification not justified", "fix": "f.", "source_id": None}
STEP0 = {"field": "procedure[0].step", "problem": "says 'keep', not 'must keep'", "fix": "f.", "source_id": None}
rej1 = QAOutcome("REJECTED", ["c"], {"factuality": 0, "completeness": 1, "formatting_safety": 1},
                 qa_llm("fake/qa"), raw_corrections=[CLS])
llm = fake_for("windows", researcher=[research_fixture("windows")] * 2)
res = run("windows", llm, qa=qa_script(rej1, QAOutcome("REJECTED", ["c"], dict(rej1.scores), qa_llm("fake/qa"),
                                                       note="REJECTED", raw_corrections=[STEP0])))
qa2 = phase(res, "QA (round 2)")
check("1d: round 2 rejects only an unchanged step round 1 passed -> SETTLED, REPORT",
      res.status == "REPORT" and qa2.status == "SETTLED", (res.status, qa2.status))
check("1d: pipeline warning and phase log name the settled correction",
      any("not counted" in w and "procedure[0].step" in w for w in res.warnings)
      and "QA round-2 corrections not counted" in (res.out_dir / "phase_log.md").read_text(),
      res.warnings)
llm = fake_for("windows", researcher=[research_fixture("windows")] * 2)
res = run("windows", llm, qa=qa_script(rej1, QAOutcome("REJECTED", ["c"], dict(rej1.scores), qa_llm("fake/qa"),
                                                       raw_corrections=[CLS])))
check("1d: round 2 on an item round 1 flagged still counts -> CHECKS_FAILED", res.status == "CHECKS_FAILED", res.status)

overruled = QAOutcome("OVERRULED", [], {"factuality": 0, "completeness": 1, "formatting_safety": 1},
                      qa_llm("fake/qa"), note="OVERRULED | 1 correction(s) overruled by the KB, after a re-judge",
                      overruled=[{"field": "caveats[3].note", "problem": "p", "fix": "f", "source_id": None,
                                  "record": "P-AGR-3.2.2-VA", "kb_note": "'Direct labour cost' ... not defined"}],
                      rejudged=True)
llm = fake_for("windows")
res = run("windows", llm, qa=qa_script(overruled))
qa1 = phase(res, "QA (round 1)")
check("Step 7.6g: QA OVERRULED by the KB -> no revision, REPORT, phase OVERRULED",
      res.status == "REPORT" and "Researcher (round 2)" not in phase_names(res) and qa1.status == "OVERRULED",
      (res.status, qa1.status))
check("OVERRULED: pipeline warning names the field; phase log lists the overruled correction",
      any("rejection overruled by the KB" in w and "caveats[3].note" in w for w in res.warnings)
      and "QA corrections overruled by the KB" in render_phase_log(res)
      and "P-AGR-3.2.2-VA" in render_phase_log(res), res.warnings)
saved = json.loads((res.out_dir / "qa_1.json").read_text())
check("OVERRULED: qa_1.json keeps the overruled corrections and the re-judge flag",
      saved["overruled_by_kb"][0]["record"] == "P-AGR-3.2.2-VA" and saved["rejudged"] is True
      and saved["raw_corrections"] == [], saved.keys())

same = QAOutcome("APPROVED", [], None, qa_llm("fake/researcher"))
res = run("windows", fake_for("windows"), qa=qa_script(same))
check("same model for Researcher and QA: warned", any("same model" in w for w in res.warnings), res.warnings)
check("same_model_warning: different models -> none", same_model_warning("a", "b") is None
      and same_model_warning("a", None) is None)

print("\n4c. The Builder prose check (Step 7.6) in the pipeline")
llm = fake_for("windows", document_builder=[builder_prose("windows")] * 2,
               prose_qa=[PROSE_REJECTS, PROSE_APPROVES])
res = run("windows", llm)
md = (res.out_dir / "phase_log.md").read_text(encoding="utf-8")
check("prose rejected then approved: REPORT with LLM prose, both rounds logged", res.status == "REPORT"
      and phase(res, "Document Builder").status == "OK" and phase(res, "Prose QA (round 1)").status == "REJECTED"
      and phase(res, "Prose QA (round 2)").status == "OK", phase_names(res))
check("prose phases follow the Builder, before the report check", phase_names(res)[-4:] == [
    "Document Builder", "Prose QA (round 1)", "Prose QA (round 2)", "Report check"], phase_names(res))
builder_calls = [m for a, m in llm.seen if a == "document_builder"]
builder_round2 = builder_calls[1][-1]["content"] if len(builder_calls) > 1 else "(no retry was sent)"
check("the prose correction reaches the Builder's retry", "QA: summary: 'eliminates your customs duty'"
      in builder_round2, builder_round2[:300])
check("phase_log.md shows the correction sent and the rejection",
      "Corrections sent (one shared revision):" in md and "| Prose QA (round 1) | REJECTED |" in md
      and "factuality 0" in md)
check("prose_qa_1.json and prose_qa_2.json saved", (res.out_dir / "prose_qa_1.json").exists()
      and json.loads((res.out_dir / "prose_qa_2.json").read_text())["status"] == "APPROVED")
saved = json.loads((res.out_dir / "builder.json").read_text())
check("builder.json records the rounds and the review status", saved["review_status"] == "APPROVED"
      and [r["prose_qa"] for r in saved["rounds"]] == ["REJECTED", "APPROVED"], saved.get("rounds"))
check("B: builder.json saves each round's prose and chain; English on auto:long, no chain fallback",
      [r["chain"] for r in saved["rounds"]] == ["auto:long"] * 2 and saved["chain_fallback"] is None
      and all(r["prose"] == builder_prose("windows") for r in saved["rounds"])
      and [c["chain"] for c in saved["calls"]] == ["auto:long"] * 2, saved.get("rounds"))

ar_in = dict(INTAKES["windows"][0], language="ar")
llm = fake_for("windows", intake=[ar_in], document_builder=[ERR, builder_prose("windows"), builder_prose("windows")])
res = run("windows", llm)
saved = json.loads((res.out_dir / "builder.json").read_text())
b = phase(res, "Document Builder")
check("B: an Arabic report whose auto:arabic call fails: the fallback is in builder.json",
      saved["chain_fallback"] and saved["chain_fallback"]["from"] == "auto:arabic"
      and saved["chain_fallback"]["to"] == "auto:long" and saved["chain_fallback"]["round"] == 1
      and [r["chain"] for r in saved["rounds"]] == ["auto:long"] * 2, saved.get("chain_fallback"))
check("B: ... the failed auto:arabic attempts and the auto:long calls, each with its chain",
      any(not c["ok"] and c["attempts"] == ERR.attempts for c in saved["calls"])
      and [c["chain"] for c in saved["calls"] if c["ok"]] == ["auto:long"] * 2, saved["calls"])
check("B: ... and named in the phase log", "chain fallback: auto:arabic -> auto:long (round 1:" in b.summary
      and "chain fallback: auto:arabic -> auto:long" in (res.out_dir / "phase_log.md").read_text(encoding="utf-8"),
      b.summary)

llm = fake_for("windows", document_builder=[builder_prose("windows")] * 2,
               prose_qa=[PROSE_REJECTS, PROSE_REJECTS])
res = run("windows", llm)
b = phase(res, "Document Builder")
check("prose rejected twice: code-only report, reason shown", res.status == "REPORT" and b.status == "FALLBACK"
      and "code-only report (fallback): prose QA still failing after round 2" in b.summary, b.summary)
check("prose rejected twice: report check still clean", phase(res, "Report check").status == "OK")

llm = fake_for("windows", prose_qa=[ERR])
res = run("windows", llm)
pq_phase = phase(res, "Prose QA (round 1)")
check("prose check fails: report keeps the LLM prose, phase FAILED with attempts",
      res.status == "REPORT" and phase(res, "Document Builder").status == "OK" and pq_phase.status == "FAILED"
      and any(c.get("attempts") == ERR.attempts for c in pq_phase.calls))
check("prose check fails: pipeline warns the prose was NOT reviewed",
      any("report prose NOT reviewed by QA" in w for w in res.warnings), res.warnings)
check("prose check fails: Builder summary says so", "prose NOT reviewed by QA"
      in phase(res, "Document Builder").summary)

res = run("windows", fake_for("windows", prose_qa=[]), prose_qa=None)
check("prose_qa=None: no prose check phase, no call", not any(n.startswith("Prose QA") for n in phase_names(res))
      and "prose QA not run" in phase(res, "Document Builder").summary)

res = run("windows", fake_for("windows", document_builder=[ERR], prose_qa=[]))
check("Builder call fails: no prose check (nothing to read)",
      not any(n.startswith("Prose QA") for n in phase_names(res)) and phase(res, "Document Builder").status
      == "FALLBACK")


def same_model_review(facts_text, prose, *, llm):
    return ProseQAOutcome("APPROVED", scores={"factuality": 1, "completeness": 1}, note="APPROVED",
                          llm=LLMResult(text="{}", data={}, routed_via="fake/document_builder",
                                        finish_reason="stop", latency_s=0.1))


res = run("windows", fake_for("windows"), prose_qa=same_model_review)
check("same model for Builder and prose check: warned",
      any("Document Builder and prose QA were served by the same model" in w for w in res.warnings), res.warnings)
check("builder_vs_prose_qa_warning: different models -> none",
      builder_vs_prose_qa_warning("a", "b") is None and builder_vs_prose_qa_warning(None, "a") is None)


# ---------------------------------------------------------------- 5
print("\n5. LLM failures")
res = run("windows", fake_for("windows", intake=[ERR]))
check("Intake fails: LLM_ERROR", res.status == "LLM_ERROR" and "busy" in res.output)
check("Intake fails: failed attempts in the phase log", res.phases[0].calls[0]["attempts"] == ERR.attempts)

res = run("windows", fake_for("windows", researcher=[ERR]))
check("Researcher fails: LLM_ERROR with its attempts", res.status == "LLM_ERROR"
      and res.phases[-1].calls[0]["attempts"] == ERR.attempts)

llm = fake_for("windows", researcher=[bad, ERR])
res = run("windows", llm)
check("Researcher revision fails: LLM_ERROR, corrections recorded", res.status == "LLM_ERROR"
      and res.phases[-1].details.get("corrections_sent"))

res = run("windows", fake_for("windows", document_builder=[ERR]))
b = phase(res, "Document Builder")
check("Builder fails: still a REPORT (code-only)", res.status == "REPORT" and b.status == "FALLBACK")
check("Builder fails: failed attempts kept in the phase log",
      any(c["attempts"] == ERR.attempts for c in b.calls))
saved = json.loads((res.out_dir / "builder.json").read_text())
check("Builder fails: failed attempts saved in builder.json",
      any(c["attempts"] == ERR.attempts for c in saved["calls"]))

# ---------------------------------------------------------------- 6
print("\n6. Data protection: the bill of materials never leaves code")
for case in ("windows", "chargers"):
    res, llm = results[case]
    folder = Path(PIPELINE_CASES[case][1])
    rows = list(csv.DictReader((folder / "bom.csv").open(encoding="utf-8")))
    suppliers = [r["supplier"] for r in rows]
    values = {v for r in rows for v in number_keys(r["value"])}
    sent = llm.sent_text()
    saved = "\n".join(f.read_text(encoding="utf-8") for f in res.out_dir.iterdir())
    for where, text in (("LLM prompts", sent), ("saved files", saved)):
        found = [s for s in suppliers if s in text] + [s.split(" (")[0] for s in suppliers
                                                       if s.split(" (")[0] in text]
        check(f"{case}: no supplier name in {where}", not found, found)
        # Individual input values must not appear. (Totals and percentages may.)
        leaked = sorted(values & number_keys(text))
        check(f"{case}: no individual input value in {where}", not leaked, leaked)

# ---------------------------------------------------------------- 7
print("\n7. Readable phase log (phase_log.md)")
res, _ = results["windows"]
md = (res.out_dir / "phase_log.md").read_text(encoding="utf-8")
check("phase_log.md saved and equals render_phase_log()", md == render_phase_log(res))
check("title gives status and verdict", md.startswith("# Mansha run: REPORT (ELIGIBLE)"))
check("message shown", "We run a factory in Sharjah" in md)
check("one table row per phase", all(f"| {i} | {p.name} |" in md for i, p in enumerate(res.phases, 1)))
check("model column filled for LLM phases", "| fake/researcher |" in md and "| fake/intake |" in md)
check("QA result visible", "| QA (round 1) | OK |" in md and "APPROVED | factuality 1" in md)

llm = fake_for("windows", researcher=[bad, research_fixture("windows")], document_builder=[ERR])
res = run("windows", llm)
md = (res.out_dir / "phase_log.md").read_text(encoding="utf-8")
check("revision: corrections shown", "Corrections sent (one shared revision):" in md
      and "origin_result.status" in md)
check("failed call: attempt trail with the wait", "call FAILED" in md and "HTTP 502 -> waited 30 s" in md
      and "#2 router" in md, md[-600:])
check("fallback visible", "| FALLBACK |" in md)
copied = research_fixture("chargers")
copied["gaps"] = [c["note"] for c in copied["caveats"]]
res = run("chargers", fake_for("chargers", researcher=[copied]))
md = (res.out_dir / "phase_log.md").read_text(encoding="utf-8")
check("caveats copied into gaps: dropped by code, shown in phase_log.md, not in the report",
      "Normalized by code:" in md and "gaps: dropped a copy of a caveat" in md
      and "What's still needed" not in res.output, md[-800:])
check("report check row", "| Report check | OK |" in md)
# Step 7.6c (problems 74-75, live 19 Oct): bracketed IDs and follow-ups in a NOT_ELIGIBLE answer
asks = research_fixture("chargers")
asks["follow_up_questions"] = ["Where was the final manufacture of these battery chargers completed?",
                               "What is the FOB value of this shipment?"]
asks["origin_result"]["source_id"] = "[" + asks["origin_result"]["source_id"] + "]"
res = run("chargers", fake_for("chargers", researcher=[asks, asks]))  # 2nd: a missing fix fails by name
md = (res.out_dir / "phase_log.md").read_text(encoding="utf-8")
check("NOT_ELIGIBLE follow-ups and bracketed IDs: fixed by code in round 1, shown in phase_log.md, "
      "no 'What's still needed' in the report",
      res.status == "REPORT" and "Researcher (round 2)" not in md
      and "follow_up_questions: dropped for verdict NOT_ELIGIBLE" in md
      and "square brackets removed" in md
      and "What's still needed" not in res.output and "final manufacture of these" not in res.output, md[-900:])
# Step 7.6d (problem 76, live 19 Oct 04:16): claim notes in a NOT_ELIGIBLE answer, one with an
# invented website, are dropped by code before QA, so QA never reviews text the report won't show.
claims = research_fixture("chargers")
claims["caveats"] += [{"source_id": "P-UAE-ISSUER", "note": "The India-specific page is still on doit.gov.ae."},
                      {"source_id": "TOOL:coo_fee", "note": "The certificate fee for this shipment is AED 50."},
                      {"source_id": "P-IN-IMPORTER", "note": "The importer claims the CEPA rate on the bill of entry."}]
llm = fake_for("chargers", researcher=[claims, claims])  # 2nd: a missing fix fails by name
res = run("chargers", llm)
md = (res.out_dir / "phase_log.md").read_text(encoding="utf-8")
qa_text = "\n".join(m["content"] for a, msgs in llm.seen if a == "qa" for m in msgs)
check("NOT_ELIGIBLE claim notes: dropped by code before QA (QA never sees them), shown in phase_log.md, "
      "one QA call, report OK",
      res.status == "REPORT" and "Researcher (round 2)" not in md and llm.agents().count("qa") == 1
      and md.count("caveats: dropped a note about claiming the CEPA rate") >= 3
      and "doit.gov.ae" not in qa_text and "doit.gov.ae" not in res.output, md[-900:])

# A report with a problem is FLAGGED but still shown (decision 9.6b: flag only)
# Mandatory notes are printed verbatim from the Researcher's caveats (path of problem 34), so a
# raw Python value there gets past the Builder's checks; only the report check sees it. (Until 7.6j this
# used a raw field name, "price_basis"; the Researcher's own checks now catch those in round 1.) Since O1
# (30 Oct) code writes the origin tool's notes, so the raw value rides on a duty-tool note (also mandatory).
leaky = research_fixture("windows")
leaky["caveats"].append({"note": "Operations declared: ['b', 'k'].", "source_id": "TOOL:duty:76101000"})
res = run("windows", fake_for("windows", researcher=[leaky], document_builder=[ERR]))   # code prose
rc = phase(res, "Report check")
check("flagged report: still a REPORT, shown to the user", res.status == "REPORT"
      and (res.out_dir / "report.md").exists())
check("flagged report: phase FLAGGED with the problems", rc.status == "FLAGGED" and rc.problems, rc.problems)
check("flagged report: pipeline warning", any(w.startswith("Report check:") for w in res.warnings),
      res.warnings)
md = (res.out_dir / "phase_log.md").read_text(encoding="utf-8")
check("flagged report: visible in phase_log.md", "| Report check | FLAGGED |" in md
      and "report shown anyway (flag only)" in md)

res = run("brazil", fake_for("brazil"))
md = (res.out_dir / "phase_log.md").read_text(encoding="utf-8")
check("stop: title has no verdict, reason in table", md.startswith("# Mansha run: NOT_COVERED\n")
      and "not covered" in md)

# ---------------------------------------------------------------- 8
print("\n8. The runner (scripts.run_pipeline) with a fake LLM")
root = TMP / "runner"
code = runner_main(["vague", "brazil"], llm=FakeLLM(intake=[NULL_INTAKE, EXTRA_INTAKES["brazil"]]),
                   runs_root=root)
folders = sorted(f.name for f in root.iterdir())
check("two dev cases as expected: exit 0", code == 0, code)
check("one timestamped folder per case", len(folders) == 2
      and {f.split("_", 1)[1] for f in folders} == {"vague", "brazil"}, folders)
code = runner_main(["vague"], llm=FakeLLM(intake=[EXTRA_INTAKES["brazil"]]), runs_root=root)
check("unexpected status: exit 1", code == 1, code)
code = runner_main(["--message", "We make aluminium window frames for India.",
                    "--bom", "samples/windows_qualifies"],
                   llm=fake_for("windows"), runs_root=root)
check("--message with --bom: runs, folder named _msg", code == 0
      and any(f.name.endswith("_msg") and (f / "report.md").exists() for f in root.iterdir()))
code = runner_main(["--message", "We make aluminium window frames for India.",
                    "--bom", "samples/windows_qualifies"],
                   llm=fake_for("windows", researcher=[leaky], document_builder=[ERR]), runs_root=root)
check("report check problem: exit 1 (report still saved)", code == 1, code)
real_check, runner.ROUTER_CHECK = runner.ROUTER_CHECK, lambda: (False, "router not answering (fake)")
n_before = len(list(root.iterdir()))
code = runner_main(["vague"], runs_root=root)   # the real call_llm: the pre-flight check runs
check("router down: exit 2, nothing run (no new folder)", code == 2 and len(list(root.iterdir())) == n_before, code)
code = runner_main(["--message", "We make aluminium window frames for India."], runs_root=root)
check("router down with --message: exit 2", code == 2 and len(list(root.iterdir())) == n_before, code)
runner.ROUTER_CHECK = lambda: (_ for _ in ()).throw(AssertionError("checked with a fake llm"))
code = runner_main(["vague"], llm=FakeLLM(intake=[NULL_INTAKE]), runs_root=root)
check("a fake llm skips the pre-flight check", code == 0, code)
runner.ROUTER_CHECK = real_check
for bad_args in (["--bom", "samples/windows_qualifies"], ["nope"], ["vague", "--message", "x"]):
    try:
        runner_main(bad_args, llm=FakeLLM(), runs_root=root)
        check(f"bad arguments {bad_args} rejected", False, "no error")
    except SystemExit as e:
        check(f"bad arguments {bad_args} rejected", e.code == 2, e.code)

# ---------------------------------------------------------------- 9
print("\n9. Trying a new chain (scripts.try_chain) with a fake LLM")


def chain_spy(fake: FakeLLM):
    seen = []

    def llm(agent, chain, messages, **kwargs):
        seen.append((agent, chain))
        return fake(agent, chain, messages, **kwargs)
    return llm, seen


llm, seen = chain_spy(fake_for("windows"))
code = try_chain_main(["trial", "windows"], llm=llm, runs_root=TMP / "try")
check("try_chain: dev case runs, exit 0", code == 0, code)
check("try_chain: Researcher and Builder on auto:trial, Intake and QA keep theirs",
      seen == [("intake", "auto:qa"), ("researcher", "auto:trial"), ("qa", "auto:judge"),
               ("qa", "auto:judge"), ("document_builder", "auto:trial"), ("prose_qa", "auto:judge")],
      seen)
check("try_chain: runs saved apart, in runs/try_trial/",
      any(f.name.endswith("_windows") and (f / "report.md").exists() for f in (TMP / "try" / "try_trial").iterdir()))
llm, seen = chain_spy(fake_for("windows"))
try_chain_main(["auto:trial", "windows", "--agents", "researcher"], llm=llm, runs_root=TMP / "try")
check("try_chain --agents researcher: only the Researcher switched",
      seen == [("intake", "auto:qa"), ("researcher", "auto:trial"), ("qa", "auto:judge"),
               ("qa", "auto:judge"), ("document_builder", "auto:long"), ("prose_qa", "auto:judge")],
      seen)
budgets = []


def budget_spy(agent, chain, messages, **kwargs):
    budgets.append((agent, chain, kwargs.get("max_tokens")))
    return fake_for_qa(agent, chain, messages, **kwargs)


fake_for_qa = fake_for("windows")
try_chain_main(["trial", "windows", "--agents", "qa"], llm=budget_spy, runs_root=TMP / "try")
check("try_chain --agents qa: QA on auto:trial with the part budget (windows splits), others unchanged",
      budgets == [("intake", "auto:qa", None), ("researcher", "auto:long", None),
                  ("qa", "auto:trial", 3000), ("qa", "auto:trial", 3000),  # part budget 3,000 (7.6h)
                  ("document_builder", "auto:long", None), ("prose_qa", "auto:judge", 2000)], budgets)
try:
    try_chain_main(["long"], llm=FakeLLM(), runs_root=TMP / "try")
    check("try_chain refuses a pipeline chain", False, "no error")
except SystemExit as e:
    check("try_chain refuses a pipeline chain", e.code == 2, e.code)

print(f"\n(outputs in {TMP})")
print("\n" + ("ALL PASSED" if not failures else f"{len(failures)} FAILED: {failures}"))
sys.exit(1 if failures else 0)
