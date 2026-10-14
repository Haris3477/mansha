"""Offline tests for the Researcher's code checks (no LLM, no router).

Run: python -m scripts.test_researcher
"""

import copy
import sys

from mansha.evidence import build_evidence, fmt_num
from mansha.researcher import GAP, build_messages, check_researcher, number_keys

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
                    {"note": "Verify the current issuing ministry.", "source_id": "P-UAE-ISSUER"}],
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

ok = copy.deepcopy(GOOD_W); ok["estimated_saving"]["amount"] = "10,000"
problems, _, _ = run(ok, w)
check("saving written as '10,000' is accepted", not problems, problems)

warn = copy.deepcopy(GOOD_W); warn["origin_result"]["basis"] = "VA 62% meets the 45% threshold."
problems, warnings, _ = run(warn, w)
check("number not in record -> warning, not problem", not problems and bool(warnings), (problems, warnings))
warn = copy.deepcopy(GOOD_W); warn["procedure"][0]["authority"] = "Ministry of Economy"
problems, warnings, _ = run(warn, w)
check("authority not in passage -> warning, not problem", not problems and bool(warnings),
      (problems, warnings))

gap = copy.deepcopy(GOOD_W)
gap["classification"] = {"tariff_line": GAP, "description": GAP, "confidence": "low",
                         "source_id": "TOOL:tariff_lookup"}
gap["origin_result"] = {"status": GAP, "basis": "No tariff line chosen.", "source_id": "TOOL:tariff_lookup"}
gap["estimated_saving"] = {"status": GAP, "amount": None, "currency": None, "source_id": "TOOL:tariff_lookup"}
gap["procedure"] = []
problems, _, v = run(gap, w)
check("declared classification gap is accepted", not problems, problems)
check("classification gap -> verdict GAP", v == GAP, v)

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
check("revision: corrections included", "fix the saving" in m2[3]["content"])

print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")
sys.exit(1 if failures else 0)