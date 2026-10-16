"""Orchestrator (Step 9): one user message in, one answer out, every phase logged.

Plain Python decides the order and when to stop; the agents only do their own job.

    message -> Intake -> coverage check -> tools + evidence -> Researcher
            -> [QA slot] -> (one shared revision) -> Document Builder -> report

Stops, each with a short message written by code in the user's language:
    NEEDS_INPUT    product or destination missing (ask the user)
    NOT_COVERED    destination, or product, not in Mansha's knowledge base
    CHECKS_FAILED  Researcher still failing code checks / QA after its one revision
    LLM_ERROR      Intake or Researcher call failed (provider outage); the Builder
                   never causes this, it has a code-only fallback

The QA slot is a pass-through until Step 7: it returns SKIPPED (never APPROVED),
and the phase log says the output was NOT reviewed by QA.

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

from mansha.document_builder import BuilderResult, run_document_builder
from mansha.evidence import EvidencePack, build_evidence
from mansha.intake import IntakeResult, detect_language, run_intake
from mansha.kb import CORRIDORS, corridor_for
from mansha.llm_client import LLMCallError, LLMResult, call_llm
from mansha.researcher import ResearcherResult, run_researcher

log = logging.getLogger("mansha.orchestrator")

# Official list of the UAE's CEPAs (Ministry of Foreign Trade), checked 16 Oct 2026.
MOFT_CEPA_URL = "https://www.trade.gov.ae/comprehensive-economic-partnership-agreements"

# Run statuses
REPORT = "REPORT"
NEEDS_INPUT = "NEEDS_INPUT"
NOT_COVERED = "NOT_COVERED"
CHECKS_FAILED = "CHECKS_FAILED"
LLM_ERROR = "LLM_ERROR"

# QA statuses (APPROVED / REJECTED from Step 7; SKIPPED = the pass-through)
QA_APPROVED, QA_REJECTED, QA_SKIPPED = "APPROVED", "REJECTED", "SKIPPED"
QA_ACCEPTS = {QA_APPROVED, QA_SKIPPED}


# ---------- results ----------

@dataclass
class QAOutcome:
    status: str                              # APPROVED | REJECTED | SKIPPED
    corrections: list[str] = field(default_factory=list)
    scores: dict | None = None
    llm: LLMResult | None = None
    note: str = ""


@dataclass
class Phase:
    name: str                                # e.g. "Researcher (round 1)"
    status: str                              # OK | STOP | FAILED | SKIPPED | FALLBACK
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
    """Placeholder until Step 7. Approves nothing: the output is simply not reviewed."""
    return QAOutcome(status=QA_SKIPPED,
                     note="QA Evaluator not built yet (Step 7): output NOT reviewed by QA")


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


def _covered_list() -> str:
    return ", ".join(CORRIDORS)


def msg_needs_input(missing: list[str], lang: str) -> str:
    lines = [ASK_INTRO[lang], ""] + [f"- {ASK[lang][f]}" for f in missing] + ["", ASK_END[lang]]
    return "\n".join(lines) + "\n"


def msg_destination_not_covered(country: str, lang: str) -> str:
    if lang == "ar":
        return (f"يغطي منشأ حاليًا التصدير من الإمارات إلى: {_covered_list()} فقط. "
                f"لا تتوفر لديه بيانات عن {country}، لذلك لا يستطيع التحقق من المنشأ أو الرسوم لهذا السوق.\n\n"
                f"هذا لا يعني أنه لا توجد اتفاقية تجارية بين الإمارات و{country}. "
                f"راجع قائمة اتفاقيات الشراكة الاقتصادية الشاملة لدى وزارة التجارة الخارجية: {MOFT_CEPA_URL}\n")
    return (f"Mansha currently covers exports from the UAE to {_covered_list()} only. "
            f"It has no data for {country}, so it can't check origin or duty for that market.\n\n"
            f"This does not mean the UAE has no trade agreement with {country}. "
            f"See the Ministry of Foreign Trade's list of CEPAs: {MOFT_CEPA_URL}\n")


def msg_product_not_covered(product: str, hs_code: str | None, country: str, lang: str) -> str:
    if lang == "ar":
        what = f"\"{product}\"" + (f" (الرمز الجمركي {hs_code})" if hs_code else "")
        advice = ("تحقق من التصنيف والرسوم مع الجمارك أو مع وسيط جمركي." if hs_code else
                  "إذا كنت تعرف الرمز الجمركي (HS) للمنتج، أعد المحاولة مع ذكره. "
                  "وإلا فتحقق من التصنيف والرسوم مع الجمارك أو مع وسيط جمركي.")
        return (f"لا تتضمن بيانات منشأ للتعريفة الجمركية في {country} بندًا يطابق {what} بعد، "
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


def research_record(res: ResearcherResult) -> dict:
    return {"served_by": res.llm.routed_via if res.llm else None,
            "latency_s": res.llm.latency_s if res.llm else None,
            "attempts": res.llm.attempts if res.llm else [],
            "problems": res.problems, "warnings": res.warnings, "output": res.data}


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


# ---------- the pipeline ----------

def run_pipeline(message: str, *, case_folder: str | Path | None = None, llm=call_llm,
                 qa: Callable[..., QAOutcome] = qa_passthrough,
                 out_dir: str | Path | None = None) -> PipelineResult:
    """Run Mansha end to end on one user message.

    case_folder: folder with bom.csv / declaration.json (read only by code), or None.
    llm: the LLM call function for every agent (tests pass a fake one).
    qa: the QA slot (Step 7 replaces the pass-through; tests pass fakes).
    out_dir: if given, every phase's input/output is saved there (it is created).
    """
    total = _Timer()
    phases: list[Phase] = []
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
                                intake=intake, research=research, out_dir=out, seconds=total())
        _write(out, "report.md" if status == REPORT else "notice.md", output)
        _write(out, "phase_log.json", result.log_dict())
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
            details={"corrections_sent": corrections} if round_no == 2 else {}))

        if round_no == 2 and not research.passed:
            phases.append(Phase("QA (round 2)", "SKIPPED", 0.0, "not run: code checks still fail"))
            break

        t = _Timer()
        q = qa(intake, pack, research, llm=llm)
        q_calls = [call_record(q.llm)] if q.llm else []
        _write(out, f"qa_{round_no}.json", {"status": q.status, "scores": q.scores,
                                            "corrections": q.corrections, "note": q.note,
                                            "served_by": q.llm.routed_via if q.llm else None,
                                            "code_warnings_given": research.warnings})
        phases.append(Phase(
            f"QA (round {round_no})", {QA_APPROVED: "OK", QA_SKIPPED: "SKIPPED"}.get(q.status, "FAILED"),
            t(), q.note or f"{q.status} | scores {q.scores}", calls=q_calls, problems=q.corrections))
        w = same_model_warning(research.llm.routed_via if research.llm else None,
                               q.llm.routed_via if q.llm else None)
        if w and w not in warnings:
            warnings.append(w)
        if q.status == QA_SKIPPED and research.warnings:
            warnings.append(f"Researcher round {round_no}: {len(research.warnings)} code warning(s) "
                            "not reviewed (QA not built yet)")

        # Code problems and QA corrections share the single revision.
        corrections = list(research.problems)
        if q.status not in QA_ACCEPTS:
            corrections += [f"QA: {c}" for c in q.corrections] or ["QA: rejected without corrections"]
        if not corrections:
            accepted = research
            break

    if accepted is None:
        return finish(CHECKS_FAILED, msg_checks_failed(lang), intake=intake, research=research.data)
    research = accepted

    # 5. Document Builder (always returns a report; code-only fallback on failure)
    t = _Timer()
    br: BuilderResult = run_document_builder(research.data, intake, pack.id_sources,
                                             corridor=corridor, llm=llm)
    calls = [call_record(c) for c in br.llm_calls]
    if br.failed_attempts:
        calls.append({"ok": False, "served_by": None, "error": "LLM call failed",
                      "attempts": br.failed_attempts})
    n_mand = sum(n["mandatory"] for n in br.notes)
    _write(out, "builder.json", {"calls": calls, "used_fallback": br.used_fallback,
                                 "problems_left": br.problems, "prose": br.prose, "notes": br.notes})
    phases.append(Phase(
        "Document Builder", "FALLBACK" if br.used_fallback else "OK", t(),
        f"{'code-only report (fallback)' if br.used_fallback else 'LLM prose passed the checks'} | "
        f"notes: {len(br.notes)} in ({n_mand} mandatory, verbatim) -> "
        f"{n_mand + len(br.prose.get('notes', []))} in the report",
        calls=calls, problems=br.problems))
    return finish(REPORT, br.markdown, intake=intake, research=research.data)
