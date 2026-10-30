"""Orchestrator (Step 9): one user message in, one answer out, every phase logged.

Plain Python decides the order and when to stop; the agents only do their own job.

    message -> Intake -> coverage check -> tools + evidence -> Researcher
            -> [QA slot] -> (one shared revision) -> Document Builder -> report
            -> Report check (code; flags problems in the finished report, never blocks it)

Stops, each with a short message written by code in the user's language:
    NEEDS_INPUT    product or destination missing (ask the user)
    NOT_COVERED    destination, or product, not in Mansha's knowledge base
    CHECKS_FAILED  Researcher still failing code checks / QA after its one revision
    LLM_ERROR      Intake or Researcher call failed (provider outage); the Builder
                   never causes this, it has a code-only fallback

The QA slot runs the QA Evaluator (Step 7, mansha/qa.py) by default. It returns
APPROVED or REJECTED (corrections join the single shared revision), or ERROR when
QA could not review the output (call failed, or its answer stayed invalid): the run
then goes on, and the phase log and a pipeline warning say the output was NOT
reviewed by QA (decision D5 A, Haris 17 Oct). `qa_passthrough` (SKIPPED, never
APPROVED) runs the pipeline without QA.

The Document Builder's prose is checked for meaning by the Builder prose check (Step 7.6,
mansha/prose_qa.py, D2 = B) on the same `judge` chain: one call per Builder round, never
split; its corrections join the Builder's single retry; still rejected -> the code-only
report; ERROR -> the code-checked prose is kept and the run says it was NOT reviewed.
`prose_qa=None` runs without it.

The report check (Step 9.6b, mansha/report_check.py) is FLAG ONLY (Haris, 17 Oct): its
problems and warnings go to the phase log and the pipeline warnings; the report is shown.

Data protection: only code reads the bill of materials (in build_evidence's
origin calculator). Nothing from it except totals and percentages reaches a prompt
or a saved file; scripts/test_pipeline.py checks this.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from mansha.document_builder import (
    CHECKLIST_VERDICTS,
    BuilderResult,
    run_document_builder,
)
from mansha.evidence import EvidencePack, build_evidence
from mansha.intake import IntakeResult, detect_language, run_intake
from mansha.kb import CORRIDOR_NAMES_AR, CORRIDORS, corridor_for
from mansha.llm_client import LLMCallError, LLMResult, call_llm
from mansha.prose_qa import ProseQAOutcome, review_prose
from mansha.qa import (
    QA_ACCEPTS,
    QA_APPROVED,
    QA_ERROR,
    QA_NOT_REVIEWED,
    QA_OVERRULED,
    QA_REJECTED,
    QA_SETTLED,
    QA_SKIPPED,
    QAOutcome,
    overruled_text,
    run_qa,
    settle_round_2,
    settled_text,
)
from mansha.report_check import check_report
from mansha.researcher import ResearcherResult, run_researcher
from mansha.tools.origin_calculator import TOOL_PREFIX as ORIGIN_TOOL_PREFIX

log = logging.getLogger("mansha.orchestrator")

# Official list of the UAE's CEPAs (Ministry of Foreign Trade), checked 16 Oct 2026.
MOFT_CEPA_URL = "https://www.trade.gov.ae/comprehensive-economic-partnership-agreements"

# Run statuses
REPORT = "REPORT"
NEEDS_INPUT = "NEEDS_INPUT"
NOT_COVERED = "NOT_COVERED"
CHECKS_FAILED = "CHECKS_FAILED"
LLM_ERROR = "LLM_ERROR"

# QA statuses and QAOutcome live in mansha/qa.py (imported above):
# APPROVED / REJECTED from the QA Evaluator; SKIPPED = the pass-through; ERROR = not reviewed.


# ---------- results ----------

@dataclass
class Phase:
    name: str                                # e.g. "Researcher (round 1)"
    status: str                              # OK | STOP | FAILED | SKIPPED | FALLBACK | FLAGGED | REJECTED
    seconds: float
    summary: str                             # one line a judge can read
    calls: list[dict] = field(default_factory=list)    # LLM calls, every attempt included
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    status: str                              # REPORT | NEEDS_INPUT | NOT_COVERED | CHECKS_FAILED | LLM_ERROR
    output: str                              # Markdown shown to the user (report or short message)
    language: str                            # "en" | "ar"
    phases: list[Phase]
    warnings: list[str] = field(default_factory=list)  # pipeline-level (e.g. same model for Researcher and QA)
    verdict: str | None = None
    intake: dict | None = None
    research: dict | None = None
    out_dir: Path | None = None
    seconds: float = 0.0
    message: str = ""

    def log_dict(self) -> dict:
        """Everything for phase_log.json (no report text: that is in report.md)."""
        return {
            "status": self.status, "verdict": self.verdict, "language": self.language,
            "seconds": self.seconds, "warnings": self.warnings,
            "phases": [asdict(p) for p in self.phases],
        }


# ---------- the QA slot ----------

def qa_passthrough(intake: dict, pack: EvidencePack, research: ResearcherResult,
                   *, llm=call_llm) -> QAOutcome:
    """No QA (tests, or a run without QA). Approves nothing: the output is simply not reviewed."""
    return QAOutcome(status=QA_SKIPPED, note="QA not run: output NOT reviewed by QA")


# ---------- user-facing messages (code-written, en/ar) ----------

ASK = {
    "en": {"product_description": "What product do you want to export, and what is its main material?",
           "destination_country": "Which country are you exporting it to?"},
    "ar": {"product_description": "ما المنتج الذي تريد تصديره، وما المادة الرئيسية المصنوع منها؟",
           "destination_country": "إلى أي دولة تريد تصديره؟"},
}
ASK_INTRO = {
    "en": "To check whether your product qualifies for a lower duty under a UAE trade agreement, "
          "Mansha needs a little more information:",
    "ar": "للتحقق مما إذا كان منتجك مؤهلًا لرسوم جمركية مخفّضة بموجب اتفاقية تجارية للإمارات، "
          "يحتاج منشأ إلى بعض المعلومات الإضافية:",
}
ASK_END = {
    "en": "If you make or process the product in the UAE, a bill of materials (each input's origin, "
          "HS code and value) lets Mansha check the rule of origin as well.",
    "ar": "إذا كنت تصنع المنتج أو تعالجه في الإمارات، فإن قائمة المواد (منشأ كل مدخل ورمزه الجمركي "
          "وقيمته) تمكّن منشأ من التحقق من قاعدة المنشأ أيضًا.",
}


def _covered_list(lang: str = "en") -> str:
    if lang == "ar":
        return "، ".join(CORRIDOR_NAMES_AR.get(c, c) for c in CORRIDORS)
    return ", ".join(CORRIDORS)


def _country_ar(country: str) -> str:
    """A destination's name for an Arabic message: its Arabic name when Mansha covers it, otherwise
    "this country" with the Intake's English name in brackets (no Arabic name table for every country)."""
    return CORRIDOR_NAMES_AR.get(country) or f"هذه الدولة ({country})"


