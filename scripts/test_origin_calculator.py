"""Offline tests for the origin calculator. Run: python -m scripts.test_origin_calculator"""

import copy
import csv
import json

from mansha.tools.origin_calculator import calculate_origin, origin_from_folder

failures = []


def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def results(r):
    return {c["check"]: c["result"] for c in r.checks}


def va(r):
    return next(c["values"] for c in r.checks if c["check"] == "VA")


with open("samples/windows_qualifies/bom.csv", encoding="utf-8-sig") as f:
    WIN_BOM = list(csv.DictReader(f))
with open("samples/windows_qualifies/declaration.json", encoding="utf-8") as f:
    WIN_DEC = json.load(f)

# --- demo case 1: qualifies ---
r = origin_from_folder("76101000", "samples/windows_qualifies")
check("windows MEETS", r.status == "MEETS", r.to_dict())
check("windows CTSH and VA pass", results(r).get("CTSH") == "PASS" and results(r).get("VA") == "PASS", results(r))
check("windows VA 49% vs 45% (FOB)", va(r)["build_down_pct"] == 49.0 and va(r)["threshold_pct"] == 45, va(r))
check("rule cited", r.rule_text == "CTSH + VA 45%" and r.rule_id, r.rule_id)

dump = json.dumps(r.to_dict())
check("no supplier names leak", "Supplier" not in dump)
check("no individual input values leak", "38000" not in dump and "9000.0" not in dump)

# --- Ex-Works lowers the threshold by 5 points ---
dec = dict(WIN_DEC, price_basis="EXW")
r = calculate_origin("76101000", WIN_BOM, dec)
check("Ex-Works threshold 40%", va(r)["threshold_pct"] == 40, va(r))

# --- demo case 2: repacked chargers fail three ways ---
r = origin_from_folder("85044030", "samples/chargers_repacked")
res = results(r)
check("chargers FAILS", r.status == "FAILS", r.status)
check("chargers fail final manufacture, minimal ops, CTH and VA",
      res.get("final_manufacture_in_uae") == "FAIL" and res.get("minimal_operations") == "FAIL"
      and res.get("CTH") == "FAIL" and res.get("VA") == "FAIL", res)
check("chargers VA 12%", va(r)["build_down_pct"] == 12.0, va(r))
mo = next(ch for ch in r.to_dict()["checks"] if ch["check"] == "minimal_operations")["basis"]
check("minimal operations named from Art. 3.5.1, not as raw codes",
      "(b) changes of packaging" in mo and "(l) affixing or printing marks, labels" in mo
      and "['b'" not in mo and " / " not in mo, mo)
r2 = calculate_origin("76101000", WIN_BOM, dict(WIN_DEC, operations=["zz"]))
check("unknown operation code reported readably",
      any("unknown operation codes: zz" in m for m in r2.missing), r2.missing)

# --- demo case 3: no files -> needs more data ---
r = origin_from_folder("76101000", None)
check("no BOM -> INSUFFICIENT_DATA with a request", r.status == "INSUFFICIENT_DATA" and r.missing, r.missing)

# --- data problems ---
bom = copy.deepcopy(WIN_BOM)
bom[0]["currency"] = "USD"
r = calculate_origin("76101000", bom, WIN_DEC)
check("mixed currency -> INSUFFICIENT_DATA, never converted",
      r.status == "INSUFFICIENT_DATA" and any("never converted" in m for m in r.missing), r.missing)

bom = copy.deepcopy(WIN_BOM)
bom[0]["hs_code"] = ""
r = calculate_origin("76101000", bom, WIN_DEC)
check("missing HS of non-originating input -> INSUFFICIENT_DATA",
      r.status == "INSUFFICIENT_DATA" and any("6-digit HS" in m for m in r.missing), r.missing)

r = calculate_origin("76101000", WIN_BOM, dict(WIN_DEC, operations=["xyz"]))
check("unknown operation code -> INSUFFICIENT_DATA", r.status == "INSUFFICIENT_DATA", r.missing)

# --- de minimis on the tariff shift ---
small = {"input_description": "Imported frame part", "hs_code": "761010", "origin_country": "CN",
         "value": "2000", "currency": "AED", "value_basis": "CIF"}
r = calculate_origin("76101000", WIN_BOM + [small], WIN_DEC)
check("same-subheading input at 2% passes via de minimis",
      results(r).get("CTSH") == "PASS" and r.status == "MEETS", r.to_dict()["checks"])
big = dict(small, value="12000")
r = calculate_origin("76101000", WIN_BOM + [big], WIN_DEC)
check("same-subheading input at 12% fails CTSH", results(r).get("CTSH") == "FAIL" and r.status == "FAILS",
      results(r))

# --- build-up method can rescue VA ---
bom = copy.deepcopy(WIN_BOM)
bom[0]["value"] = "45000"  # NOM 58,000 -> build-down 42% < 45%
r = calculate_origin("76101000", bom, WIN_DEC)
check("build-down alone fails at 42%", results(r).get("VA") == "FAIL" and va(r)["build_down_pct"] == 42.0, va(r))
r = calculate_origin("76101000", bom, dict(WIN_DEC, direct_labour=30000, direct_overhead=12000))
check("build-up 47% passes (either method)", results(r).get("VA") == "PASS" and va(r)["build_up_pct"] == 47.0,
      va(r))

# --- rule not loaded ---
r = origin_from_folder("71131910", "samples/windows_qualifies")
check("chapter 71 -> RULE_GAP", r.status == "RULE_GAP" and any("REGULATORY_GAP_DETECTED" in n for n in r.notes),
      r.notes)

print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")