"""Offline tests for the evaluation set (sub-steps 1-2): dry run, grading, anchors, budget guard.

Run: python -m scripts.test_eval_set
No router: the pipeline runs with a fake LLM that answers from the saved fixtures
(samples/researcher_outputs/), and the grader is checked on those clean runs and on copies
with one failure planted at a time. The global anchors are also replayed over the saved
live runs in runs/pipeline/ (git-ignored; skipped when absent).
"""

import copy
import json
import re
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

from mansha.document_builder import build_facts, fallback_prose, max_llm_notes
from mansha.llm_client import LLMResult
from mansha.orchestrator import run_pipeline
from scripts import eval_set
from scripts.eval_cases import BY_ID, CASES
from scripts.eval_grade import case_anchor_problems, compare, derive, grade, load_run, slips

TMP = Path(tempfile.mkdtemp(prefix="mansha_eval_"))
FIXTURES = Path("samples/researcher_outputs")
failures: list[str] = []


def check(name: str, cond: bool, detail="") -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


class FakeLLM:
    def __init__(self, **queues):
        self.queues = {k: list(v) for k, v in queues.items()}

    def __call__(self, agent, chain, messages, **kwargs):
        r = self.queues[agent].pop(0)
        r = r(messages) if callable(r) else r
        return LLMResult(text=json.dumps(r), data=copy.deepcopy(r), routed_via=f"fake/{agent}",
                         finish_reason="stop", latency_s=0.1,
                         attempts=[{"attempt": 1, "ok": True, "chain": chain, "routed_via": f"fake/{agent}",
                                    "usage": {"prompt": 100, "completion": 10}}])


def qa_approves(messages):
    ids = re.findall(r"^(W\d+): ", messages[1]["content"], re.MULTILINE)
    return {"warnings": [{"id": w, "judgement": "NOISE", "reason": "fake"} for w in ids],
            "corrections": [], "scores": {"factuality": 1, "completeness": 1, "formatting_safety": 1}}


FIXTURE_FOR = {"C1": "windows", "C2": "chargers", "C3": "windows_nodata", "C4": "plastic"}


def fake_for(case_id: str) -> FakeLLM:
    case = BY_ID[case_id]
    research = json.loads((FIXTURES / f"{FIXTURE_FOR[case_id]}.json").read_text(encoding="utf-8"))["output"]
    _, notes = build_facts(research, case.intake)
    prose = fallback_prose(research, notes)
    prose["notes"] = prose["notes"][:max_llm_notes(notes)]
    return FakeLLM(intake=[case.intake], researcher=[research], qa=[qa_approves] * 8,
                   document_builder=[prose],
                   prose_qa=[{"corrections": [], "scores": {"factuality": 1, "completeness": 1}}] * 2)


def clean_run(case_id: str) -> Path:
    case = BY_ID[case_id]
    out = TMP / "clean" / f"{case.id}_{case.name}"
    run_pipeline(case.message, case_folder=case.folder, llm=fake_for(case_id), out_dir=out)
    return out


def planted(src: Path, name: str, edit) -> Path:
    """A copy of a clean run folder with one failure planted by edit(folder)."""
    dst = TMP / "planted" / name / src.name
    shutil.copytree(src, dst)
    edit(dst)
    return dst


def edit_json(path: Path, fn) -> None:
    d = json.loads(path.read_text(encoding="utf-8"))
    fn(d)
    path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


def append(path: Path, text: str) -> None:
    path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")


# ---------------------------------------------------------------------------
print("1. Dry run: the tools still match the answer key")
check("dry run clean (core, stop, new)", eval_set.main(["--dry-run"]) == 0)
check("dry run clean (reserves)", eval_set.main(["--dry-run", "--group", "reserve"]) == 0)
c = copy.deepcopy(BY_ID["N4"]); c.key["va_threshold"] = 45
check("a changed key is caught", any("va_threshold" in p for p in compare(c, derive(c))))
c = copy.deepcopy(BY_ID["N8"]); c.key["checks"] = {"CTSH": "PASS"}
check("a changed check result is caught", any("CTSH" in p for p in compare(c, derive(c))))
check("every case has a unique ID and name", len({x.id for x in CASES}) == len({x.name for x in CASES}) == len(CASES))
check("every case folder exists", all(Path(x.folder).is_dir() for x in CASES if x.folder))
check("bills of materials use synthetic suppliers only",
      all(r["supplier"].endswith("(synthetic)") for x in CASES for r in __import__("scripts.eval_grade", fromlist=["bom_rows"]).bom_rows(x)))

