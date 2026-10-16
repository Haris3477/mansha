"""Offline tests for the orchestrator (Step 9.3): fake LLM, no router.

Run: python -m scripts.test_pipeline
The fake LLM answers each agent with saved outputs (samples/researcher_outputs/) or
canned JSON, so every path of run_pipeline() is checked in about a second:
statuses, stops, the shared revision, the QA slot, LLM failures, saved files, and
that nothing from a bill of materials (supplier names, input values) reaches an LLM
or a saved file.
"""

import copy
import csv
import json
import logging
import sys
import tempfile
from pathlib import Path

from mansha.document_builder import build_facts, fallback_prose, max_llm_notes
from mansha.llm_client import LLMCallError, LLMResult
from mansha.orchestrator import (
    MOFT_CEPA_URL,
    QAOutcome,
    render_phase_log,
    run_pipeline,
    same_model_warning,
)
from mansha.researcher import number_keys
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
        if isinstance(r, Exception):
            raise r
        return LLMResult(text=json.dumps(r), data=copy.deepcopy(r), routed_via=f"fake/{agent}",
                         finish_reason="stop", latency_s=0.1,
                         attempts=[{"attempt": 1, "ok": True, "routed_via": f"fake/{agent}"}])

    def agents(self) -> list[str]:
        return [a for a, _ in self.seen]

    def sent_text(self) -> str:
        return "\n".join(m["content"] for _, msgs in self.seen for m in msgs)


def fake_for(case: str, **overrides) -> FakeLLM:
    queues = {"intake": [EXTRA_INTAKES.get(case) or INTAKES[case][0]]}
    if case in INTAKES:
        queues["researcher"] = [research_fixture(case)]
        queues["document_builder"] = [builder_prose(case)]
    queues.update(overrides)
    return FakeLLM(**queues)


def run(case: str, llm: FakeLLM, **kwargs):
    message, folder, _, _ = PIPELINE_CASES[case]
    out = TMP / f"{case}_{len(list(TMP.iterdir()))}"
    return run_pipeline(message, case_folder=folder, llm=llm, out_dir=out, **kwargs)


def phase_names(res) -> list[str]:
    return [p.name for p in res.phases]


def phase(res, name: str):
    return next(p for p in res.phases if p.name == name)


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
    "Document Builder", "Report check"], phase_names(res))
check("windows: agents called intake -> researcher -> builder",
      llm.agents() == ["intake", "researcher", "document_builder"], llm.agents())
check("windows: LLM prose used (no fallback)", phase(res, "Document Builder").status == "OK")
check("windows: every LLM phase records who served it",
      all(c.get("served_by") for p in res.phases for c in p.calls))
files = sorted(f.name for f in res.out_dir.iterdir())
check("windows: all phase files saved", files == sorted([
    "message.txt", "intake.json", "evidence.txt", "researcher_1.json", "qa_1.json",
    "builder.json", "report.md", "phase_log.json", "phase_log.md"]), files)
check("windows: report.md is the report", (res.out_dir / "report.md").read_text() == res.output
      and res.output.startswith("#"))
plog = json.loads((res.out_dir / "phase_log.json").read_text())
check("phase_log.json: status, verdict and 7 phases", plog["status"] == "REPORT"
      and plog["verdict"] == "ELIGIBLE" and len(plog["phases"]) == 7)
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
sent = llm.seen[2][1][-1]["content"]
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
res, _ = results["windows"]
qa_phase = res.phases[4]
check("pass-through: QA SKIPPED, not APPROVED", qa_phase.status == "SKIPPED"
      and "NOT reviewed by QA" in qa_phase.summary)
check("pass-through: nothing in the phase log says APPROVED",
      "APPROVED" not in (res.out_dir / "phase_log.json").read_text())

warn = research_fixture("windows")
warn["procedure"][0]["step"] += " It costs AED 777."   # a number not in the cited record -> warning
res = run("windows", fake_for("windows", researcher=[warn]))
check("code warnings with QA skipped: pipeline warns they were not reviewed",
      any("not reviewed" in w for w in res.warnings), res.warnings)


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

same = QAOutcome("APPROVED", [], None, qa_llm("fake/researcher"))
res = run("windows", fake_for("windows"), qa=qa_script(same))
check("same model for Researcher and QA: warned", any("same model" in w for w in res.warnings), res.warnings)
check("same_model_warning: different models -> none", same_model_warning("a", "b") is None
      and same_model_warning("a", None) is None)

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
check("QA pass-through visible", "NOT reviewed by QA" in md)

llm = fake_for("windows", researcher=[bad, research_fixture("windows")], document_builder=[ERR])
res = run("windows", llm)
md = (res.out_dir / "phase_log.md").read_text(encoding="utf-8")
check("revision: corrections shown", "Corrections sent (one shared revision):" in md
      and "origin_result.status" in md)
check("failed call: attempt trail with the wait", "call FAILED" in md and "HTTP 502 -> waited 30 s" in md
      and "#2 router" in md, md[-600:])
check("fallback visible", "| FALLBACK |" in md)
check("report check row", "| Report check | OK |" in md)

# A report with a problem is FLAGGED but still shown (decision 9.6b: flag only)
# Mandatory notes are printed verbatim from the Researcher's caveats (path of problem 34), so a
# raw field name there gets past the Builder's checks; only the report check sees it.
leaky = research_fixture("windows")
leaky["caveats"].append({"note": "Totals: price_basis FOB.", "source_id": "TOOL:origin:76101000"})
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
check("try_chain: Researcher and Builder on auto:trial, Intake keeps auto:qa",
      seen == [("intake", "auto:qa"), ("researcher", "auto:trial"), ("document_builder", "auto:trial")],
      seen)
check("try_chain: runs saved apart, in runs/try_trial/",
      any(f.name.endswith("_windows") and (f / "report.md").exists() for f in (TMP / "try" / "try_trial").iterdir()))
llm, seen = chain_spy(fake_for("windows"))
try_chain_main(["auto:trial", "windows", "--agents", "researcher"], llm=llm, runs_root=TMP / "try")
check("try_chain --agents researcher: only the Researcher switched",
      seen == [("intake", "auto:qa"), ("researcher", "auto:trial"), ("document_builder", "auto:long")],
      seen)
try:
    try_chain_main(["long"], llm=FakeLLM(), runs_root=TMP / "try")
    check("try_chain refuses a pipeline chain", False, "no error")
except SystemExit as e:
    check("try_chain refuses a pipeline chain", e.code == 2, e.code)

print(f"\n(outputs in {TMP})")
print("\n" + ("ALL PASSED" if not failures else f"{len(failures)} FAILED: {failures}"))
sys.exit(1 if failures else 0)
