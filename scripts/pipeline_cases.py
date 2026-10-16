"""Dev cases for the full pipeline (Step 9): a user message, an optional bill-of-materials
folder (read only by code), and the expected outcome.

Used by scripts/test_pipeline.py (offline, fake LLM) and scripts/run_pipeline.py (live).
The first four are the four branches (qualifies / fails / needs data / excluded);
the last two are the stops before any research (missing input, destination not covered).

DEV_INTAKES holds the Intake JSON for the four branches, fixed by hand, so the offline tests
can run the Researcher fixtures (samples/researcher_outputs/) and the Builder without an
Intake call. (Moved here from the retired scripts/run_researcher.py in Step 9.6c.)
"""


def intake(product, hs=None, role="manufacturer", processing=None, value=None):
    missing = [k for k, v in (("hs_code_given", hs), ("uae_processing", processing),
                              ("shipment_value", value)) if v is None]
    return {
        "product_description": product, "hs_code_given": hs, "destination_country": "India",
        "exporter_role": role, "uae_processing": processing, "shipment_value": value,
        "language": "en", "missing_fields": missing,
    }


AED_100K = {"amount": 100000, "currency": "AED"}
AED_50K = {"amount": 50000, "currency": "AED"}

# case name -> (intake JSON, case folder with bom.csv/declaration.json, expected verdict)
DEV_INTAKES = {
    "windows": (intake("aluminium window frames",
                       processing="cut and assembled from imported aluminium profiles", value=AED_100K),
                "samples/windows_qualifies", "ELIGIBLE"),
    "chargers": (intake("battery chargers", role="trader",
                        processing="repacked and relabelled only", value=AED_50K),
                 "samples/chargers_repacked", "NOT_ELIGIBLE"),
    "windows_nodata": (intake("aluminium window frames",
                              processing="cut and assembled from imported aluminium profiles"),
                       None, "NEEDS_MORE_DATA"),
    "plastic": (intake("plastic packing articles", hs="39239090", value=AED_50K),
                None, "NO_PREFERENCE"),
}

# name -> (message, case folder or None, expected status, expected verdict or None)
PIPELINE_CASES: dict[str, tuple[str, str | None, str, str | None]] = {
    "windows": (
        ("We run a factory in Sharjah. We cut and assemble aluminium window frames from imported "
         "aluminium profiles and want to export them to India. The shipment is worth AED 100,000."),
        "samples/windows_qualifies", "REPORT", "ELIGIBLE"),
    "chargers": (
        ("We are a trading company in Dubai. We buy battery chargers from China, repack and relabel "
         "them, and re-export them to India. The shipment is worth AED 50,000."),
        "samples/chargers_repacked", "REPORT", "NOT_ELIGIBLE"),
    "windows_nodata": (
        ("We make aluminium window frames in Sharjah from imported aluminium profiles "
         "and want to export them to India."),
        None, "REPORT", "NEEDS_MORE_DATA"),
    "plastic": (
        ("We make plastic packing articles in Ajman, HS code 39239090, and want to ship "
         "AED 50,000 worth of them to India."),
        None, "REPORT", "NO_PREFERENCE"),
    "vague": (
        "Can I pay less customs duty on my exports?",
        None, "NEEDS_INPUT", None),
    "brazil": (
        "We make polyethylene shopping bags in Ajman and want to export them to Brazil.",
        None, "NOT_COVERED", None),
}
