"""Offline tests for the automatic report check (Step 9.6b). No LLM, no router.

Run: python -m scripts.test_report_check
Builds the code-only report of each saved Researcher output (samples/researcher_outputs/),
checks it is clean, then breaks it one way at a time: each check must fire on its own
mistake (break test) and stay quiet on look-alikes that real reports contain.
"""

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

from mansha.document_builder import DISCLAIMER, run_document_builder
from mansha.evidence import build_evidence
from mansha.llm_client import LLMCallError
from mansha.report_check import check_report, reader_text
from scripts.check_reports import main as check_reports_main
from scripts.pipeline_cases import DEV_INTAKES as CASES

FIXTURES = Path("samples/researcher_outputs")
failures: list[str] = []


def check(name: str, cond: bool, detail="") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def no_llm(*args, **kwargs):
    raise LLMCallError("offline test", [])


def case(name: str) -> dict:
    """Everything check_report needs for one dev case, with the code-only (fallback) report."""
    research = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))["output"]
    intake, folder, _ = CASES[name]
    pack = build_evidence(intake, folder)
    report = run_document_builder(research, intake, pack.id_sources, llm=no_llm).markdown
    message = f"We want to export {intake['product_description']} to India."
    return {"markdown": report, "research": research, "evidence_text": pack.text, "message": message}


def run(c: dict, markdown: str | None = None, **over):
    args = dict(c, **over)
    if markdown is not None:
        args["markdown"] = markdown
    return check_report(args.pop("markdown"), **args)


def add_note(markdown: str, text: str) -> str:
    """Put a sentence where the LLM's prose goes (the end of the Summary)."""
    return markdown.replace("\n\n## ", f" {text}\n\n## ", 1)


CASES_BUILT = {name: case(name) for name in ("windows", "chargers", "windows_nodata", "plastic")}
win, chg = CASES_BUILT["windows"], CASES_BUILT["chargers"]

# ---------------------------------------------------------------- 1
print("\n1. Clean reports pass")
for name, c in CASES_BUILT.items():
    p, w = run(c)
    check(f"{name}: no problems, no warnings", not p and not w, p + w)

# ---------------------------------------------------------------- 2
print("\n2. Each check fires on its own mistake (break test)")
BREAKS = [
    ("evidence ID", "The rule PSR-IN-R118 is met.", "evidence ID or note number 'PSR-IN-R118'"),
    ("tariff record ID", "See TL-IN-76101000.", "'TL-IN-76101000'"),
    ("tool ID", "Per TOOL:origin:76101000.", "evidence ID"),
    ("note number", "As note N2 says.", "'N2'"),
    ("internal word", "The code was not provided in the intake.", "internal word 'intake'"),
    ("builder status code", "Result: NOT_ELIGIBLE.", "status code 'NOT_ELIGIBLE'"),
    ("tool status code", "Final manufacture (FAIL).", "status code 'FAIL'"),
    ("gap code", "Rule: REGULATORY_GAP_DETECTED.", "status code 'REGULATORY_GAP_DETECTED'"),
    ("raw field name", "Totals: price_basis FOB, inputs_count 2.", "raw field name 'price_basis'"),
    ("python list", "Declared operations ['b', 'k', 'l'].", "raw Python value"),
    ("python dict", "Totals {'price_basis': 'FOB'}.", "raw Python value"),
    ("number from nowhere", "The fee is AED 777.", "not in the evidence or the message: 777"),
]
for what, sentence, expect in BREAKS:
    p, _ = run(win, add_note(win["markdown"], sentence))
    check(f"{what}: flagged", any(expect in x for x in p), p)

p, _ = run(win, win["markdown"].replace(DISCLAIMER["en"], "This report is informational only."))
check("disclaimer changed: flagged", any("disclaimer" in x for x in p), p)
p, _ = run(win, language="ar")
check("Arabic report without the Arabic disclaimer: flagged", any("disclaimer" in x for x in p), p)