print("\n2. Clean fake-LLM runs of the four branches pass every code check")
clean = {cid: clean_run(cid) for cid in FIXTURE_FOR}
for cid, folder in clean.items():
    g = grade(BY_ID[cid], load_run(folder))
    check(f"{cid} passes", g.passed, "; ".join(f"{n}: {d}" for n, _, d in g.failed))
    # The windows_nodata fixture carries the duty-scope note on AIDC ("only for lines in Table II") on a
    # Table I line: a real G12 instance, so C3 is expected to show exactly that slip.
    want = {"G12"} if cid == "C3" else set()
    check(f"{cid} slips: {sorted(want) or 'none'}", set(g.slips) == want, str(g.slips))
    check(f"{cid} counts its requests", g.cost.get("auto:long", {}).get("requests", 0) >= 2, str(g.cost))

print("\n3. One planted failure at a time is caught (and only that one)")
C1 = clean["C1"]


def failed_names(folder: Path, case_id: str = "C1") -> set[str]:
    return {n for n, _, _ in grade(BY_ID[case_id], load_run(folder)).failed}


f = planted(C1, "status", lambda d: edit_json(d / "phase_log.json", lambda x: x.update(status="CHECKS_FAILED", verdict=None)))
check("CHECKS_FAILED -> status and verdict fail", {"status", "verdict"} <= failed_names(f))
f = planted(C1, "intake", lambda d: edit_json(d / "intake.json", lambda x: x["output"].update(hs_code_given="39239090")))
check("a wrong Intake HS code -> intake fails", "intake" in failed_names(f))
f = planted(C1, "value", lambda d: edit_json(d / "intake.json", lambda x: x["output"].update(
    shipment_value={"amount": 100000, "currency": "USD"})))
check("a wrong shipment currency -> intake fails", "intake" in failed_names(f))
f = planted(C1, "line", lambda d: edit_json(d / "researcher_1.json", lambda x: x["output"]["classification"].update(tariff_line="76109010")))
check("a wrong tariff line -> researcher fails", "researcher" in failed_names(f))
f = planted(C1, "saving", lambda d: edit_json(d / "researcher_1.json", lambda x: x["output"]["estimated_saving"].update(amount="15000.00")))
check("a wrong saving amount -> researcher fails", failed_names(f) == {"researcher"}, str(failed_names(f)))


def qa_failed(d: Path) -> None:
    edit_json(d / "phase_log.json", lambda x: [p.update(status="FAILED") for p in x["phases"] if p["name"].startswith("QA")])


f = planted(C1, "qa_error", qa_failed)
check("a QA phase that failed -> QA fails", failed_names(f) == {"QA"}, str(failed_names(f)))


def refusal(d: Path) -> None:
    def add(x):
        for p in x["phases"]:
            if p["name"].startswith("QA"):
                p["calls"][0]["attempts"].insert(0, {"attempt": 1, "chain": "auto:judge", "ok": False, "http_status": 429})
                return
    edit_json(d / "phase_log.json", add)


f = planted(C1, "refusal", refusal)
check("a router refusal the retry got past -> no failure (E3, 24 Oct 19:21)", not failed_names(f), str(failed_names(f)))
check("... but it is counted", grade(BY_ID["C1"], load_run(f)).cost["refusals"] == 1)
f = planted(f, "refusal_unreviewed", lambda d: edit_json(d / "phase_log.json", lambda x: [
    p.update(summary=p["summary"] + " | part 2/2 NOT reviewed") for p in x["phases"] if p["name"].startswith("QA")]))
check("a refusal that left a part NOT reviewed -> QA fails", failed_names(f) == {"QA"}, str(failed_names(f)))
f = planted(C1, "not_reviewed", lambda d: edit_json(d / "phase_log.json", lambda x: [
    p.update(summary=p["summary"] + " | NOT reviewed") for p in x["phases"] if p["name"].startswith("Prose QA")]))
