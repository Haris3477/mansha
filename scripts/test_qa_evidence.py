"""Offline tests for the QA Evaluator's compact evidence (Step 7.2). No LLM, no router.

Uses the 4 saved Researcher outputs (samples/researcher_outputs/) with the evidence
rebuilt from DEV_INTAKES.

Run: python -m scripts.test_qa_evidence
"""

import copy
import csv
import json
import sys
from pathlib import Path

from mansha.evidence import build_evidence
from mansha.qa_evidence import cited_ids, qa_evidence, research_for_qa
from mansha.researcher import GAP, digits, number_keys, split_records
from scripts.pipeline_cases import DEV_INTAKES

FIXTURES = Path("samples/researcher_outputs")
failures: list[str] = []


def check(name: str, cond: bool, detail="") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def clean(block: str) -> str:
    """A record's own lines: everything before the next section header."""
    out = []
    for ln in block.strip().splitlines():
        if ln.startswith("=== "):
            break
        out.append(ln)
    return "\n".join(out).strip()


def load(case: str) -> dict:
    return json.loads((FIXTURES / f"{case}.json").read_text(encoding="utf-8"))["output"]


sizes = []
for case, (intake, folder, _) in DEV_INTAKES.items():
    print(f"\n== {case}")
    research = load(case)
    pack = build_evidence(intake, folder)
    full = {rid: clean(t) for rid, t in split_records(pack.text).items()}
    text = qa_evidence(pack, research)
    got = split_records(text)
    line = digits(research["classification"]["tariff_line"])
    cited = cited_ids(research)

    check("every cited record is included in full",
          all(clean(got.get(rid, "")) == full[rid] for rid in cited if rid in full),
          [rid for rid in cited if rid in full and clean(got.get(rid, "")) != full[rid]])
    tools = [p + line for p in ("TOOL:rule_lookup:", "TOOL:origin:", "TOOL:duty:")]
    check("the chosen line's tool results are included in full",
          all(clean(got[t]) == full[t] for t in tools if t in full) and any(t in got for t in tools))
    others = [rid for rid in full if rid.startswith(("TOOL:rule_lookup:", "TOOL:origin:", "TOOL:duty:"))
              and not rid.endswith(line) and rid not in cited]
    check("other lines' tool results are left out", not [r for r in others if r in got], others)
    for c in pack.candidates:
        if c["id"] not in got:
            check(f"candidate {c['id']} listed", False)
            continue
        if digits(c.get("tariff_line")) != line and c["id"] not in cited:
            brief = got[c["id"]]
            check(f"candidate {c['id']} (not chosen): brief with its description, no notes",
                  "description:" in brief and "notes" not in brief, brief)
    headers = [m for m in text.splitlines() if m.startswith("[")]
    check("no record appears twice", len(headers) == len(set(headers)))
    index = [ln for ln in text.split("=== NOT CITED (titles only) ===")[1].splitlines() if ln.startswith("- [")]
    index_ids = [ln[3:ln.index("]")] for ln in index]
    uncited = [rid for rid in pack.allowed_ids if rid.startswith(("P-", "PSR-")) and rid not in cited]
    check("every uncited rule and passage is in the index, once, with a title",
          index_ids == uncited and all(len(ln) > len(f"- [{i}] ") + 3 for ln, i in zip(index, index_ids)),
          (index_ids, uncited))
    check("smaller than the full evidence", len(text) < len(pack.text), (len(text), len(pack.text)))
    if folder:
        rows = list(csv.DictReader((Path(folder) / "bom.csv").open(encoding="utf-8")))
        names = [r["supplier"].split(" (")[0] for r in rows]
        values = {v for r in rows for v in number_keys(r["value"])}
        check("no supplier name", not [n for n in names if n in text])
        check("no individual input value", not (values & number_keys(text)), values & number_keys(text))

    view = research_for_qa(research)
    check("QA view: no code-filled verdict or step authority",
          "verdict" not in view and all("authority" not in s for s in view["procedure"]))
    check("QA view: code-verified fields hidden (origin status, rule, saving)",
          "status" not in view["origin_result"] and "origin_rule" not in view
          and "estimated_saving" not in view)
    check("QA view: classification reasoning only", view["reasoning"] == research["reasoning"][:1])
    check("QA view: findings unchanged",
          all(view[k] == research[k] for k in ("classification", "caveats", "gaps"))
          and view["origin_result"]["basis"] == research["origin_result"]["basis"])
    check("QA view: the Researcher JSON itself is not changed",
          research == load(case))
    sizes.append((case, len(pack.text), len(text), len(json.dumps(view, ensure_ascii=False))))

print("\n== classification is a gap")
intake, folder, _ = DEV_INTAKES["windows"]
pack = build_evidence(intake, folder)
gap = copy.deepcopy(load("windows"))
gap["classification"] = {"tariff_line": GAP, "description": GAP, "confidence": "low",
                         "source_id": "TOOL:tariff_lookup"}
text = qa_evidence(pack, gap)
check("no tool results, says so", "none (no tariff line chosen)" in text)
check("all candidates still listed",
      all(c["id"] in split_records(text) for c in pack.candidates))

print("\n== sizes (characters; ~3.6 per token)")
for case, full_len, qa_len, view_len in sizes:
    print(f"  {case:15} evidence {full_len:6} -> {qa_len:6}   Researcher JSON for QA {view_len:5}")

print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")
sys.exit(1 if failures else 0)
