"""Offline tests for the Document Builder (no LLM, no router).

Uses the 4 saved Researcher outputs in samples/researcher_outputs/ and a fake LLM.
Section 5 (Step 7.6) checks the call loop with a scripted prose check (review=...).
Run: python -m scripts.test_document_builder
Also saves the code-only (fallback) report of each case to runs/<case>/report_fallback.md.
"""

import copy
import json
import re
import sys
from pathlib import Path

from mansha.document_builder import (
    AUTHORITY_TEXT,
    CHECKLIST_POINTER,
    FALLBACK_NOTICE,
    HEADINGS,
    CONDITION_TEXT,
    ESTIMATE_NOTE_START,
    EVIDENCE_ID_RE,
    FACTORY_REG_ID,
    FREE_ZONE_STEP_TEXT,
    MAX_NOTES,
    MIN_LLM_NOTES,
    SAVING_HOW_RE,
    TRANSLATED_KEYS,
    build_facts,
    check_translations,
    build_messages,
    check_prose,
    cite,
    condition_sentences,
    fallback_prose,
    is_mandatory,
    max_llm_notes,
    render_report,
    run_document_builder,
    script_problems,
    BRAND_LINE_AR,
    brand_slips,
    sent_notes,
    still_needed,
)
from mansha.evidence import build_evidence
from mansha.kb import load_corridor
from mansha.llm_client import LLMCallError, LLMResult
from mansha.prose_qa import ProseQAOutcome
from mansha.report_check import check_report
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
                   "rate in India. The estimated saving is AED 10,000.",   # code adds the checklist pointer (2A)
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
check("tariff-lookup notes are printed verbatim (problem 98, 7.6l)",
      is_mandatory("TOOL:tariff_lookup", "8-digit codes are national and differ between the UAE and India."))
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
# 7.6h 4a, problem 67: wording that explains how the saving is worked out is a problem.
# Replays: the exact live fields (runs/pipeline/*/builder.json) from 17, 19 and 23 Oct windows_nodata.
LIVE_67 = [
    ("17 Oct 17:01 summary", "summary", "Mansha cannot confirm whether the aluminium window frames qualify for the preferential duty rate under the India-UAE CEPA because the required information is missing. If the product qualifies, the saving would be the difference between the normal rate and the CEPA rate, but the exact amount cannot be estimated without the shipment value. To proceed, the exporter needs to provide a bill of materials, a declaration, and the shipment value in AED."),
    ("17 Oct 18:06 summary", "summary", "Mansha cannot confirm the result yet, because information is missing. To proceed, you need to provide a bill of materials, a declaration, the shipment value in AED, and confirm the HS code. If the product qualifies, the duty saving would be the difference between the normal import duty rate (MFN rate) and the reduced rate under the trade agreement (CEPA rate), but the amount cannot be estimated without the shipment value."),
    ("17 Oct 18:06 duty", "duty", "Under the India-UAE CEPA, the normal (MFN) rate for this product is 10% and the CEPA rate is 0%. The saving would be the difference between these rates, but the exact amount cannot be estimated without the shipment value in AED."),
    ("19 Oct 18:38 duty", "duty", "Under the India-UAE CEPA, the normal (MFN) rate for this product is 10%, while the CEPA rate is 0%. Because the shipment value is not provided, the estimated saving cannot be calculated yet. Once the shipment value is known, the saving can be determined based on the difference between the two rates."),
    ("23 Oct 20:05 summary", "summary", "Mansha cannot confirm the result yet because complete bill of materials data and manufacturer origin declaration details are missing. If the product qualifies, the saving would be the difference between the normal (MFN) rate and the CEPA rate."),
    ("23 Oct 20:08 summary", "summary", "Mansha cannot confirm the result yet, because the bill of materials, declaration and shipment value are missing. If the product qualifies, the saving would be the difference between the normal rate and the CEPA rate."),
]
for label, fld, text in LIVE_67:
    p = copy.deepcopy(good)
    p[fld] = text
    probs = check_prose(p, facts, notes)
    check(f"67 replay {label}: caught in `{fld}` with the fix", any(
        x.startswith(f"`{fld}`") and "explains how the saving is worked out" in x for x in probs), probs)
