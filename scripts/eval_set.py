"""Evaluation set runner (G15): the fixed exam Mansha retakes after every change.

    python -m scripts.eval_set --dry-run                  # tools only, no LLM (core, stop, new)
    python -m scripts.eval_set                            # live: dry run, budget guard, then every case
    python -m scripts.eval_set --case N4 --case N7        # some cases; --group reserve for the reserves
    python -m scripts.eval_set --only-repeat --repeat 3   # the repeat group (E6), three times each
    python -m scripts.eval_set --grade runs/eval_set/<time>   # grade saved runs again (no LLM)

The dry run runs the plain-Python tools on each case's expected Intake JSON and compares them
with the answer key (scripts/eval_cases.py); a live run refuses to start unless it is clean.
Then a pre-flight check (llm_client.router_answering, no quota): a router that doesn't answer
stops the run with exit 2 before anything is sent; --force does not skip it.
The budget guard (E1) reads the router's own sliding-24 h request counts (rate_limit_usage,
read-only; for OpenRouter :free models also every attempt since 00:00 UTC, request_attempts) and stops if the worst case doesn't fit, unless --force (D3 = A). Each case then
runs through the real pipeline in this one process (so the judge pacing covers the gaps
between cases) and is graded in code (scripts/eval_grade.py). Results go to
runs/eval_set/<time>/: one folder per run, summary.md / summary.json, and reading.md (the
reading checks Haris and Claude fill in: must say / must not say, problem 56, G35).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import sys
import time
from pathlib import Path

from mansha.llm_client import router_answering
from scripts.eval_cases import BY_ID, CASES, GROUPS, EvalCase
from scripts.eval_grade import Grade, compare, derive, grade, load_run, supplier_leaks
from scripts.router_db import CHAINS, ROUTER_DB, chain_capacity, utc_text  # noqa: F401 (utc_text: tests)

RUNS_ROOT = Path("runs/eval_set")
DEFAULT_GROUPS = ("core", "stop", "new")
ROUTER_CHECK = router_answering   # replaceable in tests


def privacy_problems(case: EvalCase, facts: dict) -> list[str]:
    return supplier_leaks(case, facts["evidence_text"]) if "evidence_text" in facts else []


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


# ---------- budget guard (E1, D3 = A) ----------

# Worst case per run, in requests: both Researcher and Builder rounds plus one retry each (long),
# Intake plus a retry (qa), and up to 3 QA parts x (2 rounds + format retry/re-judge) + prose QA (judge).
# B (28 Oct): an Arabic report's Builder rounds (2 + one retry) ask auto:arabic; long keeps its full worst
# case, because a failed Arabic call falls back once to auto:long.
WORST = {"REPORT": {"long": 5, "qa": 2, "judge": 14}, "STOP": {"long": 0, "qa": 2, "judge": 0},
         "REPORT_AR": {"long": 5, "qa": 2, "judge": 14, "arabic": 3}}
TYPICAL = {"REPORT": {"long": 3, "qa": 1, "judge": 4}, "STOP": {"long": 0, "qa": 1, "judge": 0},
           "REPORT_AR": {"long": 1, "qa": 1, "judge": 4, "arabic": 2}}
# Chains that share models: long + qa (Step 9), long + arabic (Gemini 3.5; Google's daily quota is project-wide).
SHARED = (("long", "qa"), ("long", "arabic"))
WARN_MIN_ATTEMPTS = 2


def need(cases: list[EvalCase], repeat: int, table: dict) -> dict[str, int]:
    tot = {c: 0 for c in CHAINS}
    for case in cases:
        kind = "STOP" if case.status != "REPORT" else (
            "REPORT_AR" if (case.intake or {}).get("language") == "ar" else "REPORT")
        for ch, n in table[kind].items():
            tot[ch] += n * repeat
    return tot


def left(models: list[dict]) -> float:
    """Requests left now across a set of models: a benched model has 0; one with no cap is unlimited."""
    free = [m for m in models if not m.get("benched_min")]
    if any(m["rpd"] is None for m in free):
        return float("inf")
    return sum(max(m["rpd"] - m["used"], 0) for m in free)


def model_text(m: dict) -> str:
    cap = m["rpd"] if m["rpd"] is not None else "no cap"
    bench = f" BENCHED {m['benched_min']:g} min ({m['bench_source']})" if m.get("benched_min") else ""
    day = (f" (OpenRouter UTC day: {m['day_attempts']} attempts; router 24 h: {m['router_used']})"
           if m.get("day_attempts") is not None else "")
    return f"{m['model']} {m['used']}/{cap}{day}{bench}"


def upstream_warnings(cap: dict[str, list[dict]]) -> list[str]:
    """Models with upstream errors on at least half of >= WARN_MIN_ATTEMPTS attempts in the last hour.
    A warning only (Haris, 26 Oct): a provider's 503 burst often ends in minutes."""
    seen, lines = set(), []
    for ch in CHAINS:
        for m in cap[ch]:
            bad, n = m.get("upstream_errors", (0, 0))
            if m["model"] not in seen and n >= WARN_MIN_ATTEMPTS and 2 * bad >= n:
                seen.add(m["model"])
                lines.append(f"  WARNING {m['model']}: upstream error on {bad} of {n} attempts in the last "
                             "hour (not counted as capacity loss; you decide)")
    return lines


