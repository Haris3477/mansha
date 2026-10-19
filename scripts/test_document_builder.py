"""Offline tests for the Document Builder (no LLM, no router).

Uses the 4 saved Researcher outputs in samples/researcher_outputs/ and a fake LLM.
Section 5 (Step 7.6) checks the call loop with a scripted prose check (review=...).
Run: python -m scripts.test_document_builder
Also saves the code-only (fallback) report of each case to runs/<case>/report_fallback.md.
"""

import copy
import json
import sys
from pathlib import Path

from mansha.document_builder import (
    ESTIMATE_NOTE_START,
    EVIDENCE_ID_RE,
    MAX_NOTES,
    MIN_LLM_NOTES,
    build_facts,
    build_messages,
    check_prose,
    cite,
    fallback_prose,
    is_mandatory,
    max_llm_notes,
    render_report,
    run_document_builder,
    still_needed,
)
from mansha.evidence import build_evidence
from mansha.kb import load_corridor
from mansha.llm_client import LLMCallError, LLMResult
from mansha.prose_qa import ProseQAOutcome
from mansha.tools.duty_estimate import duty_estimate
from scripts.pipeline_cases import DEV_INTAKES as CASES

FIXTURES = Path("samples/researcher_outputs")
failures: list[str] = []


def check(name: str, cond: bool, detail="") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def load(name: str):
    research = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))["output"]
    intake, folder, _ = CASES[name]
    pack = build_evidence(intake, folder)   # pure code: same evidence as the saved run
    return research, intake, pack


def good_windows_prose(notes: list[dict]) -> dict:
    optional = [n["nid"] for n in notes if not n["mandatory"]]
    return {
        "summary": "Your aluminium window frames meet the rule of origin, so you can claim the CEPA "
                   "rate in India. The estimated saving is AED 10,000. Follow the checklist below.",
        "classification": "The product falls under tariff line 76101000 (aluminium doors, windows and "
                          "their frames), with high confidence. Confirm the code with Indian customs "
                          "or a customs broker before shipping.",
        "duty": "Under the India-UAE CEPA, the normal (MFN) rate is 10% and the CEPA rate is 0%. "
                "The estimated saving on this shipment is 10000.00 AED.",
        "origin": "The rule is CTSH + VA 45%: every imported input must change tariff subheading, "
                  "and value addition must be at least 45%. Your product passed both: value addition "
                  "is 49.0% against the 45% threshold.",
        "notes": [{"text": "These points also affect how this result should be read.",
                   "from": optional[:1]}],
    }


def fake_llm(*replies):
    """A stand-in for call_llm that returns the given dicts (or raises an exception) in order."""
    queue = list(replies)
    seen: list[list[dict]] = []

    def llm(agent, chain, messages, **kwargs):
        seen.append(messages)
        r = queue.pop(0)
        if isinstance(r, Exception):
            raise r
        return LLMResult(text=json.dumps(r), data=copy.deepcopy(r), routed_via="fake/model",
                         finish_reason="stop", latency_s=0.0)
    llm.seen = seen
    return llm


def notes_section(md: str) -> str:
    start = md.index("## Important notes")
    return md[start:md.index("\n## ", start + 1)]


print("\n1. FACTS and NOTES")
cases = {name: load(name) for name in ("windows", "chargers", "windows_nodata", "plastic")}
for name, (research, intake, _) in cases.items():
    facts, notes = build_facts(research, intake)
    found = EVIDENCE_ID_RE.search(facts)
    check(f"{name}: no evidence IDs in FACTS", not found, found and found.group(0))
    check(f"{name}: FACTS gives the verdict", f"VERDICT: {research['verdict']}" in facts)
    check(f"{name}: no gap marker in FACTS", "REGULATORY_GAP_DETECTED" not in facts)
    hidden = [n["nid"] for n in notes if n["mandatory"] and n["text"] in facts]
    check(f"{name}: mandatory notes are not sent to the LLM", not hidden, hidden)
    check(f"{name}: no 'MANDATORY' label in FACTS", "MANDATORY" not in facts)