check("prose NOT reviewed -> prose QA fails", failed_names(f) == {"prose QA"}, str(failed_names(f)))
f = planted(C1, "supplier", lambda d: append(d / "report.md", "\nSupplier A Trading (synthetic)\n"))
check("a supplier name in the report -> privacy fails", "privacy" in failed_names(f))
f = planted(C1, "amount", lambda d: append(d / "evidence.txt", "\nprofiles cost 38,000 AED\n"))
check("an input amount in the evidence -> privacy fails", failed_names(f) == {"privacy"}, str(failed_names(f)))
# 25 Oct: an amount the duty/fee tools printed is no leak (N5: saving 10000.00 AED = an input's value)
from scripts.eval_grade import tool_figures, value_leaks
EV = ("[TOOL:coo_fee]\nstatus: ESTIMATED\ncertificate fee: AED 50 (band: invoice value up to AED 100000)\n"
      "invoice value used: 100000.00 AED\nnotes:\n- Fee bands 208/2025.\n\n"
      "[TOOL:duty:32091010]\nshipment value: 100000.00 AED\n"
      "duty without CEPA: 10000.00 AED; duty with CEPA: 0.00 AED; saving: 10000.00 AED\nnotes:\n- x\n\n"
      "[TOOL:origin:32091010]\nnon-originating inputs are 35% of the price\n")
figs = tool_figures(EV)
check("tool figures: saving, value and fee read", {10000.0, 100000.0, 50.0} <= figs, str(figs))
check("tool figures: notes and other records not read", 208.0 not in figs and 35.0 not in figs, str(figs))
check("N5: the saving that equals an input value is no leak",
      not value_leaks(BY_ID["N5"], "saving: 10000.00 AED", "", figs))
check("... but without the tool figure it would be flagged", value_leaks(BY_ID["N5"], "saving: 10000.00 AED", ""))
check("... and another input amount still is", value_leaks(BY_ID["N5"], "Titanium dioxide 25,000 AED", "", figs))
f = planted(C1, "arabic", lambda d: append(d / "report.md", "\nملاحظة\n"))
check("Arabic letters in an English report -> language fails", "language" in failed_names(f))

print("\n4. Global anchors count known open problems as slips; they don't fail a case (D1 = A)")
f = planted(C1, "slip72", lambda d: append(d / "report.md",
            "\n- The Ministry of Foreign Trade provides the 'Certificate of Origin for India' e-service.\n"))
g = grade(BY_ID["C1"], load_run(f))
check("problem 72 counted", "72" in g.slips)
check("... and the case still passes", g.passed, str(g.failed))
# 72 widened (25 Oct): live wordings the old anchor missed, and decision C's wording, which is no slip
run = load_run(C1)
for w in ("The Ministry of Foreign Trade issues the Certificate of Origin for India through its e-service.",
          "The Ministry of Foreign Trade receives applications through the Certificate of Origin for India e-service portal.",
          "The Ministry of Foreign Trade requires the applicant to log in to the e-services portal and choose the Certificate of Origin for India service.",
          "The exporter applies for the Certificate of Origin for India via the Ministry of Foreign Trade e-services portal."):
    run.output = w
    check(f"72: {w[29:70]}...", "72" in slips(run), str(slips(run)))
for w in ("The Ministry of Foreign Trade issues the certificate of origin for India.",
          "Apply via the 'Certificate of Origin for India' e-service: log in to the ministry e-services portal.",
          "No official page read names the Ministry of Foreign Trade as the issuer of the India CEPA certificate specifically."):
    run.output = w
    check(f"no 72: {w[:45]}...", "72" not in slips(run), str(slips(run)))
# 96 (25 Oct): the box note as an instruction is a slip; the KB's own wording is not
for w in ("Since India's form governs entry into the country, you must use box 9 on your certificate.",
          "For the retrospective mark, use box 9 on the certificate as per India's form.",
          "India's certificate form requires box 9 to be completed for entry into India."):
    run.output = w
    check(f"96: {w[:45]}...", "96" in slips(run), str(slips(run)))
for w in ("The agreement says box 8, but India's origin rules and certificate form say box 9; India's form governs entry into India.",
          "The agreement refers to box 8, but India's origin rules and certificate form use box 9.",
          "It may be issued retrospectively, marked 'ISSUED RETROSPECTIVELY' in box 9 of India's certificate form."):
    run.output = w
    check(f"no 96: {w[:45]}...", "96" not in slips(run), str(slips(run)))