def msg_needs_input(missing: list[str], lang: str) -> str:
    lines = [ASK_INTRO[lang], ""] + [f"- {ASK[lang][f]}" for f in missing] + ["", ASK_END[lang]]
    return "\n".join(lines) + "\n"


def msg_destination_not_covered(country: str, lang: str) -> str:
    if lang == "ar":
        return (f"يغطي منشأ حاليًا التصدير من الإمارات إلى: {_covered_list('ar')} فقط. "
                f"لا تتوفر لديه بيانات عن {_country_ar(country)}، لذلك لا يستطيع التحقق من المنشأ أو الرسوم لهذا السوق.\n\n"
                "هذا لا يعني أنه لا توجد اتفاقية تجارية بين الإمارات وهذه الدولة. "
                f"راجع قائمة اتفاقيات الشراكة الاقتصادية الشاملة لدى وزارة التجارة الخارجية: {MOFT_CEPA_URL}\n")
    return (f"Mansha currently covers exports from the UAE to {_covered_list()} only. "
            f"It has no data for {country}, so it can't check origin or duty for that market.\n\n"
            f"This does not mean the UAE has no trade agreement with {country}. "
            f"See the Ministry of Foreign Trade's list of CEPAs: {MOFT_CEPA_URL}\n")


def msg_product_not_covered(product: str, hs_code: str | None, country: str, lang: str) -> str:
    if lang == "ar":
        # The Intake writes the product in English (for the KB search): name it as "this product" with the
        # English phrase in brackets, like an uncovered country (_country_ar).
        what = f"هذا المنتج ({product}" + (f"، الرمز الجمركي {hs_code})" if hs_code else ")")
        advice = ("تحقق من التصنيف والرسوم مع الجمارك أو مع وسيط جمركي." if hs_code else
                  "إذا كنت تعرف الرمز الجمركي (HS) للمنتج، أعد المحاولة مع ذكره. "
                  "وإلا فتحقق من التصنيف والرسوم مع الجمارك أو مع وسيط جمركي.")
        return (f"لا تتضمن بيانات منشأ للتعريفة الجمركية في {_country_ar(country)} بندًا يطابق {what} بعد، "
                f"لذلك لا يستطيع إعطاء نتيجة لهذا المنتج.\n\n{advice}\n")
    what = f"\"{product}\"" + (f" (HS code {hs_code})" if hs_code else "")
    advice = ("Check the classification and duty with customs or a customs broker." if hs_code else
              "If you know the product's HS code, try again and include it. "
              "Otherwise, check the classification and duty with customs or a customs broker.")
    return (f"Mansha's tariff data for {country} does not include a line matching {what} yet, "
            f"so it can't give a result for this product.\n\n{advice}\n")


