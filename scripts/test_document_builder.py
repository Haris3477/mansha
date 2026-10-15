"""Offline tests for the Document Builder (no LLM, no router).

Uses the 4 saved Researcher outputs in samples/researcher_outputs/ and a fake LLM.
Run: python -m scripts.test_document_builder
Also saves the code-only (fallback) report of each case to runs/<case>/report_fallback.md.
"""

import copy
import json
import sys
from pathlib import Path

from mansha.document_builder import (
    EVIDENCE_ID_RE,
    build_facts,
    build_messages,
    check_prose,
    fallback_prose,
    render_report,
    run_document_builder,
)
from mansha.evidence import build_evidence
from mansha.kb import load_corridor
from mansha.llm_client import LLMCallError, LLMResult
from scripts.run_researcher import CASES

FIXTURES = Path("samples/researcher_outputs")
failures: list[str] = []


def check(name: str, cond: bool, detail="") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def load(name: str):
    research = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))["output"]
    intake, folder, _ = CASES[name]
    pack = build_evidence(intake, folder)   # pure code: same evidence as the saved run
    return research, intake, pack


def good_windows_prose(notes: list[dict]) -> dict:
    mandatory = [n["nid"] for n in notes if n["mandatory"]]
    return {
        "summary": "Your aluminium window frames meet the rule of origin, so you can claim the CEPA "
                   "rate in India. The estimated saving is AED 10,000. Follow the checklist below.",
        "classification": "The product falls under tariff line 76101000 (aluminium doors, windows and "
                          "their frames), with high confidence. Confirm the code with Indian customs "
                          "or a customs broker before shipping.",
        "duty": "Under the India-UAE CEPA, the normal (MFN) rate is 10% and the CEPA rate is 0%. "
                "The estimated saving on this shipment is 10000.00 AED.",
        "origin": "The rule is CTSH + VA 45%: every imported input must change tariff subheading, "
                  "and value addition must be at least 45%. Your product passed both: value addition "
                  "is 49.0% against the 45% threshold.",
        "notes": [{"text": "The certificate issuer, the duty basis and your own declaration all "
                           "affect this result.", "from": mandatory}],
    }


def fake_llm(*replies):
    """A stand-in for call_llm that returns the given dicts (or raises an exception) in order."""
    queue = list(replies)
    seen: list[list[dict]] = []

    def llm(agent, chain, messages, **kwargs):
        seen.append(messages)
        r = queue.pop(0)
        if isinstance(r, Exception):
            raise r
        return LLMResult(text=json.dumps(r), data=copy.deepcopy(r), routed_via="fake/model",
                         finish_reason="stop", latency_s=0.0)
    llm.seen = seen
    return llm


print("\n1. FACTS and NOTES")
cases = {name: load(name) for name in ("windows", "chargers", "windows_nodata", "plastic")}
for name, (research, intake, _) in cases.items():
    facts, notes = build_facts(research, intake)
    found = EVIDENCE_ID_RE.search(facts)
    check(f"{name}: no evidence IDs in FACTS", not found, found and found.group(0))
    check(f"{name}: FACTS gives the verdict", f"VERDICT: {research['verdict']}" in facts)
    check(f"{name}: no gap marker in FACTS", "REGULATORY_GAP_DETECTED" not in facts)

research, intake, _ = cases["windows"]
facts, notes = build_facts(research, intake)
mand = {n["source_id"] for n in notes if n["mandatory"]}
check("windows: mandatory notes are issuer, duty basis and self-declaration",
      mand == {"P-UAE-ISSUER", "TOOL:duty:76101000", "TOOL:origin:76101000"}, mand)
check("windows: rule-interpretation note is optional",
      not any(n["mandatory"] for n in notes if n["source_id"].startswith("TOOL:rule_lookup")))
check("windows: saving in FACTS", "ESTIMATED SAVING: 10000.00 AED" in facts)
check("windows: CTSH and VA terms sent", "CTSH = " in facts and "VA = " in facts)
_, nd_notes = build_facts(*cases["windows_nodata"][:2])
n_cav = len(cases["windows_nodata"][0]["caveats"])
check(f"windows_nodata: all {n_cav} caveats numbered as notes",
      [n["nid"] for n in nd_notes] == [f"N{i}" for i in range(1, n_cav + 1)])
check("windows_nodata: 2 mandatory notes", sum(n["mandatory"] for n in nd_notes) == 2)
nd_facts, _ = build_facts(*cases["windows_nodata"][:2])
check("windows_nodata: saving needs the value", "cannot be estimated without the shipment value" in nd_facts)
pl_facts, _ = build_facts(*cases["plastic"][:2])
check("plastic: CEPA rate shown as excluded", "CEPA RATE: excluded" in pl_facts)

print("\n2. Prose checks")
good = good_windows_prose(notes)
check("good prose passes", check_prose(good, facts, notes) == [], check_prose(good, facts, notes))


