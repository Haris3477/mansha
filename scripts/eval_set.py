"""Evaluation set runner (G15). Sub-step 1: the tools-only dry run.

    python -m scripts.eval_set --dry-run                  # core, stop, new (reserves skipped)
    python -m scripts.eval_set --dry-run --group reserve  # or --case N4 --case N7, -v for all facts

The dry run calls no LLM. For each case it runs the plain-Python tools (the same
build_evidence the pipeline uses) on the case's expected Intake JSON and bill of
materials, and compares what they return with the case's answer key
(scripts/eval_cases.py). A mismatch means the key or the tools changed: the live run
(sub-step 2) refuses to start until the dry run is clean. It also checks that no
supplier name from a bill of materials reaches the evidence text (privacy).
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from mansha.evidence import build_evidence, is_excluded
from mansha.kb import corridor_for
from scripts.eval_cases import BY_ID, CASES, GROUPS, EvalCase

DEFAULT_GROUPS = ("core", "stop", "new")


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def derive(case: EvalCase) -> dict:
    """The facts the tools produce for this case's expected intake (no LLM)."""
    facts: dict = {}
    if case.intake is None:
        return facts
    corridor = corridor_for(case.intake.get("destination_country"))
    facts["corridor"] = corridor
    if corridor is None:
        return facts
    if case.folder and not Path(case.folder).is_dir():
        raise FileNotFoundError(f"{case.id}: bill-of-materials folder {case.folder} is missing")
    pack = build_evidence(case.intake, case.folder, corridor)
    tl = pack.tool_results["TOOL:tariff_lookup"]
    facts["candidates"] = [c["id"] for c in pack.candidates]
    facts["tariff_notes"] = tl.get("notes") or []
    facts["evidence_text"] = pack.text

    line = case.key.get("line")
    cand = next((c for c in pack.candidates if c.get("tariff_line") == line), None) if line else None
    facts["line_found"] = cand is not None
    if cand:
        mfn, cepa = cand.get("mfn") or {}, cand.get("cepa") or {}
        facts.update(excluded=is_excluded(cand), hs2017=cand.get("hs2017_code"),
                     mfn_tariff=mfn.get("tariff_rate_pct"), mfn_effective=mfn.get("effective_rate_pct"),
                     cepa=cepa.get("rate_pct"))
    elif pack.candidates and case.key.get("excluded") is not None:
        facts["excluded"] = all(is_excluded(c) for c in pack.candidates)

    o = pack.tool_results.get(f"TOOL:origin:{line}") if line else None
    facts["no_origin"] = o is None
    if o:
        checks: dict[str, str] = {}
        for ch in o.get("checks", []):
            checks.setdefault(ch["check"], ch["result"])
            if ch["check"] == "VA" and "va_build_down" not in facts:
                v = ch.get("values") or {}
                facts["va_build_down"], facts["va_threshold"] = v.get("build_down_pct"), v.get("threshold_pct")
        facts.update(origin=o.get("status"), checks=checks, origin_missing=o.get("missing") or [],
                     origin_notes=o.get("notes") or [])
    d = pack.tool_results.get(f"TOOL:duty:{line}") if line else None
    if d:
        facts.update(duty_status=d.get("status"), saving=_f(d.get("saving")), currency=d.get("currency"))
    fee = pack.tool_results.get("TOOL:coo_fee") or {}
    facts.update(fee_status=fee.get("status"), fee_aed=fee.get("fee_aed"))
    return facts


def compare(case: EvalCase, facts: dict) -> list[str]:
    """Every way the tools' facts differ from the case's answer key."""
    out: list[str] = []
    for k, want in case.key.items():
        if k in ("line",):
            if not facts.get("line_found"):
                out.append(f"line {want} not among the candidates {facts.get('candidates')}")
        elif k == "checks":
            got = facts.get("checks") or {}
            out += [f"check {n}: expected {r}, got {got.get(n)}" for n, r in want.items() if got.get(n) != r]
        elif k in ("tariff_notes_contain", "origin_notes_contain", "origin_missing_contains"):
            src = {"tariff_notes_contain": "tariff_notes", "origin_notes_contain": "origin_notes",
                   "origin_missing_contains": "origin_missing"}[k]
            text = " | ".join(facts.get(src) or [])
            out += [f"{src} lacks {s!r}" for s in want if s not in text]
        elif k in ("va_build_down", "va_threshold", "mfn_tariff", "mfn_effective", "cepa", "saving"):
            if _f(facts.get(k)) != _f(want):
                out.append(f"{k}: expected {want}, got {facts.get(k)}")
        elif facts.get(k) != want:
            out.append(f"{k}: expected {want!r}, got {facts.get(k)!r}")
    return out


def privacy_problems(case: EvalCase, facts: dict) -> list[str]:
    """Supplier names from the bill of materials must never reach the evidence text."""
    if not case.folder or "evidence_text" not in facts:
        return []
    bom = Path(case.folder) / "bom.csv"
    if not bom.exists():
        return []
    with bom.open(encoding="utf-8-sig", newline="") as f:
        suppliers = [r.get("supplier") for r in csv.DictReader(f) if r.get("supplier")]
    return [f"supplier {s!r} appears in the evidence" for s in suppliers if s in facts["evidence_text"]]


def select(groups, ids) -> list[EvalCase]:
    if ids:
        return [BY_ID[i] for i in ids]
    return [c for c in CASES if c.group in groups]


def dry_run(cases: list[EvalCase], verbose: bool = False) -> int:
    bad = 0
    print(f"Dry run (tools only, no LLM): {len(cases)} case(s)\n")
    for c in cases:
        facts = derive(c)
        problems = compare(c, facts) + privacy_problems(c, facts)
        mark = "OK" if not problems else "MISMATCH"
        bad += bool(problems)
        note = " (expected failure live: " + c.expected_fail.split(":")[0] + ")" if c.expected_fail else ""
        print(f"{c.id:4} {c.name:22} {mark}{note}")
        for p in problems:
            print(f"       - {p}")
        if verbose:
            shown = {k: v for k, v in facts.items() if k not in ("evidence_text", "origin_notes", "tariff_notes")}
            print(f"       facts: {shown}")
    print(f"\n{len(cases) - bad}/{len(cases)} match the answer key" + ("" if not bad else ": FIX BEFORE ANY LIVE RUN"))
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="tools only, no LLM calls")
    ap.add_argument("--group", action="append", choices=GROUPS, help="case group(s); default core, stop, new")
    ap.add_argument("--case", action="append", choices=sorted(BY_ID), help="run these case IDs only")
    ap.add_argument("-v", "--verbose", action="store_true", help="print every derived fact")
    a = ap.parse_args(argv)
    cases = select(a.group or DEFAULT_GROUPS, a.case)
    if not a.dry_run:
        ap.error("only --dry-run exists so far (the live run is sub-step 2)")
    return dry_run(cases, a.verbose)


if __name__ == "__main__":
    sys.exit(main())