def budget_check(cases: list[EvalCase], repeat: int, cap: dict[str, list[dict]]) -> tuple[bool, list[str]]:
    """True when the worst case fits every chain and the models chains share (SHARED)."""
    worst, typical = need(cases, repeat, WORST), need(cases, repeat, TYPICAL)
    lines, ok = [], True
    for ch in CHAINS:
        cap_ch = left(cap[ch])
        fits = worst[ch] <= cap_ch
        ok &= fits
        models = ", ".join(model_text(m) for m in cap[ch]) or "no models"
        lines.append(f"  {ch:6} need {typical[ch]}-{worst[ch]}, left {cap_ch:g}  {'OK' if fits else 'SHORT'}  ({models})")
    for a, b in SHARED:
        shared = {m["model"]: m for ch in (a, b) for m in cap[ch]}
        both = worst[a] + worst[b]
        if worst[b] and both > left(list(shared.values())):
            ok = False
            lines.append(f"  {a}+{b} share models: need up to {both}, left {left(list(shared.values())):g}  SHORT")
    return ok, lines + upstream_warnings(cap)


# ---------- live run ----------

def run_name(case: EvalCase, r: int, repeat: int) -> str:
    return f"{case.id}_{case.name}" + (f"_r{r}" if repeat > 1 else "")


def grade_line(g: Grade) -> str:
    r = g.run
    long_n = (g.cost.get("auto:long") or {}).get("requests", 0)
    judge_n = (g.cost.get("auto:judge") or {}).get("requests", 0)
    arabic_n = (g.cost.get("auto:arabic") or {}).get("requests", 0)
    mark = "PASS" if g.passed else ("XFAIL" if g.case.expected_fail else "FAIL")
    slips = ",".join(sorted(g.slips)) or "-"
    return (f"{g.case.id:4} {g.case.name:22} {mark:5} {r.status or '-':13} {r.verdict or '-':24} "
            f"{r.seconds:6.1f}s long {long_n}" + (f" arabic {arabic_n}" if arabic_n else "")
            + f" judge {judge_n} slips {slips}")


def live(cases: list[EvalCase], repeat: int, root: Path) -> list[Grade]:
    from mansha.llm_client import call_llm      # only the live run needs the router
    from mansha.orchestrator import run_pipeline
    grades = []
    for r in range(1, repeat + 1):
        for case in cases:
            out = root / run_name(case, r, repeat)
            print(f"\n--- {case.id} {case.name}" + (f" (repeat {r}/{repeat})" if repeat > 1 else ""), flush=True)
            run_pipeline(case.message, case_folder=case.folder, llm=call_llm, out_dir=out)
            g = grade(case, load_run(out))
            print(grade_line(g), flush=True)
            for name, _, detail in g.failed:
                print(f"       {name}: {detail}")
            grades.append(g)
    return grades


def regrade(folders: list[Path]) -> list[Grade]:
    """Grade saved eval-set run folders again (case from the folder name: <ID>_<name>[_rN])."""
    out = []
    for f in folders:
        runs = sorted(p for p in f.iterdir() if p.is_dir()) if (f / "summary.json").exists() else [f]
        for run in runs:
            cid = run.name.split("_", 1)[0]
            if cid in BY_ID:
                out.append(grade(BY_ID[cid], load_run(run)))
    return out


# ---------- summary and reading sheet ----------

