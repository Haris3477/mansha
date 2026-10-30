"""Offline tests for the Researcher's code checks (no LLM, no router).

Run: python -m scripts.test_researcher
"""

import copy
import dataclasses
import glob
import json
import re
import sys
from pathlib import Path

import mansha.researcher as researcher_mod
from mansha.document_builder import (
    NOTE_MATCH_OF_NOTE,
    NOTE_MATCH_OF_ORIGINAL,
    note_match,
    note_originals,
)
from mansha.evidence import build_evidence, fmt_num, passages_of
from mansha.kb import load_corridor
from mansha.llm_client import LLMCallError, LLMResult
from mansha.researcher import (
    BCD_ONLY_RE,
    CLAIM_STEPS,
    EVIDENCE_ID_RE,
    GAP,
    GAP_BASIS,
    ORIGIN_DUP_OF_CAVEAT,
    ORIGIN_DUP_OF_NOTE,
    _plain_ids_in,
    add_tariff_notes,
    build_messages,
    check_researcher,
    claim_steps,
    coverage,
    drop_caveat_gaps,
    drop_claim_caveats,
    drop_follow_ups,
    drop_free_zone_follow_ups,
    drop_hs_follow_ups,
    drop_line_notes,
    drop_step_caveats,
    drop_user_data_gaps,
    fee_step,
    fill_authorities,
    fill_fixed_notes,
    fill_gap,
    fill_steps,
    fill_tariff_line,
    number_keys,
    plain_check_names,
    plain_evidence_ids,
    plain_follow_ups,
    qualifier_drops,
    recite_duty_notes,
    record_notes,
    record_sentences,
    restore_qualified_notes,
    run_researcher,
    strip_list_markers,
    unbracket_ids,
    write_origin_notes,
)
from mansha.tools.origin_calculator import (
    FREE_ZONE_NOTE,
    INDIAN_INPUTS_NOTE,
    OWN_DECLARATION_NOTE,
)
from scripts.eval_cases import BY_ID as EVAL_BY_ID
from scripts.pipeline_cases import DEV_INTAKES

failures: list[str] = []


def check(name: str, cond: bool, detail="") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def run(data, pack):
    return check_researcher(copy.deepcopy(data), pack)


def expect_ok(name, data, pack, verdict):
    problems, warnings, v = run(data, pack)
    check(f"{name}: no problems", not problems, problems)
    check(f"{name}: no warnings", not warnings, warnings)
    check(f"{name}: verdict {verdict}", v == verdict, v)


def expect_problem(name, data, pack):
    problems, _, _ = run(data, pack)
    check(f"{name}: caught", bool(problems), "no problem reported")


def cand(pack, cid):
    return next(c for c in pack.candidates if c["id"] == cid)


def not_o1(changes):
    """Change lines other than O1's (code writes the chosen line's origin-tool notes, 30 Oct)."""
    return [x for x in changes if not ("notes are written by code" in x or "note written from TOOL:origin:" in x
                                       or "it restates TOOL:origin:" in x
                                       or x.startswith("caveats: TOOL:origin:"))]


def origin_notes(data, pack, line):
    """(the answer's caveats citing TOOL:origin:<line>, that tool's notes): equal after O1."""
    tid = f"TOOL:origin:{line}"
    return [cv["note"] for cv in data["caveats"] if cv.get("source_id") == tid], pack.tool_results[tid]["notes"]


def _eq(a, b):
    return a == b


def pct(x):
    return f"{fmt_num(x)}%"


STEPS = [
    {"step": "Register the factory through Factory Registration.", "authority": "the ministry",
     "source_id": "P-MOET-FACTORY-REG"},
    {"step": "Apply through the Certificate of Origin for India e-service; fees from AED 10 to AED 200.",
     "authority": "the ministry e-services portal", "source_id": "P-MOET-COO-INDIA"},
]

print("== number_keys")
check("thousands and decimals", number_keys("10,000.00 AED") == {"10000"})
check("trailing .0", number_keys("49.0%") == {"49"})
check("article numbers kept", number_keys("Art. 3.5.1") == {"3.5.1"})
check("comma list split", number_keys("84,85") == {"84", "85"})

print("\n== strip_list_markers (Step 7.2: list numbering is not a fact)")
check("'(3)' and '(4)' removed", number_keys(strip_list_markers("(3) one input; (4) build-down 12%")) == {"12"})
check("line-start '3.' and '4)' removed",
      number_keys(strip_list_markers("1. Register\n  2) Apply\n3. Pay AED 10")) == {"10"})
check("article numbers kept", number_keys(strip_list_markers("Art. 3.5.1 (b)")) == {"3.5.1"})
check("decimals kept", number_keys(strip_list_markers("12.0% against 40%")) == {"12", "40"})
check("number ending a sentence kept", number_keys(strip_list_markers("a threshold of 40. Then")) == {"40"})
check("number in brackets with words kept", number_keys(strip_list_markers("(10 working days)")) == {"10"})
# The 17 Oct 14:29 chargers basis (Dots3): numbered the failed checks (1)-(4); the old check
# warned "number(s) ['3', '4'] not found in TOOL:origin:85044030".
LIVE_BASIS = (
    "The origin check failed on four counts: (1) final manufacture did not take place in the UAE; "
    "(2) the declared operations are all minimal operations under Art. 3.5.1 \u2014 (b) changes of "
    "packaging and breaking up and assembly of packages, (k) simple placing in bottles/cans/cases/boxes "
    "and simple packaging operations, (l) affixing or printing marks, labels, logos and like "
    "distinguishing signs \u2014 which never confer origin; (3) one non-originating input is in the same "
    "heading 8504 as the finished battery chargers, representing 88.0% of the FOB price, above the 10% "
    "de minimis tolerance; (4) value addition by build-down is 12.0% against a required threshold of "
    "40%, on an FOB basis. The shipment had 2 inputs, of which 1 is non-originating, on an FOB price basis.")
ci, cf, _ = DEV_INTAKES["chargers"]
cpack = build_evidence(ci, cf)
live = json.loads(Path("samples/researcher_outputs/chargers.json").read_text(encoding="utf-8"))["output"]
live["origin_result"]["basis"] = LIVE_BASIS
_, warns, _ = check_researcher(copy.deepcopy(live), cpack)
check("17 Oct chargers basis: no number warning", not [w for w in warns if "number(s)" in w], warns)
# Break test: without the stripping, the old false warning comes back.
saved_strip = researcher_mod.strip_list_markers
researcher_mod.strip_list_markers = lambda t: t
_, warns, _ = check_researcher(copy.deepcopy(live), cpack)
researcher_mod.strip_list_markers = saved_strip
check("break test: without stripping the '3', '4' warning returns",
      any("['3', '4']" in w for w in warns), warns)
wrong = copy.deepcopy(live)
wrong["origin_result"]["basis"] = LIVE_BASIS.replace("12.0%", "21.0%")
_, warns, _ = check_researcher(wrong, cpack)
check("a real wrong number is still caught", any("['21']" in w for w in warns), warns)

# ---------------- windows: qualifies ----------------
print("\n== Windows (qualifies)")
w = build_evidence({"product_description": "aluminium window frames", "hs_code_given": None,
                    "shipment_value": {"amount": 100000, "currency": "AED"}},
                   "samples/windows_qualifies")
wc = cand(w, "TL-IN-76101000")
GOOD_W = {
    "reasoning": ["..."] * 7,
    "classification": {"tariff_line": "76101000", "description": wc["description"],
                       "confidence": "high", "source_id": "TL-IN-76101000"},
    "tariff": {"agreement": "India-UAE CEPA", "mfn_rate": pct(wc["mfn"]["effective_rate_pct"]),
               "preferential_rate": pct(wc["cepa"]["rate_pct"]), "source_id": "TL-IN-76101000"},
    "origin_rule": {"rule": "CTSH + VA 45%", "source_id": "PSR-IN-R118"},
    "origin_result": {"status": "QUALIFIES",
                      "basis": "Final manufacture PASS; minimal operations PASS; CTSH PASS; "
                               "VA PASS: build-down 49.0% against a threshold of 45%.",
                      "source_id": "TOOL:origin:76101000"},
    "estimated_saving": {"status": "ESTIMATED", "amount": "10000.00", "currency": "AED",
                         "source_id": "TOOL:duty:76101000"},
    "procedure": STEPS,
    "caveats": [{"note": "Duty estimated on BCD only.", "source_id": "TOOL:duty:76101000"},
                {"note": w.fixed_notes["P-UAE-ISSUER"], "source_id": "P-UAE-ISSUER"}],  # as the KB says (7.6f)
    "follow_up_questions": [],
    "gaps": [],
}
expect_ok("windows correct answer", GOOD_W, w, "ELIGIBLE")

bad = copy.deepcopy(GOOD_W); bad["classification"]["source_id"] = "TL-IN-99999999"
expect_problem("invented source ID", bad, w)
bad = copy.deepcopy(GOOD_W)
bad["classification"].update(tariff_line="76109000", source_id="TOOL:tariff_lookup")
expect_problem("line not among candidates", bad, w)
bad = copy.deepcopy(GOOD_W); bad["origin_result"]["status"] = "NEEDS_MORE_DATA"
expect_problem("status contradicts calculator", bad, w)
bad = copy.deepcopy(GOOD_W); bad["origin_result"]["source_id"] = "TOOL:origin:76151030"
expect_problem("cites another line's origin result", bad, w)
bad = copy.deepcopy(GOOD_W); bad["estimated_saving"]["amount"] = "20000.00"
expect_problem("wrong saving amount", bad, w)
bad = copy.deepcopy(GOOD_W); bad["procedure"] = []
expect_problem("missing procedure", bad, w)
bad = copy.deepcopy(GOOD_W); bad["procedure"][0]["source_id"] = "TOOL:duty:76101000"
expect_problem("procedure step not from a passage", bad, w)
bad = copy.deepcopy(GOOD_W)
bad["caveats"] = [cv for cv in bad["caveats"] if cv["source_id"] != "P-UAE-ISSUER"]
expect_problem("procedure without the issuer caveat", bad, w)
ok = copy.deepcopy(GOOD_W)
ok["procedure"].append({"step": "Pay the certificate fee of AED 50.", "source_id": "TOOL:coo_fee"})
problems, warnings, _ = run(ok, w)
check("fee step citing TOOL:coo_fee accepted", not problems and not warnings, (problems, warnings))

ok = copy.deepcopy(GOOD_W); ok["estimated_saving"]["amount"] = "10,000"
problems, _, _ = run(ok, w)
check("saving written as '10,000' is accepted", not problems, problems)

warn = copy.deepcopy(GOOD_W); warn["origin_result"]["basis"] = "VA 62% meets the 45% threshold."
problems, warnings, _ = run(warn, w)
check("number not in record -> warning, not problem", not problems and bool(warnings), (problems, warnings))

gap = copy.deepcopy(GOOD_W)
gap["classification"] = {"tariff_line": GAP, "description": GAP, "confidence": "low",
                         "source_id": "TOOL:tariff_lookup"}
gap["origin_result"] = {"status": GAP, "basis": "No tariff line chosen.", "source_id": "TOOL:tariff_lookup"}
gap["estimated_saving"] = {"status": GAP, "amount": None, "currency": None, "source_id": "TOOL:tariff_lookup"}
gap["procedure"] = []
problems, _, v = run(gap, w)
check("declared classification gap is accepted", not problems, problems)
check("classification gap -> verdict GAP", v == GAP, v)

# ---------------- authority filled by code (6.4g) ----------------
print("\n== Authority filled by code")
kb = load_corridor("india")
kb_actors = {p["id"]: p["actor"] for p in passages_of(kb) if p.get("actor")}
check("pack.actors holds every passage actor from the KB",
      all(w.actors.get(pid) == a for pid, a in kb_actors.items()), w.actors)
# KB batch (27 Oct, slip 72): the fee is charged by the issuer (P-UAE-ISSUER); the certificate service's own
# actor is the exporter, who applies.
check("pack.actors has the fee tool's actor (the issuer's)",
      w.actors.get("TOOL:coo_fee") == kb_actors.get("P-UAE-ISSUER"), w.actors.get("TOOL:coo_fee"))
check("actor line shown in the evidence", "actor: the Ministry of Foreign Trade" in w.text)

filled = copy.deepcopy(GOOD_W)
filled["procedure"] = [
    {"step": "Register the factory.", "authority": "Ministry of Economy", "source_id": "P-MOET-FACTORY-REG"},
    {"step": "Apply for the certificate.", "source_id": "P-MOET-COO-INDIA"},
    {"step": "Pay the certificate fee.", "authority": "CBIC", "source_id": "TOOL:coo_fee"},
    {"step": "The certificate is issued.", "source_id": "P-UAE-ISSUER"},
    {"step": "Keep the origin records.", "source_id": "P-AGR-RECORDS-VERIFICATION"},
    {"step": "Meet the origin criteria.", "authority": "the exporter", "source_id": "P-AGR-3.2-ORIGIN"},
]
fill_authorities(filled, w)
got = [s["authority"] for s in filled["procedure"]]
check("model's wrong authority overwritten by the passage actor",
      got[0] == "the Ministry of Economy and Tourism", got[0])
check("missing authority filled from the passage", got[1] == "the exporter", got[1])
check("fee step authority comes from TOOL:coo_fee, not the model",
      got[2] == "the Ministry of Foreign Trade", got[2])
check("issuer step -> the Ministry of Foreign Trade", got[3] == "the Ministry of Foreign Trade", got[3])
check("records step -> the exporter", got[4] == "the exporter", got[4])
check("record without an actor -> GAP, even if the model named one", got[5] == GAP, got[5])
problems, warnings, _ = run(filled, w)
check("filled procedure passes the checks", not problems and not warnings, (problems, warnings))

print("\n== Step text names an actor its record does not")
named = copy.deepcopy(GOOD_W)
named["procedure"].append({"step": "The Ministry of Foreign Trade issues the certificate within one working day.",
                           "source_id": "P-AGR-COO-RULES"})
problems, warnings, _ = run(named, w)
check("ministry not in the cited record -> warning, not problem",
      not problems and any("Ministry of Foreign Trade" in x for x in warnings), (problems, warnings))
ok = copy.deepcopy(GOOD_W)
ok["procedure"].append({"step": "Register the factory with the Ministry of Economy and Tourism.",
                        "source_id": "P-MOET-FACTORY-REG"})
ok["procedure"].append({"step": "Pay the fee to the Ministry of Foreign Trade under its fee resolution.",
                        "source_id": "TOOL:coo_fee"})
problems, warnings, _ = run(ok, w)
check("ministry named by its own record -> no warning", not problems and not warnings, (problems, warnings))

# ---------------- windows: needs more data ----------------
print("\n== Windows, no files, no value (needs more data)")
wn = build_evidence({"product_description": "aluminium window frames", "hs_code_given": None,
                     "shipment_value": None}, None)