f = planted(clean["C3"], "slip95", lambda d: append(d / "report.md", "\nSee the checklist below.\n"))
check("problem 95 counted in NEEDS_MORE_DATA", "95" in grade(BY_ID["C3"], load_run(f)).slips)
f = planted(C1, "no95", lambda d: append(d / "report.md", "\nFollow the claim checklist below.\n"))
check("'checklist below' is no slip in an ELIGIBLE report", "95" not in grade(BY_ID["C1"], load_run(f)).slips)
# 26 Oct: a report with no checklist section pointing to one (C4 NO_PREFERENCE, N7 NOT_ELIGIBLE wording)
f = planted(clean["C4"], "slip95np", lambda d: append(d / "report.md", "\nPlease refer to the claim checklist below.\n"))
check("problem 95 counted in a NO_PREFERENCE report (no checklist)", "95" in grade(BY_ID["C4"], load_run(f)).slips)
f = planted(clean["C2"], "slip95ne", lambda d: append(d / "report.md", "\nPlease review the checklist and details below.\n"))
check("problem 95 counted in a NOT_ELIGIBLE report ('checklist and details below')", "95" in grade(BY_ID["C2"], load_run(f)).slips)
f = planted(clean["C3"], "slip92", lambda d: edit_json(d / "researcher_1.json", lambda x: x["output"][
    "follow_up_questions"].append("Please confirm the HS code for aluminium window frames.")))
check("problem 92 counted when the tariff lookup noted nothing", "92" in grade(BY_ID["C3"], load_run(f)).slips)
f = planted(clean["C3"], "no92", lambda d: edit_json(d / "researcher_1.json", lambda x: x["output"][
    "follow_up_questions"].append("Please give the 6-digit HS code of each input in the bill of materials.")))
check("a bill-of-materials HS question is no slip", "92" not in grade(BY_ID["C3"], load_run(f)).slips)
f = planted(clean["C3"], "slip67", lambda d: append(d / "report.md", "\nThe saving is the difference between the normal rate and the CEPA rate.\n"))
check("problem 67 counted", "67" in grade(BY_ID["C3"], load_run(f)).slips)

print("\n5. Case anchors (D2 = A)")
run = load_run(C1)
run.output = "Saving: 8100.00 AED on the shipment."
check("N1: an AED saving is caught", case_anchor_problems(BY_ID["N1"], run))
run.output = "Saving: 8100.00 USD. Certificate fee: AED 10 to AED 200."
check("N1: USD amounts and the AED fee range are fine", not case_anchor_problems(BY_ID["N1"], run))
run.output = "The CEPA rate makes these goods duty-free."
check("N2: duty-free is caught", case_anchor_problems(BY_ID["N2"], run))
# problem 97 (Haris option ii, 25 Oct): the free-zone caution must be in the summary paragraph
SUM_OK = ("## Summary\n\nYour furniture meets the rule of origin, but your factory is in a free zone and is likely "
          "not eligible for factory registration, so confirm with the ministry.\n\n## Product classification\n\nx\n")
SUM_BAD = ("## Summary\n\nYour furniture meets the rule of origin, so the CEPA rate can be claimed.\n\n"
           "## Important notes\n\n- Factory declared in a free zone: likely not eligible.\n")
run.output = SUM_OK
check("N2: free-zone caution in the summary passes", not case_anchor_problems(BY_ID["N2"], run), str(case_anchor_problems(BY_ID["N2"], run)))
run.output = SUM_BAD
check("N2: free zone only in the notes is caught (problem 97)",
      "must say the free-zone caution in the summary" in case_anchor_problems(BY_ID["N2"], run))
run.output = "## الملخص\n\nالمصنع في منطقة حرة (free zone)\n"
check("N2: the Arabic summary heading is read too", not case_anchor_problems(BY_ID["N2"], run))
# problem 97 in N5 (25 Oct): the Indian-origin proof condition must be in the summary
for w in ("It meets the rule only if you can prove that the resin bought in India is originating.",
          "The result relies on bilateral cumulation for the Indian resin.",
          "This holds if the Indian resin has proof of originating status."):
    run.output = "## Summary\n\n" + w + "\n\n## Product classification\n\nx\n"
    check(f"N5 ok: {w[:40]}...", not case_anchor_problems(BY_ID["N5"], run), str(case_anchor_problems(BY_ID["N5"], run)))