def summarize(grades: list[Grade]) -> dict:
    scored = [g for g in grades if not g.case.expected_fail]
    reports = [g for g in grades if g.run.status == "REPORT"]
    slips: dict[str, int] = {}
    for g in grades:
        for k in g.slips:
            slips[k] = slips.get(k, 0) + 1
    tok = {}
    for g in grades:
        for ch, v in g.cost.items():
            if isinstance(v, dict):
                t = tok.setdefault(ch, {"requests": 0, "prompt": 0, "completion": 0})
                for k in t:
                    t[k] += v[k]
    return {
        "runs": len(grades),
        "passed": sum(g.passed for g in scored), "scored": len(scored),
        "verdict_correct": sum(g.run.verdict == g.case.verdict for g in scored if g.case.verdict),
        "verdict_cases": sum(1 for g in scored if g.case.verdict),
        "expected_failures": [f"{g.case.id}: {'still fails' if not g.passed else 'NOW PASSES'}"
                              for g in grades if g.case.expected_fail],
        "checks_failed": sum(g.run.status == "CHECKS_FAILED" for g in grades),
        "llm_error": sum(g.run.status == "LLM_ERROR" for g in grades),
        "qa_rejections": sum(p["status"] == "REJECTED" for g in grades for p in g.run.phases
                             if p["name"].startswith("QA")),
        "qa_overruled": sum(p["status"] == "OVERRULED" for g in grades for p in g.run.phases),
        "router_refusals": sum(g.cost.get("refusals", 0) for g in grades),
        "paced_wait_s": round(sum(g.cost.get("paced_wait_s", 0) for g in grades), 1),
        "median_seconds_reports": round(statistics.median([g.run.seconds for g in reports]), 1) if reports else None,
        "slips": dict(sorted(slips.items())),
        "requests": tok,
        "failed_checks": {f"{g.case.id}{'' if len(grades) == len({x.case.id for x in grades}) else ' ' + g.run.folder.name}":
                          [f"{n}: {d}" for n, _, d in g.failed] for g in grades if g.failed},
    }


def summary_md(grades: list[Grade], s: dict, root: Path) -> str:
    lines = [f"# Evaluation set run {root.name}", "",
             f"**{s['passed']}/{s['scored']} runs pass every code check** (expected failures not counted); "
             f"verdicts correct {s['verdict_correct']}/{s['verdict_cases']}; CHECKS_FAILED {s['checks_failed']}; "
             f"LLM_ERROR {s['llm_error']}; QA rejections {s['qa_rejections']}, overruled {s['qa_overruled']}; "
             f"router refusals {s['router_refusals']}; pacing waits {s['paced_wait_s']} s; "
             f"median report time {s['median_seconds_reports']} s.", "",
             "| Case | Result | Status | Verdict | Seconds | long | arabic | judge | Slips |", "|---|---|---|---|---|---|---|---|---|"]
    for g in grades:
        mark = "PASS" if g.passed else ("XFAIL" if g.case.expected_fail else "FAIL")
        lines.append(f"| {g.run.folder.name} | {mark} | {g.run.status} | {g.run.verdict or '-'} | {g.run.seconds:.1f} | "
                     f"{(g.cost.get('auto:long') or {}).get('requests', 0)} | {(g.cost.get('auto:arabic') or {}).get('requests', 0)} | "
                     f"{(g.cost.get('auto:judge') or {}).get('requests', 0)} | "
                     f"{', '.join(f'{k} ×{len(v)}' for k, v in sorted(g.slips.items())) or '-'} |")
    if s["failed_checks"]:
        lines += ["", "## Failed code checks"]
        for k, v in s["failed_checks"].items():
            lines += [f"- **{k}**"] + [f"  - {x}" for x in v]
    if s["expected_failures"]:
        lines += ["", "## Expected failures", *[f"- {x}" for x in s["expected_failures"]]]
    lines += ["", "## Slips (global anchors: known open problems, counted, confirmed by reading)"]
    lines += [f"- problem {k}: {n} run(s)" for k, n in s["slips"].items()] or ["- none"]
    for g in grades:
        for k, v in sorted(g.slips.items()):
            lines.append(f"  - {g.run.folder.name} [{k}]: " + " | ".join(repr(x[:100]) for x in v))
    lines += ["", "## Requests and tokens", "| Chain | Requests | Prompt | Completion |", "|---|---|---|---|"]
    lines += [f"| {ch} | {v['requests']} | {v['prompt']} | {v['completion']} |" for ch, v in sorted(s["requests"].items())]
    return "\n".join(lines) + "\n"


