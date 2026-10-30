"""Builder prose check (Step 7.6, decision D2 = B): a second model checks the MEANING of the
Document Builder's text against what the Builder was given.

    review_prose(facts_text, notes, prose, *, llm) -> ProseQAOutcome

Why: the Builder rewrites approved findings in plain words, and code can only check the
form of that text (numbers, IDs, code words). Rewrites that change the meaning passed
every check and reached reports: "likely not eligible" became "cannot obtain" (problem
57), "eliminates your customs duty" (53), "minimal operations were completed" (30).

1. Code sends the judge exactly what the Builder saw: FACTS (with TERMS) and the optional
   NOTES that were sent, plus the Builder's JSON. Mandatory notes are never sent (the
   Builder never sees them; code prints them verbatim). FACTS carries no evidence IDs,
   no supplier names and no input costs (counts and percentages only).
2. ONE call on the `judge` chain (GPT-OSS 120B), which shares no model with `long` (the
   Builder's chain). FACTS + prose always fits one call inside Groq's 8,000-token limit
   (largest case on 17 Oct: ~3,050 estimated prompt tokens + 2,000 answer budget). This
   module never splits a review and does not use plan B's code (mansha/qa.py plan_parts):
   if a review would not fit, it returns ERROR without a call.
3. Code validates the answer (check_prose_qa); one retry with the problems listed.
4. Code decides the status: any score 0 -> REJECTED, else APPROVED.
5. Call failed, or answer still invalid after its retry -> ERROR: the Builder keeps its
   code-checked prose and the run says it was NOT reviewed by QA (same rule as D5 A).

The Builder (mansha/document_builder.py) runs this after its code checks in each round:
code problems and QA corrections share its single retry; still failing after the retry
-> the code-only report.
"""

from __future__ import annotations

import copy
import json
import logging
import re
from dataclasses import dataclass, field

from mansha.llm_client import LLMCallError, LLMResult, call_llm
from mansha.prompts import build_system_prompt
from mansha.qa import QA_APPROVED, QA_CHAIN, QA_ERROR, QA_REJECTED

log = logging.getLogger("mansha.prose_qa")

AGENT = "prose_qa"
PROSE_QA_CHAIN = QA_CHAIN            # "auto:judge"
REQUIRED_KEYS = ("corrections", "scores")
METRICS = ("factuality", "completeness")
TEXT_FIELDS = ("summary", "classification", "origin")   # M4 (30 Oct): no `duty` field

# Size guard (tokens). Own copy of the estimate (~3.6 characters per token, ~10% high against
# Groq's counts on 17 Oct), so a change to plan B's numbers can't change this check.
ANSWER_BUDGET = 2000
SIZE_LIMIT = 7600                    # Groq allows 8,000 per request, prompt + answer budget
CHARS_PER_TOKEN = 3.6

# "summary" | "notes[2]" | "notes[2].text"
FIELD_RE = re.compile(r"^(?:(summary|classification|duty|origin)|notes\[(\d+)\](?:\.text)?)$")
NOTE_ID_RE = re.compile(r"^N\d+$")


@dataclass
class ProseQAOutcome:
    status: str                                            # APPROVED | REJECTED | ERROR
    corrections: list[str] = field(default_factory=list)   # for the Builder, in plain sentences
    scores: dict | None = None
    llm: LLMResult | None = None                           # the call whose answer was used
    note: str = ""
    llm_calls: list[LLMResult] = field(default_factory=list)   # every successful call (incl. the retry)
    failed_attempts: list[dict] = field(default_factory=list)  # attempts of a call that failed
    output_problems: list[str] = field(default_factory=list)   # what was wrong with the judge's answer
    seconds: float = 0.0


def sent_note_ids(facts_text: str) -> list[str]:
    """The optional note numbers the Builder received (N1, N2, ...), read from its input."""
    notes_part = facts_text.split("\n\nNOTES", 1)[1] if "\n\nNOTES" in facts_text else ""
    return re.findall(r"^(N\d+): ", notes_part, re.MULTILINE)


def build_messages(facts_text: str, prose: dict, *, previous: dict | None = None,
                   problems: list[str] | None = None) -> list[dict]:
    """facts_text: the Builder's input (FACTS + optional NOTES), exactly as the Builder got it."""
    user = facts_text + "\n\nBUILDER JSON:\n" + json.dumps(prose, ensure_ascii=False, indent=1)
    messages = [
        {"role": "system", "content": build_system_prompt("prose_qa")},
        {"role": "user", "content": user},
    ]
    if problems:
        messages.append({"role": "assistant", "content": json.dumps(previous, ensure_ascii=False)})
        messages.append({"role": "user", "content":
                         "Your JSON has these problems. Fix all of them and return the full JSON only:\n"
                         + "\n".join(f"- {p}" for p in problems)})
    return messages


def estimate_tokens(messages: list[dict]) -> int:
    return int(sum(len(m["content"]) for m in messages) / CHARS_PER_TOKEN) + 1


def _score(v) -> int | None:
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, int) and v in (0, 1):
        return v
    if isinstance(v, str) and v.strip() in ("0", "1"):
        return int(v.strip())
    return None


