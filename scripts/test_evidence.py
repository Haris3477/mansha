"""Offline tests for the evidence builder (no LLM, no router needed).

Run: python -m scripts.test_evidence          # tests only
     python -m scripts.test_evidence --show   # also print the windows EVIDENCE block
"""

import csv
import sys
from pathlib import Path

from mansha.evidence import HEADER_RE, build_evidence, passages_of
from mansha.kb import load_corridor

WINDOWS = {"product_description": "aluminium window frames", "hs_code_given": None,
           "shipment_value": {"amount": 100000, "currency": "AED"}}
WINDOWS_NO_VALUE = {**WINDOWS, "shipment_value": None}
CHARGERS = {"product_description": "battery chargers", "hs_code_given": None,
            "shipment_value": {"amount": 50000, "currency": "AED"}}
PLASTIC = {"product_description": "plastic packing articles", "hs_code_given": "39239090",
           "shipment_value": {"amount": 50000, "currency": "AED"}}

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def status(pack, tool_id: str):
    return pack.tool_results.get(tool_id, {}).get("status")


def supplier_names(folder: str) -> list[str]:
    with open(Path(folder) / "bom.csv", encoding="utf-8-sig", newline="") as f:
        return [r["supplier"].strip() for r in csv.DictReader(f) if (r.get("supplier") or "").strip()]


def common_checks(name: str, pack) -> None:
    kb = load_corridor("india")
    headers = HEADER_RE.findall(pack.text)
    check(f"{name}: every [ID] header is an allowed ID, in order", headers == pack.allowed_ids)
    check(f"{name}: IDs are unique", len(headers) == len(set(headers)))
    no_url = [i for i in pack.allowed_ids if not i.startswith("TOOL:") and not pack.id_sources.get(i)]
    check(f"{name}: every KB record has a source URL", not no_url, f"missing: {no_url}")
    n_passages = sum(1 for i in pack.allowed_ids if i.startswith("P-"))
    check(f"{name}: all passages included", n_passages == len(passages_of(kb)), f"got {n_passages}")
    agreement = kb["tariff"]["metadata"].get("agreement")
    if pack.candidates:
        check(f"{name}: agreement name present", bool(agreement) and agreement in pack.text)


print("== Windows, with bill of materials")
w = build_evidence(WINDOWS, "samples/windows_qualifies")
common_checks("windows", w)
check("windows: TL-IN-76101000 is a candidate", "TL-IN-76101000" in w.allowed_ids)
check("windows: origin MEETS", status(w, "TOOL:origin:76101000") == "MEETS")
check("windows: duty ESTIMATED", status(w, "TOOL:duty:76101000") == "ESTIMATED")
check("windows: PSR-IN-R118 included", "PSR-IN-R118" in w.allowed_ids)
check("windows: general rules included", {"PSR-GEN-FOB", "PSR-GEN-EXW"} <= set(w.allowed_ids))
check("windows: candidates come before tool results",
      w.text.index("[TL-IN-76101000]") < w.text.index("[TOOL:origin:76101000]"))
names = supplier_names("samples/windows_qualifies")
check("windows: no supplier name in evidence", not any(n in w.text for n in names))

print("\n== Windows, no files, no shipment value")
wn = build_evidence(WINDOWS_NO_VALUE, None)
common_checks("windows-nodata", wn)
check("windows-nodata: origin INSUFFICIENT_DATA", status(wn, "TOOL:origin:76101000") == "INSUFFICIENT_DATA")
check("windows-nodata: duty NEEDS_VALUE", status(wn, "TOOL:duty:76101000") == "NEEDS_VALUE")

print("\n== Chargers, repacked")
c = build_evidence(CHARGERS, "samples/chargers_repacked")
common_checks("chargers", c)
check("chargers: TL-IN-85044030 is a candidate", "TL-IN-85044030" in c.allowed_ids,
      f"candidates: {[x['id'] for x in c.candidates]}")
check("chargers: origin FAILS", status(c, "TOOL:origin:85044030") == "FAILS")
names = supplier_names("samples/chargers_repacked")
check("chargers: no supplier name in evidence", not any(n in c.text for n in names))

print("\n== Plastic packing (excluded)")
p = build_evidence(PLASTIC, None)
common_checks("plastic", p)
check("plastic: marked excluded", "TL-IN-39239090" in p.excluded_ids)
check("plastic: no origin run", "TOOL:origin:39239090" not in p.allowed_ids)
check("plastic: no rule lookup run", "TOOL:rule_lookup:39239090" not in p.allowed_ids)
check("plastic: duty NO_PREFERENCE", status(p, "TOOL:duty:39239090") == "NO_PREFERENCE")

print(f"\nWindows evidence size: {len(w.text)} chars (~{len(w.text) // 4} tokens), "
      f"{len(w.allowed_ids)} IDs")

if "--show" in sys.argv:
    print("\n" + "=" * 70 + "\n" + w.text)

print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")
sys.exit(1 if failures else 0)