research, intake, _ = cases["windows"]
facts, notes = build_facts(research, intake)
mand = {n["source_id"] for n in notes if n["mandatory"]}
check("windows: mandatory notes are issuer, duty basis, self-declaration and (7.6e) the two with a qualifier",
      mand == {"P-UAE-ISSUER", "TOOL:duty:76101000", "TOOL:origin:76101000",
               "TOOL:rule_lookup:76101000", "P-MOET-FACTORY-REG"}, mand)
check("windows: rule-interpretation note is mandatory since 7.6e ('interpretation')",
      all(n["mandatory"] for n in notes if n["source_id"].startswith("TOOL:rule_lookup")))
check("windows: problem 57 prevented by code (7.6e): 'likely not eligible' printed verbatim, never sent",
      any(n["mandatory"] and "likely not eligible" in n["text"] for n in notes)
      and "likely not eligible" not in facts)
check("windows: no optional notes left, so none sent", "NOTES: none" in facts, facts.split("NOTES")[-1][:80])

print("\n   7.6e qualifier rule (problem 78)")
for text, want in (("Interpretation: de minimis helps only the tariff-shift part of a rule.", True),
                   ("Free-zone producers are likely not eligible.", True),
                   ("Electronic certificates are reportedly uploaded to e-Sanchit.", True),
                   ("This is unconfirmed.", True), ("'Direct labour cost' is not defined.", True),
                   ("Mansha has not checked anti-dumping duty.", True), ("Unlikely to apply.", True),
                   ("Cumulation is bilateral only.", False), ("India may charge anti-dumping duty.", False),
                   ("The defined term is used.", False), ("Checked by the ministry.", False)):
    check(f"qualifier rule: {'mandatory' if want else 'optional '} <- {text!r}",
          is_mandatory("P-AGR-3.7-CUMULATION", text) == want)
two_m = [{"mandatory": True}] * 6 + [{"mandatory": False}] * 3
check("Builder keeps 2 note slots even with 6 verbatim notes", max_llm_notes(two_m) == MIN_LLM_NOTES == 2)
check("...and no slots when there are no optional notes", max_llm_notes([{"mandatory": True}] * 6) == 0)
check("...and 6 minus the verbatim ones otherwise", max_llm_notes([{"mandatory": True}] * 2
                                                                  + [{"mandatory": False}] * 9) == 4)

# The real windows answer has no optional note any more (both carry a qualifier). The prose-check
# sections below need one, so they use windows with one plain note added (the KB's cumulation
# summary, no qualifier).
PLAIN_NOTE = {"note": "Cumulation is bilateral only: originating materials from India used in production "
                      "in the UAE may be counted as originating.", "source_id": "P-AGR-3.7-CUMULATION"}
cases["windows"] = (dict(cases["windows"][0], caveats=cases["windows"][0]["caveats"] + [PLAIN_NOTE]),
                    *cases["windows"][1:])
research, intake, _ = cases["windows"]
facts, notes = build_facts(research, intake)
check("windows + plain note: that note is optional and sent",
      [n["text"] for n in notes if not n["mandatory"]] == [PLAIN_NOTE["note"]] and PLAIN_NOTE["note"] in facts)
limit = max_llm_notes(notes)
check(f"windows + plain note: NOTES header gives the limit ({limit})", f"at most {limit} items" in facts)
check("windows: saving in FACTS", "ESTIMATED SAVING: 10000.00 AED" in facts)
check("windows: CTSH and VA terms sent", "CTSH = " in facts and "VA = " in facts)
check("windows: origin check names explained (problem 30)",
      "minimal operations check = " in facts and "final manufacture check = " in facts)
ch_facts, _ = build_facts(*cases["chargers"][:2])
check("chargers: check names with '_' and de minimis explained",
      "minimal operations check = " in ch_facts and "de minimis = " in ch_facts)
check("plastic: no check terms when no checks were run",
      "minimal operations check = " not in build_facts(*cases["plastic"][:2])[0])