def reading_md(grades: list[Grade], root: Path) -> str:
    lines = [f"# Reading sheet: evaluation set run {root.name}", "",
             "Fill PASS/FAIL with a short note. Code checks are in summary.md; this is what code can't judge.", ""]
    for g in grades:
        c = g.case
        lines += [f"## {g.run.folder.name}: {c.status} / {c.verdict or '-'} (got {g.run.status} / {g.run.verdict or '-'})",
                  f"Read: `{g.run.folder.name}/{'report.md' if g.run.status == 'REPORT' else 'notice.md'}`", ""]
        lines += [f"- [ ] must say: {x}" for x in c.must_say]
        lines += [f"- [ ] must not say: {x}" for x in c.must_not_say]
        if g.run.status == "REPORT":
            lines += ["- [ ] every \"What's still needed\" item is something only the user can give and could change the result (problem 56)",
                      "- [ ] no claim stated stronger or weaker than its source (G35)",
                      "- [ ] every step and note says what its cited source says, no merged facts (G8, problem 72)"]
        lines += [f"- [ ] slip {k} confirmed? {v[0][:90]!r}" for k, v in sorted(g.slips.items())]
        lines.append("")
    return "\n".join(lines)


def write_outputs(grades: list[Grade], root: Path) -> dict:
    s = summarize(grades)
    root.mkdir(parents=True, exist_ok=True)
    (root / "summary.json").write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (root / "summary.md").write_text(summary_md(grades, s, root), encoding="utf-8")
    (root / "reading.md").write_text(reading_md(grades, root), encoding="utf-8")
    return s


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="tools only, no LLM calls")
    ap.add_argument("--group", action="append", choices=GROUPS, help="case group(s); default core, stop, new")
    ap.add_argument("--case", action="append", choices=sorted(BY_ID), help="run these case IDs only")
    ap.add_argument("--only-repeat", action="store_true", help="only the repeat group (E6)")
    ap.add_argument("--repeat", type=int, default=1, help="run each selected case N times")
    ap.add_argument("--force", action="store_true", help="run even if the budget guard says it may not fit")
    ap.add_argument("--grade", nargs="+", type=Path, help="grade saved eval-set run folders again (no LLM)")
    ap.add_argument("-v", "--verbose", action="store_true", help="dry run: print every derived fact")
    a = ap.parse_args(argv)

    if a.grade:
        grades = regrade(a.grade)
        for g in grades:
            print(grade_line(g))
        s = summarize(grades)
        print(json.dumps({k: s[k] for k in ("passed", "scored", "slips")}))
        return 0 if s["passed"] == s["scored"] else 1

    cases = select(a.group or DEFAULT_GROUPS, a.case)
    if a.only_repeat:
        cases = [c for c in cases if c.repeat]
    if a.repeat < 1:
        ap.error("--repeat must be at least 1")
    rc = dry_run(cases, a.verbose)
    if a.dry_run:
        return rc
    if rc:
        print("Not started: the tools no longer match the answer key (see above).")
        return 1

    up, msg = ROUTER_CHECK()
    print(f"\nPre-flight: {msg}")
    if not up:
        print("Not started: the router is not answering (nothing was sent; --force does not skip this).")
        return 2

    print("\nBudget guard (router's sliding 24 h counts; OpenRouter :free = attempts since 00:00 UTC, "
          "04:00 Dubai):")
    try:
        ok, lines = budget_check(cases, a.repeat, chain_capacity(ROUTER_DB))
    except sqlite3.Error as exc:
        ok, lines = False, [f"  cannot read the router database {ROUTER_DB}: {exc}"]
    print("\n".join(lines))
    if not ok and not a.force:
        print("Not started: the worst case may not fit today. Run fewer cases, wait, or pass --force.")
        return 2
    root = RUNS_ROOT / time.strftime("%Y%m%d-%H%M%S")
    grades = live(cases, a.repeat, root)
    s = write_outputs(grades, root)
    print(f"\n{s['passed']}/{s['scored']} runs pass every code check; slips {s['slips'] or 'none'}")
    print(f"saved: {root}/ (summary.md, reading.md, one folder per run)")
    return 0 if s["passed"] == s["scored"] else 1


if __name__ == "__main__":
    sys.exit(main())
