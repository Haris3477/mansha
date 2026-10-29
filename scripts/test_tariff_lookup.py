"""Offline tests for the tariff lookup tool. Run: python -m scripts.test_tariff_lookup"""

from mansha.tools.tariff_lookup import tariff_lookup, tokens

failures = []


def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def ids(r):
    return [c["id"] for c in r.candidates]


# text normalisation
check("plurals and spelling", tokens("Aluminum Windows, batteries & boxes") == {"aluminium", "window", "battery", "box"},
      str(tokens("Aluminum Windows, batteries & boxes")))

# HS code path
r = tariff_lookup(hs_code_given="76101000")
check("exact 8-digit code", r.method == "hs_code" and ids(r)[:1] == ["TL-IN-76101000"]
      and r.candidates[0]["match"] == "hs_exact_8", ids(r))

r = tariff_lookup(hs_code_given="7610")
check("4-digit heading prefix", "TL-IN-76101000" in ids(r), ids(r))

r = tariff_lookup(hs_code_given="76101099")
check("unknown 8-digit -> 6-digit siblings + note",
      "TL-IN-76101000" in ids(r) and any("national" in n for n in r.notes), f"{ids(r)} {r.notes}")

r = tariff_lookup(hs_code_given="85171211")
check("HS-2017 code finds smartphone line", "TL-IN-85171300" in ids(r), ids(r))

r = tariff_lookup(hs_code_given="392321")
check("excluded heading, line not loaded -> exclusion record",
      r.status == "CANDIDATES" and r.candidates[0]["kind"] == "heading_exclusion", ids(r))

r = tariff_lookup(hs_code_given="39239090")
check("excluded line is flagged", r.candidates and r.candidates[0]["in_excluded_heading"]
      and r.candidates[0]["cepa"]["status"] == "EXCLUDED", ids(r))

# keyword path
r = tariff_lookup("aluminium window frames")
check("windows ranked first", r.method == "keywords" and ids(r)[:1] == ["TL-IN-76101000"], ids(r))

r = tariff_lookup("battery chargers")
check("chargers found", "TL-IN-85044030" in ids(r), ids(r))

r = tariff_lookup("plastic packing articles")
check("plastic packing found", any(i.startswith("TL-IN-3923") for i in ids(r)), ids(r))

# conflicts and gaps
r = tariff_lookup("aluminium window frames", hs_code_given="85044030")
check("code/description conflict noted", any("does not point to" in n for n in r.notes), r.notes)

r = tariff_lookup(hs_code_given="99999999")
check("unknown code, no description -> NOT_FOUND",
      r.status == "NOT_FOUND" and any("REGULATORY_GAP_DETECTED" in n for n in r.notes), r.notes)

r = tariff_lookup("space rocket engine")
check("unrelated product -> NOT_FOUND", r.status == "NOT_FOUND", ids(r))

# problem 98: notes on the user's own code that the report prints word for word
r = tariff_lookup("aluminium windows", hs_code_given="76101090")
check("N4: no exact 8-digit match -> one report note, also in notes",
      r.report_notes == [("The 8-digit code 76101090 you gave is not a line in India's tariff; Mansha matched it "
                         "on its first 6 digits (761010). 8-digit codes are national and differ between the UAE "
                         "and India.")] and r.report_notes[0] in r.notes, r.report_notes)
r = tariff_lookup("smartphones", hs_code_given="85171211")
check("N9: HS 2017 code -> report note naming the current line",
      r.report_notes == [("The code 85171211 you gave is India's older HS 2017 code for this product; India's "
                         "current tariff line is 85171300.")] and r.notes == r.report_notes, r.notes)
for code in ("76101000", "85171300", "39239090"):
    r = tariff_lookup(hs_code_given=code)
    check(f"current 8-digit line {code}: no report note", r.report_notes == [], r.report_notes)
r = tariff_lookup("aluminium window frames", hs_code_given="39239090")
check("N14 conflict note stays for the Researcher only", r.report_notes == [] and r.notes, r.notes)

# problem 100: best keyword candidates tie on different words -> no line describes the product
for desc, expect in [("wooden doors", ["TL-IN-76101000", "TL-IN-94036000"]), ("steel doors", None),
                     ("wooden windows", None), ("plastic kitchenware", None), ("aluminium furniture", None)]:
    r = tariff_lookup(desc)
    check(f"split match: {desc}", r.split_match and any("No candidate matches the whole description" in n
                                                           and "REGULATORY_GAP_DETECTED" in n for n in r.notes)
          and len(r.report_notes) == 1 and r.report_notes[0] in r.notes
          and not any("TL-IN-" in n for n in r.notes) and (expect is None or ids(r) == expect), (ids(r), r.notes))
r = tariff_lookup("wooden doors")
check("N13: the report note in plain words, no IDs (28 Oct fix)",
      r.report_notes == [("No tariff line in Mansha's sources matches the whole description 'wooden doors': the "
                         "closest lines are 'Doors, windows and their frames and thresholds for doors "
                         "(aluminium)' and 'Other wooden furniture'.")], r.report_notes)
# Every product description in the saved runs and eval cases up to 28 Oct: none is a split match.
for desc in ("acrylic paint", "acrylic paint (resin)", "aluminium cookware", "aluminium window frames",
             "aluminium windows", "aluminium wire rods", "battery chargers", "cosmetic skin creams",
             "hardwood bedroom furniture", "perfume", "plastic packing articles", "smartphones",
             "steel building structures", "sweet biscuits", "wooden bedroom furniture", "laptop computers"):
    r = tariff_lookup(desc)
    check(f"no split match: {desc}", not r.split_match and r.notes == [], r.notes)
r = tariff_lookup("wooden doors", hs_code_given="76101000")
check("code given: no split match (the code path decides)", not r.split_match, r.notes)

print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")