GOOD_WN = copy.deepcopy(GOOD_W)
GOOD_WN["origin_result"] = {"status": "NEEDS_MORE_DATA",
                            "basis": "No bill of materials or declaration was provided.",
                            "source_id": "TOOL:origin:76101000"}
GOOD_WN["estimated_saving"] = {"status": "NEEDS_VALUE", "amount": None, "currency": None,
                               "source_id": "TOOL:duty:76101000"}
GOOD_WN["follow_up_questions"] = ["Please provide a bill of materials and a declaration.",
                                  "What is the shipment value and currency?"]
expect_ok("needs-more-data correct answer", GOOD_WN, wn, "NEEDS_MORE_DATA")
bad = copy.deepcopy(GOOD_WN); bad["follow_up_questions"] = []
expect_problem("no follow-up questions", bad, wn)
check("fee actor present even without a shipment value",
      wn.actors.get("TOOL:coo_fee") == "the Ministry of Foreign Trade", wn.actors.get("TOOL:coo_fee"))

# ---------------- chargers: does not qualify ----------------
print("\n== Chargers (does not qualify)")
c = build_evidence({"product_description": "battery chargers", "hs_code_given": None,
                    "shipment_value": {"amount": 50000, "currency": "AED"}},
                   "samples/chargers_repacked")
cc = cand(c, "TL-IN-85044030")
corig = c.tool_results["TOOL:origin:85044030"]
GOOD_C = {
    "reasoning": ["..."] * 7,
    "classification": {"tariff_line": "85044030", "description": cc["description"],
                       "confidence": "high", "source_id": "TL-IN-85044030"},
    "tariff": {"agreement": "India-UAE CEPA", "mfn_rate": pct(cc["mfn"]["effective_rate_pct"]),
               "preferential_rate": pct(cc["cepa"]["rate_pct"]), "source_id": "TL-IN-85044030"},
    "origin_rule": {"rule": corig["rule_text"], "source_id": corig["rule_id"]},
    "origin_result": {"status": "DOES_NOT_QUALIFY",
                      "basis": "Final manufacture FAIL; minimal operations FAIL; CTH FAIL; VA FAIL.",
                      "source_id": "TOOL:origin:85044030"},
    "estimated_saving": {"status": "NOT_APPLICABLE", "amount": None, "currency": None,
                         "source_id": "TOOL:duty:85044030"},
    "procedure": [],
    "caveats": [],
    "follow_up_questions": [],
    "gaps": [],
}
expect_ok("chargers correct answer", GOOD_C, c, "NOT_ELIGIBLE")
bad = copy.deepcopy(GOOD_C); bad["origin_rule"]["source_id"] = "TOOL:rule_lookup:85044030"
expect_problem("origin rule cites the lookup, not the rule record", bad, c)
bad = copy.deepcopy(GOOD_C); bad["procedure"] = STEPS
expect_problem("procedure given for a failing product", bad, c)
bad = copy.deepcopy(GOOD_C)
bad["estimated_saving"] = {"status": "ESTIMATED", "amount": "10000.00", "currency": "AED",
                           "source_id": "TOOL:duty:85044030"}
expect_problem("saving claimed for a failing product", bad, c)

# ---------------- plastic: excluded ----------------
print("\n== Plastic packing (excluded)")
p = build_evidence({"product_description": "plastic packing articles", "hs_code_given": "39239090",
                    "shipment_value": {"amount": 50000, "currency": "AED"}}, None)
pc = cand(p, "TL-IN-39239090")
GOOD_P = {
    "reasoning": ["..."] * 7,
    "classification": {"tariff_line": "39239090", "description": pc["description"],
                       "confidence": "high", "source_id": "TL-IN-39239090"},
    "tariff": {"agreement": "India-UAE CEPA", "mfn_rate": pct(pc["mfn"]["effective_rate_pct"]),
               "preferential_rate": "EXCLUDED", "source_id": "TL-IN-39239090"},
    "origin_rule": {"rule": "Not applicable: the line is excluded from CEPA preference.",
                    "source_id": "TL-IN-39239090"},
    "origin_result": {"status": "NOT_APPLICABLE", "basis": "Excluded line; origin not assessed.",
                      "source_id": "TL-IN-39239090"},
    "estimated_saving": {"status": "NO_PREFERENCE", "amount": None, "currency": None,
                         "source_id": "TOOL:duty:39239090"},
    "procedure": [],
    "caveats": [],
    "follow_up_questions": [],
    "gaps": [],
}
expect_ok("plastic correct answer", GOOD_P, p, "NO_PREFERENCE")
bad = copy.deepcopy(GOOD_P); bad["tariff"]["preferential_rate"] = "0%"
expect_problem("excluded line given a CEPA rate", bad, p)
bad = copy.deepcopy(GOOD_P); bad["origin_result"]["status"] = "QUALIFIES"
expect_problem("excluded line marked as qualifying", bad, p)

# ---------------- messages ----------------
print("\n== Messages")
m = build_messages({"product_description": "x"}, w)
check("first pass: system + user", [x["role"] for x in m] == ["system", "user"])
check("evidence in the user message", "[TOOL:origin:76101000]" in m[1]["content"])
m2 = build_messages({"product_description": "x"}, w, previous={**GOOD_W, "verdict": "ELIGIBLE"},
                    corrections=["fix the saving"])
check("revision: system, user, assistant, user", [x["role"] for x in m2] ==
      ["system", "user", "assistant", "user"])
check("revision: verdict not sent back", "verdict" not in m2[2]["content"])
check("revision: code-filled authorities not sent back", '"authority"' not in m2[2]["content"])
check("revision: previous answer itself not changed", "authority" in GOOD_W["procedure"][0])
check("revision: corrections included", "fix the saving" in m2[3]["content"])
check("prompt no longer asks the model for authority", '"authority"' not in m[0]["content"])

# ---------------- text shown to the exporter (Step 9.5) ----------------
print("\n== No evidence IDs or internal words in text the exporter reads")
bad = copy.deepcopy(GOOD_W)
bad["caveats"].append({"note": "The '+' in the rule PSR-IN-R118 is read as 'and'.",
                       "source_id": "TOOL:origin:76101000"})
expect_problem("evidence ID in a caveat", bad, w)
bad = copy.deepcopy(GOOD_W); bad["follow_up_questions"] = ["Confirm the code (not provided in the intake)."]
expect_problem("internal word 'intake' in a follow-up question", bad, w)
bad = copy.deepcopy(GOOD_W); bad["procedure"][0]["step"] += " See P-MOET-FACTORY-REG."
expect_problem("evidence ID in a procedure step", bad, w)
bad = copy.deepcopy(GOOD_W); bad["origin_result"]["basis"] += " (TOOL:origin:76101000)"
expect_problem("evidence ID in the origin basis", bad, w)
problems, _, _ = run(GOOD_W, w)
check("plain text passes", not problems, problems)

# ---------------- tariff line format filled by code (Step 9.5b) ----------------
print("\n== Tariff line written as the record's 8 digits")
for given in ("TL-IN-76101000", "76101000 (7610 10 00)", "7610 10 00", "76101000"):
    d = copy.deepcopy(GOOD_W); d["classification"]["tariff_line"] = given
    fill_tariff_line(d, w)
    check(f"{given!r} -> '76101000'", d["classification"]["tariff_line"] == "76101000",
          d["classification"]["tariff_line"])
d = copy.deepcopy(GOOD_W); d["classification"]["tariff_line"] = "76151030"
fill_tariff_line(d, w)
check("a different line is not 'fixed' (left for the checks)", d["classification"]["tariff_line"] == "76151030")
expect_problem("different line from its source", d, w)
d = copy.deepcopy(GOOD_W); d["classification"]["tariff_line"] = GAP
fill_tariff_line(d, w)
check("gap marker left alone", d["classification"]["tariff_line"] == GAP)

# ---------------- run_researcher with a fake LLM ----------------
print("\n== run_researcher (fake LLM)")
calls = []


def fake_llm(*replies):
    queue = list(replies)

    def llm(agent, chain, messages, **kwargs):
        calls.append((agent, chain, messages))
        r = queue.pop(0)
        if isinstance(r, Exception):
            raise r
        return LLMResult(text="{}", data=copy.deepcopy(r), routed_via="fake/model",
                         finish_reason="stop", latency_s=0.0)
    return llm


wi = {"product_description": "aluminium window frames"}
res = run_researcher(wi, w, llm=fake_llm({**GOOD_W, "verdict": "NOT_ELIGIBLE"}))
check("called as researcher on auto:long", calls[-1][:2] == ("researcher", "auto:long"))
check("good answer: passed, verdict set by code", res.passed and res.data["verdict"] == "ELIGIBLE",
      res.data.get("verdict"))
check("authorities filled by code", all(s.get("authority") == w.actors.get(s["source_id"], GAP)
                                        for s in res.data["procedure"]))
check("served_by kept for the phase log", res.llm.routed_via == "fake/model")
bad = copy.deepcopy(GOOD_W); bad["origin_result"]["status"] = "DOES_NOT_QUALIFY"
res = run_researcher(wi, w, llm=fake_llm(bad))
check("wrong status: problems returned (not raised)", not res.passed and res.problems)
res2 = run_researcher(wi, w, previous=res.data, corrections=res.problems, llm=fake_llm(GOOD_W))
check("revision sends the corrections", "CORRECTIONS" in calls[-1][2][-1]["content"])
check("revision fixes it", res2.passed)
err = LLMCallError("router down", [{"attempt": 1, "ok": False, "problem": "HTTP 502"}])
try:
    run_researcher(wi, w, llm=fake_llm(err))
    check("LLM error reaches the caller with its attempts", False, "no exception")
except LLMCallError as e:
    check("LLM error reaches the caller with its attempts", e.attempts == err.attempts)

# ---------------- caveats copied into gaps (Step 9.6e, problem 52) ----------------
print("\n== drop_caveat_gaps (problem 52)")
d = copy.deepcopy(GOOD_W)
note = d["caveats"][0]["note"]
real_gap = "The rule for this line is not in Mansha's sources."
d["gaps"] = [note, "  " + note.upper().rstrip(".") + " ", real_gap]
changes = drop_caveat_gaps(d)
check("exact copy and a case/space/period variant dropped", d["gaps"] == [real_gap], d["gaps"])
check("each drop recorded in changes", len(changes) == 2 and all(c.startswith("gaps: dropped") for c in changes))
check("the caveat itself stays", d["caveats"][0]["note"] == note)
check("nothing to drop: no change", drop_caveat_gaps(copy.deepcopy(GOOD_W)) == [])
leaky = copy.deepcopy(GOOD_W)
leaky["gaps"] = [c["note"] for c in leaky["caveats"]]
res = run_researcher(wi, w, llm=fake_llm(leaky))
check("run_researcher: copies dropped, recorded, still passes",
      res.passed and res.data["gaps"] == []
      and sum(c.startswith("gaps: dropped") for c in res.changes) == len(leaky["caveats"])
      and any(c.startswith("gaps: ") and "plain-text item(s)" in c for c in res.changes), res.changes)
check("prompt forbids copying caveats into gaps",
      "Never copy a caveat or a note into `gaps`" in build_messages(wi, w)[0]["content"])

# ---------------- bracketed IDs (Step 7.6c, problem 75) ----------------
print("\n== unbracket_ids (problem 75)")
ci_ = {"product_description": "battery chargers"}
br = copy.deepcopy(GOOD_C)
br["caveats"] = [{"note": "Operations and final manufacture are the exporter's own declaration.",
                  "source_id": "TOOL:origin:85044030"}]
for k in ("classification", "tariff", "origin_rule", "origin_result", "estimated_saving"):
    br[k]["source_id"] = f"[{br[k]['source_id']}]"
br["caveats"][0]["source_id"] = " [ TOOL:origin:85044030 ] "
d = copy.deepcopy(br)
changes = unbracket_ids(d, c)
check("every bracketed evidence ID written plainly",
      all(d[k]["source_id"] == GOOD_C[k]["source_id"]
          for k in ("classification", "tariff", "origin_rule", "origin_result", "estimated_saving"))
      and d["caveats"][0]["source_id"] == "TOOL:origin:85044030", d)
check("one change line naming the 6 fields", len(changes) == 1 and "6 evidence ID(s)" in changes[0]
      and "caveats[0]" in changes[0], changes)
unknown = copy.deepcopy(GOOD_C); unknown["tariff"]["source_id"] = "[TL-IN-99999999]"
check("unknown ID keeps its brackets (left for the checks)",
      unbracket_ids(unknown, c) == [] and unknown["tariff"]["source_id"] == "[TL-IN-99999999]")
expect_problem("unknown bracketed ID is still a problem", unknown, c)
check("plain IDs: no change", unbracket_ids(copy.deepcopy(GOOD_C), c) == [])
res = run_researcher(ci_, c, llm=fake_llm(br))
check("run_researcher: bracketed answer passes without using the revision",
      res.passed and res.data["verdict"] == "NOT_ELIGIBLE" and len(not_o1(res.changes)) == 1,
      (res.problems, res.changes))
brw = copy.deepcopy(GOOD_W)
brw["classification"]["source_id"] = f"[{brw['classification']['source_id']}]"
for st in brw["procedure"]:
    st["source_id"] = f"[{st['source_id']}]"
res = run_researcher(wi, w, llm=fake_llm(brw))
check("brackets removed before code fills the tariff line and the step authorities",
      res.passed and all(s.get("authority") == w.actors.get(s["source_id"], GAP) for s in res.data["procedure"]),
      res.problems)

# ---------------- no follow-ups when no CEPA rate can apply (Step 7.6c, problem 74) ----------------
print("\n== drop_follow_ups (problem 74)")
LIVE_74 = [("What manufacturing operations were performed on these battery chargers in the UAE, "
           "beyond repacking and relabeling?"),
           "Where was the final manufacture of these battery chargers completed?",
           ("What is the FOB value of this shipment and the customs (CIF) value of any "
           "non-originating materials used?")]
asks = copy.deepcopy(GOOD_C); asks["follow_up_questions"] = list(LIVE_74)
d = copy.deepcopy(asks)
changes = drop_follow_ups(d, "NOT_ELIGIBLE")
check("NOT_ELIGIBLE: every follow-up dropped, one change each",
      d["follow_up_questions"] == [] and len(changes) == 3
      and all(x.startswith("follow_up_questions: dropped for verdict NOT_ELIGIBLE") for x in changes), changes)
d = copy.deepcopy(GOOD_P); d["follow_up_questions"] = ["Can you confirm the HS code?"]
check("NO_PREFERENCE: dropped", drop_follow_ups(d, "NO_PREFERENCE") and d["follow_up_questions"] == [])
for v in ("NEEDS_MORE_DATA", GAP):
    d = copy.deepcopy(GOOD_WN)
    check(f"{v}: follow-ups kept", drop_follow_ups(d, v) == []
          and d["follow_up_questions"] == GOOD_WN["follow_up_questions"])

