"""Test the Intake Agent.

Run from the project root:
    python -m scripts.test_intake            # offline + live (6 LLM calls)
    python -m scripts.test_intake --offline  # offline only, no LLM calls
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from dotenv import load_dotenv

from mansha.intake import normalize, run_intake
from mansha.llm_client import LLMResult

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

failures = 0


def check(label: str, actual, expected) -> None:
    global failures
    ok = actual == expected
    failures += 0 if ok else 1
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {actual!r}" + ("" if ok else f" (expected {expected!r})"))


def offline_tests() -> None:
    print("\n=== OFFLINE: normalize() ===")

    raw = {
        "product_description": " aluminium window frames ",
        "hs_code_given": "7610.10",
        "destination_country": "الهند",
        "exporter_role": "Producer",
        "uae_processing": "N/A",
        "shipment_value": {"amount": "٢٥٠٬٠٠٠", "currency": "درهم"},
        "language": "arabic",
        "missing_fields": [],
    }
    data, _ = normalize(raw, "نصدّر إطارات نوافذ إلى الهند، الرمز 7610.10، بقيمة ٢٥٠٬٠٠٠ درهم")
    print("Case A: messy Arabic output")
    check("product_description", data["product_description"], "aluminium window frames")
    check("hs_code_given", data["hs_code_given"], "761010")
    check("destination_country", data["destination_country"], "India")
    check("exporter_role", data["exporter_role"], "manufacturer")
    check("uae_processing", data["uae_processing"], None)
    check("shipment_value", data["shipment_value"], {"amount": 250000, "currency": "AED"})
    check("language", data["language"], "ar")
    check("missing_fields", data["missing_fields"], ["uae_processing"])

    raw = {
        "product_description": "phone chargers",
        "hs_code_given": "85044090",
        "destination_country": "India",
        "exporter_role": "importer",
        "uae_processing": None,
        "shipment_value": {"amount": -5, "currency": "usd"},
        "language": "en",
        "missing_fields": [],
    }
    data, _ = normalize(raw, "We resell phone chargers to India.")
    print("Case B: invented HS code, bad role, negative amount")
    check("hs_code_given (not in message)", data["hs_code_given"], None)
    check("exporter_role", data["exporter_role"], None)
    check("shipment_value", data["shipment_value"], None)
    check("missing_fields", data["missing_fields"],
          ["hs_code_given", "exporter_role", "uae_processing", "shipment_value"])

    print("\n=== OFFLINE: run_intake() with a fake LLM ===")
    seen = []

    def fake_llm(agent, chain, messages, **kwargs):
        seen.append((agent, chain, kwargs.get("required_keys")))
        reply = dict(raw, hs_code_given=None, missing_fields=[])
        return LLMResult(text=json.dumps(reply), data=reply, routed_via="fake/model",
                         finish_reason="stop", latency_s=0.0)

    result = run_intake("We make aluminium window frames in Sharjah for India.", llm=fake_llm)
    check("fake LLM called once, as intake on auto:qa", [s[:2] for s in seen], [("intake", "auto:qa")])
    check("JSON keys validated by the client", "missing_fields" in (seen[0][2] or ()), True)
    check("output normalized by code", result.data["destination_country"], "India")
    check("served_by kept for the phase log", result.llm.routed_via, "fake/model")


LIVE_CASES = [
    {
        "name": "1. English manufacturer -> India, with BoM",
        "message": "We run a factory in Sharjah. We cut and assemble aluminium window frames "
                   "from imported aluminium profiles and want to export them to India. "
                   "The shipment is worth AED 250,000. I have a bill of materials.",
        "expect": {"destination_country": "India", "exporter_role": "manufacturer", "language": "en",
                   "hs_code_given": None,
                   "shipment_value": {"amount": 250000, "currency": "AED"}, "blocking": []},
    },
    {
        "name": "2. Same in Arabic",
        "message": "نحن مصنع في الشارقة نقص ونجمّع إطارات نوافذ من الألومنيوم من مقاطع ألومنيوم "
                   "مستوردة، ونريد تصديرها إلى الهند. قيمة الشحنة ٢٥٠٬٠٠٠ درهم.",
        "expect": {"destination_country": "India", "exporter_role": "manufacturer", "language": "ar",
                   "shipment_value": {"amount": 250000, "currency": "AED"}, "blocking": []},
    },
    {
        "name": "3. Vague message",
        "message": "Can I pay less customs duty on my exports?",
        "expect": {"product_description": None, "destination_country": None, "language": "en",
                   "blocking": ["product_description", "destination_country"]},
    },
    {
        "name": "4. Trader re-exporting without processing",
        "message": "We are a trading company in Dubai. We buy mobile phone chargers from China, "
                   "repack them and re-export them to India. HS code 8504.40.",
        "expect": {"destination_country": "India", "exporter_role": "trader",
                   "hs_code_given": "850440", "shipment_value": None, "blocking": []},
    },
    {
        "name": "5. Destination not in the knowledge base",
        "message": "We make polyethylene shopping bags in Ajman and want to export them to Brazil.",
        "expect": {"destination_country": "Brazil", "exporter_role": "manufacturer", "blocking": []},
    },
    {
        "name": "6. Shipment value in USD",
        "message": "We manufacture steel water tanks in Abu Dhabi for export to India. "
                   "The shipment is worth USD 80,000.",
        "expect": {"destination_country": "India",
                   "shipment_value": {"amount": 80000, "currency": "USD"}, "blocking": []},
    },
]


def live_tests() -> None:
    print("\n=== LIVE: 6 dev cases (auto:qa) ===")
    for case in LIVE_CASES:
        print(f"\n--- {case['name']} ---")
        result = run_intake(case["message"])
        print(f"  served by: {result.llm.routed_via}")
        print(json.dumps(result.data, ensure_ascii=False, indent=2))
        for field, expected in case["expect"].items():
            actual = result.blocking_missing if field == "blocking" else result.data.get(field)
            check(field, actual, expected)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="skip LLM calls")
    args = parser.parse_args()

    load_dotenv()
    offline_tests()
    if not args.offline:
        live_tests()

    print(f"\n{'ALL PASSED' if failures == 0 else f'{failures} CHECK(S) FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()