_, nd_notes = build_facts(*cases["windows_nodata"][:2])
n_cav = len(cases["windows_nodata"][0]["caveats"])
n_opt = sum(not n["mandatory"] for n in nd_notes)
check(f"windows_nodata: all {n_cav} caveats kept as notes", len(nd_notes) == n_cav)
check("windows_nodata: 6 mandatory notes since 7.6e (2 by source, 4 by qualifier), numbered M1..M6",
      [n["nid"] for n in nd_notes if n["mandatory"]] == [f"M{i}" for i in range(1, 7)])
check(f"windows_nodata: {n_opt} optional notes, numbered N1..N{n_opt}",
      [n["nid"] for n in nd_notes if not n["mandatory"]] == [f"N{i}" for i in range(1, n_opt + 1)])
nd_facts, _ = build_facts(*cases["windows_nodata"][:2])
check("windows_nodata: saving needs the value", "cannot be estimated without the shipment value" in nd_facts)
check(f"windows_nodata: LLM may still write {MIN_LLM_NOTES} notes (7.6e floor; 6 are verbatim)",
      f"at most {MIN_LLM_NOTES} items" in nd_facts)
pl_facts, _ = build_facts(*cases["plastic"][:2])
check("plastic: CEPA rate shown as excluded", "CEPA RATE: excluded" in pl_facts)

for name in ("chargers", "plastic"):
    _, n = build_facts(*cases[name][:2])
    check(f"{name}: estimate note dropped (no saving shown)",
          not any(x["text"].startswith(ESTIMATE_NOTE_START) for x in n))
    check(f"{name}: no notes about claiming the CEPA rate (no CEPA rate can apply)",
          not any(x["source_id"].startswith(("TOOL:duty:", "TOOL:coo_fee"))
                  or x["source_id"] in ("P-IN-DUTY-SCOPE", "P-UAE-ISSUER", "P-MOET-FACTORY-REG", "P-IN-IMPORTER")
                  for x in n),
          [x["source_id"] for x in n])
paraphrased = dict(cases["chargers"][0], caveats=[
    {"note": "India charges duty on the CIF value, so actual amounts will differ from the estimate.",
     "source_id": "TOOL:duty:85044030"},
    {"note": "Operations and final manufacture are the exporter's own declaration.",
     "source_id": "TOOL:origin:85044030"},
    {"note": "No official page names the Ministry of Foreign Trade as the issuer.", "source_id": "P-UAE-ISSUER"},
    {"note": "Free-zone producers are likely not eligible for Factory Registration.",
     "source_id": "P-MOET-FACTORY-REG"},
    {"note": "Mansha has not checked anti-dumping duty on this product.", "source_id": "TL-IN-85044030"}])
_, n = build_facts(paraphrased, cases["chargers"][1])
check("not eligible: claim notes dropped by source (duty, issuer, factory registration); others kept",
      [x["source_id"] for x in n] == ["TOOL:origin:85044030", "TL-IN-85044030"], [x["source_id"] for x in n])
_, n = build_facts(*cases["windows"][:2])
check("eligible: duty and issuer notes kept", any(x["source_id"].startswith("TOOL:duty:") for x in n)
      and any(x["source_id"] == "P-UAE-ISSUER" for x in n))
check("windows: estimate note kept (saving shown)",
      any(x["text"].startswith(ESTIMATE_NOTE_START) for x in notes))
tool_notes = duty_estimate("76101000", {"amount": 100000, "currency": "AED"}).notes
check("duty tool's estimate note still starts with ESTIMATE_NOTE_START",
      any(x.startswith(ESTIMATE_NOTE_START) for x in tool_notes), tool_notes)

# Problem 53 (Step 9.6e): the Builder must know the CEPA rate cuts Basic Customs Duty only.
for name, want in (("windows", True), ("chargers", True), ("plastic", False)):
    r53, i53, _ = load(name)
    facts53, _ = build_facts(r53, i53)
    terms = facts53.split("TERMS:")[1].split("\n\n")[0]
    check(f"{name}: TERMS {'says' if want else 'does not say'} 'Basic Customs Duty only'",
          ("Basic Customs Duty only" in terms) == want, terms)