# ELIGIBLE (27 Oct, C1 live, Dots3): only an AED-value question, or an HS-code question when the tariff
# lookup wrote a note (N4), is kept.
LIVE_C1 = [("Is your factory located in a free zone? (Free-zone factories may not be eligible for the required "
           "factory registration.)"),
           ("Can you confirm that the final manufacture in the UAE went beyond the minimal operations listed in "
           "Article 3.5.1 of the agreement? (This is based on your declaration.)")]
d = copy.deepcopy(GOOD_W); d["follow_up_questions"] = list(LIVE_C1)
changes = drop_follow_ups(d, "ELIGIBLE", w)
check("ELIGIBLE (C1 27 Oct): both follow-ups dropped, one change each",
      d["follow_up_questions"] == [] and len(changes) == 2
      and all(x.startswith("follow_up_questions: dropped for verdict ELIGIBLE") for x in changes), changes)
LIVE_N1 = ("Provide the invoice value in AED to determine the exact certificate of origin fee, since the fee bands "
           "are in AED and the shipment value is given in USD.")   # 25 Oct N1
d = copy.deepcopy(GOOD_W); d["follow_up_questions"] = [LIVE_C1[0], LIVE_N1]
drop_follow_ups(d, "ELIGIBLE", w)
check("ELIGIBLE (N1 25 Oct): the AED-value question is kept, the rest dropped",
      d["follow_up_questions"] == [LIVE_N1], d["follow_up_questions"])
LIVE_N4 = ("Please confirm that the product should be classified under tariff line 76101000, as the closest match "
           "to the given HS code 76101090.")   # 25 Oct N4 researcher_2
n4 = build_evidence(EVAL_BY_ID["N4"].intake, EVAL_BY_ID["N4"].folder)
check("N4: the tariff lookup notes the given code (no exact match)", bool(n4.tool_results["TOOL:tariff_lookup"]["notes"]))
d = copy.deepcopy(GOOD_W); d["follow_up_questions"] = [LIVE_N4, LIVE_C1[1]]
drop_follow_ups(d, "ELIGIBLE", n4)
check("ELIGIBLE with a tariff-lookup note (N4): the HS-code question is kept, the declaration re-ask dropped",
      d["follow_up_questions"] == [LIVE_N4], d["follow_up_questions"])
d = copy.deepcopy(GOOD_W); d["follow_up_questions"] = [LIVE_N4]
check("ELIGIBLE, no tariff-lookup note: the same HS-code question is dropped",
      drop_follow_ups(d, "ELIGIBLE", w) and d["follow_up_questions"] == [])
asks_w = copy.deepcopy(GOOD_W); asks_w["follow_up_questions"] = list(LIVE_C1)
res = run_researcher(wi, w, llm=fake_llm(asks_w))
check("run_researcher (C1 27 Oct): ELIGIBLE, passes, no follow-ups, drops recorded",
      res.passed and res.data["verdict"] == "ELIGIBLE" and res.data["follow_up_questions"] == []
      and sum(x.startswith("follow_up_questions: dropped for verdict ELIGIBLE") for x in res.changes) == 2,
      (res.problems, res.changes))
d = copy.deepcopy(asks); d["gaps"] = ["A real gap."]
drop_follow_ups(d, "NOT_ELIGIBLE")
check("gaps are left alone", d["gaps"] == ["A real gap."])
res = run_researcher(ci_, c, llm=fake_llm(asks))
check("run_researcher (live 19 Oct case): passes, no follow-ups, drops recorded",
      res.passed and res.data["follow_up_questions"] == [] and res.data["verdict"] == "NOT_ELIGIBLE"
      and sum(x.startswith("follow_up_questions: dropped") for x in res.changes) == 3, (res.problems, res.changes))
leak = copy.deepcopy(GOOD_C); leak["follow_up_questions"] = ["Please re-check TOOL:origin:85044030."]
check("a follow-up with an evidence ID is a problem on its own", any("follow_up" in x for x in run(leak, c)[0]))
res = run_researcher(ci_, c, llm=fake_llm(leak))
check("...but no stale problem once code has dropped it (checked again)", res.passed, res.problems)
res = run_researcher(wi, wn, llm=fake_llm(GOOD_WN))
check("run_researcher NEEDS_MORE_DATA: follow-ups kept, no change",
      res.passed and res.data["follow_up_questions"] == GOOD_WN["follow_up_questions"]
      and [x for x in not_o1(res.changes) if not x.startswith("procedure:")] == [],  # S3: code writes the steps
      (res.problems, res.changes))
check("... O1: the origin tool's note written word for word", _eq(*origin_notes(res.data, wn, "76101000")),
      origin_notes(res.data, wn, "76101000"))

# ---------------- no claim notes when no CEPA rate can apply (Step 7.6d, problem 76) ----------------
print("\n== drop_claim_caveats (problem 76)")
# The 17 caveats of the 19 Oct 04:16 chargers run (Dots3), by source; [11] had the invented website.
LIVE_76 = [("TOOL:duty:85044030", "Duty estimate on the shipment value given."),
           ("TOOL:duty:85044030", "CEPA rates reduce Basic Customs Duty (BCD) only."),
           ("TOOL:origin:85044030", "The result relies on the exporter's own declaration."),
           ("TOOL:rule_lookup:85044030", "The '+' in the rule is read as 'and'."),
           ("TL-IN-85044030", "A lower 15% rate applies only for electric-vehicle manufacture."),
           ("TL-IN-85044030", "Mansha has not checked anti-dumping duty on this product."),
           ("P-AGR-3.4-DEMINIMIS", "De minimis helps only the tariff-shift part of a rule."),
           ("TOOL:origin:85044030", "The non-originating input is 88% of the price."),
           ("TOOL:origin:85044030", "The value addition build-down is 12%."),
           ("P-AGR-3.5-MINIMAL", "The declared operations are minimal operations."),
           ("TOOL:coo_fee", "The certificate fee for this shipment value is AED 50."),
           ("P-UAE-ISSUER", "The India-specific service page is still on doit.gov.ae."),
           ("P-MOET-FACTORY-REG", "Factory registration is a prerequisite for the certificate."),
           ("P-AGR-3.2.2-VA", "The agreement does not define 'direct labour cost'."),
           ("P-AGR-RECORDS-VERIFICATION", "The exporter must keep origin records for five years."),
           ("P-IN-IMPORTER", "The Indian importer must claim the CEPA rate on the bill of entry."),
           ("P-IN-IMPORTER", "Electronic certificates are reportedly uploaded to e-Sanchit.")]
CLAIM_SIDS = {"TOOL:duty:85044030", "TOOL:coo_fee", "P-UAE-ISSUER", "P-MOET-FACTORY-REG",
              "P-AGR-RECORDS-VERIFICATION", "P-IN-IMPORTER"}
many = copy.deepcopy(GOOD_C)
many["caveats"] = [{"source_id": s, "note": n} for s, n in LIVE_76]
kept_live = [(s, n) for s, n in LIVE_76 if s not in CLAIM_SIDS]
d = copy.deepcopy(many)
changes = drop_claim_caveats(d, "NOT_ELIGIBLE")
check("NOT_ELIGIBLE: the 8 claim notes go (duty, fee, issuer, factory registration, records, importer)",
      len(changes) == 8 and all(x.startswith("caveats: dropped a note about claiming") for x in changes), changes)
check("...the 9 others stay, in order (origin, rule, tariff line, origin-rule passages)",
      [(c["source_id"], c["note"]) for c in d["caveats"]] == kept_live, d["caveats"])
check("the invented-website note is among the dropped", "doit.gov.ae" not in json.dumps(d))
d = copy.deepcopy(GOOD_P)
d["caveats"] = [{"source_id": "TOOL:duty:39239090", "note": "No CEPA rate."},
                {"source_id": "TL-IN-39239090", "note": "Excluded heading."}]
check("NO_PREFERENCE: claim note dropped, tariff-line note kept",
      len(drop_claim_caveats(d, "NO_PREFERENCE")) == 1 and [c["source_id"] for c in d["caveats"]] == ["TL-IN-39239090"])
for v in ("ELIGIBLE", "NEEDS_MORE_DATA", GAP):
    d = copy.deepcopy(many)
    check(f"{v}: every caveat kept", drop_claim_caveats(d, v) == [] and d["caveats"] == many["caveats"])
res = run_researcher(ci_, c, llm=fake_llm(many))
check("run_researcher (live 19 Oct case): passes, 8 caveats (O1: the 3 origin caveats become the tool's 2 "
      "notes), 8 drops recorded",
      res.passed and len(res.data["caveats"]) == 8 and res.data["verdict"] == "NOT_ELIGIBLE"
      and _eq(*origin_notes(res.data, c, "85044030"))
      and sum(x.startswith("caveats: dropped a note about claiming") for x in res.changes) == 8,
      (res.problems, res.changes))
leak = copy.deepcopy(GOOD_C)
leak["caveats"] = [{"source_id": "P-UAE-ISSUER", "note": "See P-UAE-ISSUER for the issuer."}]
check("a claim note with an evidence ID is a problem on its own", any("caveats[0]" in x for x in run(leak, c)[0]))
res = run_researcher(ci_, c, llm=fake_llm(leak))
check("...but no stale problem once code has dropped it", res.passed, res.problems)
res = run_researcher(wi, w, llm=fake_llm(GOOD_W))
check("run_researcher ELIGIBLE: caveats untouched, no change",
      res.passed and res.data["caveats"] == GOOD_W["caveats"] + [{"note": n, "source_id": "TOOL:origin:76101000"}
                                                                  for n in w.tool_results["TOOL:origin:76101000"]["notes"]]
      and [x for x in not_o1(res.changes) if not x.startswith("procedure:")] == [], (res.problems, res.changes))
check("pack knows its corridor", c.corridor == "india")

# ---------------- fixed notes written from the KB (Step 7.6f, problem 79) ----------------
print("\n== fill_fixed_notes (problem 79)")
kb_note = next(p["notes"] for p in passages_of(load_corridor("india")) if p["id"] == "P-UAE-ISSUER")
check("pack carries the issuer note from the KB, verbatim", w.fixed_notes.get("P-UAE-ISSUER") == " ".join(kb_note))
check("only the fixed-note passages are in the map", set(w.fixed_notes) == {"P-UAE-ISSUER"}, set(w.fixed_notes))
check("the KB note names moet.gov.ae", "moet.gov.ae" in w.fixed_notes["P-UAE-ISSUER"])
invented = copy.deepcopy(GOOD_W)
invented["caveats"][1]["note"] = w.fixed_notes["P-UAE-ISSUER"].replace("moet.gov.ae", "doit.gov.ae")
ch = fill_fixed_notes(invented, w)
check("invented domain replaced by the KB note",
      invented["caveats"][1]["note"] == w.fixed_notes["P-UAE-ISSUER"] and "doit" not in json.dumps(invented))
check("the change is logged", ch == ["caveats[1]: note written from the KB (P-UAE-ISSUER)"], ch)
check("other caveats untouched", invented["caveats"][0] == GOOD_W["caveats"][0])
check("already verbatim: no change", fill_fixed_notes(copy.deepcopy(GOOD_W), w) == [])
check("no caveats list: no change, no crash", fill_fixed_notes({"caveats": None}, w) == [])
invented = copy.deepcopy(GOOD_W)  # fresh copy: fill_fixed_notes above fixed the first one in place
invented["caveats"][1]["note"] = w.fixed_notes["P-UAE-ISSUER"].replace("moet.gov.ae", "doit.gov.ae")
res = run_researcher(wi, w, llm=fake_llm(invented))
check("run_researcher: invented domain gone, change recorded, still passes",
      res.passed and "doit" not in json.dumps(res.data)
      and "caveats[1]: note written from the KB (P-UAE-ISSUER)" in res.changes, (res.problems, res.changes))
missing = copy.deepcopy(GOOD_W)
missing["caveats"] = [cv for cv in missing["caveats"] if cv["source_id"] != "P-UAE-ISSUER"]
res = run_researcher(wi, w, llm=fake_llm(missing))
check("a missing issuer caveat is still a problem (code does not add it)",
      any("P-UAE-ISSUER" in x for x in res.problems), res.problems)
# Replay the two 19 Oct answers that invented "doit.gov.ae" (runs are git-ignored: skipped if absent).
RUNS = Path(__file__).resolve().parent.parent / "runs" / "pipeline"
for folder in ("20261019-041546_chargers", "20261019-183123_windows"):
    f = RUNS / folder / "researcher_1.json"
    if not f.exists():
        print(f"  SKIP  replay {folder} (run folder not on this machine)")
        continue
    saved = json.loads(f.read_text())
    d = copy.deepcopy(saved["output"])
    intake = json.loads((RUNS / folder / "intake.json").read_text())["output"]
    pack = build_evidence(intake, None)
    fill_fixed_notes(d, pack)
    check(f"replay {folder}: no invented domain left", "doit.gov.ae" not in json.dumps(d))

print("\n== drop_user_data_gaps (problem 85, Step 7.6h)")
# The two gaps of 23 Oct 20:08 windows_nodata (researcher_1 and _2), word for word.
GAPS_2008 = [
    {"text": "No shipment value in AED is available, so the actual duty saving cannot be computed.",
     "source_id": "TOOL:duty:76101000"},
    {"text": "No bill of materials or declaration is available, so the origin rule PSR-IN-R118 cannot be "
             "evaluated.", "source_id": "TOOL:origin:76101000"},
]
check("windows_nodata pack: origin INSUFFICIENT_DATA, duty NEEDS_VALUE",
      wn.tool_results["TOOL:origin:76101000"]["status"] == "INSUFFICIENT_DATA"
      and wn.tool_results["TOOL:duty:76101000"]["status"] == "NEEDS_VALUE")
d = copy.deepcopy(GOOD_WN); d["gaps"] = copy.deepcopy(GAPS_2008)
ch = drop_user_data_gaps(d, wn)
check("20:08 replay: both gaps dropped", d["gaps"] == [], d["gaps"])
check("20:08 replay: each drop logged with its tool and status",
      len(ch) == 2 and "TOOL:duty:76101000 NEEDS_VALUE" in ch[0] and "TOOL:origin:76101000 INSUFFICIENT_DATA" in ch[1], ch)
check("20:08 replay: follow-up questions untouched", d["follow_up_questions"] == GOOD_WN["follow_up_questions"])
expect_ok("20:08 replay: still a correct needs-more-data answer", d, wn, "NEEDS_MORE_DATA")
keep = [{"text": "Mansha's data has no rule for this line.", "source_id": None},
        {"text": "The fee band is not in the sources.", "source_id": "TOOL:coo_fee"},
        {"text": "The agreement does not say X.", "source_id": "PSR-IN-R118"}]
d = copy.deepcopy(GOOD_WN); d["gaps"] = copy.deepcopy(keep)
check("other gaps stay (no source, fee tool, rule)", drop_user_data_gaps(d, wn) == [] and d["gaps"] == keep, d["gaps"])
# The same tool IDs with other statuses are gaps in Mansha's data, not user data: they stay.
d = copy.deepcopy(GOOD_W); d["gaps"] = copy.deepcopy(GAPS_2008)
check("windows (files and value given): tool-cited gaps stay (status MEETS / ESTIMATED)",
      drop_user_data_gaps(d, w) == [] and len(d["gaps"]) == 2)