def check_prose_qa(data: dict, prose: dict, note_ids) -> list[str]:
    """Problems in the judge's own answer (empty = valid). Pure code.

    note_ids: the optional note numbers the Builder received.
    """
    problems: list[str] = []
    allowed_refs = {"FACTS", *note_ids}

    scores = data.get("scores")
    if not isinstance(scores, dict) or set(scores) != set(METRICS):
        problems.append(f"`scores` must have exactly these keys: {', '.join(METRICS)}")
        scores = {}
    for m in METRICS:
        if m in scores and _score(scores[m]) is None:
            problems.append(f"scores.{m} must be 0 or 1, not {scores[m]!r}")

    corrections = data.get("corrections")
    if not isinstance(corrections, list):
        problems.append("`corrections` must be a list")
        corrections = []
    n_notes = len(prose.get("notes") or []) if isinstance(prose.get("notes"), list) else 0
    for i, c in enumerate(corrections):
        if not isinstance(c, dict):
            problems.append(f"corrections[{i}] must be an object with field, problem, fix and based_on")
            continue
        f = str(c.get("field") or "")
        m = FIELD_RE.match(f)
        if not m:
            problems.append(f"corrections[{i}]: field {f!r} must be one of "
                            f"{', '.join(TEXT_FIELDS)} or notes[i].text")
        elif m.group(2) is not None and int(m.group(2)) >= n_notes:
            problems.append(f"corrections[{i}]: {f} does not exist (`notes` has {n_notes} item(s))")
        for k in ("problem", "fix"):
            if not str(c.get(k) or "").strip():
                problems.append(f"corrections[{i}] needs a `{k}`")
        ref = c.get("based_on")
        if ref not in (None, "", "null") and ref not in allowed_refs:
            problems.append(f"corrections[{i}]: based_on {ref!r} must be \"FACTS\", one of the notes "
                            f"you were given ({', '.join(note_ids) or 'none'}), or null")

    got = [_score(scores.get(m)) for m in METRICS if m in scores]
    if got and None not in got:
        if 0 in got and not corrections:
            problems.append("a score of 0 needs at least one correction")
        if 0 not in got and corrections:
            problems.append("corrections were given but every score is 1: set the score of each "
                            "metric a correction belongs to to 0, or remove the corrections")
    return problems


def correction_text(c: dict) -> str:
    s = f"{c.get('field')}: {str(c.get('problem')).strip()} Fix: {str(c.get('fix')).strip()}"
    ref = c.get("based_on")
    return s + (f" (see {ref})" if ref not in (None, "", "null") else "")


def _note(status: str, scores: dict | None) -> str:
    if not scores:
        return status
    return f"{status} | " + ", ".join(f"{m} {scores[m]}" for m in METRICS)


def review_prose(facts_text: str, prose: dict, *, llm=call_llm) -> ProseQAOutcome:
    """Review the Builder's prose against its own input. One call (plus one retry), never split."""
    calls: list[LLMResult] = []
    previous: dict | None = None
    problems: list[str] = []
    first_problems: list[str] = []
    note_ids = sent_note_ids(facts_text)

    first = build_messages(facts_text, prose)
    size = estimate_tokens(first) + ANSWER_BUDGET
    if size > SIZE_LIMIT:   # never expected (largest 17 Oct case ~5,050); never split, never guess
        note = (f"review too large for one call (~{size} > {SIZE_LIMIT} tokens): prose NOT reviewed by QA")
        log.warning("prose qa | %s", note)
        return ProseQAOutcome(status=QA_ERROR, note=note)

    for attempt in (1, 2):
        try:
            res = llm(AGENT, PROSE_QA_CHAIN,
                      build_messages(facts_text, prose, previous=previous, problems=problems or None),
                      expect_json=True, required_keys=REQUIRED_KEYS, max_tokens=ANSWER_BUDGET)
        except LLMCallError as exc:
            log.info("prose qa | call failed: %s", exc)
            return ProseQAOutcome(status=QA_ERROR, llm_calls=calls, failed_attempts=list(exc.attempts),
                                  output_problems=first_problems,
                                  seconds=_seconds(calls) + _seconds_attempts(exc.attempts),
                                  note="prose QA call failed: prose NOT reviewed by QA")
        calls.append(res)
        answer = copy.deepcopy(res.data)
        problems = check_prose_qa(answer, prose, note_ids)
        log.info("prose qa | attempt %d | served_by=%s | answer problems=%d",
                 attempt, res.routed_via, len(problems))
        if not problems:
            break
        if attempt == 1:
            first_problems = problems
        previous = answer
    else:
        return ProseQAOutcome(status=QA_ERROR, llm=calls[-1], llm_calls=calls, seconds=_seconds(calls),
                              output_problems=first_problems + [f"after retry: {p}" for p in problems],
                              note="prose QA answer still invalid after its retry: prose NOT reviewed by QA")

    scores = {m: _score(answer["scores"][m]) for m in METRICS}
    status = QA_REJECTED if 0 in scores.values() else QA_APPROVED
    out = ProseQAOutcome(status=status, corrections=[correction_text(c) for c in answer["corrections"]],
                         scores=scores, llm=calls[-1], llm_calls=calls, output_problems=first_problems,
                         seconds=_seconds(calls), note=_note(status, scores))
    log.info("prose qa | %s", out.note)
    return out


def _seconds(calls: list[LLMResult]) -> float:
    return round(sum(c.latency_s or 0 for c in calls), 2)


def _seconds_attempts(attempts: list[dict]) -> float:
    return round(sum((a.get("latency_s") or 0) + (a.get("waited_before_retry_s") or 0) for a in attempts), 2)