def msg_checks_failed(lang: str) -> str:
    if lang == "ar":
        return ("لم يتمكن منشأ من التحقق من هذه النتيجة، لذلك لا يعرض تقريرًا. "
                "يرجى المحاولة مرة أخرى، أو التحقق مع وسيط جمركي.\n")
    return ("Mansha couldn't verify this result, so it is not showing a report. "
            "Please try again, or check with a customs broker.\n")


def msg_llm_error(lang: str) -> str:
    if lang == "ar":
        return ("خدمة الذكاء الاصطناعي في منشأ مشغولة حاليًا، لذلك لم يكتمل التحقق. "
                "يرجى المحاولة مرة أخرى بعد بضع دقائق.\n")
    return ("Mansha's AI service is busy right now, so it couldn't finish the check. "
            "Please try again in a few minutes.\n")


# ---------- phase-log helpers ----------

def call_record(res: LLMResult) -> dict:
    return {"ok": True, "served_by": res.routed_via, "latency_s": res.latency_s,
            "attempts": res.attempts}


def failed_call_record(exc: LLMCallError) -> dict:
    return {"ok": False, "served_by": None, "error": str(exc), "attempts": exc.attempts}


def served_by(calls: list[dict]) -> str | None:
    """The model of the last successful call in a phase."""
    ok = [c for c in calls if c.get("ok")]
    return ok[-1]["served_by"] if ok else None


def same_model_warning(researcher_model: str | None, qa_model: str | None) -> str | None:
    """QA should not grade its own model's work (agent_prompts.md, ORCHESTRATION 7)."""
    if researcher_model and qa_model and researcher_model == qa_model:
        return (f"Researcher and QA were served by the same model ({researcher_model}): "
                "QA is not an independent check in this run")
    return None


def builder_vs_prose_qa_warning(builder_model: str | None, qa_model: str | None) -> str | None:
    """The prose check should not grade its own model's text (Step 7.6)."""
    if builder_model and qa_model and builder_model == qa_model:
        return (f"Document Builder and prose QA were served by the same model ({builder_model}): "
                "the prose check is not an independent check in this run")
    return None


def prose_qa_record(q: ProseQAOutcome) -> dict:
    """prose_qa_N.json: everything the judge said, and every call."""
    calls = [call_record(c) for c in q.llm_calls]
    if q.failed_attempts:
        calls.append({"ok": False, "served_by": None, "error": "LLM call failed",
                      "attempts": q.failed_attempts})
    return {"status": q.status, "scores": q.scores, "corrections": q.corrections, "note": q.note,
            "answer_problems": q.output_problems, "served_by": q.llm.routed_via if q.llm else None,
            "calls": calls}


def research_record(res: ResearcherResult) -> dict:
    return {"served_by": res.llm.routed_via if res.llm else None,
            "latency_s": res.llm.latency_s if res.llm else None,
            "attempts": res.llm.attempts if res.llm else [],
            "problems": res.problems, "warnings": res.warnings, "normalized_by_code": res.changes,
            "output": res.data}


class _Timer:
    def __init__(self) -> None:
        self.start = time.monotonic()

    def __call__(self) -> float:
        return round(time.monotonic() - self.start, 2)