for wrong in ("The saving is calculated by multiplying the shipment value by the rate difference.",
              "Multiply the shipment value by the difference in rates.",
              "Your saving is worked out as the gap between the two rates."):
    expect_problem(f"67: {wrong!r} fails", lambda p, w=wrong: p.update(duty=p["duty"] + " " + w))
expect_problem("67: also inside a note",
               lambda p: p["notes"][0].update(text="The saving is the difference between the two rates."))
for fine in ("The estimated saving cannot be estimated without the shipment value.",
             "If the product qualifies, the saving cannot be estimated without the shipment value.",
             "The estimated saving cannot be determined without the shipment value.",
             "The CEPA rate is lower than the normal (MFN) rate.",
             "The saving cannot be calculated yet."):
    p = copy.deepcopy(good)
    p["duty"] += " " + fine
    check(f"67: {fine!r} is fine", check_prose(p, facts, notes) == [], check_prose(p, facts, notes))
n2 = copy.deepcopy(notes)
src = next(n for n in n2 if not n["mandatory"])
src["text"] += " The saving depends on the difference between the two rates."
p = copy.deepcopy(good)
p["notes"] = [{"text": "The saving depends on the difference between the two rates.", "from": [src["nid"]]}]
check("67: a note item may repeat it when its own note says it",
      not any("worked out" in x for x in check_prose(p, facts, n2)), check_prose(p, facts, n2))
p = copy.deepcopy(good)
p["summary"] = p["summary"].replace("AED 10,000", "AED 10000")
check("thousands separators are the same number", check_prose(p, facts, notes) == [])

# N15 (222746): the script check. Arabic prose with Dots3's faults, then clean Arabic (215427 style).
ar_good = {"summary": "لا يمكن لـ Mansha تأكيد النتيجة بعد، لأن قائمة المواد ناقصة.",
           "classification": "الرمز الجمركي HS للمنتج مذكور أعلاه (رمز النظام المنسق).",
           "duty": "السعر العادي MFN أعلى من سعر الاتفاقية CEPA، ويُحسب على أساس FOB أو Ex-Works.",
           "origin": "تشترط القاعدة تغيير البند الفرعي CTSH مع قيمة مضافة VA، وتُقدَّم الشهادة عبر e-Sanchit "
                     "وفق قواعد CAROTAR، ويطالب المستورد بالسعر عند تقديم بيان الإدخال (bill of entry) "
                     "عبر eservices.moec.gov.ae.",
           "notes": []}
check("N15: clean Arabic prose passes the script check", check_prose(ar_good, facts, notes, "ar") == [],
      check_prose(ar_good, facts, notes, "ar"))
bad = {"summary": "وال迈尔斯 الم估算", "classification": "الرمز للproduct", "duty": "ال_AGREEMENT هي",
       "origin": "Rule of origin هي CTSH (يتم including التحقق)"}
for key, want in (("summary", "another script (迈尔斯估算)"), ("classification", "['للproduct']"),
                  ("duty", "['ال_AGREEMENT']"), ("origin", "['Rule', 'of', 'origin', 'including']")):
    p = copy.deepcopy(ar_good)
    p[key] = bad[key]
    probs = check_prose(p, facts, notes, "ar")
    check(f"N15: {key} {bad[key]!r} -> {want}", len(probs) == 1 and probs[0].startswith(f"`{key}`")
          and want in probs[0], probs)
p = copy.deepcopy(ar_good)
p["notes"] = [{"text": "عملية بسيطة أوucceeding لا تمنح المنشأ.", "from": [n["nid"] for n in sent_notes(notes)][:1]}]
check("N15: a note item is checked too", any(x.startswith("notes[0]") and "أوucceeding" in x
                                              for x in check_prose(p, facts, notes, "ar")))
