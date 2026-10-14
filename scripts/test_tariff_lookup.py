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

print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")