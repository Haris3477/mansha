"""QA Evaluator (Step 7): a second model checks the MEANING of the Researcher's findings.

Code already checks the form (IDs, the status mapping, the saving, required fields).
QA judges what code cannot: whether each finding says what its cited record says,
whether the tariff line is justified by its description, whether "What's still needed"
makes sense for the verdict, and whether each code warning is a real problem or noise.

    run_qa(intake, pack, research, *, llm) -> QAOutcome

1. Code builds QA's input: the Intake JSON, the code warnings numbered W1, W2, ...,
   the compact evidence (mansha/qa_evidence.py) and the Researcher JSON as QA reads it.
2. One LLM call on the `judge` chain, which shares no model with `long` (the
   Researcher's chain), so QA never grades its own model's work.
3. Code validates QA's answer (check_qa): scores are 0/1, every warning judged once,
   every correction names a real field and a real evidence ID, and scores agree with
   the corrections. A failing answer gets ONE retry with the problems listed.
4. Code decides the status: any score 0 -> REJECTED, else APPROVED. The model never
   writes the status (a fixed rule is code's job).
5. If the call fails (provider outage) or QA's answer is still invalid after the retry:
   status ERROR. The pipeline continues (decision D5 A): the report is produced and
   the phase log and a pipeline warning say it was NOT reviewed by QA.

Corrections go back to the orchestrator, which sends them to the Researcher together
with any code problems, in the pipeline's single shared revision.
"""

from __future__ import annotations

import copy
import json
import logging
import re
from dataclasses import dataclass, field

from mansha.evidence import EvidencePack
from mansha.llm_client import LLMCallError, LLMResult, call_llm
from mansha.prompts import build_system_prompt
from mansha.qa_evidence import qa_evidence, research_for_qa

log = logging.getLogger("mansha.qa")

QA_CHAIN = "auto:judge"
REQUIRED_KEYS = ("warnings", "corrections", "scores")
METRICS = ("factuality", "completeness", "formatting_safety")
JUDGEMENTS = ("REAL", "NOISE")

# QA statuses. APPROVED / REJECTED come from run_qa; SKIPPED is the orchestrator's
# pass-through (no QA); ERROR means QA could not review this output.
QA_APPROVED, QA_REJECTED, QA_SKIPPED, QA_ERROR = "APPROVED", "REJECTED", "SKIPPED", "ERROR"
QA_ACCEPTS = {QA_APPROVED, QA_SKIPPED, QA_ERROR}  # statuses that let the pipeline go on
QA_NOT_REVIEWED = {QA_SKIPPED, QA_ERROR}

# "procedure[2].step" -> ("procedure", 2); "classification" -> ("classification", None)
FIELD_RE = re.compile(r"^([a-z_]+)(?:\[(\d+)\])?(?:\.[a-z_]+)?$")


@dataclass
class QAOutcome:
    status: str                              # APPROVED | REJECTED | SKIPPED | ERROR
    corrections: list[str] = field(default_factory=list)   # for the Researcher, in plain sentences
    scores: dict | None = None
    llm: LLMResult | None = None             # the call whose answer was used
    note: str = ""
    judgements: list[dict] = field(default_factory=list)   # [{id, warning, judgement, reason}]
    llm_calls: list[LLMResult] = field(default_factory=list)  # every successful call (incl. the retry)
    failed_attempts: list[dict] = field(default_factory=list)  # attempts of a call that failed
    output_problems: list[str] = field(default_factory=list)   # what was wrong with QA's own answer


def warning_ids(warnings: list[str]) -> list[str]:
    return [f"W{i}" for i in range(1, len(warnings) + 1)]


def build_messages(intake: dict, pack: EvidencePack, research: dict, warnings: list[str], *,
                   previous: dict | None = None, problems: list[str] | None = None) -> list[dict]:
    listed = "\n".join(f"{wid}: {w}" for wid, w in zip(warning_ids(warnings), warnings)) or "none"
    user = ("INTAKE JSON:\n" + json.dumps(intake, ensure_ascii=False, indent=2)
            + "\n\nCODE WARNINGS:\n" + listed
            + "\n\nEVIDENCE:\n" + qa_evidence(pack, research)
            + "\n\nRESEARCHER JSON:\n" + json.dumps(research_for_qa(research), ensure_ascii=False, indent=1))
    messages = [
        {"role": "system", "content": build_system_prompt("qa")},
        {"role": "user", "content": user},
    ]
    if problems:
        messages.append({"role": "assistant", "content": json.dumps(previous, ensure_ascii=False)})
        messages.append({"role": "user", "content":
                         "Your JSON has these problems. Fix all of them and return the full JSON only:\n"
                         + "\n".join(f"- {p}" for p in problems)})
    return messages


def _score(v) -> int | None:
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, int) and v in (0, 1):
        return v
    if isinstance(v, str) and v.strip() in ("0", "1"):
        return int(v.strip())
    return None