check("N15: English prose is not held to the Arabic rules", check_prose(good, facts, notes, "en") == [])
p = copy.deepcopy(good)
p["summary"] += " 估算"
check("N15: another script fails an English report too",
      any("another script (估算)" in x for x in check_prose(p, facts, notes)), check_prose(p, facts, notes))
check("N15: accented Latin letters are Latin", script_problems("café naïve", "en")["other"] == [])

# Brand (015311): Arabic FACTS carry "منشأ"; English FACTS and all NOTES are unchanged.
w_research, w_intake, _ = cases["windows"]
en_facts, en_notes = build_facts(w_research, w_intake)
ar_facts, ar_notes = build_facts(w_research, {**w_intake, "language": "ar"})
ar_head, en_head = ar_facts.split("\n\nNOTES")[0], en_facts.split("\n\nNOTES")[0]
check("brand: Arabic FACTS open with the NAME line", ar_facts.startswith("FACTS:\n" + BRAND_LINE_AR + "\n"))
check("brand: Arabic FACTS say منشأ, never Mansha", "Mansha" not in ar_head and "(منشأ's confidence:" in ar_head,
      ar_head)
check("brand: Arabic FACTS are the English ones with only the name changed",
      ar_head == en_head.replace("FACTS:\n", "FACTS:\n" + BRAND_LINE_AR + "\n").replace("Mansha", "منشأ"))
check("brand: NOTES are the same in both languages",
      ar_facts.split("\n\nNOTES")[1] == en_facts.split("\n\nNOTES")[1] and ar_notes == en_notes)
check("brand: English FACTS keep Mansha and get no NAME line",
      "(Mansha's confidence:" in en_facts and "NAME:" not in en_facts)
check("brand: the 015311 slips are found",
      brand_slips("لا يمكن لمنصة منشأة تأكيد ذلك، بدرجة ثقة عالية من منشأة، ومستوى ثقة منشأة متوسط.")
      == ["منصة منشأة", "ثقة عالية من منشأة", "ثقة منشأة"])
check("brand: the ordinary word and the right name are not flagged",
      brand_slips("صُنع المنتج في منشأة صناعية في الإمارات، ومنشأة المصدّر مسجلة. بدرجة ثقة عالية من منشأ، "
                  "وفق مصادر منشأ.") == [])

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
# N15 step 2: the authority itself in Arabic; an actor not in AUTHORITY_TEXT stays as the KB has it.
auth_ar = re.findall(r"\*الجهة المختصة: ([^*]*)\.\*", md_ar)
check("N15: every Arabic authority line names an Arabic authority",
      auth_ar and all(a in AUTHORITY_TEXT["ar"].values() for a in auth_ar), auth_ar)
odd = copy.deepcopy(research)
odd["procedure"][0]["authority"] = "the Port Authority"
check("N15: an actor with no Arabic name stays in English",
      "*الجهة المختصة: The Port Authority.*" in render_report(odd, ar_intake, good, notes, pack.id_sources,
                                                             kb_sources))
kb_actors = {p["actor"].strip().lower() for p in load_corridor("india")["passages"]["passages"] if p.get("actor")}
check("N15: every actor in the KB has an Arabic name", kb_actors and kb_actors <= set(AUTHORITY_TEXT["ar"]),
      sorted(kb_actors - set(AUTHORITY_TEXT["ar"])))
md_en = render_report(research, intake, good, notes, pack.id_sources, kb_sources)
check("N15: English reports keep the English authority",
      not any(a in md_en for a in AUTHORITY_TEXT["ar"].values()))

print("\n3a. Deciding conditions: code cautions in the summary (problem 97, fix round 26 Oct)")


def summary_of(md: str) -> str:
    return md.split("## Summary\n\n", 1)[1].split("\n## ", 1)[0] if "## Summary\n\n" in md else \
        md.split("## الملخص\n\n", 1)[1].split("\n## ", 1)[0]