fake_pack = copy.copy(wn)
fake_pack.tool_results = {**wn.tool_results,
                          "TOOL:origin:76101000": {**wn.tool_results["TOOL:origin:76101000"], "status": "RULE_GAP"},
                          "TOOL:duty:76101000": {**wn.tool_results["TOOL:duty:76101000"],
                                                 "status": "REGULATORY_GAP_DETECTED"}}
d = {"gaps": copy.deepcopy(GAPS_2008)}
check("RULE_GAP / REGULATORY_GAP_DETECTED gaps stay", drop_user_data_gaps(d, fake_pack) == [] and len(d["gaps"]) == 2)
check("plain-string or missing gaps: no crash", drop_user_data_gaps({"gaps": ["x"]}, wn) == []
      and drop_user_data_gaps({}, wn) == [])
d = copy.deepcopy(GOOD_WN); d["gaps"] = copy.deepcopy(GAPS_2008); d["follow_up_questions"] = []
res = run_researcher(wi, wn, llm=fake_llm(d))
check("run_researcher: gaps dropped, but missing follow-ups are still a problem (check 7)",
      res.data["gaps"] == [] and any("follow_up_questions" in x for x in res.problems)
      and sum("data the user must supply" in c for c in res.changes) == 2, (res.problems, res.changes))
d = copy.deepcopy(GOOD_WN); d["gaps"] = copy.deepcopy(GAPS_2008)
res = run_researcher(wi, wn, llm=fake_llm(d))
check("run_researcher: 20:08 answer passes with the gaps dropped", res.passed and res.data["gaps"] == [],
      (res.problems, res.data["gaps"]))
for name in ("researcher_1.json", "researcher_2.json"):  # the saved answers (git-ignored: skipped if absent)
    f = RUNS / "20261023-200806_windows_nodata" / name
    if not f.exists():
        print(f"  SKIP  replay 20261023-200806_windows_nodata/{name} (run folder not on this machine)")
        continue
    saved = json.loads(f.read_text())["output"]
    intake = json.loads((RUNS / "20261023-200806_windows_nodata" / "intake.json").read_text())["output"]
    pack = build_evidence(intake, None)
    d = copy.deepcopy(saved)
    ch = drop_user_data_gaps(d, pack)
    check(f"replay 20:08 {name}: both tool-cited gaps dropped, follow-ups kept",
          len(ch) == 2 and d["gaps"] == [] and len(d["follow_up_questions"]) == 2, (ch, d["gaps"]))

print("\n== Step 7.6j: check names in plain words, raw names, confidence")
BASIS_0359 = ("final_manufacture_in_uae: PASS - final manufacture took place in the UAE; minimal_operations: PASS - "
              "manufacturing goes beyond the minimal operations of Art. 3.5.1; CTSH: PASS - all 3 non-originating "
              "inputs are classified outside subheading 761010; VA: PASS - build-down 49.0% against a threshold of "
              "45%, FOB basis.")   # 24 Oct 03:59 windows, researcher_1 and _2, word for word
d = copy.deepcopy(GOOD_W); d["origin_result"]["basis"] = BASIS_0359
ch = plain_check_names(d)
check("03:59 replay: check names written in plain words",
      d["origin_result"]["basis"].startswith("final manufacture check: passed")   # F2: results in plain words too
      and "minimal operations check: passed" in d["origin_result"]["basis"] and "_" not in d["origin_result"]["basis"],
      d["origin_result"]["basis"])
from mansha.report_check import TOOL_CODE_RE

check("F2: no status code left in the 03:59 basis (CTSH: passed, VA: passed)",
      not TOOL_CODE_RE.search(d["origin_result"]["basis"]) and "VA: passed - build-down 49.0%" in d["origin_result"]["basis"],
      d["origin_result"]["basis"])
d = copy.deepcopy(GOOD_W); d["origin_result"]["basis"] = "CTH: FAILS - one input; VA: FAIL - 30%; minimal operations check: PASSED."
plain_check_names(d)
check("F2: FAIL / FAILS / PASSED after a colon too",
      d["origin_result"]["basis"] == "CTH: failed - one input; VA: failed - 30%; minimal operations check: passed.",
      d["origin_result"]["basis"])
check("03:59 replay: the change is logged", ch == ["origin_result.basis: check names written in plain words"], ch)
check("03:59 replay: no raw-name problem after the rewrite",
      not any("internal name" in x for x in run(d, w)[0]), run(d, w)[0])
res = run_researcher(wi, w, llm=fake_llm({**copy.deepcopy(GOOD_W), "origin_result": {
    **GOOD_W["origin_result"], "basis": BASIS_0359}}))
check("run_researcher: 03:59 basis fixed by code, no problem, change recorded",
      not any("internal name" in x for x in res.problems) and "_" not in res.data["origin_result"]["basis"]
      and "origin_result.basis: check names written in plain words" in res.changes, (res.problems, res.changes))
for where, mutate in (
        ("basis", lambda x: x["origin_result"].update(basis="price_basis: FOB; VA 49.0%.")),
        ("a caveat", lambda x: x["caveats"][0].update(note="non_originating_share_pct is 51.0.")),
        ("a follow-up", lambda x: x.update(follow_up_questions=["Set final_manufacture_flag to true."]))):
    d = copy.deepcopy(GOOD_W); mutate(d)
    check(f"another raw name in {where} is a problem", any("internal name" in x for x in run(d, w)[0]), run(d, w)[0])
check("plain English with no underscore: no raw-name problem", not any("internal name" in x for x in run(GOOD_W, w)[0]))
for bad in (None, "", "certain"):
    d = copy.deepcopy(GOOD_W); d["classification"]["confidence"] = bad
    check(f"confidence {bad!r} is a problem (03:59: QA made it null)",
          any("classification.confidence" in x for x in run(d, w)[0]), run(d, w)[0])
d = copy.deepcopy(GOOD_W); d["classification"]["confidence"] = "High"
check("confidence 'High' is fine (case ignored)", not any("confidence" in x for x in run(d, w)[0]))
d = copy.deepcopy(GOOD_W)
d["classification"] = {"tariff_line": GAP, "description": GAP, "confidence": GAP, "source_id": "TOOL:tariff_lookup"}
check("no fitting line: the gap marker as confidence is not a confidence problem",
      not any("classification.confidence" in x for x in run(d, w)[0]), run(d, w)[0])

print("\n== Step 7.8: qualifiers kept (G35, problem 71)")
NOTES_WN = record_notes(wn)
DEMIN = NOTES_WN["P-AGR-3.4-DEMINIMIS"][0]
SWS, AD = NOTES_WN["P-IN-DUTY-SCOPE"]
PLUS = NOTES_WN["TOOL:origin:76101000"][0]
# KB batch (27 Oct, item 4): the SWS and anti-dumping notes say "likely" instead of a leading "Inference:",
# and the de minimis note "By interpretation," instead of "Interpretation:".
check("KB notes carry the qualifiers this step protects",
      DEMIN.startswith("By interpretation,") and " likely " in SWS and " likely " in AD, (DEMIN, SWS, AD))


def with_caveats(*cavs, base=None):
    d = copy.deepcopy(base or GOOD_WN)
    d["caveats"] = d["caveats"] + [{"note": n, "source_id": sid} for sid, n in cavs]
    return d


def restored(sid, text, pack=wn):
    d = with_caveats((sid, text))
    ch = restore_qualified_notes(d, pack)
    return d["caveats"][-1]["note"], ch


# Live wordings, word for word: problem 71 (18 Oct 05:17 and 16:50 windows_nodata) and 24 Oct 15:58 windows.
LIVE_DROPS = [
    ("P-AGR-3.4-DEMINIMIS", "The de minimis tolerance helps only the tariff-shift part of a rule, not the VA percentage.",
     DEMIN, "18 Oct 05:17 (problem 71)"),
    ("P-AGR-3.4-DEMINIMIS", "De minimis helps only the tariff-shift part of a rule, not the VA percentage.",
     DEMIN, "18 Oct 16:50 (problem 71)"),
    ("P-IN-DUTY-SCOPE", "SWS is charged on the reduced BCD (no CEPA-specific text found).", SWS, "24 Oct 15:58 #7"),
    ("P-IN-DUTY-SCOPE", "Anti-dumping and safeguard duties still apply (no exemption found).", AD, "24 Oct 15:58 #8"),
    ("P-AGR-3.4-DEMINIMIS", ("The de minimis tolerance applies only to the tariff-shift part of a rule, not to the "
     "value-addition percentage."), DEMIN, "16 Oct 17:46 chargers (reworded most)"),
    ("P-IN-DUTY-SCOPE", ("SWS is charged on the reduced BCD (no CEPA-specific text found); anti-dumping and safeguard "
     "duties still apply (no exemption found)."), f"{SWS} {AD}", "two notes in one caveat"),
    ("TOOL:origin:76101000", "The agreement does not define '+' in the rule; read as 'and' (both tests must pass).",
     None, "the '+' note keeps 'does not define'"),
]
for sid, text, want, label in LIVE_DROPS:
    got, ch = restored(sid, text)
    if want is None:
        check(f"kept qualifier, not rewritten: {label}", got == text and ch == [], (got, ch))
    else:
        check(f"restored from the KB: {label}", got == want, got)
        check(f"logged: {label}", ch and "note written from the KB, qualifier kept" in ch[0], ch)

# The ways the model rewords a qualifier it kept (saved runs 16-24 Oct): never rewritten, never a problem.
KEPT = [
    ("TOOL:origin:76101000", ("The agreement does not define '+' in the rule 'CTSH + VA 45%'; Mansha interprets it as "
     "'and' (both tests must pass)."), wn),
    ("P-AGR-3.2.2-VA", ("The agreement does not specify whether the build-down and build-up methods use the same "
     "threshold apart from the 5-point Ex-Works adjustment."), wn),
    ("P-AGR-3.2.2-VA", ("'Direct labour cost' and 'direct overhead cost' are not defined in the agreement, and it is "
     "unclear whether the build-down and build-up methods use the same threshold apart from the 5-point Ex-Works "
     "adjustment."), wn),
    ("TL-IN-85044030", ("Whether India charges anti-dumping duty on battery chargers has not been checked; confirm with "
     "Indian customs or a customs broker."), c),
    ("P-IN-IMPORTER", ("Electronic certificates are reportedly accepted and uploaded to India's e-Sanchit system, but "
     "this is seen only in secondary sources (CBIC Instruction 28/2022)."), wn),
]
for sid, text, pack in KEPT:
    got, ch = restored(sid, text, pack)
    check(f"reworded qualifier kept ({sid}): not rewritten", got == text and ch == [], (got, ch))
    check(f"reworded qualifier kept ({sid}): no problem",
          not qualifier_drops(text, record_sentences(pack).get(sid, [])))

# A caveat that also says other things is not rewritten (nothing lost): the revision fixes it instead.
SEED_11 = ("The Indian importer must hold origin information under CAROTAR 2020, including the origin criterion "
           "claimed, keep supporting documents for at least 5 years, and respond to customs requests within 10 "
           "working days. Electronic certificates are accepted and uploaded to e-Sanchit.")  # eval_qa seed
# KB batch (27 Oct, 101): P-IN-IMPORTER now states the e-certificate fact plainly (CBIC Instruction 28/2022 read
# in the official text). The mechanism is still tested on a synthetic pack holding the old hedged sentence.
IMP_NOW = ("Electronic certificates from the UAE issuing authority are accepted and uploaded to e-Sanchit by the "
           "importer or customs broker.")
IMP_HEDGED = ("Electronic certificates are reportedly accepted and uploaded to e-Sanchit (unconfirmed: seen only in "
              "secondary sources).")
check("P-IN-IMPORTER states the e-certificate fact plainly now",
      (IMP_NOW in w.text and IMP_NOW in wn.text and "reportedly" not in w.text), IMP_NOW)
w_hedged = dataclasses.replace(w, text=w.text.replace(IMP_NOW, IMP_HEDGED))
wn_hedged = dataclasses.replace(wn, text=wn.text.replace(IMP_NOW, IMP_HEDGED))
got, ch = restored("P-IN-IMPORTER", SEED_11, wn_hedged)
check("caveat with other facts and a dropped 'reportedly': not rewritten", got == SEED_11 and ch == [], (got, ch))
d = with_caveats(("P-IN-IMPORTER", SEED_11))
check("... but a hard problem naming the qualifier",
      any("plain fact" in x and "'reportedly'" in x for x in run(d, wn_hedged)[0]), run(d, wn_hedged)[0])
check("... and no problem against today's plain record", not any("plain fact" in x for x in run(d, wn)[0]),
      run(d, wn)[0])
MERGED_1956 = ("The Social Welfare Surcharge is charged on the reduced BCD (no CEPA-specific text found), and "
               "anti-dumping and safeguard duties still apply.")   # 23 Oct 19:56 windows caveats[15]
got, ch = restored("P-IN-DUTY-SCOPE", MERGED_1956)
check("23 Oct 19:56 merged caveat (SWS qualifier dropped, anti-dumping stated plainly by the summary): "
      "not rewritten, left to the revision", got == MERGED_1956 and ch == [], (got, ch))
d = with_caveats(("P-IN-DUTY-SCOPE", MERGED_1956))
check("23 Oct 19:56 merged caveat: hard problem on 'likely'",
      any("plain fact" in x and "'likely'" in x for x in run(d, wn)[0]), run(d, wn)[0])

# The record also says it plainly: supported as written (a caveat copying the whole summary, 16 Oct plastic).
summary = next(u for k, u in record_sentences(wn)["P-IN-DUTY-SCOPE"] if k == "summary" and "anti-dumping" in u)
got, ch = restored("P-IN-DUTY-SCOPE", summary)
check("summary sentence copied (anti-dumping stated plainly there): untouched", got == summary and ch == [], ch)
check("... and no problem", not any("plain fact" in x for x in run(with_caveats(("P-IN-DUTY-SCOPE", summary)), wn)[0]))

# Procedure steps: checked against the record's summary sentences only (notes belong to caveats).
STEP_1956 = ("The Ministry of Economy and Tourism requires the factory to be registered before applying for a "
             "certificate of origin; registration requires the factory to be located outside a free zone, a MoIAT "
             "industrial licence, and a letter confirming 40% domestic value added.")  # 23 Oct 19:56 procedure[0]
ok = copy.deepcopy(GOOD_W); ok["procedure"][0] = {"step": STEP_1956, "source_id": "P-MOET-FACTORY-REG"}
check("factory step sharing words with the free-zone Inference note: no problem",
      not any("plain fact" in x for x in run(ok, w)[0]), run(ok, w)[0])