def check_qa(data: dict, research: dict, warnings: list[str], allowed_ids) -> list[str]:
    """Problems in QA's own answer (empty = valid). Pure code."""
    problems: list[str] = []
    allowed = set(allowed_ids)

    scores = data.get("scores")
    if not isinstance(scores, dict) or set(scores) != set(METRICS):
        problems.append(f"`scores` must have exactly these keys: {', '.join(METRICS)}")
        scores = {}
    for m in METRICS:
        if m in scores and _score(scores[m]) is None:
            problems.append(f"scores.{m} must be 0 or 1, not {scores[m]!r}")

    ids = warning_ids(warnings)
    judged = data.get("warnings")
    if not isinstance(judged, list):
        problems.append("`warnings` must be a list")
        judged = []
    seen: list[str] = []
    for j in judged:
        if not isinstance(j, dict):
            problems.append("each item of `warnings` must be an object with id, judgement and reason")
            continue
        wid = j.get("id")
        if wid not in ids:
            problems.append(f"warnings: unknown id {wid!r} (the code warnings are: {', '.join(ids) or 'none'})")
        elif wid in seen:
            problems.append(f"warnings: {wid} is judged twice")
        else:
            seen.append(wid)
        if j.get("judgement") not in JUDGEMENTS:
            problems.append(f"warnings: {wid} judgement must be REAL or NOISE")
        if not str(j.get("reason") or "").strip():
            problems.append(f"warnings: {wid} needs a reason")
    missing = [w for w in ids if w not in seen]
    if missing:
        problems.append(f"warnings: judge every code warning; missing {', '.join(missing)}")

    corrections = data.get("corrections")
    if not isinstance(corrections, list):
        problems.append("`corrections` must be a list")
        corrections = []
    for i, c in enumerate(corrections):
        if not isinstance(c, dict):
            problems.append(f"corrections[{i}] must be an object with field, problem, fix and source_id")
            continue
        f = str(c.get("field") or "")
        m = FIELD_RE.match(f)
        if not m or m.group(1) not in research:
            problems.append(f"corrections[{i}]: field {f!r} is not a field of the Researcher JSON")
        elif m.group(2) is not None:
            items = research.get(m.group(1))
            if not isinstance(items, list) or int(m.group(2)) >= len(items):
                problems.append(f"corrections[{i}]: {f} does not exist "
                                f"({m.group(1)} has {len(items) if isinstance(items, list) else 0} item(s))")
        for k in ("problem", "fix"):
            if not str(c.get(k) or "").strip():
                problems.append(f"corrections[{i}] needs a `{k}`")
        sid = c.get("source_id")
        if sid not in (None, "", "null") and sid not in allowed:
            problems.append(f"corrections[{i}]: source_id {sid!r} is not an evidence ID")

    got = [_score(scores.get(m)) for m in METRICS if m in scores]
    if got and None not in got:
        if 0 in got and not corrections:
            problems.append("a score of 0 needs at least one correction")
        if 0 not in got and corrections:
            problems.append("corrections were given but every score is 1: set the score of each "
                            "metric a correction belongs to to 0, or remove the corrections")
    real = [j.get("id") for j in judged if isinstance(j, dict) and j.get("judgement") == "REAL"]
    if real and _score(scores.get("factuality")) == 1:
        problems.append(f"{', '.join(map(str, real))} judged REAL, so factuality must be 0 with a correction")
    return problems


def correction_text(c: dict) -> str:
    s = f"{c.get('field')}: {str(c.get('problem')).strip()} Fix: {str(c.get('fix')).strip()}"
    sid = c.get("source_id")
    return s + (f" (see {sid})" if sid not in (None, "", "null") else "")


def run_qa(intake: dict, pack: EvidencePack, research, *, llm=call_llm) -> QAOutcome:
    """Review one Researcher result (a ResearcherResult: `.data` and `.warnings`)."""
    data = research.data
    warnings = list(research.warnings)
    calls: list[LLMResult] = []
    previous: dict | None = None
    problems: list[str] = []
    first_problems: list[str] = []   # what the retry had to fix (kept for the phase log)
    for attempt in (1, 2):
        try:
            res = llm("qa", QA_CHAIN, build_messages(intake, pack, data, warnings,
                                                     previous=previous, problems=problems or None),
                      expect_json=True, required_keys=REQUIRED_KEYS)
        except LLMCallError as exc:
            log.info("qa | call failed: %s", exc)
            return QAOutcome(status=QA_ERROR, llm_calls=calls, failed_attempts=list(exc.attempts),
                             output_problems=first_problems,
                             note="QA call failed: output NOT reviewed by QA")
        calls.append(res)
        answer = copy.deepcopy(res.data)
        problems = check_qa(answer, data, warnings, pack.allowed_ids)
        log.info("qa | attempt %d | served_by=%s | answer problems=%d", attempt, res.routed_via, len(problems))
        if not problems:
            break
        if attempt == 1:
            first_problems = problems
        previous = answer
    else:
        return QAOutcome(status=QA_ERROR, llm=calls[-1], llm_calls=calls,
                         output_problems=first_problems + [f"after retry: {p}" for p in problems],
                         note="QA answer still invalid after its retry: output NOT reviewed by QA")

    scores = {m: _score(answer["scores"][m]) for m in METRICS}
    by_id = dict(zip(warning_ids(warnings), warnings))
    judgements = [{"id": j["id"], "warning": by_id.get(j["id"], ""), "judgement": j["judgement"],
                   "reason": str(j.get("reason", "")).strip()} for j in answer["warnings"]]
    corrections = [correction_text(c) for c in answer["corrections"]]
    status = QA_REJECTED if 0 in scores.values() else QA_APPROVED
    real = sum(j["judgement"] == "REAL" for j in judgements)
    note = (f"{status} | factuality {scores['factuality']}, completeness {scores['completeness']}, "
            f"formatting_safety {scores['formatting_safety']} | code warnings judged: "
            f"{len(judgements)} ({real} real)")
    log.info("qa | %s", note)
    return QAOutcome(status=status, corrections=corrections, scores=scores, llm=calls[-1], note=note,
                     judgements=judgements, llm_calls=calls, output_problems=first_problems)