run.output = ("## Summary\n\nThe product meets the rule of origin, so the CEPA rate can be claimed.\n\n"
              "## Important notes\n\n- Indian inputs count as originating only with proof of their originating status.\n")
check("N5: proof only in the notes is caught (problem 97)",
      "must say the Indian-origin proof condition in the summary" in case_anchor_problems(BY_ID["N5"], run))
run.output = "Value added 43% against a threshold of 40% (45% minus 5 points on an Ex-Works basis)."
check("N4: the Ex-Works threshold is fine", not case_anchor_problems(BY_ID["N4"], run))
run.output = "Value added 43% against 45%."
check("N4: 45% applied as the threshold is caught", case_anchor_problems(BY_ID["N4"], run))
f = planted(clean["C4"], "claim", lambda d: append(d / "report.md", "\n## Step-by-step checklist to claim the CEPA rate\n"))
check("a claim checklist in a NO_PREFERENCE report fails anchors", "anchors" in failed_names(f, "C4"))

print("\n6. Summary, reading sheet and re-grading")
root = TMP / "eval_run"
for cid, folder in clean.items():
    shutil.copytree(folder, root / folder.name)
grades = eval_set.regrade([root / x.name for x in clean.values()])
s = eval_set.write_outputs(grades, root)
check("summary counts 4/4", (s["passed"], s["scored"]) == (4, 4), str(s))
check("summary.md and reading.md written", (root / "summary.md").exists() and (root / "reading.md").exists())
reading = (root / "reading.md").read_text(encoding="utf-8")
check("reading sheet has the problem 56 and G35 slots", "problem 56" in reading and "G35" in reading)
check("--grade re-grades a saved run root", eval_set.main(["--grade", str(root)]) == 0)

print("\n7. Budget guard (E1, D3 = A) on a throwaway router database")
db = TMP / "router.db"
con = sqlite3.connect(db)
con.executescript("""
CREATE TABLE profiles (id INTEGER, name TEXT);
CREATE TABLE profile_models (profile_id INTEGER, model_db_id INTEGER, enabled INTEGER);
CREATE TABLE models (id INTEGER, platform TEXT, model_id TEXT, rpd_limit INTEGER, enabled INTEGER);
CREATE TABLE model_overrides (platform TEXT, model_id TEXT, overrides_json TEXT);
CREATE TABLE rate_limit_usage (platform TEXT, model_id TEXT, kind TEXT, created_at_ms INTEGER);
CREATE TABLE rate_limit_cooldowns (platform TEXT, model_id TEXT, key_id INTEGER, expires_at_ms INTEGER, source TEXT);
INSERT INTO profiles VALUES (3, 'long'), (4, 'qa'), (6, 'judge');
INSERT INTO models VALUES (1, 'google', 'g', 20, 1), (2, 'openrouter', 'd', 50, 1), (3, 'groq', 'q', 1000, 1),
                          (4, 'cerebras', 'j', 2400, 1), (5, 'google', 'off', 20, 0);
INSERT INTO profile_models VALUES (3, 1, 1), (3, 2, 1), (3, 5, 1), (4, 3, 1), (4, 1, 1), (6, 4, 1);
INSERT INTO model_overrides VALUES ('groq', 'q', '{"rpdLimit": 500}');
""")
now = time.time() * 1000
con.executemany("INSERT INTO rate_limit_usage VALUES ('openrouter', 'd', 'request', ?)", [(now - 3600e3,)] * 50)
con.executemany("INSERT INTO rate_limit_usage VALUES ('google', 'g', 'request', ?)", [(now - 30 * 3600e3,)] * 20)
con.execute("INSERT INTO rate_limit_usage VALUES ('google', 'g', 'request', ?)", (now - 60e3,))
con.commit(); con.close()
cap = eval_set.chain_capacity(db, now)
long_ = {m["model"]: m for m in cap["long"]}
check("only enabled models of the chain", set(long_) == {"google/g", "openrouter/d"}, str(long_))
check("used = the router's sliding 24 h count", long_["openrouter/d"]["used"] == 50 and long_["google/g"]["used"] == 1)
check("an rpdLimit override wins", cap["qa"][0]["rpd"] == 500 if cap["qa"][0]["model"] == "groq/q" else cap["qa"][1]["rpd"] == 500)
core = [x for x in CASES if x.group == "core"]
ok, _ = eval_set.budget_check(core, 1, cap)
check("the core 4 fit (19 long left, 20 worst case: SHORT)", not ok)
ok, _ = eval_set.budget_check(core[:3], 1, cap)
check("3 report cases fit", ok)
con = sqlite3.connect(db)
con.execute("INSERT INTO rate_limit_cooldowns VALUES ('google', 'g', 1, ?, 'authoritative')", (now + 15 * 3600e3,))
con.execute("INSERT INTO rate_limit_cooldowns VALUES ('openrouter', 'd', 1, ?, 'heuristic')", (now - 60e3,))
con.commit(); con.close()
cap = eval_set.chain_capacity(db, now)
g = next(m for m in cap["long"] if m["model"] == "google/g")
check("a benched model is seen (24 Oct 19:22: Google's project quota)", g["benched_min"] == 900.0, str(g))
check("an expired bench is ignored", next(m for m in cap["long"] if m["model"] == "openrouter/d")["benched_min"] is None)
check("a benched model has nothing left", eval_set.left([g]) == 0)
con = sqlite3.connect(db)
con.execute("INSERT INTO models VALUES (6, 'google', 'g2', 20, 1)")
con.execute("INSERT INTO profile_models VALUES (3, 6, 1)")
con.commit(); con.close()
g2 = next(m for m in eval_set.chain_capacity(db, now)["long"] if m["model"] == "google/g2")
check("a provider's daily-quota bench holds its other models too", g2["benched_min"] == 900.0, str(g2))
ok, lines = eval_set.budget_check(core[:3], 1, cap)
check("3 report cases no longer fit once Google is benched", not ok and "BENCHED" in "\n".join(lines), "\n".join(lines))
eval_set.ROUTER_DB = db
check("a live run that may not fit refuses to start (exit 2)", eval_set.main(["--group", "core"]) == 2)
eval_set.ROUTER_DB = TMP / "missing.db"
check("no router database -> refuses to start", eval_set.main(["--case", "C1"]) == 2)