cls = re.search(r"## Product classification\n\n(.*?)\n", win["markdown"]).group(1)
p, _ = run(win, win["markdown"].replace(cls, "The product is classified under the line for aluminium frames."))
check("tariff line missing from the classification: flagged", any("76101000" in x for x in p), p)
spaced = win["markdown"].replace(cls, cls.replace("76101000", "7610 10 00"))
p, _ = run(win, spaced)
check("tariff line written '7610 10 00': not flagged", not p, p)

p, w = run(chg, add_note(chg["markdown"], "Apply for a certificate of origin with the issuer."))
check("NOT_ELIGIBLE + claim words: warning, not problem", not p and len(w) == 2, (p, w))
p, w = run(chg, add_note(chg["markdown"], "Actual amounts will differ from the estimate shown."))
check("no saving + estimate words: warning", any("estimate" in x for x in w), w)
p, w = run(win, add_note(win["markdown"], "Apply for a certificate of origin; amounts differ from the estimate shown."))
check("ELIGIBLE with a saving: claim and estimate words are fine", not p and not w, (p, w))

# ---------------------------------------------------------------- 3
print("\n3. No false alarms on look-alikes from real reports")
LOOKALIKES = [
    ("quoted rule and 'and'", "The '+' in the rule 'CTSH + VA 45%' is read as 'and' (both tests must pass)."),
    ("quoted description in brackets", "Confirm that 76101000 ('Doors, windows and their frames') is correct."),
    ("upper-case quote from a source", "It is marked 'ISSUED RETROSPECTIVELY' in box 9."),
    ("thousands separator", "The saving is AED 10,000."),
    ("number written with decimals", "The saving is 10000.00 AED."),
    ("article number", "Under Art. 3.5.1, these are minimal operations."),
    ("Mansha's", "Mansha's confidence is high."),
]
for what, sentence in LOOKALIKES:
    p, w = run(win, add_note(win["markdown"], sentence))
    check(f"{what}: not flagged", not p and not w, p + w)
text = reader_text(win["markdown"], "en")
check("Sources (URLs with '_'), Disclaimer and [n] markers are left out of the scan",
      "## Sources" not in text and "## Disclaimer" not in text and not re.search(r"\[\d+\]", text)
      and "http" not in text)

# ---------------------------------------------------------------- 4
print("\n4. scripts.check_reports on saved run folders")
root = Path(tempfile.mkdtemp(prefix="mansha_report_check_"))


def save_run(name: str, c: dict, markdown: str) -> Path:
    d = root / name
    d.mkdir()
    (d / "report.md").write_text(markdown, encoding="utf-8")
    (d / "evidence.txt").write_text(c["evidence_text"], encoding="utf-8")
    (d / "message.txt").write_text(c["message"], encoding="utf-8")
    (d / "researcher_1.json").write_text(json.dumps({"output": c["research"]}), encoding="utf-8")
    (d / "intake.json").write_text(json.dumps({"output": {"language": "en"}}), encoding="utf-8")
    return d


good = save_run("good", win, win["markdown"])
bad = save_run("bad", win, add_note(win["markdown"], "The rule PSR-IN-R118 is met."))
stop = root / "stop"
stop.mkdir()
(stop / "notice.md").write_text("Mansha needs more information.\n", encoding="utf-8")
check("good folder: exit 0", check_reports_main([str(good), str(stop)]) == 0)
check("bad folder: exit 1", check_reports_main([str(good), str(bad)]) == 1)
(bad / "researcher_2.json").write_text(json.dumps({"output": win["research"]}), encoding="utf-8")
check("uses the last researcher round", check_reports_main([str(bad)]) == 1)
shutil.rmtree(root)

print("\n" + ("ALL PASSED" if not failures else f"{len(failures)} FAILED: {failures}"))
sys.exit(1 if failures else 0)