print("\n2. Prose checks")
good = good_windows_prose(notes)
check("good prose passes", check_prose(good, facts, notes) == [], check_prose(good, facts, notes))


def expect_problem(label, mutate):
    p = copy.deepcopy(good)
    mutate(p)
    probs = check_prose(p, facts, notes)
    check(label, bool(probs))


first_opt = next(n["nid"] for n in notes if not n["mandatory"])
expect_problem("invented number fails", lambda p: p.update(duty=p["duty"] + " That is AED 40,000."))
expect_problem("computed difference fails", lambda p: p.update(duty="The rate falls by 10 points, 9% lower."))
expect_problem("leaked evidence ID fails", lambda p: p.update(classification="See TL-IN-76101000."))
expect_problem("leaked note number fails", lambda p: p.update(summary=p["summary"] + " See N2."))
expect_problem("leaked mandatory note number fails", lambda p: p.update(summary=p["summary"] + " See M1."))
expect_problem("code word fails", lambda p: p.update(origin="The product QUALIFIES."))
expect_problem("empty field fails", lambda p: p.update(summary=" "))
expect_problem("citing a mandatory note fails (the LLM never sees them)",
               lambda p: p["notes"][0].update(**{"from": ["M1"]}))
expect_problem("unknown note number fails", lambda p: p["notes"][0]["from"].append("N99"))
expect_problem("empty from fails", lambda p: p["notes"][0].update(**{"from": []}))
expect_problem(f"more than {limit} notes fails (6 in total with the {sum(x['mandatory'] for x in notes)} mandatory)",
               lambda p: p.update(notes=[{"text": "x", "from": [first_opt]}] * (limit + 1)))
expect_problem("note number not in its own notes fails",
               lambda p: p["notes"].append({"text": "Keep records for 7 years.", "from": [first_opt]}))
# 7.6b, problem 53: "all duty removed" wording is a problem (the CEPA rate cuts Basic Customs Duty only)
for wrong in ("This eliminates your customs duty in India.", "The goods enter India duty-free.",
              "There is no customs duty to pay.", "The duty is eliminated.", "It removes all import charges.",
              "The windows enter free of customs duty."):
    expect_problem(f"53: {wrong!r} fails", lambda p, w=wrong: p.update(summary=p["summary"] + " " + w))
expect_problem("53: also inside a note", lambda p: p["notes"][0].update(text=p["notes"][0]["text"] + " It is duty-free."))
p = copy.deepcopy(good)
p["summary"] += " " + "The windows enter duty-free."
check("53: the problem names the field and says 'Basic Customs Duty only'",
      any(x.startswith("`summary`") and "Basic Customs Duty only" in x for x in check_prose(p, facts, notes)),
      check_prose(p, facts, notes))
for fine in ("The CEPA rate removes Basic Customs Duty.", "It eliminates the Basic Customs Duty.",
             "Basic Customs Duty is eliminated under the CEPA.", "No duty saving can be estimated."):
    p = copy.deepcopy(good)
    p["duty"] += " " + fine
    check(f"53: {fine!r} is fine (names BCD, or no saving)", check_prose(p, facts, notes) == [],
          check_prose(p, facts, notes))
p = copy.deepcopy(good)
p["notes"] = []
check("no LLM notes is fine (mandatory notes are added by code)", check_prose(p, facts, notes) == [])
p = copy.deepcopy(good)
p["summary"] = p["summary"].replace("AED 10,000", "AED 10000")
check("thousands separators are the same number", check_prose(p, facts, notes) == [])