fz_research = copy.deepcopy(research)
fz_research["procedure"] = [dict(fz_research["procedure"][0], source_id=FACTORY_REG_ID)] + fz_research["procedure"][1:]
md_fz = render_report(fz_research, intake, good, notes, pack.id_sources, kb_sources, ["FREE_ZONE"])
check("FREE_ZONE: the caution follows the LLM's text, then the checklist pointer (ELIGIBLE)",
      summary_of(md_fz).strip() == " ".join([good["summary"].strip(), CONDITION_TEXT["FREE_ZONE"]["en"],
                                            CHECKLIST_POINTER["en"]]))
check("FREE_ZONE: marked under the factory-registration step",
      md_fz.count(FREE_ZONE_STEP_TEXT["en"]) == 1
      and md_fz.index(FREE_ZONE_STEP_TEXT["en"]) < md_fz.index("## Important notes"))
md_in = render_report(research, intake, good, notes, pack.id_sources, kb_sources, ["INDIAN_INPUTS"])
check("INDIAN_INPUTS: caution in the summary, no step marker",
      CONDITION_TEXT["INDIAN_INPUTS"]["en"] in summary_of(md_in) and FREE_ZONE_STEP_TEXT["en"] not in md_in)
check("no conditions: the report is unchanged",
      render_report(research, intake, good, notes, pack.id_sources, kb_sources, []) ==
      render_report(research, intake, good, notes, pack.id_sources, kb_sources))
md_fz_ar = render_report(fz_research, ar_intake, good, notes, pack.id_sources, kb_sources, ["FREE_ZONE"])
check("Arabic: the Arabic caution and step marker",
      CONDITION_TEXT["FREE_ZONE"]["ar"] in summary_of(md_fz_ar) and FREE_ZONE_STEP_TEXT["ar"] in md_fz_ar
      and CONDITION_TEXT["FREE_ZONE"]["en"] not in md_fz_ar)
check("no caution when no claim is possible (NOT_ELIGIBLE, NO_PREFERENCE, gap)",
      all(condition_sentences(["FREE_ZONE", "INDIAN_INPUTS"], v, "en") == []
          for v in ("NOT_ELIGIBLE", "NO_PREFERENCE", "REGULATORY_GAP_DETECTED")))
check("NEEDS_MORE_DATA keeps the caution; unknown codes and repeats ignored",
      condition_sentences(["FREE_ZONE", "FREE_ZONE", "X"], "NEEDS_MORE_DATA", "en")
      == [CONDITION_TEXT["FREE_ZONE"]["en"]])
rc_problems, _ = check_report(md_fz, research=fz_research, evidence_text=pack.text, message="")
check("the cautions pass the report check (no numbers, IDs or code words)", rc_problems == [], rc_problems)

# KB batch (27 Oct, 2A): code writes the pointer to the checklist; the LLM no longer does.
md_plain = render_report(research, intake, good, notes, pack.id_sources, kb_sources)
check("ELIGIBLE with steps: the summary ends with the checklist pointer, once",
      summary_of(md_plain).strip() == good["summary"].strip() + " " + CHECKLIST_POINTER["en"]
      and md_plain.count(CHECKLIST_POINTER["en"]) == 1, summary_of(md_plain))
check("... and the checklist it points to is below it",
      md_plain.index(CHECKLIST_POINTER["en"]) < md_plain.index("## " + HEADINGS["en"]["checklist"]))
check("Arabic: the Arabic pointer", CHECKLIST_POINTER["ar"] in summary_of(md_ar)
      and CHECKLIST_POINTER["en"] not in md_ar)
no_steps = dict(copy.deepcopy(research), procedure=[])
check("ELIGIBLE with no steps (no checklist): no pointer",
      CHECKLIST_POINTER["en"] not in render_report(no_steps, intake, good, notes, pack.id_sources, kb_sources))