imp = next(u for k, u in record_sentences(w_hedged)["P-IN-IMPORTER"] if "reportedly" in u)
for step, bad in (("Electronic certificates are accepted and uploaded to e-Sanchit.", True),
                  ("Electronic certificates are reportedly accepted and uploaded to e-Sanchit.", False),
                  ("The importer uploads electronic certificates to e-Sanchit, which is unconfirmed.", False)):
    d = copy.deepcopy(GOOD_W); d["procedure"].append({"step": step, "source_id": "P-IN-IMPORTER"})
    found = any("plain fact" in x and x.startswith(f"procedure[{len(d['procedure']) - 1}]")
                for x in run(d, w_hedged)[0])
    check(f"step {'drops' if bad else 'keeps'} the qualifier of {imp[:40]!r}...: problem {bad}", found == bad,
          run(d, w_hedged)[0])

# The fixed issuer note is fill_fixed_notes' job: never rewritten here.
d = with_caveats(("P-UAE-ISSUER", "The Ministry of Foreign Trade issues the certificate."))
d["caveats"] = [cv for cv in d["caveats"][:-1] if cv["source_id"] != "P-UAE-ISSUER"] + d["caveats"][-1:]
check("issuer note left to fill_fixed_notes", restore_qualified_notes(d, wn) == [])

# The clean fixtures and GOOD answers are unchanged.
for name, good, pack in (("windows", GOOD_W, w), ("windows_nodata", GOOD_WN, wn)):
    d = copy.deepcopy(good)
    check(f"clean {name}: nothing restored, no problem",
          restore_qualified_notes(d, pack) == [] and not any("plain fact" in x for x in run(d, pack)[0]))
for base in ("windows", "chargers", "windows_nodata", "plastic"):
    fx = json.loads(Path(f"samples/researcher_outputs/{base}.json").read_text(encoding="utf-8"))["output"]
    intake, folder, _ = DEV_INTAKES[base]
    pk = build_evidence(intake, folder)
    d = copy.deepcopy(fx)
    check(f"fixture {base}: nothing restored, no qualifier problem",
          restore_qualified_notes(d, pk) == [] and not any("plain fact" in x for x in check_researcher(d, pk)[0]),
          (restore_qualified_notes(copy.deepcopy(fx), pk), check_researcher(d, pk)[0]))

# run_researcher: the restore runs before the checks, and is recorded.
d = with_caveats(("P-AGR-3.4-DEMINIMIS", LIVE_DROPS[1][1]))
res = run_researcher(wi, wn, llm=fake_llm(d))
check("run_researcher: dropped 'Interpretation:' restored by code, answer passes",
      res.passed and any(cv["note"] == DEMIN for cv in res.data["caveats"])
      and any("qualifier kept (P-AGR-3.4-DEMINIMIS)" in x for x in res.changes), (res.problems, res.changes))

# Replays of the saved answers (git-ignored run folders: skipped if absent).
# want: {caveat index: (record, note index)}, read from the run's own evidence (KB batch, 27 Oct: the
# SWS and anti-dumping notes were reworded after these runs).
DEMIN_0 = ("P-AGR-3.4-DEMINIMIS", 0)
for folder, name, want in (("20261018-051708_windows_nodata", "researcher_1.json", {8: DEMIN_0}),
                           ("20261018-165049_windows_nodata", "researcher_1.json", {8: DEMIN_0}),
                           ("20261018-165049_windows_nodata", "researcher_2.json", {8: DEMIN_0}),
                           ("20261024-155849_windows", "researcher_1.json",
                            {7: ("P-IN-DUTY-SCOPE", 0), 8: ("P-IN-DUTY-SCOPE", 1)})):
    f = RUNS / folder / name
    if not f.exists():
        print(f"  SKIP  replay {folder}/{name} (run folder not on this machine)")
        continue
    intake = json.loads((RUNS / folder / "intake.json").read_text())["output"]
    pack = build_evidence(intake, None)
    pack = dataclasses.replace(pack, text=(RUNS / folder / "evidence.txt").read_text())
    d = copy.deepcopy(json.loads(f.read_text())["output"])
    ch = restore_qualified_notes(d, pack)
    run_notes = record_notes(pack)
    check(f"replay {folder}/{name}: the dropped qualifier(s) restored",
          all(d["caveats"][i]["note"] == run_notes[rid][k] for i, (rid, k) in want.items())
          and len(ch) == len(want), ch)

# Fix round 1 (26 Oct, N5 live): one caveat merging both "Inference:" notes of P-IN-DUTY-SCOPE.
paint = build_evidence({"product_description": "acrylic paint", "hs_code_given": None,
                        "shipment_value": {"amount": 100000, "currency": "AED"}}, "samples/eval/paint_indian_resin")
DUTY_NOTES = [u for k, u in record_sentences(paint)["P-IN-DUTY-SCOPE"] if k == "note"]
check("P-IN-DUTY-SCOPE has the two qualified notes ('likely')", len(DUTY_NOTES) == 2
      and all(" likely " in n for n in DUTY_NOTES), DUTY_NOTES)
for text, label in (
        (("Inference: the Social Welfare Surcharge (SWS) is charged on the reduced BCD (no CEPA-specific text "
         "found); anti-dumping and safeguard duties still apply (no exemption found)."),
         "N5 round 2, word for word: one leading qualifier"),
        (("SWS is charged on the reduced BCD (no CEPA-specific text found), and anti-dumping and safeguard "
         "duties still apply (no exemption found)."), "both as plain fact")):
    note, ch = restored("P-IN-DUTY-SCOPE", text, paint)
    d = with_caveats(("P-IN-DUTY-SCOPE", text))
    restore_qualified_notes(d, paint)
    check(f"merged qualified notes ({label}): both KB notes, word for word, check 10 clean",
          note == " ".join(DUTY_NOTES) and len(ch) == 1
          and not any("plain fact" in x and "caveats" in x for x in check_researcher(d, paint)[0]),
          (note, ch, check_researcher(d, paint)[0]))
extra = ("Inference: SWS is charged on the reduced BCD (no CEPA-specific text found); anti-dumping and safeguard "
         "duties still apply (no exemption found); IGST is charged on the assessable value plus BCD.")
note, ch = restored("P-IN-DUTY-SCOPE", extra, paint)
check("merged notes plus another claim: left as written, for check 10 (nothing lost)", note == extra and ch == [])

print("\n== C2 (29 Oct night): a qualified KB note split out of a caveat that says other things too")
DEMIN = next(u for k, u in record_sentences(wn)["P-AGR-3.4-DEMINIMIS"] if k == "note")
R2 = ("A small amount of non-originating material is tolerated under de minimis: up to 10% of the FOB value or "
      "Ex-Works price. De minimis helps only the tariff-shift part of a rule, not the value-addition percentage.")
d = with_caveats(("P-AGR-3.4-DEMINIMIS", R2))
n0 = len(d["caveats"])
ch = restore_qualified_notes(d, wn)
check("221636 r2 wording: split in two, plain fact first, then the KB note word for word",
      [c["note"] for c in d["caveats"][-2:]] == [
          "A small amount of non-originating material is tolerated under de minimis: up to 10% of the FOB value or "
          "Ex-Works price.", DEMIN]
      and all(c["source_id"] == "P-AGR-3.4-DEMINIMIS" for c in d["caveats"][-2:]) and len(d["caveats"]) == n0 + 1,
      d["caveats"][-2:])
check("... logged as a split", ch == [f"caveats[{n0 - 1}]: qualified KB note split out word for word "
                                      "(P-AGR-3.4-DEMINIMIS); the rest kept"], ch)
check("... and check 10 is clean", not any("plain fact" in x and "caveats" in x for x in check_researcher(d, wn)[0]),
      check_researcher(d, wn)[0])
R2b = ("By interpretation, a small amount of non-originating material is tolerated under de minimis: up to 10% of "
       "the FOB value or Ex-Works price. De minimis helps only the tariff-shift part of a rule, not the "
       "value-addition percentage.")   # 221636 r2 round 2: the qualifier moved onto the wrong sentence
d = with_caveats(("P-AGR-3.4-DEMINIMIS", R2b))
restore_qualified_notes(d, wn)
check("221636 r2 round 2 wording: the bare sentence becomes the KB note, the other sentence kept as written",
      [c["note"] for c in d["caveats"][-2:]] == [R2b.split(". De minimis")[0] + ".", DEMIN], d["caveats"][-2:])
d = with_caveats(("P-AGR-3.4-DEMINIMIS", "Up to 10% of the FOB value is tolerated, and de minimis helps only the "
                  "tariff-shift part of a rule, not the VA percentage."))
before = copy.deepcopy(d)
check("a note restated only inside a sentence (', and') is left to the revision, unchanged",
      restore_qualified_notes(d, wn) == [] and d == before)
d = with_caveats(("P-AGR-3.4-DEMINIMIS", DEMIN), ("P-AGR-3.4-DEMINIMIS", "Up to 10% of the FOB value is tolerated."))
before = copy.deepcopy(d)
check("caveats that already pass are not touched", restore_qualified_notes(d, wn) == [] and d == before)
first = ("SWS is charged on the reduced BCD (no CEPA-specific text found); IGST is charged on the assessable "
         "value plus BCD.")
d = with_caveats(("P-IN-DUTY-SCOPE", first), base=GOOD_WN)
restore_qualified_notes(d, paint)
check("the KB note keeps its place (first here); the rest gets a capital letter and a full stop",
      [c["note"] for c in d["caveats"][-2:]] == [DUTY_NOTES[0], "IGST is charged on the assessable value plus BCD."],
      d["caveats"][-2:])
for folder, name in (("20261029-221636/N15_arabic_windows_nodata_r2", "researcher_1.json"),
                     ("20261029-221636/N15_arabic_windows_nodata_r2", "researcher_2.json"),
                     ("20261026-213601/N5_paint_indian_resin", "researcher_1.json")):
    f = RUNS.parent / "eval_set" / folder / name
    if not f.exists():
        print(f"  SKIP  replay {folder}/{name} (run folder not on this machine)")
        continue
    intake = json.loads((f.parent / "intake.json").read_text())["output"]
    pk = dataclasses.replace(build_evidence(intake, None), text=(f.parent / "evidence.txt").read_text())
    d = copy.deepcopy(json.loads(f.read_text())["output"])
    for k in ("caveats", "procedure", "gaps"):
        d.setdefault(k, [])
    ch = restore_qualified_notes(d, pk)
    check(f"replay {folder}/{name}: split, then check 10 clean",
          any("split out" in c for c in ch)
          and not any("plain fact" in x and "caveats" in x for x in check_researcher(d, pk)[0]), ch)

print("\n== Step 7.9: HS-code follow-ups without a tariff-lookup conflict (problem 92)")
check("no HS code given: the tariff lookup notes nothing (windows, windows_nodata)",
      w.tool_results["TOOL:tariff_lookup"]["notes"] == [] and wn.tool_results["TOOL:tariff_lookup"]["notes"] == [])
# Live wordings, word for word (16-24 Oct, all with no HS code given and no tariff-lookup note).
HS_LIVE = ["Please confirm the HS code for aluminium window frames.",
           "Confirm the HS code for aluminium window frames (proposed 76101000).",
           "Please provide the HS code for aluminium window frames (if different from 76101000).",
           "Please confirm the HS code for aluminium window frames (candidate 76101000) or provide the correct code.",
           ("Confirm that HS code 76101000 is correct for aluminium window frames (the code was not provided in "
           "the intake).")]
BOM_Q = [("Please provide a bill of materials with each input's description, 6-digit HS code, origin country, "
         "value and currency."),
         ("Provide a declaration with the product price, FOB or Ex-Works basis, final manufacture in the UAE, "
         "and operations done in the UAE."),
         "Please provide the shipment value in AED."]
for q in HS_LIVE:
    d = copy.deepcopy(GOOD_WN); d["follow_up_questions"] = BOM_Q[:1] + [q] + BOM_Q[1:]
    ch = drop_hs_follow_ups(d, wn)
    check(f"dropped: {q[:55]!r}", d["follow_up_questions"] == BOM_Q and len(ch) == 1
          and "HS-code confirmation dropped" in ch[0], (d["follow_up_questions"], ch))
d = copy.deepcopy(GOOD_WN); d["follow_up_questions"] = list(BOM_Q)
check("bill-of-materials, declaration and value questions kept (inputs' HS codes are not the product's)",
      drop_hs_follow_ups(d, wn) == [] and d["follow_up_questions"] == BOM_Q)
d = copy.deepcopy(GOOD_W); d["follow_up_questions"] = [HS_LIVE[0]]
drop_hs_follow_ups(d, w)
check("ELIGIBLE windows: the only follow-up was the HS question, so nothing is left for 'What's still needed'",
      d["follow_up_questions"] == [] and not run(d, w)[0], run(d, w)[0])
d = copy.deepcopy(GOOD_WN); d["follow_up_questions"] = [HS_LIVE[1]]
drop_hs_follow_ups(d, wn)
check("NEEDS_MORE_DATA left with no follow-up: check 7 still asks for the real ones",
      any("follow_up_questions must say" in x for x in run(d, wn)[0]), run(d, wn)[0])
# A tariff-lookup note (code/description conflict, no exact 8-digit match, code matched nothing): kept.
for intake, label in (({"product_description": "aluminium window frames", "hs_code_given": "39239090",
                        "shipment_value": None}, "code points elsewhere than the description"),
                      ({"product_description": "aluminium window frames", "hs_code_given": "76101099",
                        "shipment_value": None}, "8-digit code with no exact match")):
    pk = build_evidence(intake, None)
    notes = pk.tool_results["TOOL:tariff_lookup"]["notes"]
    d = copy.deepcopy(GOOD_WN); d["follow_up_questions"] = [HS_LIVE[0]] + BOM_Q
    check(f"tariff lookup noted something ({label}): HS question kept",
          bool(notes) and drop_hs_follow_ups(d, pk) == [] and d["follow_up_questions"][0] == HS_LIVE[0], notes)
# Fix round 1 (26 Oct, N10 live): a question about an input the origin tool lists as missing is kept.
cos = build_evidence({"product_description": "cosmetic skin creams", "hs_code_given": None,
                      "shipment_value": {"amount": 60000, "currency": "AED"}}, "samples/eval/cosmetics_missing_hs")
check("N10: the tariff lookup notes nothing, the origin tool lists BOM row 2 (Emollients)",
      cos.tool_results["TOOL:tariff_lookup"]["notes"] == []
      and any(m.startswith("BOM row 2 (Emollients):") for m in cos.tool_results["TOOL:origin:33049990"]["missing"]))
for q in (("Please provide the 6-digit HS code for Emollients (BOM row 2) so that compliance with the CTSH rule "
          "can be determined."),   # N10 round 1, Gemini 3.6, word for word: dropped before this fix
          "Please give the HS code for Emollients.",
          "Please provide the 6-digit HS code of row 2."):
    d = {"follow_up_questions": [q]}
    check(f"N10 kept: {q[:50]!r}", drop_hs_follow_ups(d, cos) == [] and d["follow_up_questions"] == [q])