def expect_problem(label, mutate):
    p = copy.deepcopy(good)
    mutate(p)
    probs = check_prose(p, facts, notes)
    check(label, bool(probs))


expect_problem("invented number fails", lambda p: p.update(duty=p["duty"] + " That is AED 40,000."))
expect_problem("computed difference fails", lambda p: p.update(duty="The rate falls by 10 points, 9% lower."))
expect_problem("leaked evidence ID fails", lambda p: p.update(classification="See TL-IN-76101000."))
expect_problem("leaked note number fails", lambda p: p.update(summary=p["summary"] + " See N2."))
expect_problem("code word fails", lambda p: p.update(origin="The product QUALIFIES."))
expect_problem("empty field fails", lambda p: p.update(summary=" "))
expect_problem("missing mandatory note fails", lambda p: p["notes"][0].update(**{"from": ["N1"]}))
expect_problem("unknown note number fails", lambda p: p["notes"][0]["from"].append("N99"))
expect_problem("more than 6 notes fails",
               lambda p: p.update(notes=p["notes"] + [{"text": "x", "from": ["N1"]}] * 6))
expect_problem("note number not in its own notes fails",
               lambda p: p["notes"].append({"text": "Keep records for 7 years.", "from": ["N1"]}))
p = copy.deepcopy(good)
p["summary"] = p["summary"].replace("AED 10,000", "AED 10000")
check("thousands separators are the same number", check_prose(p, facts, notes) == [])

print("\n3. Code-only report for each verdict")
kb_sources = load_corridor("india")["sources"]
for name, (research, intake, pack) in cases.items():
    _, n = build_facts(research, intake)
    md = render_report(research, intake, fallback_prose(research, n), n, pack.id_sources, kb_sources)
    out = Path("runs") / name
    out.mkdir(parents=True, exist_ok=True)
    (out / "report_fallback.md").write_text(md, encoding="utf-8")
    has_list = "## Step-by-step checklist" in md
    check(f"{name}: checklist only when a claim is possible",
          has_list == (research["verdict"] in ("ELIGIBLE", "NEEDS_MORE_DATA")))
    check(f"{name}: one checkbox per procedure step", md.count("- [ ] ") == (
        len(research["procedure"]) if has_list else 0))
    check(f"{name}: sources are numbered https links",
          "## Sources\n\n1. [" in md and "](https://" in md)
    check(f"{name}: disclaimer present", "not an official origin ruling" in md)
    leaks = [w for w in ("REGULATORY_GAP_DETECTED", "NOT_APPLICABLE", "TOOL:", "PSR-IN", "TL-IN") if w in md]
    check(f"{name}: no IDs or code words", not leaks, leaks)
md_nd = (Path("runs") / "windows_nodata" / "report_fallback.md").read_text(encoding="utf-8")
check("windows_nodata: 'What's still needed' comes right after the summary",
      md_nd.index("## What's still needed") < md_nd.index("## Product classification"))
ar_intake = dict(cases["windows"][1], language="ar")
md_ar = render_report(research, ar_intake, good, notes, cases["windows"][2].id_sources, kb_sources)
check("Arabic headings and disclaimer", "## الملخص" in md_ar and "ليس قرارًا رسميًا" in md_ar)

print("\n4. The call loop (fake LLM)")
research, intake, pack = cases["windows"]
bad = dict(good, duty="The saving is AED 40,000.")

llm = fake_llm(good)
r = run_document_builder(research, intake, pack.id_sources, llm=llm)
check("good first reply: 1 call, no fallback", len(llm.seen) == 1 and not r.used_fallback)
check("report contains the LLM summary", good["summary"] in r.markdown)

llm = fake_llm(bad, good)
r = run_document_builder(research, intake, pack.id_sources, llm=llm)
check("bad then good: 2 calls, no fallback", len(llm.seen) == 2 and not r.used_fallback)
check("round 2 sends the corrections", "CORRECTIONS" in llm.seen[1][-1]["content"]
      and "40000" in llm.seen[1][-1]["content"])

llm = fake_llm(bad, bad)
r = run_document_builder(research, intake, pack.id_sources, llm=llm)
check("bad twice: code-only report", r.used_fallback and r.problems and "40,000" not in r.markdown)

llm = fake_llm(LLMCallError("router down", []))
r = run_document_builder(research, intake, pack.id_sources, llm=llm)
check("LLM error: code-only report", r.used_fallback and "## Summary" in r.markdown)

msgs = build_messages(facts, "en")
check("system prompt has the Agent 4 section and language",
      "AGENT 4" in msgs[0]["content"] and "Write in English" in msgs[0]["content"])
check("no unfilled {language} left", "{language}" not in msgs[0]["content"])

print("\n" + ("ALL PASSED" if not failures else f"{len(failures)} FAILED: {failures}"))
sys.exit(1 if failures else 0)