for v in ("NEEDS_MORE_DATA", "NOT_ELIGIBLE", "NO_PREFERENCE"):
    rv = dict(copy.deepcopy(research), verdict=v)
    check(f"{v}: no pointer", CHECKLIST_POINTER["en"] not in render_report(rv, intake, good, notes,
                                                                           pack.id_sources, kb_sources))
check("the Builder prompt no longer asks the LLM for the pointer",
      "point the reader to the checklist" not in Path("prompts/document_builder.md").read_text(encoding="utf-8"))
rc_problems, _ = check_report(md_plain, research=research, evidence_text=pack.text, message="")
check("the pointer passes the report check", rc_problems == [], rc_problems)

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
obj_gaps = dict(ch_research, gaps=[{"text": "REGULATORY_GAP_DETECTED: the rule is not loaded.",
                                     "source_id": "TOOL:rule_lookup:85044030"}])
check("Step 7.6g gaps {text, source_id}: the text only, no source, in 'still needed'",
      still_needed(obj_gaps) == ["not in Mansha's sources: the rule is not loaded."], still_needed(obj_gaps))

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
check("N15: an English code-only report has no Arabic notice", FALLBACK_NOTICE["ar"] not in r.markdown)
r = run_document_builder(research, ar_intake, pack.id_sources, llm=fake_llm(bad, bad))
check("N15: an Arabic code-only report says first, in Arabic, that its prose is English",
      r.used_fallback and summary_of(r.markdown).startswith(FALLBACK_NOTICE["ar"] + "\n\n"),
      summary_of(r.markdown)[:120])

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

# 7.6h 4a: a 67 sentence goes into the Builder's one retry; if it persists, the code-only report.
bad67 = dict(good, summary=LIVE_67[-1][2])
llm = fake_llm(bad67, good)
r = run_document_builder(research, intake, pack.id_sources, llm=llm)
check("67: caught, then fixed in the retry (2 calls, no fallback)",
      len(llm.seen) == 2 and not r.used_fallback and "difference between" not in r.markdown)
check("67: the retry carries the saving correction",
      "explains how the saving is worked out" in llm.seen[1][-1]["content"])
llm = fake_llm(bad67, bad67)
r = run_document_builder(research, intake, pack.id_sources, llm=llm)
check("67: still there after the retry -> code-only report without it",
      r.used_fallback and not SAVING_HOW_RE.search(r.markdown))

msgs = build_messages(facts, "en")
check("system prompt has the Agent 4 section and language",
      "AGENT 4" in msgs[0]["content"] and "Write in English" in msgs[0]["content"])
check("no unfilled {language} left", "{language}" not in msgs[0]["content"])
check("prompt tells the model mandatory notes are printed by code",
      "word for word by code" in msgs[0]["content"])
check("prompt (7.6h): NEEDS_MORE_DATA gives the saving only when FACTS has an amount, never how it is worked out",
      "If FACTS gives a saving amount" in msgs[0]["content"]
      and "Never explain how a saving is worked out" in msgs[0]["content"]
      and 'give the saving only as "if the product qualifies".' not in msgs[0]["content"])

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

print("\n8. N15 (D): the title's product and 'still needed' in Arabic")
nd_research, nd_intake, nd_pack = cases["windows_nodata"]
nd_ar = dict(nd_intake, language="ar")
nd_needed = still_needed(nd_research)
check("windows_nodata has still-needed items", len(nd_needed) >= 1, nd_needed)
tr = {"product": "إطارات نوافذ من الألمنيوم", "needed": ["يرجى تقديم قائمة المواد."] * len(nd_needed)}
check("D: English reports need no translations", check_translations({}, nd_research, nd_intake, "en") == [])
check("D: good translations pass", check_translations(tr, nd_research, nd_ar, "ar") == [],
      check_translations(tr, nd_research, nd_ar, "ar"))
probs = check_translations({}, nd_research, nd_ar, "ar")
check("D: none given -> both asked for", len(probs) == 2 and probs[0].startswith("`product`")
      and probs[1].startswith("`needed`"), probs)