d = {"follow_up_questions": ["Please confirm the HS code for cosmetic skin creams."]}
check("N10: a product-code confirmation is still dropped", len(drop_hs_follow_ups(d, cos)) == 1
      and d["follow_up_questions"] == [])
res = run_researcher(wi, wn, llm=fake_llm({**copy.deepcopy(GOOD_WN),
                                           "follow_up_questions": GOOD_WN["follow_up_questions"] + [HS_LIVE[1]]}))
check("run_researcher: HS question dropped by code, answer passes, change recorded",
      res.passed and HS_LIVE[1] not in res.data["follow_up_questions"]
      and any("HS-code confirmation dropped" in x for x in res.changes), (res.problems, res.changes))
for base in ("windows", "chargers", "windows_nodata", "plastic"):
    fx = json.loads(Path(f"samples/researcher_outputs/{base}.json").read_text(encoding="utf-8"))["output"]
    intake, folder, _ = DEV_INTAKES[base]
    d = copy.deepcopy(fx)
    check(f"fixture {base}: no follow-up dropped", drop_hs_follow_ups(d, build_evidence(intake, folder)) == [])
# Replays of the saved answers (git-ignored run folders: skipped if absent).
for folder, name, idx in (("20261024-164944_windows_nodata", "researcher_1.json", 0),
                          ("20261024-152756_windows", "researcher_1.json", 0),
                          ("20261024-040243_windows_nodata", "researcher_1.json", 2)):
    f = RUNS / folder / name
    if not f.exists():
        print(f"  SKIP  replay {folder}/{name} (run folder not on this machine)")
        continue
    intake = json.loads((RUNS / folder / "intake.json").read_text())["output"]
    pk = build_evidence(intake, "samples/windows_qualifies" if folder.endswith("_windows") else None)
    d = copy.deepcopy(json.loads(f.read_text())["output"])
    before = list(d["follow_up_questions"])
    ch = drop_hs_follow_ups(d, pk)
    check(f"replay {folder}: only the HS question dropped",
          len(ch) == 1 and d["follow_up_questions"] == before[:idx] + before[idx + 1:], ch)

print("\n== Fix round 1c: follow-ups as objects (N10) and free-zone follow-ups (N2)")
N10_R2 = {"step": "Provide the 6-digit HS code for Emollients (BOM row 2) as required by the origin rule.",
          "source_id": "TOOL:origin:33049990"}   # 27 Oct 15:56, Dots3 round 2, word for word
d = {"follow_up_questions": [copy.deepcopy(N10_R2), "Please give the shipment value."]}
ch = plain_follow_ups(d)
check("object follow-up -> its text; the string one unchanged",
      d["follow_up_questions"] == [N10_R2["step"], "Please give the shipment value."] and len(ch) == 1, ch)
for k in ("question", "text", "note"):
    d = {"follow_up_questions": [{k: "Q?", "source_id": None}]}
    check(f"object with {k!r} -> its text", plain_follow_ups(d) and d["follow_up_questions"] == ["Q?"])
d = {"follow_up_questions": [{"source_id": "TOOL:origin:33049990"}]}
check("object with no text: left for the checks", plain_follow_ups(d) == []
      and isinstance(d["follow_up_questions"][0], dict))
nd = copy.deepcopy(GOOD_WN)
nd["follow_up_questions"] = [copy.deepcopy(N10_R2)]
p, _, _ = check_researcher(nd, wn)
check("without 1c the object fails the exporter-text check (the N10 failure)",
      any("follow_up_questions[0] contains" in x for x in p), p)
res = run_researcher(wi, wn, llm=fake_llm(nd))
check("run_researcher: object normalized, no exporter-text problem, change recorded",
      res.data["follow_up_questions"] == [N10_R2["step"]]
      and not any("follow_up_questions" in x for x in res.problems)
      and any("object turned into its text" in x for x in res.changes), (res.problems, res.changes))

fz_intake = {"product_description": "wooden bedroom furniture", "hs_code_given": None,
             "shipment_value": {"amount": 100000, "currency": "AED"}}
fz = build_evidence(fz_intake, "samples/eval/furniture_freezone")
check("N2: the origin tool sets FREE_ZONE",
      any("FREE_ZONE" in (r.get("conditions") or []) for t, r in fz.tool_results.items() if t.startswith("TOOL:origin:")))
N2_Q = ("Is the factory located in a free zone? If so, it may not be eligible for the required factory "
        "registration, which is a prerequisite for the certificate of origin.")   # 27 Oct 15:56, word for word
for q in (N2_Q, "Please confirm whether your facility is in a free-zone area.", "Is the plant in the Free Zone?"):
    d = {"follow_up_questions": [q, "Please give the shipment value."]}
    ch = drop_free_zone_follow_ups(d, fz)
    check(f"N2 dropped: {q[:45]!r}", len(ch) == 1 and d["follow_up_questions"] == ["Please give the shipment value."], ch)
d = {"follow_up_questions": [N2_Q]}
check("no FREE_ZONE (windows): a free-zone question is kept",
      drop_free_zone_follow_ups(d, wn) == [] and d["follow_up_questions"] == [N2_Q])
d = {"follow_up_questions": ["Please give the 6-digit HS code for hardwood."]}
check("N2: a question without 'free zone' is kept",
      drop_free_zone_follow_ups(d, fz) == [] and len(d["follow_up_questions"]) == 1)

print("\n== Step 7.6k: the duty tool's 'BCD only' note cited to P-IN-DUTY-SCOPE (N5 duty-note re-cite)")
WN_SCOPE = next(n for n in wn.tool_results["TOOL:duty:76101000"]["notes"] if "only. IGST" in n)
PAINT_SCOPE = next(n for n in paint.tool_results["TOOL:duty:32091010"]["notes"] if "only. IGST" in n)
# Live wordings, word for word: 27 Oct 19:10 N5 round 1; 24 Oct 19:09 C1 (with the record's IGST-base sentence).
N5_LIVE = ("CEPA rates reduce Basic Customs Duty (BCD) only. IGST, GST compensation cess, the Social Welfare "
           "Surcharge (SWS) and any anti-dumping or safeguard duty still apply.")
C1_LIVE = ("The CEPA rate reduces Basic Customs Duty only; IGST, GST compensation cess, Social Welfare Surcharge and "
           "any anti-dumping or safeguard duties still apply. Because the IGST base includes BCD, a lower BCD also "
           "lowers the IGST amount.")
IGST_BASE = "Because the IGST base includes BCD, a lower BCD also lowers the IGST amount."
d = copy.deepcopy(GOOD_WN)
d["classification"]["tariff_line"] = "32091010"
d["caveats"] = [{"note": N5_LIVE, "source_id": "P-IN-DUTY-SCOPE"}]
ch = recite_duty_notes(d, paint)
check("N5 live: re-cited to TOOL:duty:32091010, the tool's note word for word",
      d["caveats"] == [{"note": PAINT_SCOPE, "source_id": "TOOL:duty:32091010"}] and len(ch) == 1, (d["caveats"], ch))
d = with_caveats(("P-IN-DUTY-SCOPE", C1_LIVE))
n = len(d["caveats"])
ch = recite_duty_notes(d, wn)
check("C1 live: the tool's note re-cited in place, the IGST-base sentence kept with P-IN-DUTY-SCOPE",
      d["caveats"][n - 1:] == [{"note": WN_SCOPE, "source_id": "TOOL:duty:76101000"},
                               {"note": IGST_BASE, "source_id": "P-IN-DUTY-SCOPE"}] and len(ch) == 2, (d["caveats"], ch))
check("... and the result passes the Researcher checks", run(d, wn)[0] == [], run(d, wn)[0])
d = with_caveats(("TOOL:duty:76101000", WN_SCOPE), ("P-IN-DUTY-SCOPE", N5_LIVE))
ch = recite_duty_notes(d, wn)
check("the tool's note already cited to the tool: the passage copy is dropped (one note, not two)",
      [c["note"] for c in d["caveats"]].count(WN_SCOPE) == 1
      and not any(c["source_id"] == "P-IN-DUTY-SCOPE" for c in d["caveats"]) and len(ch) == 1, (d["caveats"], ch))
unchanged = [("AIDC / Table II wording", "P-IN-DUTY-SCOPE",
              ("The CEPA rate reduces Basic Customs Duty (BCD), and the Agriculture Infrastructure and Development Cess "
              "only for lines in Table II.")),
             ("SWS note", "P-IN-DUTY-SCOPE", SWS), ("anti-dumping note", "P-IN-DUTY-SCOPE", AD),
             ("already cited to the tool", "TOOL:duty:76101000", N5_LIVE)]
for label, sid, text in unchanged:
    d = with_caveats((sid, text))
    before = copy.deepcopy(d["caveats"])
    check(f"left as written: {label}", recite_duty_notes(d, wn) == [] and d["caveats"] == before)
no_note = copy.deepcopy(wn)   # a Table II line: the duty result has no "BCD only" note (no such line in the KB yet)
no_note.tool_results["TOOL:duty:76101000"]["notes"].remove(WN_SCOPE)
d = with_caveats(("P-IN-DUTY-SCOPE", N5_LIVE))
check("no 'BCD only' note in the duty result (Table II line): left to the checks and QA",
      recite_duty_notes(d, no_note) == [] and d["caveats"][-1]["source_id"] == "P-IN-DUTY-SCOPE")
plastic = build_evidence({"product_description": "plastic packing articles", "hs_code_given": "39239090",
                          "shipment_value": {"amount": 50000, "currency": "AED"}}, None)
check("excluded line (plastic): its duty result has no 'BCD only' note",
      not any(BCD_ONLY_RE.search(x) for x in plastic.tool_results["TOOL:duty:39239090"]["notes"]))
d = copy.deepcopy(GOOD_P); d["caveats"] = [{"note": N5_LIVE, "source_id": "P-IN-DUTY-SCOPE"}]
check("excluded line (plastic): left as written", recite_duty_notes(d, plastic) == [] and
      d["caveats"][0]["source_id"] == "P-IN-DUTY-SCOPE")
d = with_caveats(("P-IN-DUTY-SCOPE", N5_LIVE)); d["classification"]["tariff_line"] = GAP
check("no tariff line chosen: left as written", recite_duty_notes(d, wn) == [])
res = run_researcher({"product_description": "aluminium window frames"}, wn,
                     llm=fake_llm(with_caveats(("P-IN-DUTY-SCOPE", C1_LIVE))))
check("run_researcher: re-cited before the checks (both caveats, no problem)",
      {"note": WN_SCOPE, "source_id": "TOOL:duty:76101000"} in res.data["caveats"]
      and {"note": IGST_BASE, "source_id": "P-IN-DUTY-SCOPE"} in res.data["caveats"] and res.passed,
      (res.data["caveats"], res.problems))

print("\n== Step 7.6l: the tariff lookup's notes on the user's code reach the report (problem 98)")
w8 = build_evidence({"product_description": "aluminium window frames", "hs_code_given": "76101090",
                     "shipment_value": {"amount": 100000, "currency": "AED"}}, "samples/windows_qualifies")
N4_NOTE = w8.tool_results["TOOL:tariff_lookup"]["report_notes"][0]
# 27 Oct 18:38 N4 round 1, word for word: the Builder later shortened it and the "national" reason was lost.
N4_LIVE = ("The given HS code 76101090 has no exact match; the candidate tariff line 76101000 is under the same "
           "6-digit code. 8-digit codes are national and differ between the UAE and India.")
d = copy.deepcopy(GOOD_W); d["caveats"].append({"note": N4_LIVE, "source_id": "TOOL:tariff_lookup"})
ch = add_tariff_notes(d, w8)
check("N4 live: the restated note is replaced by the tool's note, word for word",
      [c for c in d["caveats"] if c["source_id"] == "TOOL:tariff_lookup"]
      == [{"note": N4_NOTE, "source_id": "TOOL:tariff_lookup"}] and len(ch) == 3, ch)
check("... confidence high -> medium", d["classification"]["confidence"] == "medium")
check("... idempotent (the revision round)", add_tariff_notes(d, w8) == [])
d = copy.deepcopy(GOOD_W); d["classification"]["confidence"] = "medium"
add_tariff_notes(d, w8)
check("N4 (25 Oct): no caveat on it -> the note is added, confidence medium kept",
      d["caveats"][-1] == {"note": N4_NOTE, "source_id": "TOOL:tariff_lookup"}
      and d["classification"]["confidence"] == "medium")
other = {"note": "The description points to another line; confirm the product.", "source_id": "TOOL:tariff_lookup"}
d = copy.deepcopy(GOOD_W); d["caveats"].append(other)
add_tariff_notes(d, w8)
check("another caveat citing the tool is kept", other in d["caveats"])
d = copy.deepcopy(GOOD_W)
check("no code note (windows by keywords): nothing changes", add_tariff_notes(d, w) == [] and d == GOOD_W)
res = run_researcher({"product_description": "aluminium window frames", "hs_code_given": "76101090"}, w8,
                     llm=fake_llm(copy.deepcopy(GOOD_W)))
check("run_researcher (N4 shape): note added, medium, ELIGIBLE, passes",
      {"note": N4_NOTE, "source_id": "TOOL:tariff_lookup"} in res.data["caveats"]
      and res.data["classification"]["confidence"] == "medium" and res.data["verdict"] == "ELIGIBLE"
      and res.passed, (res.problems, res.changes))
n9 = build_evidence(EVAL_BY_ID["N9"].intake, EVAL_BY_ID["N9"].folder)
N9_NOTE = ("The code 85171211 you gave is India's older HS 2017 code for this product; India's current tariff "
           "line is 85171300.")
d = {"classification": {"tariff_line": "85171300", "confidence": "high", "source_id": "TL-IN-85171300"},
     "caveats": []}
add_tariff_notes(d, n9)
check("N9: HS 2017 note added, confidence medium",
      d["caveats"] == [{"note": N9_NOTE, "source_id": "TOOL:tariff_lookup"}]
      and d["classification"]["confidence"] == "medium", d)
check("N9: the tool note keeps the HS-code question (7.9)",
      drop_hs_follow_ups({"follow_up_questions": ["Please confirm the HS code for smartphones."]}, n9) == [])
print("\n== Check 3b: no candidate matches the whole description (problem 100)")
n13 = build_evidence(EVAL_BY_ID["N13"].intake, EVAL_BY_ID["N13"].folder)
check("N13: the tariff lookup marks a split match", n13.tool_results["TOOL:tariff_lookup"]["split_match"])
SPLIT = "matches the whole product description"
d = copy.deepcopy(GOOD_W)
d["classification"] = {"tariff_line": "94036000", "description": "Other wooden furniture", "confidence": "medium",
                       "source_id": "TL-IN-94036000"}