def _write(out_dir: Path | None, name: str, content: Any) -> None:
    if out_dir is None:
        return
    path = out_dir / name
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_text(json.dumps(content, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


# ---------- the readable phase log (phase_log.md) ----------

def attempt_text(a: dict) -> str:
    """One attempt: '#2 gemini-3.6-flash 21.3 s OK' or '#1 router 0.0 s FAILED: HTTP 429 ...'."""
    who = a.get("routed_via") or "router"
    s = f"#{a.get('attempt')} "
    if a.get("paced_wait_s"):   # Step 7.6k
        s += f"(waited {a['paced_wait_s']} s for the per-minute limit) "
    s += f"{who} {a.get('latency_s', 0)} s "
    s += "OK" if a.get("ok") else f"FAILED: {a.get('problem', 'unknown')}"
    if a.get("cooldown"):
        s += " (router cooldown, no model tried)"
    if a.get("waited_before_retry_s"):
        s += f" -> waited {a['waited_before_retry_s']} s"
    if a.get("retry_skipped"):
        s += f" -> gave up: {a['retry_skipped']}"
    return s


def call_text(c: dict) -> str:
    attempts = c.get("attempts") or []
    head = (f"served by {c.get('served_by')} ({c.get('latency_s')} s)" if c.get("ok")
            else "call FAILED")
    if len(attempts) <= 1 and c.get("ok") and not any(a.get("paced_wait_s") for a in attempts):
        return head
    trail = " | ".join(attempt_text(a) for a in attempts) or "no attempts recorded"
    return f"{head}; attempts: {trail}"


def _cell(s: str) -> str:
    """Text safe inside a Markdown table cell (a '|' would start a new column)."""
    return str(s).replace(" | ", "; ").replace("|", "/").replace("\n", " ")


def render_phase_log(result: PipelineResult) -> str:
    """Markdown a judge can read: what each phase got, did, and which model served it."""
    title = result.status + (f" ({result.verdict})" if result.verdict else "")
    msg = result.message.strip().replace("\n", " ")
    lines = [
        f"# Mansha run: {title}",
        "",
        f"- **Message:** {msg[:300]}{'…' if len(msg) > 300 else ''}",
        f"- **Total time:** {result.seconds} s | **language:** {result.language}",
        "",
        "| # | Phase | Status | Time (s) | Model | Result |",
        "|---|---|---|---|---|---|",
    ]
    for i, p in enumerate(result.phases, 1):
        lines.append(f"| {i} | {p.name} | {p.status} | {p.seconds} | {_cell(served_by(p.calls) or '-')} "
                     f"| {_cell(p.summary)} |")
    if result.warnings:
        lines += ["", "## Warnings", ""] + [f"- {w}" for w in result.warnings]
    lines += ["", "## Phase details"]
    for i, p in enumerate(result.phases, 1):
        lines += ["", f"### {i}. {p.name}: {p.status}", "", p.summary]
        sent = p.details.get("corrections_sent")
        if sent:
            lines += ["", "Corrections sent (one shared revision):"] + [f"- {c}" for c in sent]
        by_round = p.details.get("code_problems_by_round")
        if by_round:
            lines += ["", "Code check problems by round:"] + [
                f"- round {r}: {x}" for r, xs in by_round.items() for x in xs]
        if p.calls:
            lines += ["", "LLM calls:"] + [f"- {call_text(c)}" for c in p.calls]
        if p.problems:
            lines += ["", "Problems:"] + [f"- {x}" for x in p.problems]
        if p.warnings:
            label = "Code warnings (for QA):" if p.name.startswith("Researcher") else "Warnings:"
            lines += ["", label] + [f"- {x}" for x in p.warnings]
        qa_parts = p.details.get("qa_parts")
        if qa_parts:
            lines += ["", "Review split into parts (size limit):"] + [
                f"- {x['label']}: {x['status']}"
                + (f", served by {x['served_by']} ({x['seconds']} s)" if x.get("served_by") else "")
                + (f"; code warnings {', '.join(x['warnings'])}" if x.get("warnings") else "")
                for x in qa_parts]
        judged = p.details.get("warning_judgements")
        if judged:
            lines += ["", "Code warnings judged by QA:"] + [
                f"- {j['id']} {j['judgement']}: {j['warning']} -> {j['reason']}" for j in judged]
        over = p.details.get("overruled_by_kb")
        if over:
            lines += ["", "QA corrections overruled by the KB (not sent to the Researcher):"] + [
                f"- {x}" for x in over]
        settled = p.details.get("settled_by_round_1")
        if settled:
            lines += ["", "QA round-2 corrections not counted (round 1 passed these items, unchanged since):"] + [
                f"- {x}" for x in settled]
        bad = p.details.get("qa_answer_problems")
        if bad:
            lines += ["", "Problems in QA's own answer (code validation):"] + [f"- {x}" for x in bad]
        changes = p.details.get("normalized_by_code")
        if changes:
            lines += ["", "Normalized by code:"] + [f"- {x}" for x in changes]
        tools = p.details.get("tool_status")
        if tools:
            lines += ["", "Tool results: " + "; ".join(f"{k} {v}" for k, v in tools.items())]
    return "\n".join(lines) + "\n"


# ---------- the pipeline ----------

def run_pipeline(message: str, *, case_folder: str | Path | None = None, llm=call_llm,
                 qa: Callable[..., QAOutcome] = run_qa,
                 prose_qa: Callable[..., ProseQAOutcome] | None = review_prose,
                 out_dir: str | Path | None = None,
                 on_phase: Callable[[Phase], None] | None = None) -> PipelineResult:
    """Run Mansha end to end on one user message.

    case_folder: folder with bom.csv / declaration.json (read only by code), or None.
    llm: the LLM call function for every agent (tests pass a fake one).
    qa: the QA slot: run_qa (default), qa_passthrough (no QA), or a fake in tests.
    prose_qa: the Builder prose check: review_prose (default), None (code checks only), or a fake.
    out_dir: if given, every phase's input/output is saved there (it is created).
    """
    total = _Timer()
    class PhaseList(list):
        def append(self, phase):
            super().append(phase)
            if on_phase is not None:
                try:
                    on_phase(phase)
                except Exception:
                    log.exception("phase callback failed")

    phases: list[Phase] = PhaseList()
    warnings: list[str] = []
    out = Path(out_dir) if out_dir is not None else None
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)
    _write(out, "message.txt", message)
    lang = detect_language(message)

    def finish(status: str, output: str, *, intake: dict | None = None,
               research: dict | None = None) -> PipelineResult:
        # A verdict is only reported when it reached the user in a report.
        verdict = (research or {}).get("verdict") if status == REPORT else None
        result = PipelineResult(status=status, output=output, language=lang, phases=phases,
                                warnings=warnings, verdict=verdict,
                                intake=intake, research=research, out_dir=out, seconds=total(),
                                message=message)
        _write(out, "report.md" if status == REPORT else "notice.md", output)
        _write(out, "phase_log.json", result.log_dict())
        _write(out, "phase_log.md", render_phase_log(result))
        log.info("pipeline | %s | verdict=%s | %.1fs", status, result.verdict, result.seconds)
        return result

    # 1. Intake
    t = _Timer()
    if not message.strip():
        phases.append(Phase("Intake", "STOP", t(), "empty message: nothing to extract"))
        return finish(NEEDS_INPUT, msg_needs_input(["product_description", "destination_country"], lang))
    try:
        ir: IntakeResult = run_intake(message, llm=llm)
    except LLMCallError as exc:
        phases.append(Phase("Intake", "FAILED", t(), "LLM call failed", calls=[failed_call_record(exc)],
                            problems=[str(exc)]))
        return finish(LLM_ERROR, msg_llm_error(lang))
    intake = ir.data
    lang = intake["language"]
    _write(out, "intake.json", {"served_by": ir.llm.routed_via, "changes": ir.changes, "output": intake})
    shipment = intake.get("shipment_value")
    value = f"{shipment.get('amount')} {shipment.get('currency')}" if shipment else None
    phases.append(Phase(
        "Intake", "OK", t(),
        f"product={intake.get('product_description')!r} | destination={intake.get('destination_country')!r} "
        f"| role={intake.get('exporter_role')} | value={value} | language={lang}",
        calls=[call_record(ir.llm)], details={"missing_fields": intake["missing_fields"],
                                              "normalized_by_code": ir.changes}))

    missing = ir.blocking_missing
    if missing:
        phases.append(Phase("Coverage check", "STOP", 0.0, f"missing: {', '.join(missing)}: ask the user"))
        return finish(NEEDS_INPUT, msg_needs_input(missing, lang), intake=intake)

    # 2. Coverage: is the destination in the knowledge base?
    country = intake["destination_country"]
    corridor = corridor_for(country)
    if corridor is None:
        phases.append(Phase("Coverage check", "STOP", 0.0,
                            f"destination {country!r} not covered (covered: {_covered_list()})"))
        return finish(NOT_COVERED, msg_destination_not_covered(country, lang), intake=intake)
    phases.append(Phase("Coverage check", "OK", 0.0, f"{country} -> corridor {corridor!r}"))

    # 3. Tools + evidence (pure code; the only place the bill of materials is read)
    t = _Timer()
    pack = build_evidence(intake, case_folder, corridor)
    _write(out, "evidence.txt", pack.text)
    tool_status = {k: v.get("status") for k, v in pack.tool_results.items()}
    cands = [c["id"] for c in pack.candidates]
    phases.append(Phase(
        "Tools + evidence", "OK" if cands else "STOP", t(),
        f"candidates: {', '.join(cands) or 'none'} | bill of materials: "
        f"{'given' if case_folder else 'not given'} | evidence {len(pack.text)} chars, "
        f"{len(pack.allowed_ids)} IDs",
        details={"tool_status": tool_status}))
    if not cands:
        # No tariff line matches: nothing for the Researcher to classify. Say so in code.
        return finish(NOT_COVERED, msg_product_not_covered(intake["product_description"],
                                                           intake.get("hs_code_given"), country, lang),
                      intake=intake)

    # 4. Researcher, QA slot, at most one shared revision
    research: ResearcherResult | None = None
    accepted: ResearcherResult | None = None
    corrections: list[str] = []
    round_1: tuple[dict, QAOutcome] | None = None   # (Researcher data, QA outcome) of round 1 (1d)
    for round_no in (1, 2):
        t = _Timer()
        name = f"Researcher (round {round_no})"
        try:
            research = run_researcher(intake, pack, llm=llm,
                                      previous=research.data if round_no == 2 else None,
                                      corrections=corrections if round_no == 2 else None)
        except LLMCallError as exc:
            phases.append(Phase(name, "FAILED", t(), "LLM call failed", calls=[failed_call_record(exc)],
                                problems=[str(exc)],
                                details={"corrections_sent": corrections} if round_no == 2 else {}))
            return finish(LLM_ERROR, msg_llm_error(lang), intake=intake)
        _write(out, f"researcher_{round_no}.json", research_record(research))
        d = research.data
        cls = d.get("classification") or {}
        phases.append(Phase(
            name, "OK" if research.passed else "FAILED", t(),
            f"line {cls.get('tariff_line')} ({cls.get('confidence')}) | origin "
            f"{(d.get('origin_result') or {}).get('status')} | verdict {d.get('verdict')} | "
            f"problems {len(research.problems)} | warnings {len(research.warnings)}",
            calls=[call_record(research.llm)], problems=research.problems, warnings=research.warnings,
            details={**({"corrections_sent": corrections} if round_no == 2 else {}),
                     **({"normalized_by_code": research.changes} if research.changes else {})}))

        if round_no == 2 and not research.passed:
            phases.append(Phase("QA (round 2)", "SKIPPED", 0.0, "not run: code checks still fail"))
            break

        t = _Timer()
        q = qa(intake, pack, research, llm=llm)
        if round_no == 2 and round_1 is not None:   # 1d: what round 1 passed and is unchanged stays passed
            q = settle_round_2(q, research.data, *round_1)
        q_calls = [call_record(c) for c in (q.llm_calls or ([q.llm] if q.llm else []))]
        if q.failed_attempts:
            q_calls.append({"ok": False, "served_by": None, "error": "LLM call failed",
                            "attempts": q.failed_attempts})
        _write(out, f"qa_{round_no}.json", {"status": q.status, "scores": q.scores,
                                            "corrections": q.corrections, "note": q.note,
                                            "warning_judgements": q.judgements,
                                            "answer_problems": q.output_problems,
                                            "parts": q.parts,
                                            "raw_corrections": q.raw_corrections,
                                            "overruled_by_kb": q.overruled,
                                            "rejudged": q.rejudged,
                                            "settled_by_round_1": q.settled,
                                            "served_by": q.llm.routed_via if q.llm else None,
                                            "calls": q_calls,
                                            "code_warnings_given": research.warnings})
        phases.append(Phase(
            f"QA (round {round_no})",
            {QA_APPROVED: "OK", QA_SKIPPED: "SKIPPED", QA_REJECTED: "REJECTED",
             QA_OVERRULED: "OVERRULED", QA_SETTLED: "SETTLED"}.get(q.status, "FAILED"),
            t(), q.note or f"{q.status} | scores {q.scores}", calls=q_calls, problems=q.corrections,
            details={**({"warning_judgements": q.judgements} if q.judgements else {}),
                     **({"overruled_by_kb": [overruled_text(o) for o in q.overruled]} if q.overruled else {}),
                     **({"settled_by_round_1": [settled_text(c) for c in q.settled]} if q.settled else {}),
                     **({"qa_answer_problems": q.output_problems} if q.output_problems else {}),
                     **({"qa_parts": q.parts} if q.parts else {})}))
        w = same_model_warning(research.llm.routed_via if research.llm else None,
                               q.llm.routed_via if q.llm else None)
        if w and w not in warnings:
            warnings.append(w)
        if q.status == QA_ERROR:
            warnings.append(f"QA round {round_no}: {q.note}")
        if q.status == QA_OVERRULED:
            warnings.append(f"QA round {round_no}: rejection overruled by the KB (every correction dropped a "
                            f"qualifier its record's note carries, or rejected the record's own note: "
                            f"{', '.join(str(o.get('field')) for o in q.overruled)})")
        if q.settled:
            warnings.append(f"QA round {round_no}: {len(q.settled)} correction(s) not counted, on items unchanged "
                            f"since round 1, which reviewed them without a correction "
                            f"({', '.join(str(c.get('field')) for c in q.settled)})")
        if q.status in QA_NOT_REVIEWED and research.warnings:
            warnings.append(f"Researcher round {round_no}: {len(research.warnings)} code warning(s) "
                            "not reviewed by QA")

        # Code problems and QA corrections share the single revision.
        corrections = list(research.problems)
        if q.status not in QA_ACCEPTS:
            corrections += [f"QA: {c}" for c in q.corrections] or ["QA: rejected without corrections"]
        if not corrections:
            accepted = research
            break
        round_1 = (research.data, q)

    if accepted is None:
        return finish(CHECKS_FAILED, msg_checks_failed(lang), intake=intake, research=research.data)
    research = accepted

    # 5. Document Builder (always returns a report; code-only fallback on failure).
    # Step 7.6: each round's prose is checked for meaning by the prose QA (one call, never split).
    t = _Timer()
    # Problem 97: the chosen line's deciding conditions come from the origin tool itself (the
    # Researcher may drop its note), so the Builder's code can put a caution in the summary.
    line = str((research.data.get("classification") or {}).get("tariff_line") or "")
    origin = pack.tool_results.get(f"{ORIGIN_TOOL_PREFIX}:{line}") or {}
    conditions = list(origin.get("conditions") or [])
    br: BuilderResult = run_document_builder(research.data, intake, pack.id_sources,
                                             corridor=corridor, llm=llm, review=prose_qa,
                                             conditions=conditions,
                                             origin_missing=list(origin.get("missing") or []))   # F3
    calls = [{**call_record(c), "chain": next((a.get("chain") for a in c.attempts), None)} for c in br.llm_calls]
    if br.failed_attempts:
        calls.append({"ok": False, "served_by": None, "error": "LLM call failed",
                      "chain": next((a.get("chain") for a in br.failed_attempts), None),
                      "attempts": br.failed_attempts})
    n_mand = sum(n["mandatory"] for n in br.notes)
    n_cut = sum(n["mandatory"] and n["nid"] in br.fragments_dropped for n in br.notes)   # (b), Arabic only
    reviews = [(r["round"], r["review"]) for r in br.rounds if r.get("review") is not None]
    for round_no, q in reviews:
        _write(out, f"prose_qa_{round_no}.json", prose_qa_record(q))
    _write(out, "builder.json", {
        "calls": calls, "used_fallback": br.used_fallback, "fallback_reason": br.fallback_reason,
        "review_status": br.review_status, "problems_left": br.problems, "untranslated": br.untranslated,
        "chain_fallback": br.chain_fallback, "fragments_dropped": br.fragments_dropped,
        "notes_left_out": br.notes_left_out,
        "rounds": [{"round": r["round"], "chain": r.get("chain"), "code_problems": r["code_problems"],
                    "prose_qa": r["review"].status if r.get("review") else None,
                    "prose": r.get("prose")} for r in br.rounds],
        "prose": br.prose, "notes": br.notes, "conditions": conditions})
    review_text = {QA_APPROVED: "prose QA approved", QA_ERROR: "prose NOT reviewed by QA",
                   "SKIPPED": "prose QA not run"}.get(br.review_status, "")
    if br.used_fallback:
        what = f"code-only report (fallback): {br.fallback_reason or 'LLM prose failed'}"
    else:
        what = "LLM prose passed the code checks" + (f"; {review_text}" if review_text else "")
        if br.untranslated:   # N15 (D)
            what += f"; title and still-needed kept in English ({len(br.untranslated)} problem(s) left)"
    builder_seconds = round(t() - sum(q.seconds for _, q in reviews), 2)
    round2 = next((r for r in br.rounds if r["round"] == 2), None)
    phases.append(Phase(
        "Document Builder", "FALLBACK" if br.used_fallback else "OK", max(builder_seconds, 0.0),
        f"{what} | rounds: {len(br.rounds)} | notes: {len(br.notes)} in ({n_mand} mandatory, verbatim) -> "
        f"{n_mand - n_cut + len(br.prose.get('notes', []))} in the report"
        + (f" | split-note fragments left out (already in an Arabic note): "
           f"{', '.join(f'{nid} ({keys})' for nid, keys in br.fragments_dropped.items())}"
           if br.fragments_dropped else "")
        + (f" | optional notes left out of the Arabic code-only report (no Arabic draft): "
           f"{', '.join(br.notes_left_out)}" if br.notes_left_out else "")
        + (f" | chain fallback: {br.chain_fallback['from']} -> {br.chain_fallback['to']} "
           f"(round {br.chain_fallback['round']}: {br.chain_fallback['reason']})" if br.chain_fallback else "")
        + (f" | summary cautions (code): {', '.join(conditions)}"
           if conditions and research.data.get("verdict") in CHECKLIST_VERDICTS else ""),
        calls=calls, problems=br.problems,
        details={**({"corrections_sent": round2["corrections_sent"]}
                    if round2 and round2["corrections_sent"] else {}),
                 **({"code_problems_by_round": {r["round"]: r["code_problems"] for r in br.rounds
                                                if r["code_problems"]}}
                    if any(r["code_problems"] for r in br.rounds) else {})}))
    for round_no, q in reviews:
        q_calls = prose_qa_record(q)["calls"]
        phases.append(Phase(
            f"Prose QA (round {round_no})",
            {QA_APPROVED: "OK", QA_REJECTED: "REJECTED"}.get(q.status, "FAILED"), q.seconds,
            q.note, calls=q_calls, problems=q.corrections,
            details={"qa_answer_problems": q.output_problems} if q.output_problems else {}))
        w = builder_vs_prose_qa_warning(served_by(calls), q.llm.routed_via if q.llm else None)
        if w and w not in warnings:
            warnings.append(w)
    if br.review_status == QA_ERROR:
        last = reviews[-1][1].note if reviews else "prose QA did not run"
        warnings.append(f"Document Builder: report prose NOT reviewed by QA ({last})")

    # 6. Report check: plain code on the finished report. Flag only: the report is shown anyway.
    t = _Timer()
    rc_problems, rc_warnings = check_report(br.markdown, research=research.data,
                                            evidence_text=pack.text, message=message, language=lang)
    flagged = bool(rc_problems or rc_warnings)
    phases.append(Phase(
        "Report check", "FLAGGED" if rc_problems else "OK", t(),
        f"{len(rc_problems)} problem(s), {len(rc_warnings)} warning(s)"
        + (" | report shown anyway (flag only)" if flagged else ""),
        problems=rc_problems, warnings=rc_warnings))
    if rc_problems:
        warnings.append(f"Report check: {len(rc_problems)} problem(s) in the report shown to the user "
                        "(flag only): read report.md")
    return finish(REPORT, br.markdown, intake=intake, research=research.data)