print("\n3. Code-only report for each verdict")
kb_sources = load_corridor("india")["sources"]
for name, (research, intake, pack) in cases.items():
    _, n = build_facts(research, intake)
    md = render_report(research, intake, fallback_prose(research, n), n, pack.id_sources, kb_sources)
    out = Path("runs") / name
    out.mkdir(parents=True, exist_ok=True)
    (out / "report_fallback.md").write_text(md, encoding="utf-8")
    has_list = "## Step-by-step checklist" in md
    check(f"{name}: checklist only when a claim is possible",
          has_list == (research["verdict"] in ("ELIGIBLE", "NEEDS_MORE_DATA")))
    check(f"{name}: one checkbox per procedure step", md.count("- [ ] ") == (
        len(research["procedure"]) if has_list else 0))
    if has_list:
        check(f"{name}: checklist label is 'Authority'", "*Authority: " in md and "*Who: " not in md)
    check(f"{name}: sources are numbered https links",
          "## Sources\n\n1. [" in md and "](https://" in md)
    check(f"{name}: disclaimer present", "not an official origin ruling" in md)
    leaks = [w for w in ("REGULATORY_GAP_DETECTED", "NOT_APPLICABLE", "TOOL:", "PSR-IN", "TL-IN") if w in md]
    check(f"{name}: no IDs or code words", not leaks, leaks)
    if n:
        sec = notes_section(md)
        check(f"{name}: every note appears verbatim", all(f"- {x['text']}" in sec for x in n))
md_nd = (Path("runs") / "windows_nodata" / "report_fallback.md").read_text(encoding="utf-8")
check("windows_nodata: 'What's still needed' comes right after the summary",
      md_nd.index("## What's still needed") < md_nd.index("## Product classification"))
research, intake, pack = cases["windows"]
ar_intake = dict(intake, language="ar")
md_ar = render_report(research, ar_intake, good, notes, pack.id_sources, kb_sources)
check("Arabic headings and disclaimer", "## الملخص" in md_ar and "ليس قرارًا رسميًا" in md_ar)
check("Arabic checklist label is 'الجهة المختصة'", "*الجهة المختصة: " in md_ar)

print("\n3b. Small rendering rules (Step 9.5)")
ch_research, ch_intake, _ = cases["chargers"]
_, ch_notes = build_facts(ch_research, ch_intake)
check("fallback summary for NOT_ELIGIBLE points to the failed checks",
      "checks that failed" in fallback_prose(ch_research, ch_notes)["summary"])
check("source numbers in a citation are sorted", cite([7, 9, 6, 10]) == " [6][7][9][10]")
gap_research = dict(ch_research, gaps=["REGULATORY_GAP_DETECTED: the rule for this line is not loaded."])
check("gap marker becomes plain words in 'still needed'",
      still_needed(gap_research) == ["not in Mansha's sources: the rule for this line is not loaded."],
      still_needed(gap_research))

print("\n4. The call loop (fake LLM)")
bad = dict(good, duty="The saving is AED 40,000.")

llm = fake_llm(good)
r = run_document_builder(research, intake, pack.id_sources, llm=llm)
check("good first reply: 1 call, no fallback", len(llm.seen) == 1 and not r.used_fallback)
check("report contains the LLM summary", good["summary"] in r.markdown)
sec = notes_section(r.markdown)
mand_texts = [x["text"] for x in notes if x["mandatory"]]
check("mandatory notes shown verbatim in the LLM report", all(f"- {t}" in sec for t in mand_texts))
check("mandatory notes come before the LLM notes",
      max(sec.index(t) for t in mand_texts) < sec.index(good["notes"][0]["text"]))
cap = max(MAX_NOTES, len(mand_texts) + MIN_LLM_NOTES)   # 7.6e: verbatim notes + at least 2 LLM items
check(f"report has at most {cap} notes (6, or the verbatim ones + {MIN_LLM_NOTES})",
      sec.count("\n- ") <= cap, sec.count("\n- "))
sent = "\n".join(m["content"] for m in llm.seen[0])
check("mandatory note texts never reach the LLM", not any(t in sent for t in mand_texts))