check("N13 live pick (wooden furniture): caught", any(SPLIT in p for p in run(d, n13)[0]), run(d, n13)[0])
d["classification"] = {k: GAP for k in ("tariff_line", "description", "confidence", "source_id")}
check("N13 gap: no split-match problem", not any(SPLIT in p for p in run(d, n13)[0]), run(d, n13)[0])
check("N13: the Researcher's confirm-code question is kept (7.9)",
      drop_hs_follow_ups({"follow_up_questions": ["Please confirm the HS code for wooden doors."]}, n13) == [])
check("windows by keywords: no split-match problem", not any(SPLIT in p for p in run(GOOD_W, w)[0]))
print("\n== 28 Oct fixes after sitting 20261028-191831 (N13): the split note's paraphrase, notes of unchosen lines")
N13_NOTE = n13.tool_results["TOOL:tariff_lookup"]["report_notes"][0]
PLUS = ("'+' in a rule is read as 'and' (both tests must pass). The agreement does not define '+', so this is "
        "Mansha's interpretation.")
# Live, word for word: 28 Oct 19:29 N13 round 2 (round 1 had the IDs in place of "One candidate" / "Another").
N13_LIVE = ("No candidate matches the whole description. One candidate matches only 'door' and is for aluminium "
            "products. Another matches only 'wooden' and is for other wooden furniture.")
gap_cls = {k: GAP for k in ("tariff_line", "description", "source_id")}
d = {"classification": dict(gap_cls, confidence="low"),
     "caveats": [{"note": N13_LIVE, "source_id": "TOOL:tariff_lookup"},
                 {"note": PLUS, "source_id": "TOOL:origin:76101000"}]}
ch = add_tariff_notes(d, n13)
check("N13 live paraphrase of the Researcher-only note -> replaced by the report note",
      d["caveats"][0] == {"note": PLUS, "source_id": "TOOL:origin:76101000"}
      and d["caveats"][-1] == {"note": N13_NOTE, "source_id": "TOOL:tariff_lookup"} and len(d["caveats"]) == 2
      and d["classification"]["confidence"] == "low", (d["caveats"], ch))
ch = drop_line_notes(d)
check("7.6m: gap -> the '+' note of an unchosen line is dropped, the tool's note kept",
      d["caveats"] == [{"note": N13_NOTE, "source_id": "TOOL:tariff_lookup"}] and len(ch) == 1, (d["caveats"], ch))
d = copy.deepcopy(GOOD_W)
check("7.6m: a chosen line keeps its tool notes", drop_line_notes(d) == [] and d == GOOD_W)
print("\n== Step 7.6n: code completes a gap answer (sitting 20261028-194334, N13 round 2)")
# Live shape: round 2 set only the classification to the gap and kept the line's fields, steps, questions
# and notes (3 code problems, CHECKS_FAILED). Here the line kept is the windows line (a candidate in N13).
r2 = copy.deepcopy(GOOD_W)
r2["classification"] = {k: GAP for k in ("tariff_line", "description", "confidence")}
r2["classification"]["source_id"] = "TOOL:tariff_lookup"
r2["origin_result"]["status"] = "NEEDS_MORE_DATA"
r2["follow_up_questions"] = ["Provide a bill of materials.", "Provide the shipment value in AED."]
r2["gaps"] = [{"text": "No tariff line in the evidence covers wooden doors.", "source_id": "TOOL:tariff_lookup"}]
check("before 7.6n: the live shape fails the checks", bool(run(r2, n13)[0]))
res = run_researcher(EVAL_BY_ID["N13"].intake, n13, llm=fake_llm(r2))
check("run_researcher: the gap answer is completed by code and passes",
      res.passed and res.data["verdict"] == GAP and res.data["procedure"] == [] and res.data["follow_up_questions"] == []
      and res.data["origin_result"] == {"status": GAP, "basis": GAP_BASIS, "source_id": "TOOL:tariff_lookup"}
      and res.data["estimated_saving"]["status"] == GAP and res.data["tariff"]["mfn_rate"] == GAP
      and res.data["origin_rule"]["rule"] == GAP and res.data["classification"]["confidence"] == "low",
      (res.problems, res.changes))
check("... only the tariff lookup's note is left in caveats (issuer, duty and line notes dropped)",
      res.data["caveats"] == [{"note": N13_NOTE, "source_id": "TOOL:tariff_lookup"}], res.data["caveats"])
check("... the gap text is kept", res.data["gaps"] == r2["gaps"])
d = copy.deepcopy(GOOD_W)
check("7.6n: a chosen line is left alone", fill_gap(d) == [] and d == GOOD_W)
g = copy.deepcopy(res.data)
check("7.6n: idempotent (an already complete gap)", fill_gap(g) == [])
# 28 Oct 20:53 (N13 r2, Dots3): round 1 wrote the gap but left two source_ids None and its own basis;
# fill_gap skipped both fields (status/rule already the gap): 2 code problems and a wasted round.
R2_BASIS = "No tariff line matched the product description, so origin cannot be assessed."
r2b = copy.deepcopy(res.data)
r2b.pop("verdict", None)
r2b["origin_rule"]["source_id"] = None
r2b["estimated_saving"]["source_id"] = None
r2b["origin_result"]["basis"] = R2_BASIS
g = copy.deepcopy(r2b)
ch = fill_gap(g)
check("7.6n: a gap with source_id None gets both filled (2 changes)",
      len(ch) == 2 and g["origin_rule"]["source_id"] == "TOOL:tariff_lookup"
      and g["estimated_saving"]["source_id"] == "TOOL:tariff_lookup", ch)
check("... the Researcher's own gap basis is kept", g["origin_result"]["basis"] == R2_BASIS)
check("... idempotent", fill_gap(g) == [])
g = copy.deepcopy(r2b)
g["estimated_saving"]["amount"] = 0
g["tariff"]["mfn_rate"] = "5%"
ch = fill_gap(g)
check("7.6n: other wrong fixed keys in a gap object are written too",
      g["estimated_saving"]["amount"] is None and g["tariff"]["mfn_rate"] == GAP and len(ch) == 4, ch)
g = copy.deepcopy(r2b)
g["origin_result"]["basis"] = " "
fill_gap(g)
check("7.6n: an empty gap basis gets the code's sentence", g["origin_result"]["basis"] == GAP_BASIS)
res2 = run_researcher(EVAL_BY_ID["N13"].intake, n13, llm=fake_llm(r2b))
check("run_researcher: the r2 shape passes in round 1 with no problems",
      res2.passed and not res2.problems and res2.data["origin_result"]["basis"] == R2_BASIS,
      (res2.problems, res2.changes))
check("N13 report note passes the shown-text check",
      not any("caveats" in p for p in run({**copy.deepcopy(GOOD_W), "caveats": [
          {"note": N13_NOTE, "source_id": "TOOL:tariff_lookup"}]}, n13)[0]), run(GOOD_W, n13)[0])

# ---------------- step shield: code writes the claim checklist from the KB (S3, 28 Oct) ----------------
print("\n== fill_steps (step shield, S3)")
kb_steps = {p["id"]: p["step"] for p in load_corridor("india")["passages"]["passages"] if p.get("step")}
d = copy.deepcopy(GOOD_W)
d["procedure"] = [{"step": "The Ministry of Economy and Tourism registers the factory.", "source_id": "P-MOET-FACTORY-REG"}]
ch = fill_steps(d, w)
check("ELIGIBLE: the 8 claim steps, in order, the model's actor-first step replaced",
      [st["source_id"] for st in d["procedure"]] == CLAIM_STEPS["india"]
      and ch == ["procedure: 8 step(s) written by code from the knowledge base (replaced 1 written by the model)"],
      ([st["source_id"] for st in d["procedure"]], ch))
check("... each record's step is its KB text word for word",
      all(st["step"] == kb_steps[st["source_id"]]["en"] for st in d["procedure"] if st["source_id"] in kb_steps))
check("... no step starts with a ministry or authority (G14)",
      not any(st["step"].startswith(("The Ministry", "The issuing", "The competent")) for st in d["procedure"]))
check("... idempotent", fill_steps(d, w) == [])
fee = w.tool_results["TOOL:coo_fee"]
check("... the fee step is the fee tool's band",
      d["procedure"][3]["step"] == fee_step(fee, "en") and f"AED {fee['fee_aed']} " in d["procedure"][3]["step"],
      d["procedure"][3])
check("... it passes the checks (numbers, actors, shown text)", run(d, w)[0] == [] and not any(
      x.startswith("procedure") for x in run(d, w)[1]), run(d, w))
d_ar = copy.deepcopy(GOOD_W)
fill_steps(d_ar, w, "ar")
check("Arabic: the Arabic texts, the same records",
      [st["source_id"] for st in d_ar["procedure"]] == CLAIM_STEPS["india"]
      and d_ar["procedure"][0]["step"] == kb_steps["P-MOET-FACTORY-REG"]["ar"]
      and d_ar["procedure"][3]["step"].startswith("ادفع رسوم الشهادة"), d_ar["procedure"][3])
d = copy.deepcopy(GOOD_WN)
fill_steps(d, wn)
check("NEEDS_MORE_DATA: the 8 steps too", len(d["procedure"]) == 8)
d = copy.deepcopy(GOOD_C)
d["procedure"] = [{"step": "Apply for the certificate.", "source_id": "P-MOET-COO-INDIA"}]
ch = fill_steps(d, c)
check("NOT_ELIGIBLE: the model's steps emptied", d["procedure"] == [] and len(ch) == 1, (d["procedure"], ch))
check("NOT_ELIGIBLE without steps: no change", fill_steps(copy.deepcopy(GOOD_C), c) == [])
g = copy.deepcopy(r2b)
g["procedure"] = [{"step": "Register the factory.", "source_id": "P-MOET-FACTORY-REG"}]
fill_steps(g, n13)
check("a gap: no steps", g["procedure"] == [])
bad = copy.deepcopy(GOOD_W)
bad["classification"]["tariff_line"] = "99999999"
check("a classification code rejects: steps left for the checks", fill_steps(bad, w) == []
      and bad["procedure"] == GOOD_W["procedure"])
check("fee_step: no value -> the range",
      fee_step({"status": "NEEDS_VALUE", "fee_range_aed": {"min": 10, "max": 200}}, "en")
      == "Pay the certificate fee: from AED 10 to AED 200, depending on the invoice value in AED.")
check("fee_step: a currency other than AED -> the range",
      "from AED 10 to AED 200" in fee_step({"status": "CURRENCY_NOT_AED", "fee_range_aed": {"min": 10, "max": 200}}, "en"))
check("fee_step: no fee (gap) -> no step",
      fee_step({"status": GAP, "fee_range_aed": {"min": 10, "max": 200}}, "en") is None and fee_step(None, "en") is None)
check("fee_step: top band, thousands shown",
      "AED 200 for an invoice value of AED 750,000.50 " in fee_step(
          {"status": "ESTIMATED", "fee_aed": 200, "invoice_value": "750000.50",
           "fee_range_aed": {"min": 10, "max": 200}}, "en"))
import dataclasses

short = dataclasses.replace(w, allowed_ids=[i for i in w.allowed_ids if i != "P-AGR-3.12-DIRECT"])
check("a record missing from the evidence: its step is left out",
      [st["source_id"] for st in claim_steps(short, "en")] == [i for i in CLAIM_STEPS["india"] if i != "P-AGR-3.12-DIRECT"])
res = run_researcher(wi, w, llm=fake_llm(GOOD_W))
check("run_researcher: passes with the code's steps, authorities from the records",
      res.passed and [st["source_id"] for st in res.data["procedure"]] == CLAIM_STEPS["india"]
      and res.data["procedure"][0]["authority"] == "the Ministry of Economy and Tourism"
      and res.data["procedure"][3]["authority"] == "the Ministry of Foreign Trade", (res.problems, res.changes))
empty = copy.deepcopy(GOOD_W)
empty["procedure"] = []
res = run_researcher(wi, w, llm=fake_llm(empty))
check("run_researcher: the model leaves procedure empty (new prompt) -> steps written, passes",
      res.passed and len(res.data["procedure"]) == 8, (res.problems, res.changes))
msgs = build_messages(wi, w, previous=res.data, corrections=["x: y"])
check("a revision shows the model an empty procedure (code writes it)",
      json.loads(msgs[-2]["content"])["procedure"] == [])

# ---------------- F1: no caveats repeating the checklist (sitting 20261028-215427, N2 and N10) ----------------
print("\n== drop_step_caveats (F1)")
FZ = record_notes(w)["P-MOET-FACTORY-REG"][0]
d = copy.deepcopy(GOOD_W)
fill_steps(d, w)
base = copy.deepcopy(d["caveats"])
d["caveats"] = base + [
    {"note": "Preference is given only to originating goods shipped directly from the UAE to India.", "source_id": "P-AGR-3.12-DIRECT"},
    {"note": ("A certificate of origin is valid for 12 months from issue, covers one import, and can be issued "
              "retrospectively up to 12 months from shipment with 'ISSUED RETROSPECTIVELY' in box 9."), "source_id": "P-AGR-COO-RULES"},
    {"note": FZ, "source_id": "P-MOET-FACTORY-REG"},
    {"note": FZ, "source_id": "P-MOET-FACTORY-REG"},
]
ch = drop_step_caveats(d, w)
check("restatements of step records dropped (direct shipment, the box-9 certificate note)",
      not any(c["source_id"] in ("P-AGR-3.12-DIRECT", "P-AGR-COO-RULES") for c in d["caveats"])
      and "box 9" not in json.dumps(d["caveats"]), ch)
check("... the record's own KB note kept once (free zone), every other caveat untouched",
      [c for c in d["caveats"] if c["source_id"] == "P-MOET-FACTORY-REG"] == [{"note": FZ, "source_id": "P-MOET-FACTORY-REG"}]
      and [c for c in d["caveats"] if c["source_id"] != "P-MOET-FACTORY-REG"]
      == [c for c in base if c["source_id"] != "P-MOET-FACTORY-REG"], d["caveats"])
check("... each drop logged", len(ch) == 3 and sum("restates the checklist step" in c for c in ch) == 2, ch)
d = copy.deepcopy(GOOD_W)
fill_steps(d, w)
d["caveats"] = [c for c in d["caveats"] if c["source_id"] != "P-MOET-FACTORY-REG"] + [{"note": (
    "Factory registration through the Ministry of Economy and Tourism is a prerequisite; it requires the factory "
    "to be outside a free zone. " + FZ), "source_id": "P-MOET-FACTORY-REG"}]   # N10's shape
ch = drop_step_caveats(d, w)
check("a restatement carrying the KB note is cut to the note (N10)",
      d["caveats"][-1] == {"note": FZ, "source_id": "P-MOET-FACTORY-REG"} and len(ch) == 1, (ch, d["caveats"][-1]))
d = copy.deepcopy(GOOD_C)
d["caveats"].append({"note": "Preference requires direct shipment.", "source_id": "P-AGR-3.12-DIRECT"})
check("no checklist (NOT_ELIGIBLE): caveats left alone", drop_step_caveats(d, c) == [])
res = run_researcher(wi, w, llm=fake_llm({**copy.deepcopy(GOOD_W), "procedure": [], "caveats": GOOD_W["caveats"] + [
    {"note": "Preference is given only to originating goods shipped directly from the UAE to India.",
     "source_id": "P-AGR-3.12-DIRECT"}]}))