for label, bad_tr, want in (
        ("one item too many", dict(tr, needed=tr["needed"] + ["زائد"]), "`needed` must be a list of"),
        ("an English word in the product", dict(tr, product="إطارات Window"), "['Window']"),
        ("a number not in the item", dict(tr, needed=["قائمة المواد 999"] + tr["needed"][1:]), "['999']"),
        ("a note number", dict(tr, product="إطارات N1"), "remove 'N1'"),
        ("a long product", dict(tr, product="إطار " * 30), "short name")):
    probs = check_translations(bad_tr, nd_research, nd_ar, "ar")
    check(f"D: {label} -> {want}", any(want in x for x in probs), probs)

check("D: nothing still needed -> `needed` may be left out",
      still_needed(research) == [] and check_translations({"product": tr["product"]}, research,
                                                          ar_intake, "ar") == [])


def title_of(md: str) -> str:
    return md.split("\n", 1)[0]

def needed_of(md: str) -> str:
    return md.split("## " + HEADINGS["ar"]["needed"] + "\n\n", 1)[1].split("\n## ", 1)[0]

llm = fake_llm(dict(ar_good, **tr))
r = run_document_builder(nd_research, nd_ar, nd_pack.id_sources, llm=llm)
check("D: good translations are used: Arabic title and still-needed, one call",
      len(llm.seen) == 1 and not r.used_fallback and r.untranslated == []
      and title_of(r.markdown).endswith(": " + tr["product"])
      and needed_of(r.markdown).strip() == "\n".join(f"- {x}" for x in tr["needed"])
      and nd_needed[0] not in r.markdown, title_of(r.markdown))
llm = fake_llm(ar_good, dict(ar_good, **tr))
r = run_document_builder(nd_research, nd_ar, nd_pack.id_sources, llm=llm)
check("D: missing at first -> asked for in the one retry, then used",
      len(llm.seen) == 2 and "`needed`" in llm.seen[1][-1]["content"] and r.untranslated == []
      and title_of(r.markdown).endswith(tr["product"]))
llm = fake_llm(ar_good, ar_good)
r = run_document_builder(nd_research, nd_ar, nd_pack.id_sources, llm=llm)
check("D: still missing after the retry -> Arabic prose kept, English originals printed",
      len(llm.seen) == 2 and not r.used_fallback and len(r.untranslated) == 2
      and ar_good["summary"] in r.markdown and nd_needed[0] in r.markdown
      and title_of(r.markdown).endswith(nd_intake["product_description"])
      and not set(TRANSLATED_KEYS) & set(r.prose), r.untranslated)
r = run_document_builder(nd_research, nd_intake, nd_pack.id_sources, llm=fake_llm(dict(ar_good, **tr)))
check("D: in an English report the keys are ignored", tr["product"] not in r.markdown
      and nd_needed[0] in r.markdown and not set(TRANSLATED_KEYS) & set(r.prose))
rv = scripted(ok_review())
r = run_document_builder(nd_research, nd_ar, nd_pack.id_sources, llm=fake_llm(dict(ar_good, **tr)), review=rv)
check("D: prose QA reads only the fields it was built for", rv.seen[0][1] == ar_good
      and r.review_status == "APPROVED" and title_of(r.markdown).endswith(tr["product"]), rv.seen[0][1].keys())

print("\n9. B (28 Oct): the chain by language, the one code fallback to auto:long, every round's prose")


def chain_llm(*replies):
    """fake_llm that also records the chain of each call."""
    inner = fake_llm(*replies)

    def llm(agent, chain, messages, **kwargs):
        llm.chains.append(chain)
        return inner(agent, chain, messages, **kwargs)
    llm.chains, llm.seen = [], inner.seen
    return llm


ar_ok = dict(ar_good, **tr)
ar_bad = dict(ar_ok, summary=ar_good["summary"] + " 中文")
down = [{"attempt": 1, "ok": False, "problem": "connection error", "chain": "auto:arabic"}]
check("B: the bad Arabic used here is caught by the code checks",
      check_prose(ar_bad, build_facts(nd_research, nd_ar, "india")[0], build_facts(nd_research, nd_ar, "india")[1], "ar"))
