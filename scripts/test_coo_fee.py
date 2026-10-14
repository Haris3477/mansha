"""Offline tests for the certificate-fee tool. Run: python -m scripts.test_coo_fee"""

import sys

from mansha.tools.coo_fee import certificate_fee

failures: list[str] = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def fee(amount, currency="AED"):
    return certificate_fee({"amount": amount, "currency": currency})


print("== Bands (edges)")
for amount, expected in [(1, 10), (1000, 10), (1001, 20), (5000, 20), (5001, 30), (40000, 40),
                         (40001, 50), (100000, 50), (100001, 100), (500000, 100), (500001, 200),
                         (9_000_000, 200)]:
    r = fee(amount)
    check(f"AED {amount} -> fee AED {expected}", r.status == "ESTIMATED" and r.fee_aed == expected,
          (r.status, r.fee_aed))

r = fee(600000)
check("top band has no upper limit", r.band_max_aed is None)
check("amount written as '100,000' accepted", fee("100,000").fee_aed == 50)
check("lowercase currency accepted", fee(100000, "aed").fee_aed == 50)

print("\n== No value / other currency")
r = certificate_fee(None)
check("no value -> NEEDS_VALUE", r.status == "NEEDS_VALUE" and r.fee_aed is None)
check("no value -> range 10-200", r.fee_range_aed == {"min": 10, "max": 200}, r.fee_range_aed)
check("zero amount -> NEEDS_VALUE", fee(0).status == "NEEDS_VALUE")
check("missing currency -> NEEDS_VALUE", certificate_fee({"amount": 5000, "currency": None}).status == "NEEDS_VALUE")
r = fee(5000, "USD")
check("USD -> CURRENCY_NOT_AED", r.status == "CURRENCY_NOT_AED" and r.fee_aed is None)
check("USD -> never converted", r.invoice_value == "5000.00" and r.currency == "USD")

print("\n== Sources and notes")
r = fee(100000)
check("has source URLs", bool(r.sources))
check("states the invoice-value assumption", any("invoice value equals" in n for n in r.notes))
check("tool id", r.to_dict()["tool_id"] == "TOOL:coo_fee")

print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")
sys.exit(1 if failures else 0)