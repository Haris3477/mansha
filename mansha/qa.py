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

Plan B (Step 7.4b): Groq's free tier allows 8,000 tokens per minute per request,
prompt and answer together. When code estimates that one review will not fit
(prompt + 3,000-token answer > SPLIT_LIMIT), it splits the review into parts:
part 1 reviews the findings (classification, origin basis, what's still needed);
the steps and notes are packed, in order, into as many further parts as needed, each
with only the records they cite (packed assuming a 2,000-token answer; since 7.6h each
part is sent with a 3,000-token answer budget, problem 83). Each part is
validated and retried like a single review; code merges them: the lowest score wins
per metric, all corrections and judgements are kept; APPROVED only if every part
approves, REJECTED if any part rejects, ERROR if a part failed and none rejected.
A paid model without this limit makes the split unnecessary (it then never triggers).

KB shield (Step 7.6g, gap G39, problem 82): a QA correction is itself a claim, and nothing
checked it. On 23 Oct QA "fixed" a correct note ("no official page names the Ministry of
Foreign Trade as issuer") into "the Ministry of Foreign Trade is identified as the issuer",
and the writer copied it. Code now checks each correction on a note or gap whose cited record
has KB notes (kb_shield): when the item keeps a qualifier that the matching KB note carries
("not defined", "no official ...", "Inference ... likely") and the fix drops every qualifier,
the correction contradicts the KB, so it is OVERRULED and never reaches the Researcher. If
every correction of a rejection is overruled, the judge gets ONE re-judge with the KB notes
shown (Haris, 23 Oct: option iii); still all overruled -> status OVERRULED (option i: the run
goes on, the phase log and a pipeline warning say QA's rejection was overruled by the KB).
"""

from __future__ import annotations

import copy
import json
import logging
import re
from dataclasses import dataclass, field

from mansha.evidence import EvidencePack
from mansha.llm_client import CHAIN_LIMITS, LLMCallError, LLMResult, call_llm
from mansha.prompts import build_system_prompt
from mansha.researcher import content_words, coverage, record_notes
from mansha.qa_evidence import (
    CODE_OWNED,
    FINDINGS_KEYS,
    checked_facts,
    item_keys,
    qa_evidence,
    research_for_qa,
)

log = logging.getLogger("mansha.qa")

QA_CHAIN = "auto:judge"
REQUIRED_KEYS = ("warnings", "corrections", "scores")
METRICS = ("factuality", "completeness", "formatting_safety")
JUDGEMENTS = ("REAL", "NOISE")

# QA statuses. APPROVED / REJECTED come from run_qa; SKIPPED is the orchestrator's
# pass-through (no QA); ERROR means QA could not review this output.
QA_APPROVED, QA_REJECTED, QA_SKIPPED, QA_ERROR = "APPROVED", "REJECTED", "SKIPPED", "ERROR"
# OVERRULED: QA rejected, but code showed every correction contradicts the KB (Step 7.6g).
QA_OVERRULED = "OVERRULED"
QA_ACCEPTS = {QA_APPROVED, QA_SKIPPED, QA_ERROR, QA_OVERRULED}  # statuses that let the pipeline go on
QA_NOT_REVIEWED = {QA_SKIPPED, QA_ERROR}

# Plan B sizes (tokens). Estimates use ~3.6 characters per token, which ran ~10% high
# against Groq's real counts on 17 Oct (windows: estimated 6,214, real 5,675).
GROQ_TPM = 8000
SPLIT_LIMIT = 7600                      # estimated prompt + answer budget must stay under this
PLAN_BUDGET = 2000                      # answer budget assumed when packing parts (planning only)
# Answer budget sent with each part (7.6h, problem 83): on Cerebras the reasoning model cut off
# at 2,000 in 4 of 8 part calls (23 Oct), and every retry at 3,000 worked. Planning still uses
# PLAN_BUDGET, so QA sees the same parts as before. If free Groq returns to `judge`, revisit
# this: Groq refuses a request whose prompt + max_tokens exceeds 8,000 (gap G11).
PART_BUDGET = 3000
MAX_PARTS = 6                           # beyond this, the review is not attempted (ERROR)
CHARS_PER_TOKEN = 3.6
# A code warning starts with the field it is about: "procedure[2]: number(s) ..."
WARNING_FIELD_RE = re.compile(r"^([a-z_]+(?:\[\d+\])?)")

# "procedure[2].step" -> ("procedure", 2); "classification" -> ("classification", None)
FIELD_RE = re.compile(r"^([a-z_]+)(?:\[(\d+)\])?(?:\.[a-z_]+)?$")

# KB shield (Step 7.6g): qualifiers a KB note can carry. The Builder's QUALIFIER_RE (7.6e) plus
# "no official ..." and "does/do not define|confirm|state|say|name"; kept separate so the
# Builder's mandatory-note rule does not change.
SHIELD_QUALIFIER_RE = re.compile(
    r"\b(?:interpretation|inference|(?:un)?likely|reportedly|unconfirmed|"
    r"not (?:confirmed|defined|verified|checked|named|stated)|no official|"
    r"(?:does|do) not (?:define|confirm|state|say|name))\b", re.IGNORECASE)
SHIELDED_FIELDS = ("caveats", "gaps")  # notes and gaps: the items that restate KB notes
# Step 7.6j: fields QA may not correct. On 24 Oct 03:59 (windows) QA said the confidence "is not supported
# by any cited evidence" and asked to remove it; the Researcher set it to null.
NO_QA_FIELDS = ("classification.confidence",)
# Step 7.6j: fields whose source_id code requires (the chosen line's record or tool result). A QA
# "cite X" for them can only break that rule: on 24 Oct 04:09 QA told the Researcher to cite the rule
# lookup for origin_result, the Researcher did, and the code check failed the run.
CODE_SOURCE_FIELDS = ("classification", "tariff", "origin_rule", "origin_result", "estimated_saving")
# Step 7.6i: an item that IS its record's KB note (each text has at least this share of the other's
# content words) cannot be "unsupported" by that record. On 24 Oct 03:49 QA rejected the
# P-IN-IMPORTER note, copied word for word, as "not in the cited record" (its fix kept
# "reportedly", so the qualifier rule above did not see it). A fix that removes the item is
# kept: a KB note can still not apply to this result (completeness rule 3), which QA may say.
VERBATIM_COVERAGE = 0.9
REMOVE_FIX_RE = re.compile(r"\b(?:remove|delete|drop|omit)\b", re.IGNORECASE)


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
    parts: list[dict] = field(default_factory=list)  # plan B: one summary per part (empty = one call)
    raw_corrections: list[dict] = field(default_factory=list)  # QA's corrections as given (kept ones)
    overruled: list[dict] = field(default_factory=list)  # corrections the KB shield overruled
    rejudged: bool = False                   # a re-judge with the KB notes was asked for


@dataclass
class Part:
    """One QA call of a review: the whole review, the findings, or some steps and notes."""
    label: str                                # e.g. "part 2/3: steps and notes"
    scope: list[str] | None                   # None (all) | ["findings", "procedure[0]", "caveats[1]", ...]
    warnings: list[tuple[str, str]]           # (W-id, warning text) for this part's fields
    max_tokens: int | None = None             # None = the chain's default (3,000)

    def fields(self) -> set[str] | None:
        """Correction fields this part may use (None = any)."""
        if self.scope is None:
            return None
        items = {k for k in self.scope if k != "findings"}
        out = set(FINDINGS_KEYS) if "findings" in self.scope else set()
        return out | items | ({"caveats", "procedure"} if items else set())


def warning_ids(warnings: list[str]) -> list[str]:
    return [f"W{i}" for i in range(1, len(warnings) + 1)]


def numbered(warnings) -> list[tuple[str, str]]:
    """Warnings as (W-id, text) pairs; accepts plain strings (numbered W1, W2, ...) or pairs."""
    warnings = list(warnings)
    if warnings and isinstance(warnings[0], tuple):
        return warnings
    return list(zip(warning_ids(warnings), warnings))


def part_header(part: Part | None) -> str:
    if part is None or part.scope is None:
        return ""
    what = []
    if "findings" in part.scope:
        what.append("the findings (classification, tariff, origin basis, follow-up questions, gaps)")
    if any(k != "findings" for k in part.scope):
        what.append("the steps and notes listed under `items`, each keyed by its field name: use that "
                    "name in corrections (for example `procedure[4].step`, `caveats[2].note`)")
    extra = ("" if "findings" in part.scope else
             " `origin_basis_for_context` is context only; it is reviewed in another part.")
    return (f"REVIEW {part.label.upper()}. The review is split into parts to fit the model's limit. "
            f"This part covers only {' and '.join(what)}; everything else is reviewed in other parts. "
            f"Score only what is shown here.{extra}\n\n")


def build_messages(intake: dict, pack: EvidencePack, research: dict, warnings, *,
                   previous: dict | None = None, problems: list[str] | None = None,
                   part: Part | None = None) -> list[dict]:
    scope = part.scope if part else None
    pairs = part.warnings if part else numbered(warnings)
    listed = "\n".join(f"{wid}: {w}" for wid, w in pairs) or "none"
    user = (part_header(part)
            + "INTAKE JSON:\n" + json.dumps(intake, ensure_ascii=False, indent=2)
            + "\n\nCHECKED BY CODE (correct; never correct these):\n" + checked_facts(research, intake, pack)
            + "\n\nCODE WARNINGS:\n" + listed
            + "\n\nEVIDENCE:\n" + qa_evidence(pack, research, scope)
            + "\n\nRESEARCHER JSON:\n"
            + json.dumps(research_for_qa(research, scope), ensure_ascii=False, indent=1))
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


def check_qa(data: dict, research: dict, warnings, allowed_ids, *,
             allowed_fields: set[str] | None = None) -> list[str]:
    """Problems in QA's own answer (empty = valid). Pure code.

    warnings: plain strings (numbered W1, W2, ...) or (W-id, text) pairs.
    allowed_fields: the fields one review part covers (plan B); None = any field.
    """
    problems: list[str] = []
    allowed = set(allowed_ids)

    scores = data.get("scores")
    if not isinstance(scores, dict) or set(scores) != set(METRICS):
        problems.append(f"`scores` must have exactly these keys: {', '.join(METRICS)}")
        scores = {}
    for m in METRICS:
        if m in scores and _score(scores[m]) is None:
            problems.append(f"scores.{m} must be 0 or 1, not {scores[m]!r}")

    ids = [wid for wid, _ in numbered(warnings)]
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
        if f in NO_QA_FIELDS:
            problems.append(f"corrections[{i}]: {f} is the Researcher's own judgement of how well the "
                            "description matches, not a claim from a record; judge the chosen tariff line "
                            "instead (factuality rule 1), and remove this correction and rescore without it")
        elif any(f == o or f.startswith(o + ".") for o in CODE_OWNED):
            problems.append(f"corrections[{i}]: {f} is checked by code against the tools and is correct "
                            "(see CHECKED BY CODE); remove this correction and rescore without it")
        elif not m or m.group(1) not in research:
            problems.append(f"corrections[{i}]: field {f!r} is not a field of the Researcher JSON")
        elif m.group(2) is not None and (not isinstance(research.get(m.group(1)), list)
                                         or int(m.group(2)) >= len(research[m.group(1)])):
            items = research.get(m.group(1))
            problems.append(f"corrections[{i}]: {f} does not exist "
                            f"({m.group(1)} has {len(items) if isinstance(items, list) else 0} item(s))")
        elif allowed_fields is not None:
            base = m.group(1) + (f"[{m.group(2)}]" if m.group(2) is not None else "")
            if base not in allowed_fields and m.group(1) not in allowed_fields:
                problems.append(f"corrections[{i}]: {f} is not in this part; correct only the fields shown")
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
    """A correction for the Researcher. The record goes in its own sentence, as a source_id to
    cite, not glued to the fix: on 23 Oct the writer copied "(see P-MOET-COO-INDIA)" into
    exporter text (Step 7.6g)."""
    s = f"{c.get('field')}: {str(c.get('problem')).strip()} Fix: {str(c.get('fix')).strip()}"
    sid = c.get("source_id")
    m = FIELD_RE.match(str(c.get("field") or ""))
    if m and m.group(1) in CODE_SOURCE_FIELDS:   # Step 7.6j: code fixes these sources; keep them
        return s + " Keep this field's source_id as it is."
    return s + (f" Cite {sid} in source_id, not in the text." if sid not in (None, "", "null") else "")


def _item(research: dict, f: str):
    """(text, source_id) of the note or gap a correction names, or None."""
    m = FIELD_RE.match(str(f or ""))
    if not m or m.group(1) not in SHIELDED_FIELDS or m.group(2) is None:
        return None
    items = research.get(m.group(1))
    i = int(m.group(2))
    if not isinstance(items, list) or i >= len(items):
        return None
    it = items[i]
    if isinstance(it, dict):
        return str(it.get("note") or it.get("text") or ""), it.get("source_id")
    return str(it or ""), None


def kb_shield(corrections: list[dict], research: dict, notes: dict[str, list[str]]) -> tuple[list, list]:
    """Split QA corrections into (kept, overruled) against the KB notes. Pure code.

    Overruled, when the corrected item is a note or gap citing a record with KB notes, and
    - "qualifier" (7.6g): its best matching note carries a qualifier; the item keeps a qualifier
      too; and the fix has none. Then the fix would turn what the KB qualifies into a plain fact
      (problem 82);
    - "verbatim" (7.6i): the item is that note almost word for word (VERBATIM_COVERAGE both
      ways), and the fix does not remove the item. A record's own note cannot be unsupported
      by it.
    Each overruled item is {**correction, "record": id, "kb_note": note, "why": rule}.
    """
    kept, overruled = [], []
    for c in corrections:
        item = _item(research, c.get("field"))
        record = item[1] if item else None
        if item and record in notes:
            text = item[0]
            fix = str(c.get("fix") or "")
            note = max(notes[record], key=lambda n: coverage(n, text))
            if (content_words(note) & content_words(text) and SHIELD_QUALIFIER_RE.search(note)
                    and SHIELD_QUALIFIER_RE.search(text) and not SHIELD_QUALIFIER_RE.search(fix)):
                overruled.append({**c, "record": record, "kb_note": note, "why": "qualifier"})
                continue
            if (coverage(text, note) >= VERBATIM_COVERAGE and coverage(note, text) >= VERBATIM_COVERAGE
                    and not REMOVE_FIX_RE.search(fix)):
                overruled.append({**c, "record": record, "kb_note": note, "why": "verbatim"})
                continue
        kept.append(c)
    return kept, overruled


def overruled_text(o: dict) -> str:
    """One line for the phase log: why code overruled this correction."""
    if o.get("why") == "verbatim":
        return (f"{o.get('field')}: fix {o.get('fix')!r} rejects text that is {o['record']}'s own KB note "
                f"{o['kb_note']!r}")
    return f"{o.get('field')}: fix {o.get('fix')!r} drops the qualifier of {o['record']}'s note {o['kb_note']!r}"


def rejudge_problems(overruled: list[dict]) -> list[str]:
    """What the judge is told when code overruled every correction of its rejection."""
    out = []
    for o in overruled:
        if o.get("why") == "verbatim":
            out.append(f"{o.get('field')}: this text is the knowledge base's own note for record {o['record']}: "
                       f"\"{o['kb_note']}\" A record's notes are part of it, so the text is supported by "
                       "its cited record. Remove this correction and rescore, unless the note does not apply "
                       "to this result")
        else:
            out.append(f"{o.get('field')}: your fix drops the qualifier the knowledge base itself states. Record "
                       f"{o['record']} has this note: \"{o['kb_note']}\" The text keeps that qualifier, so it is "
                       "supported. Remove this correction and rescore, unless something else in this field is wrong")
    return out


def estimate_tokens(messages: list[dict]) -> int:
    return int(sum(len(m["content"]) for m in messages) / CHARS_PER_TOKEN) + 1


def plan_parts(intake: dict, pack: EvidencePack, research: dict, warnings) -> list[Part]:
    """One part when the review fits Groq's limit; else the findings, then the steps and notes in
    order, packed into as few parts as fit (each prompt + PLAN_BUDGET <= SPLIT_LIMIT); each
    part is then sent with a PART_BUDGET answer budget."""
    pairs = numbered(warnings)
    whole = Part("whole review", None, pairs)
    budget = CHAIN_LIMITS[QA_CHAIN]["default"]
    if estimate_tokens(build_messages(intake, pack, research, pairs, part=whole)) + budget <= SPLIT_LIMIT:
        return [whole]

    def fits(scope: list[str]) -> bool:
        trial = Part("part 9/9", scope, pairs)  # worst case: every warning listed
        return (estimate_tokens(build_messages(intake, pack, research, pairs, part=trial))
                + PLAN_BUDGET <= SPLIT_LIMIT)

    groups: list[list[str]] = []
    for key in ["findings"] + item_keys(research):
        if groups and fits(groups[-1] + [key]):
            groups[-1].append(key)
        else:
            groups.append([key])

    def owner(text: str) -> int:
        m = WARNING_FIELD_RE.match(text)
        for i, g in enumerate(groups):
            if m and m.group(1) in g:
                return i
        return 0  # the findings part (it always comes first)

    n = len(groups)
    parts = []
    for i, scope in enumerate(groups):
        kinds = (["findings"] if "findings" in scope else []) + (
            ["steps and notes"] if any(k != "findings" for k in scope) else [])
        parts.append(Part(f"part {i + 1}/{n}: {' + '.join(kinds)}", scope,
                          [(w, t) for w, t in pairs if owner(t) == i], PART_BUDGET))
    return parts


def _review(intake: dict, pack: EvidencePack, data: dict, part: Part, llm) -> QAOutcome:
    """One QA call (with its one retry) for one part."""
    calls: list[LLMResult] = []
    previous: dict | None = None
    problems: list[str] = []
    first_problems: list[str] = []   # what the retry had to fix (kept for the phase log)
    kwargs = {"max_tokens": part.max_tokens} if part.max_tokens else {}
    notes = record_notes(pack)
    overruled: list[dict] = []
    rejudged = False
    attempt, retried = 0, False
    while True:
        attempt += 1
        try:
            res = llm("qa", QA_CHAIN, build_messages(intake, pack, data, None, previous=previous,
                                                     problems=problems or None, part=part),
                      expect_json=True, required_keys=REQUIRED_KEYS, **kwargs)
        except LLMCallError as exc:
            log.info("qa | %s | call failed: %s", part.label, exc)
            return QAOutcome(status=QA_ERROR, llm_calls=calls, failed_attempts=list(exc.attempts),
                             output_problems=first_problems,
                             note="QA call failed: output NOT reviewed by QA")
        calls.append(res)
        answer = copy.deepcopy(res.data)
        problems = check_qa(answer, data, part.warnings, pack.allowed_ids, allowed_fields=part.fields())
        log.info("qa | %s | attempt %d | served_by=%s | answer problems=%d",
                 part.label, attempt, res.routed_via, len(problems))
        if problems:
            if retried:
                return QAOutcome(status=QA_ERROR, llm=calls[-1], llm_calls=calls,
                                 output_problems=first_problems + [f"after retry: {p}" for p in problems],
                                 note="QA answer still invalid after its retry: output NOT reviewed by QA",
                                 overruled=overruled, rejudged=rejudged)
            retried, first_problems, previous = True, problems, answer
            continue
        kept, over = kb_shield(answer["corrections"], data, notes)
        rejected = 0 in [_score(answer["scores"][m]) for m in METRICS]
        if rejected and over and not kept and not rejudged:
            # Every correction contradicts the KB: one re-judge with the notes shown (option iii).
            overruled += over
            rejudged, previous, problems = True, answer, rejudge_problems(over)
            log.info("qa | %s | %d correction(s) overruled by the KB: re-judge", part.label, len(over))
            continue
        overruled += over
        break

    scores = {m: _score(answer["scores"][m]) for m in METRICS}
    by_id = dict(part.warnings)
    judgements = [{"id": j["id"], "warning": by_id.get(j["id"], ""), "judgement": j["judgement"],
                   "reason": str(j.get("reason", "")).strip()} for j in answer["warnings"]]
    if 0 not in scores.values():
        status = QA_APPROVED
    elif kept:
        status = QA_REJECTED
    else:
        status = QA_OVERRULED  # option i: still every correction contradicts the KB
    return QAOutcome(status=status, corrections=[correction_text(c) for c in kept],
                     scores=scores, llm=calls[-1], judgements=judgements, llm_calls=calls,
                     output_problems=first_problems, raw_corrections=kept, overruled=overruled,
                     rejudged=rejudged)


def _note(status: str, scores: dict | None, judgements: list[dict], n_parts: int,
          overruled: list[dict] | None = None, rejudged: bool = False) -> str:
    real = sum(j["judgement"] == "REAL" for j in judgements)
    s = status
    if scores:
        s += (f" | factuality {scores['factuality']}, completeness {scores['completeness']}, "
              f"formatting_safety {scores['formatting_safety']}")
    s += f" | code warnings judged: {len(judgements)} ({real} real)"
    if overruled:
        s += (f" | {len(overruled)} correction(s) overruled by the KB"
              + (", after a re-judge" if rejudged else ""))
    return s + (f" | {n_parts} parts" if n_parts > 1 else "")


def run_qa(intake: dict, pack: EvidencePack, research, *, llm=call_llm) -> QAOutcome:
    """Review one Researcher result (a ResearcherResult: `.data` and `.warnings`)."""
    data = research.data
    parts = plan_parts(intake, pack, data, list(research.warnings))
    if len(parts) > MAX_PARTS:
        return QAOutcome(status=QA_ERROR, note=f"review too large ({len(parts)} parts > {MAX_PARTS}): "
                                               "output NOT reviewed by QA")
    if len(parts) == 1:
        q = _review(intake, pack, data, parts[0], llm)
        if q.status != QA_ERROR:
            q.note = _note(q.status, q.scores, q.judgements, 1, q.overruled, q.rejudged)
        log.info("qa | %s", q.note)
        return q

    results = [_review(intake, pack, data, p, llm) for p in parts]
    done = [r for r in results if r.status != QA_ERROR]
    calls = [c for r in results for c in r.llm_calls]
    summaries = [{"label": p.label, "status": r.status, "scores": r.scores,
                  "served_by": r.llm.routed_via if r.llm else None,
                  "seconds": round(sum(c.latency_s or 0 for c in r.llm_calls), 2),
                  "scope": p.scope,
                  "warnings": [w for w, _ in p.warnings], "note": r.note}
                 for p, r in zip(parts, results)]
    scores = ({m: min(r.scores[m] for r in done) for m in METRICS} if done else None)
    judgements = [j for r in results for j in r.judgements]
    overruled = [o for r in results for o in r.overruled]
    rejudged = any(r.rejudged for r in results)
    if any(r.status == QA_REJECTED for r in results):
        status = QA_REJECTED
    elif any(r.status == QA_ERROR for r in results):
        status = QA_ERROR
    elif any(r.status == QA_OVERRULED for r in results):
        status = QA_OVERRULED
    else:
        status = QA_APPROVED
    if status == QA_ERROR:
        failed = ", ".join(p.label.split(":")[0] for p, r in zip(parts, results) if r.status == QA_ERROR)
        note = f"QA {failed} failed: output NOT reviewed by QA in full ({len(parts)} parts)"
    else:
        note = _note(status, scores, judgements, len(parts), overruled, rejudged)
    log.info("qa | %s", note)
    return QAOutcome(
        status=status, corrections=[c for r in results for c in r.corrections], scores=scores,
        llm=next((r.llm for r in reversed(results) if r.llm), None), note=note,
        judgements=judgements, llm_calls=calls,
        failed_attempts=[a for r in results for a in r.failed_attempts],
        output_problems=[f"{p.label}: {x}" for p, r in zip(parts, results) for x in r.output_problems],
        parts=summaries, raw_corrections=[c for r in results for c in r.raw_corrections],
        overruled=overruled, rejudged=rejudged)