llm = chain_llm(good)
r = run_document_builder(research, intake, pack.id_sources, llm=llm)
check("B: English -> auto:long, no fallback", llm.chains == ["auto:long"] and r.chain_fallback is None
      and r.rounds[0]["chain"] == "auto:long", llm.chains)
llm = chain_llm(ar_ok)
r = run_document_builder(nd_research, nd_ar, nd_pack.id_sources, llm=llm)
check("B: Arabic -> auto:arabic, no fallback", llm.chains == ["auto:arabic"] and r.chain_fallback is None
      and r.rounds[0]["chain"] == "auto:arabic" and not r.used_fallback, llm.chains)
llm = chain_llm(ar_bad, ar_ok)
r = run_document_builder(nd_research, nd_ar, nd_pack.id_sources, llm=llm)
check("B: Arabic round 2 stays on auto:arabic when round 1 only failed the checks",
      llm.chains == ["auto:arabic", "auto:arabic"] and r.chain_fallback is None, llm.chains)
check("B: every round's prose is saved (the rejected round 1 too)",
      r.rounds[0]["prose"] == ar_bad and r.rounds[1]["prose"] == ar_ok, [x["prose"] for x in r.rounds])
llm = chain_llm(LLMCallError("gemini down", down), ar_ok)
r = run_document_builder(nd_research, nd_ar, nd_pack.id_sources, llm=llm)
check("B: auto:arabic fails in round 1 -> the same round on auto:long, its prose used",
      llm.chains == ["auto:arabic", "auto:long"] and not r.used_fallback and r.rounds[0]["chain"] == "auto:long"
      and ar_good["summary"] in r.markdown, llm.chains)
check("B: the fallback is recorded by name, with the failed attempts",
      r.chain_fallback == {"from": "auto:arabic", "to": "auto:long", "round": 1, "reason": "gemini down"}
      and r.failed_attempts == down, r.chain_fallback)
llm = chain_llm(LLMCallError("gemini down", down), ar_bad, ar_ok)
r = run_document_builder(nd_research, nd_ar, nd_pack.id_sources, llm=llm)
check("B: after a fallback, round 2 stays on auto:long (once per run)",
      llm.chains == ["auto:arabic", "auto:long", "auto:long"] and r.chain_fallback["round"] == 1, llm.chains)
llm = chain_llm(ar_bad, LLMCallError("gemini down", down), ar_ok)
r = run_document_builder(nd_research, nd_ar, nd_pack.id_sources, llm=llm)
check("B: auto:arabic fails in round 2 -> round 2 on auto:long",
      llm.chains == ["auto:arabic", "auto:arabic", "auto:long"] and r.chain_fallback["round"] == 2
      and [x["chain"] for x in r.rounds] == ["auto:arabic", "auto:long"] and not r.used_fallback, llm.chains)
llm = chain_llm(LLMCallError("gemini down", down), LLMCallError("router down", failed[:1]))
r = run_document_builder(nd_research, nd_ar, nd_pack.id_sources, llm=llm)
check("B: auto:long fails too -> code-only report, both chains' failed attempts kept, no second fallback",
      llm.chains == ["auto:arabic", "auto:long"] and r.used_fallback and r.failed_attempts == down + failed[:1]
      and r.chain_fallback["to"] == "auto:long" and r.rounds[0]["prose"] is None, llm.chains)
llm = chain_llm(LLMCallError("router down", failed[:1]))
r = run_document_builder(research, intake, pack.id_sources, llm=llm)
check("B: an English auto:long failure has no chain fallback", llm.chains == ["auto:long"]
      and r.chain_fallback is None and r.used_fallback)

print("\n" + ("ALL PASSED" if not failures else f"{len(failures)} FAILED: {failures}"))
sys.exit(1 if failures else 0)