print("\n8. Replay of the global anchors over the saved live runs (runs/pipeline/)")
saved = Path("runs/pipeline")
if not saved.is_dir():
    print("  (skipped: runs/pipeline/ not here)")
else:
    def slips_of(name: str) -> dict:
        p = saved / name
        return slips(load_run(p)) if p.is_dir() else None
    known = {"20261024-171929_windows_nodata": "72", "20261024-165309_windows_nodata": "95",
             "20261024-164944_windows_nodata": "92", "20261024-153744_windows_nodata": "G12",
             "20261024-040622_windows_nodata": "93", "20261023-190109_windows_nodata": "86",
             "20261023-200806_windows_nodata": "67", "20261024-035156_windows_nodata": "94"}
    for name, pid in known.items():
        got = slips_of(name)
        if got is not None:
            check(f"{name[:15]}: problem {pid} found", pid in got, str(got))
    # widened 72 and new 96 (25 Oct), one live wording each
    for name, pid in {"20261023-200806_windows_nodata": "72", "20261024-164944_windows_nodata": "72",
                      "20261024-035156_windows_nodata": "96", "20261024-153744_windows_nodata": "96"}.items():
        got = slips_of(name)
        if got is not None:
            check(f"{name[:15]}: problem {pid} found (25 Oct anchors)", pid in got, str(got))
    for name in ("20261024-152756_windows", "20261018-165049_windows_nodata"):
        got = slips_of(name)
        if got is not None:
            check(f"{name[:15]}: no 72/96 (decision C wording / clean steps)", not {"72", "96"} & set(got), str(got))
    n5 = Path("runs/eval_set/20261025-151048/N5_paint_indian_resin")
    if n5.is_dir():
        got5 = failed_names(n5, "N5")
        check("saved N5 (25 Oct): privacy passes, the problem-97 anchor fails", got5 == {"anchors"}, str(got5))
    after_79 = [p for p in saved.iterdir() if p.name >= "20261024-1741" and (p / "phase_log.json").exists()]
    check("no problem-92 slip after 7.9 was built", all("92" not in slips(load_run(p)) for p in after_79))

shutil.rmtree(TMP, ignore_errors=True)
print("\n" + ("ALL PASSED" if not failures else f"{len(failures)} FAILED: {failures}"))
sys.exit(1 if failures else 0)