llm = fake_llm(bad, good)
r = run_document_builder(research, intake, pack.id_sources, llm=llm)
check("bad then good: 2 calls, no fallback", len(llm.seen) == 2 and not r.used_fallback)
check("round 2 sends the corrections", "CORRECTIONS" in llm.seen[1][-1]["content"]
      and "40000" in llm.seen[1][-1]["content"])

llm = fake_llm(bad, bad)
r = run_document_builder(research, intake, pack.id_sources, llm=llm)
check("bad twice: code-only report", r.used_fallback and r.problems and "40,000" not in r.markdown)
check("code-only report keeps the mandatory notes verbatim",
      all(f"- {t}" in notes_section(r.markdown) for t in mand_texts))

failed = [{"attempt": 1, "ok": False, "http_status": 502, "problem": "HTTP 502",
           "waited_before_retry_s": 30}, {"attempt": 2, "ok": False, "problem": "empty reply"}]
llm = fake_llm(LLMCallError("router down", failed))
r = run_document_builder(research, intake, pack.id_sources, llm=llm)
check("LLM error: code-only report", r.used_fallback and "## Summary" in r.markdown)
check("LLM error: the failed call's attempts are kept", r.failed_attempts == failed, r.failed_attempts)
llm = fake_llm(bad, LLMCallError("router down", failed[:1]))
r = run_document_builder(research, intake, pack.id_sources, llm=llm)
check("error in round 2: round 1 call and failed attempts both kept",
      len(r.llm_calls) == 1 and r.failed_attempts == failed[:1] and r.used_fallback)
llm = fake_llm(good)
r = run_document_builder(research, intake, pack.id_sources, llm=llm)
check("no error: no failed attempts", r.failed_attempts == [])

msgs = build_messages(facts, "en")
check("system prompt has the Agent 4 section and language",
      "AGENT 4" in msgs[0]["content"] and "Write in English" in msgs[0]["content"])
check("no unfilled {language} left", "{language}" not in msgs[0]["content"])
check("prompt tells the model mandatory notes are printed by code",
      "word for word by code" in msgs[0]["content"])

print("\n5. The prose check in the call loop (Step 7.6, scripted review)")


def scripted(*outcomes):
    """A stand-in for review_prose: returns the given ProseQAOutcomes in order, records its input."""
    queue = list(outcomes)
    seen: list[tuple[str, dict]] = []

    def review(facts_text, prose, *, llm):
        seen.append((facts_text, copy.deepcopy(prose)))
        return queue.pop(0)
    review.seen = seen
    return review


def ok_review():
    return ProseQAOutcome("APPROVED", scores={"factuality": 1, "completeness": 1}, note="APPROVED")


def rejected_review(*corrections):
    return ProseQAOutcome("REJECTED", list(corrections), {"factuality": 0, "completeness": 1}, note="REJECTED")


def error_review():
    return ProseQAOutcome("ERROR", note="prose QA call failed: prose NOT reviewed by QA")


FIX = "notes[0].text: drops 'likely'. Fix: keep 'likely not eligible' (see N1)"

r = run_document_builder(research, intake, pack.id_sources, llm=fake_llm(good))
check("no review asked for: review_status SKIPPED, one round", r.review_status == "SKIPPED"
      and len(r.rounds) == 1 and r.rounds[0]["review"] is None)

rv = scripted(ok_review())
llm = fake_llm(good)
r = run_document_builder(research, intake, pack.id_sources, llm=llm, review=rv)
check("approved: 1 Builder call, 1 review, LLM prose kept", len(llm.seen) == 1 and len(rv.seen) == 1
      and not r.used_fallback and r.review_status == "APPROVED" and good["summary"] in r.markdown)
check("review gets exactly the Builder's input (FACTS + sent NOTES) and its prose",
      rv.seen[0][0] == facts and rv.seen[0][1] == good)

rv = scripted(rejected_review(FIX), ok_review())
llm = fake_llm(good, good)
r = run_document_builder(research, intake, pack.id_sources, llm=llm, review=rv)
retry = llm.seen[1][-1]["content"] if len(llm.seen) > 1 else "(no retry was sent)"
check("QA rejects, then approves: 2 Builder calls, 2 reviews, no fallback",
      len(llm.seen) == 2 and len(rv.seen) == 2 and not r.used_fallback and r.review_status == "APPROVED")
