"""Offline tests for the Researcher's code checks (no LLM, no router).

Run: python -m scripts.test_researcher
"""

import copy
import json
import sys
from pathlib import Path

import mansha.researcher as researcher_mod
from mansha.evidence import build_evidence, fmt_num, passages_of
from mansha.kb import load_corridor
from mansha.llm_client import LLMCallError, LLMResult
from mansha.researcher import (
    GAP,
    build_messages,
    check_researcher,
    drop_caveat_gaps,
    drop_claim_caveats,
    drop_follow_ups,
    fill_authorities,
    fill_fixed_notes,
    fill_tariff_line,
    number_keys,
    run_researcher,
    strip_list_markers,
    unbracket_ids,
)
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
check("pack.actors has the fee tool's actor",
      w.actors.get("TOOL:coo_fee") == kb_actors.get("P-MOET-COO-INDIA"), w.actors.get("TOOL:coo_fee"))
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
check("missing authority filled from the passage", got[1] == "the Ministry of Foreign Trade", got[1])
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
      res.passed and res.data["verdict"] == "NOT_ELIGIBLE" and len(res.changes) == 1, (res.problems, res.changes))
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
LIVE_74 = ["What manufacturing operations were performed on these battery chargers in the UAE, "
           "beyond repacking and relabeling?",
           "Where was the final manufacture of these battery chargers completed?",
           "What is the FOB value of this shipment and the customs (CIF) value of any "
           "non-originating materials used?"]
asks = copy.deepcopy(GOOD_C); asks["follow_up_questions"] = list(LIVE_74)
d = copy.deepcopy(asks)
changes = drop_follow_ups(d, "NOT_ELIGIBLE")
check("NOT_ELIGIBLE: every follow-up dropped, one change each",
      d["follow_up_questions"] == [] and len(changes) == 3
      and all(x.startswith("follow_up_questions: dropped for verdict NOT_ELIGIBLE") for x in changes), changes)
d = copy.deepcopy(GOOD_P); d["follow_up_questions"] = ["Can you confirm the HS code?"]
check("NO_PREFERENCE: dropped", drop_follow_ups(d, "NO_PREFERENCE") and d["follow_up_questions"] == [])
for v in ("ELIGIBLE", "NEEDS_MORE_DATA", GAP):
    d = copy.deepcopy(GOOD_WN)
    check(f"{v}: follow-ups kept", drop_follow_ups(d, v) == []
          and d["follow_up_questions"] == GOOD_WN["follow_up_questions"])
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
      res.passed and res.data["follow_up_questions"] == GOOD_WN["follow_up_questions"] and res.changes == [],
      (res.problems, res.changes))

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
check("run_researcher (live 19 Oct case): passes, 9 caveats, 8 drops recorded",
      res.passed and len(res.data["caveats"]) == 9 and res.data["verdict"] == "NOT_ELIGIBLE"
      and sum(x.startswith("caveats: dropped a note about claiming") for x in res.changes) == 8,
      (res.problems, res.changes))
leak = copy.deepcopy(GOOD_C)
leak["caveats"] = [{"source_id": "P-UAE-ISSUER", "note": "See P-UAE-ISSUER for the issuer."}]
check("a claim note with an evidence ID is a problem on its own", any("caveats[0]" in x for x in run(leak, c)[0]))
res = run_researcher(ci_, c, llm=fake_llm(leak))
check("...but no stale problem once code has dropped it", res.passed, res.problems)
res = run_researcher(wi, w, llm=fake_llm(GOOD_W))
check("run_researcher ELIGIBLE: caveats untouched, no change",
      res.passed and res.data["caveats"] == GOOD_W["caveats"] and res.changes == [], (res.problems, res.changes))
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

print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")
sys.exit(1 if failures else 0)