check("run_researcher: the restating caveat dropped, still passes",
      res.passed and not any(c["source_id"] == "P-AGR-3.12-DIRECT" for c in res.data["caveats"]), (res.problems, res.changes))

print("\n== Problem 99: rule and tariff-line IDs written in plain words by code")

RULES = {"PSR-IN-R118": "CTSH + VA 45%", "PSR-IN-R126": "CTH + VA 40%"}
REAL_99 = [   # round-1 text from saved runs, word for word -> what code writes
    ("The '+' in the rule PSR-IN-R126 is read as 'and' (both tests must pass).",   # 24 Oct C2
     "The '+' in the rule \"CTH + VA 40%\" is read as 'and' (both tests must pass)."),
    ('rule: PSR-IN-R118 "CTSH + VA 45%"; checks: none; missing: a bill of materials',   # 25 Oct N15 (problem 99)
     'rule: "CTSH + VA 45%"; checks: none; missing: a bill of materials'),
    ("No checks were run. The rule PSR-IN-R118 requires 'CTSH + VA 45%' (both tests must pass).",   # 18 Oct
     "No checks were run. The rule requires 'CTSH + VA 45%' (both tests must pass)."),
    ("are missing, so the checks under PSR-IN-R118 cannot be run.",   # 23 Oct 20:08
     "are missing, so the checks under the rule \"CTSH + VA 45%\" cannot be run."),
    ("so the origin rule PSR-IN-R118 cannot be evaluated.",   # 23 Oct 20:08 gap
     "so the origin rule \"CTSH + VA 45%\" cannot be evaluated."),
    ("the description best matches TL-IN-76101000, which was not returned",   # 25 Oct N14
     "the description best matches tariff line 76101000, which was not returned"),
    (("No tariff line in the evidence describes 'wooden doors'. TL-IN-76101000 covers aluminium doors and "
      "TL-IN-94036000 covers other wooden furniture."),   # 28 Oct N13
     ("No tariff line in the evidence describes 'wooden doors'. Tariff line 76101000 covers aluminium doors and "
      "tariff line 94036000 covers other wooden furniture.")),
]
for before, after in REAL_99:
    got = _plain_ids_in(before, RULES)
    check(f"99 real: {before[:50]}...", got == after and not EVIDENCE_ID_RE.search(got), got)
for before, after in (("PSR-IN-R118 applies here.", 'The rule "CTSH + VA 45%" applies here.'),
                      ("Under PSR-IN-R118 (CTSH + VA 45%), both tests apply.",
                       'Under the rule "CTSH + VA 45%", both tests apply.'),
                      ("the tariff line TL-IN-76101000 is chosen", "the tariff line 76101000 is chosen"),
                      ("See PSR-IN-R999 for details.", "See PSR-IN-R999 for details."),   # unknown: left to the check
                      ("No ID here (CTSH + VA 45%).", "No ID here (CTSH + VA 45%).")):
    got = _plain_ids_in(before, RULES)
    check(f"99 edge: {before[:45]}", got == after, got)

d = copy.deepcopy(GOOD_W)
d["caveats"].append({"note": "The '+' in the rule PSR-IN-R118 is read as 'and'.", "source_id": "PSR-IN-R118"})
d["gaps"] = [{"text": "TL-IN-76101000 is the only candidate.", "source_id": "TL-IN-76101000"}]
ch = plain_evidence_ids(d, w)   # the real KB's rule texts
check("99: caveat and gap rewritten from the KB, source_id untouched",
      d["caveats"][-1] == {"note": "The '+' in the rule \"CTSH + VA 45%\" is read as 'and'.", "source_id": "PSR-IN-R118"}
      and d["gaps"][0] == {"text": "Tariff line 76101000 is the only candidate.", "source_id": "TL-IN-76101000"},
      (d["caveats"][-1], d["gaps"]))
check("99: each change logged", ch == [f"caveats[{len(d['caveats']) - 1}].note: rule / tariff-line IDs written in plain words",
                                       "gaps[0].text: rule / tariff-line IDs written in plain words"], ch)
d = copy.deepcopy(GOOD_W)
check("99: an answer without IDs is not touched", plain_evidence_ids(d, w) == [] and d == GOOD_W)
leaky99 = copy.deepcopy(GOOD_W)
leaky99["caveats"].append({"note": "The '+' in the rule PSR-IN-R118 is read as 'and'.",
                           "source_id": "TOOL:origin:76101000"})
res = run_researcher(wi, w, llm=fake_llm(leaky99))
check("99 wired in: the rule ID costs no revision (no ID problem), change logged",
      not any("evidence IDs" in p for p in res.problems)
      and any("rule / tariff-line IDs written in plain words" in c for c in res.changes), (res.problems, res.changes))

# Replay over every saved round-1 answer (Haris's Mac; skipped where runs/ is absent)

KB_RULES = {r["id"]: r["rule_text"] for r in load_corridor("india")["psr"]["rules"]}
saved = sorted(glob.glob("runs/eval_set/*/*/researcher_1.json") + glob.glob("runs/pipeline/*/researcher_1.json"))
had, left, touched_clean = 0, [], []
for f in saved:
    out = json.loads(Path(f).read_text(encoding="utf-8")).get("output") or {}
    texts = [(out.get("origin_result") or {}).get("basis")]
    texts += [c.get("note") for c in out.get("caveats", []) if isinstance(c, dict)]
    texts += [g.get("text") if isinstance(g, dict) else g for g in out.get("gaps", [])]
    texts += [s.get("step") for s in out.get("procedure", []) if isinstance(s, dict)]
    texts += [q for q in out.get("follow_up_questions", []) if isinstance(q, str)]
    for tx in (x for x in texts if isinstance(x, str)):
        new = _plain_ids_in(tx, KB_RULES)
        if re.search(r"\b(?:PSR|TL)-[A-Z]{2}-", tx):
            had += 1
            if re.search(r"\b(?:PSR|TL)-[A-Z]{2}-", new):
                left.append((f, new))
        elif new != tx:
            touched_clean.append((f, tx))
if saved:
    print(f"  (replay: {len(saved)} saved round-1 answers, {had} texts with a rule or tariff-line ID)")
    check("99 replay: no rule or tariff-line ID left in any saved round-1 text", not left, left[:2])
    check("99 replay: text without such IDs is never changed", not touched_clean, touched_clean[:2])

# ---------------- O1: the origin tool's notes on the chosen line, written by code (30 Oct) ----------------
print("\n== O1: origin-tool notes word for word")
O_ID = "TOOL:origin:76101000"
PLUS = wn.tool_results[O_ID]["notes"][0]
W_NOTES = w.tool_results[O_ID]["notes"]
check("fixtures: windows (data) has the '+' and own-declaration notes; no data has only '+'",
      W_NOTES == [PLUS, OWN_DECLARATION_NOTE] and wn.tool_results[O_ID]["notes"] == [PLUS], (W_NOTES, PLUS))
# 230334 N16 r2, verbatim: the own-declaration note reworded (printed English in the Arabic report)
N16R2_DECL = ("The origin result relies on the exporter's own declaration that final manufacture took place in "
              "the UAE and that manufacturing goes beyond minimal operations.")
N16R2_PLUS = ("Mansha interprets the '+' in the rule 'CTSH + VA 45%' as 'and' (both tests must pass); the "
              "agreement does not define '+'.")
d = copy.deepcopy(GOOD_W)
d["caveats"] = [d["caveats"][0], {"note": N16R2_DECL, "source_id": O_ID}, {"note": N16R2_PLUS, "source_id": O_ID},
                d["caveats"][1]]
ch = write_origin_notes(d, w)
check("N16 r2 wording: both rewordings replaced by the tool's notes, word for word, in place",
      d["caveats"] == [GOOD_W["caveats"][0], {"note": PLUS, "source_id": O_ID},
                       {"note": OWN_DECLARATION_NOTE, "source_id": O_ID}, GOOD_W["caveats"][1]], d["caveats"])
check("... logged: 2 dropped, 2 written", sum("dropped" in c for c in ch) == 2
      and sum("note written" in c for c in ch) == 2, ch)
check("... idempotent (the revision round)", write_origin_notes(d, w) == [])
check("... both notes now have an Arabic draft", all(note_match(cv["note"]) for cv in d["caveats"]
                                                    if cv["source_id"] == O_ID))
expect_ok("... and the answer still passes the checks", d, w, "ELIGIBLE")
# 230334 N15 r1, verbatim: a made-up own-declaration note (no data, so the tool has no declaration)
N15R1 = ("The result relies on the exporter's own declaration; a bill of materials and declaration are needed "
         "to apply the rule.")
d = with_caveats((O_ID, N15R1))
ch = write_origin_notes(d, wn)
got = [cv["note"] for cv in d["caveats"] if cv["source_id"] == O_ID]
check("N15 r1 wording: the made-up note dropped, only the tool's own note written", got == [PLUS], got)
check("... no own-declaration note anywhere",
      not any("declaration" in str(cv.get("note")) for cv in d["caveats"]), d["caveats"])
d = copy.deepcopy(GOOD_W)
ch = write_origin_notes(d, w)
check("notes left out by the Researcher: written at the end",
      d["caveats"][-2:] == [{"note": n, "source_id": O_ID} for n in W_NOTES] and len(ch) == 2, ch)
d = copy.deepcopy(GOOD_W)
d["caveats"] += [{"note": n, "source_id": O_ID} for n in W_NOTES]
before = copy.deepcopy(d)
check("exact copies in the tool's order: nothing changes", write_origin_notes(d, w) == [] and d == before)
d = copy.deepcopy(GOOD_W)
d["caveats"] += [{"note": n, "source_id": O_ID} for n in reversed(W_NOTES)] + [{"note": PLUS, "source_id": O_ID}]
ch = write_origin_notes(d, w)
check("exact copies out of order or repeated: once each, tool's order, logged",
      [cv["note"] for cv in d["caveats"] if cv["source_id"] == O_ID] == W_NOTES and len(ch) == 1, ch)
d = with_caveats(("TOOL:origin:76041010", "A note on another candidate's origin result."))
ch = write_origin_notes(d, wn)
check("a caveat citing another line's origin result is left to the checks",
      any(cv["source_id"] == "TOOL:origin:76041010" for cv in d["caveats"]), d["caveats"])
d = copy.deepcopy(GOOD_W); d["caveats"].append({"note": "The value addition build-down is 12%, below the 40% "
                                                "threshold.", "source_id": O_ID})   # 19 Oct chargers kind
write_origin_notes(d, w)
check("a check result restated as a caveat is dropped (the origin section shows it)",
      not any("12%" in cv["note"] for cv in d["caveats"]), d["caveats"])
d = copy.deepcopy(GOOD_W)
d["classification"] = {"tariff_line": GAP, "description": GAP, "confidence": GAP, "source_id": "TOOL:tariff_lookup"}
d["caveats"].append({"note": N16R2_DECL, "source_id": O_ID})
before = copy.deepcopy(d)
check("gap (no line chosen): nothing written, left to drop_line_notes", write_origin_notes(d, w) == [] and d == before)
d = copy.deepcopy(GOOD_P); before = copy.deepcopy(d)
check("excluded line (plastic): no origin result, nothing changes",
      write_origin_notes(d, plastic) == [] and d == before)

# D1: no note printed twice (the '+' note is also the rule lookup's interpretation)
print("\n== O1 / D1: a restated origin note under another record is dropped")
check("D1 bar = the Builder's Arabic-draft bar", (ORIGIN_DUP_OF_NOTE, ORIGIN_DUP_OF_CAVEAT)
      == (NOTE_MATCH_OF_ORIGINAL, NOTE_MATCH_OF_NOTE))
RL_PLUS = "The '+' in the rule is interpreted as 'and' (both tests must pass); the agreement does not define '+'."
d = with_caveats(("TOOL:rule_lookup:76101000", RL_PLUS))   # the most common live wording (9 saved answers)
ch = write_origin_notes(d, wn)
check("'+' reworded under the rule lookup: dropped, the origin copy written once",
      [cv["note"] for cv in d["caveats"] if "'+'" in cv["note"]] == [PLUS]
      and any("it restates TOOL:origin:76101000" in x for x in ch), (d["caveats"], ch))
d = copy.deepcopy(GOOD_W)
d["caveats"] += [{"note": PLUS, "source_id": "TOOL:rule_lookup:76101000"}]
write_origin_notes(d, w)
check("'+' word for word under the rule lookup: kept once (the origin copy)",
      sum(cv["note"] == PLUS for cv in d["caveats"]) == 1, d["caveats"])
d = with_caveats(("TOOL:rule_lookup:76101000", "The '+' in the rule is read as 'and'."))
write_origin_notes(d, wn)
check("a short '+' mention below the bar stays (a miss is only a duplicate)",
      any(cv["note"] == "The '+' in the rule is read as 'and'." for cv in d["caveats"]))
fz_w = dataclasses.replace(w, tool_results={**w.tool_results, O_ID: {**w.tool_results[O_ID],
                                                                     "notes": W_NOTES + [FREE_ZONE_NOTE]}})
FZ_COPY = ("A factory declared in a free zone is likely not eligible for the ministry's factory registration; "
           "confirm with the ministry.")   # a saved answer: the tool's note cited to the KB
FZ_KB = ("A producer in a free zone is likely not eligible for Factory Registration, which is required before "
         "applying for the certificate; confirm with the Ministry of Economy and Tourism.")   # 13 saved answers
d = copy.deepcopy(GOOD_W)
d["caveats"] += [{"note": FZ_COPY, "source_id": "P-MOET-FACTORY-REG"}, {"note": FZ_KB, "source_id": "P-MOET-FACTORY-REG"}]
write_origin_notes(d, fz_w)
kb_fz = [cv["note"] for cv in d["caveats"] if cv["source_id"] == "P-MOET-FACTORY-REG"]
check("free zone: the tool's note restated under the KB is dropped, the KB's own wording kept",
      kb_fz == [FZ_KB] and {"note": FREE_ZONE_NOTE, "source_id": O_ID} in d["caveats"], d["caveats"])
origin_tool_notes = [PLUS, OWN_DECLARATION_NOTE, FREE_ZONE_NOTE, INDIAN_INPUTS_NOTE,
                     "'Direct labour cost' and 'direct overhead cost' are not defined in the agreement."]
hits = [(k, n[:30]) for k, v in note_originals().items() for n in origin_tool_notes
        if v != n and coverage(n, v) >= ORIGIN_DUP_OF_NOTE and coverage(v, n) >= ORIGIN_DUP_OF_CAVEAT]
check("guard: no other KB or tool note with an Arabic draft restates an origin-tool note (so D1 drops none)",
      not hits, hits)

print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")
sys.exit(1 if failures else 0)