check("QA's correction reaches the Builder's retry, prefixed 'QA:'", "CORRECTIONS" in retry
      and "QA: notes[0].text: drops 'likely'" in retry, retry)
check("rounds record what was sent", r.rounds[1]["corrections_sent"] == [f"QA: {FIX}"])

rv = scripted(rejected_review(FIX), ok_review())
llm = fake_llm(bad, good)
r = run_document_builder(research, intake, pack.id_sources, llm=llm, review=rv)
retry = llm.seen[1][-1]["content"] if len(llm.seen) > 1 else "(no retry was sent)"
check("P1: code problem + QA rejection share the ONE retry", len(llm.seen) == 2 and len(rv.seen) == 2
      and "40000" in retry and "QA: notes[0].text" in retry and not r.used_fallback, retry)
check("code problems kept per round", r.rounds[0]["code_problems"] and not r.rounds[1]["code_problems"])

rv = scripted(rejected_review(FIX), rejected_review(FIX))
llm = fake_llm(good, good)
r = run_document_builder(research, intake, pack.id_sources, llm=llm, review=rv)
check("P2 A: rejected twice -> code-only report", r.used_fallback and r.review_status == "FALLBACK"
      and good["summary"] not in r.markdown and "## Summary" in r.markdown)
check("rejected twice: reason and corrections kept", "prose QA" in r.fallback_reason
      and r.problems == [f"QA: {FIX}"], (r.fallback_reason, r.problems))

rv = scripted(error_review())
llm = fake_llm(good)
r = run_document_builder(research, intake, pack.id_sources, llm=llm, review=rv)
check("P3 A: QA ERROR -> code-checked prose kept, marked ERROR (NOT reviewed)",
      len(llm.seen) == 1 and not r.used_fallback and r.review_status == "ERROR"
      and good["summary"] in r.markdown)

rv = scripted(error_review(), ok_review())
llm = fake_llm(bad, good)
r = run_document_builder(research, intake, pack.id_sources, llm=llm, review=rv)
check("QA ERROR + code problem: retry, then the new prose is reviewed and approved",
      len(llm.seen) == 2 and len(rv.seen) == 2 and r.review_status == "APPROVED"
      and "QA:" not in llm.seen[1][-1]["content"])

rv = scripted(ok_review(), error_review())
llm = fake_llm(bad, good)
r = run_document_builder(research, intake, pack.id_sources, llm=llm, review=rv)
check("final prose not reviewed (round 2 ERROR) -> ERROR, prose kept", r.review_status == "ERROR"
      and not r.used_fallback)

rv = scripted(rejected_review(FIX))
llm = fake_llm(good, LLMCallError("router down", failed[:1]))
r = run_document_builder(research, intake, pack.id_sources, llm=llm, review=rv)
check("QA rejects, Builder retry fails -> code-only report", r.used_fallback
      and r.fallback_reason == "Builder call failed in round 2" and len(rv.seen) == 1, r.fallback_reason)

llm = fake_llm(good, good)
r = run_document_builder(research, intake, pack.id_sources, llm=llm, review=scripted(rejected_review(), ok_review()))
check("rejected without corrections: the retry still says so", len(llm.seen) == 2
      and "QA: rejected without corrections" in llm.seen[1][-1]["content"])

rv = scripted(ok_review())
llm = fake_llm(dict(good, summary=""), good)
r = run_document_builder(research, intake, pack.id_sources, llm=llm, review=rv)
check("malformed prose is not sent for review (nothing to read); the retry's prose is",
      len(rv.seen) == 1 and rv.seen[0][1] == good and r.rounds[0]["review"] is None
      and r.review_status == "APPROVED")

print("\n" + ("ALL PASSED" if not failures else f"{len(failures)} FAILED: {failures}"))
sys.exit(1 if failures else 0)
