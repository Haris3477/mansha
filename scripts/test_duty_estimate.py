"""Offline tests for the duty estimate tool. Run: python -m scripts.test_duty_estimate"""

from mansha.tools.duty_estimate import duty_estimate

failures = []


def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


AED_100K = {"amount": 100000, "currency": "AED"}

r = duty_estimate("76101000", AED_100K)
check("windows: 10% -> 0%, saving 10,000 AED",
      r.status == "ESTIMATED" and r.duty_without_cepa == "10000.00" and r.duty_with_cepa == "0.00"
      and r.saving == "10000.00" and r.currency == "AED", r.to_dict())
check("cites the tariff line record", r.line_id == "TL-IN-76101000" and "N09" in r.sources, r.sources)

r = duty_estimate("73089090", AED_100K)
check("steel: effective 10% used, not tariff 15%",
      r.mfn_rate_pct == 10 and r.saving == "10000.00" and any("prints 15" in n for n in r.notes), r.to_dict())

r = duty_estimate("94036000", {"amount": 50000, "currency": "AED"})
check("furniture: 20% -> 12.5%, saving 3,750", r.saving == "3750.00" and r.rate_difference_pts == 7.5,
      r.to_dict())

r = duty_estimate("76041010", {"amount": 1000, "currency": "AED"})
check("wire rods: 7.5% -> 3.75% exact decimals",
      r.duty_without_cepa == "75.00" and r.duty_with_cepa == "37.50" and r.saving == "37.50", r.to_dict())

r = duty_estimate("39239090", AED_100K)
check("excluded plastics: NO_PREFERENCE, MFN 15% charged, saving 0",
      r.status == "NO_PREFERENCE" and r.cepa_rate_pct is None and r.duty_without_cepa == "15000.00"
      and r.saving == "0.00", r.to_dict())

r = duty_estimate("76101000", None)
check("no value: NEEDS_VALUE with rate gap only",
      r.status == "NEEDS_VALUE" and r.rate_difference_pts == 10 and r.saving is None, r.to_dict())

r = duty_estimate("76101000", {"amount": -5, "currency": "AED"})
check("negative value treated as missing", r.status == "NEEDS_VALUE", r.status)

r = duty_estimate("76101000", {"amount": 27000, "currency": "usd"})
check("USD kept, never converted", r.currency == "USD" and r.saving == "2700.00", r.to_dict())

r = duty_estimate("99999999", AED_100K)
check("unknown line -> REGULATORY_GAP_DETECTED", r.status == "REGULATORY_GAP_DETECTED" and r.saving is None,
      r.notes)

r = duty_estimate("76101000", AED_100K)
check("caveats present (CIF value, BCD only, needs qualifying origin)",
      any("assessable" in n for n in r.notes) and any("Basic Customs Duty" in n for n in r.notes)
      and any("qualifies" in n for n in r.notes), r.notes)

r = duty_estimate("39239090", AED_100K)
check("excluded line: no note about what the CEPA rate reduces (it has none)",
      not any("Basic Customs Duty" in n for n in r.notes) and not any("qualifies" in n for n in r.notes),
      r.notes)

print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")