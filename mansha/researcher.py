"""Researcher Agent (Step 6.3): evidence in, cited findings out, then code checks.

The LLM picks the tariff line and explains the tool results. Code then checks
everything that can be checked mechanically:
- hard problems (certain errors) -> corrections, using the single revision
- warnings (numbers not found in the cited record) -> passed to QA to judge
Code, not the LLM, sets the final `verdict` and each procedure step's
`authority` (copied from the cited record's `actor`, Step 6.4g). Code also drops
`gaps` items that repeat a caveat (Step 9.6e, problem 52), removes square brackets around
evidence IDs in `source_id` (Step 7.6c, problem 75) and, when the verdict is NOT_ELIGIBLE or
NO_PREFERENCE, empties `follow_up_questions` (Step 7.6c, problem 74) and drops the caveats
about claiming the CEPA rate (Step 7.6d, problem 76); each change is recorded in `changes`.

Gaps carry a source (Step 7.6g, gap G39, problems 81-82): each `gaps` item is
{text, source_id}, where source_id is the record that shows the gap or null when no record
covers it. A gap that cites a passage with KB notes is a note, not something the user can
supply, so code moves it into `caveats` (move_note_gaps); the prompt already said so, and
on 23 Oct the model put three KB notes into `gaps`, where QA could not see their record and
called them unsupported. Plain-string gaps (the old format) are read as source null.
A gap citing the origin tool (INSUFFICIENT_DATA) or the duty tool (NEEDS_VALUE) asks for data the
user must supply, which the follow-up questions already ask for, so code drops it (Step 7.6h,
problem 85, drop_user_data_gaps).
"""

from __future__ import annotations

import copy
import json
import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from mansha.evidence import HEADER_RE, EvidencePack
from mansha.kb import load_corridor
from mansha.llm_client import LLMResult, call_llm
from mansha.prompts import build_system_prompt

log = logging.getLogger("mansha.researcher")

GAP = "REGULATORY_GAP_DETECTED"
REQUIRED_KEYS = (
    "reasoning", "classification", "tariff", "origin_rule", "origin_result",
    "estimated_saving", "procedure", "caveats", "follow_up_questions", "gaps",
)
OBJECT_KEYS = ("classification", "tariff", "origin_rule", "origin_result", "estimated_saving")
LIST_KEYS = ("reasoning", "procedure", "caveats", "follow_up_questions", "gaps")

ORIGIN_MAP = {
    "MEETS": "QUALIFIES",
    "FAILS": "DOES_NOT_QUALIFY",
    "INSUFFICIENT_DATA": "NEEDS_MORE_DATA",
    "RULE_GAP": GAP,
}
VERDICT_MAP = {
    "QUALIFIES": "ELIGIBLE",
    "DOES_NOT_QUALIFY": "NOT_ELIGIBLE",
    "NEEDS_MORE_DATA": "NEEDS_MORE_DATA",
    "NOT_APPLICABLE": "NO_PREFERENCE",
    GAP: GAP,
}
PROCEDURE_STATUSES = {"QUALIFIES", "NEEDS_MORE_DATA"}
# UAE is always the exporting side, so every corridor's KB has this passage.
ISSUER_PASSAGE_ID = "P-UAE-ISSUER"
# Tool records a procedure step may cite besides P-... passages.
PROCEDURE_TOOL_IDS = {"TOOL:coo_fee"}
# Evidence IDs: allowed in `source_id` fields only, never in text the exporter reads.
EVIDENCE_ID_RE = re.compile(r"\b(?:TL|EXC|PSR)-[A-Z0-9]|\bP-[A-Z]|TOOL:")
INTERNAL_WORD_RE = re.compile(r"\bintake\b", re.IGNORECASE)   # Mansha's own pipeline words
# Step 7.6j: raw tool names (snake_case, e.g. "final_manufacture_in_uae: PASS") copied from the EVIDENCE
# into text the exporter reads. On 24 Oct 03:59 (windows) QA missed them in round 1 and caught them in
# round 2, after the one revision was spent. Plain English never has an underscore inside a word.
RAW_NAME_RE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
# Step 7.6j: the origin calculator's check names, written in plain words by code (the same words as the
# Builder's TERMS). They reached `origin_result.basis` in 8 of 71 saved Researcher answers (17-24 Oct).
CHECK_NAME_WORDS = {"final_manufacture_in_uae": "final manufacture check",
                    "minimal_operations": "minimal operations check"}
# Step 7.6j: the classification's confidence is one of these (or the gap marker with the line).
CONFIDENCE_VALUES = ("high", "medium", "low")


@dataclass
class ResearcherResult:
    data: dict                      # LLM JSON + code-added "verdict" and step authorities
    problems: list[str]             # hard failures -> corrections
    warnings: list[str] = field(default_factory=list)  # for QA to judge
    llm: LLMResult | None = None
    changes: list[str] = field(default_factory=list)   # what code changed in the model's JSON

    @property
    def passed(self) -> bool:
        return not self.problems


# ---------- small helpers ----------

def digits(s) -> str:
    return re.sub(r"\D", "", str(s or ""))


def split_records(text: str) -> dict[str, str]:
    """EVIDENCE text -> {ID: that record's text}."""
    matches = list(HEADER_RE.finditer(text))
    out = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[m.group(1)] = text[m.start():end]
    return out


NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)*")
THOUSANDS_RE = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?")


def _norm_number(t: str) -> str:
    if t.count(".") <= 1:
        try:
            return format(Decimal(t).normalize(), "f")  # "10000.00" -> "10000", "49.0" -> "49"
        except InvalidOperation:
            return t
    return t  # article numbers like "3.5.1" are compared as text


def number_keys(text: str) -> set[str]:
    """All numbers in a text, normalized so '10,000.00' == '10000' and '49.0' == '49'."""
    keys = set()
    for t in NUM_RE.findall(text or ""):
        t = t.rstrip(",")
        if THOUSANDS_RE.fullmatch(t):
            keys.add(_norm_number(t.replace(",", "")))
        elif "," in t:  # a list like "84,85"
            keys.update(_norm_number(p) for p in t.split(",") if p)
        else:
            keys.add(_norm_number(t))
    return keys


# List numbering the model adds to its own text: "(3)" anywhere, "3." or "3)" at a line start.
# Not facts, so the number check ignores them (17 Oct chargers: "(3)", "(4)" gave a false warning).
LIST_MARKER_RE = re.compile(r"\(\d{1,2}\)|^[ \t]*\d{1,2}[.)](?=\s)", re.MULTILINE)


def strip_list_markers(text: str) -> str:
    return LIST_MARKER_RE.sub(" ", text or "")


def as_decimal(x) -> Decimal | None:
    try:
        return Decimal(str(x).replace(",", ""))
    except (InvalidOperation, ValueError):
        return None


# ---------- what the answer must be, from the tools ----------

def find_chosen(data: dict, pack: EvidencePack) -> tuple[dict | None, list[str]]:
    """Return (chosen candidate or None, problems). None with no problems = declared gap."""
    cls = data["classification"]
    if str(cls.get("tariff_line", "")).strip() == GAP:
        return None, []
    by_id = {c["id"]: c for c in pack.candidates}
    line = digits(cls.get("tariff_line"))
    sid = cls.get("source_id")
    if sid in by_id:
        c = by_id[sid]
        if c.get("tariff_line") and line != c["tariff_line"]:
            msg = (f"classification.tariff_line {cls.get('tariff_line')!r} does not match "
                   f"its source {sid} (line {c['tariff_line']})")
            return c, [msg]
        return c, []
    for c in pack.candidates:
        if c.get("tariff_line") == line or (
                c.get("kind") == "heading_exclusion" and line == digits(c.get("heading"))):
            return c, []
    ids = ", ".join(c["id"] for c in pack.candidates) or "none"
    msg = (f"classification.tariff_line {cls.get('tariff_line')!r} is not one of the "
           f"candidates ({ids}); choose a candidate or write {GAP}")
    return None, [msg]


def expected_origin(c: dict | None, pack: EvidencePack) -> str:
    if c is None:
        return GAP
    if c["id"] in pack.excluded_ids:
        return "NOT_APPLICABLE"
    o = pack.tool_results.get(f"TOOL:origin:{c.get('tariff_line')}")
    return ORIGIN_MAP.get(o.get("status"), GAP) if o else GAP


def expected_saving(c: dict | None, origin: str, pack: EvidencePack) -> tuple[str, dict | None]:
    if c is None:
        return GAP, None
    duty = pack.tool_results.get(f"TOOL:duty:{c.get('tariff_line')}")
    if c["id"] in pack.excluded_ids:
        return "NO_PREFERENCE", duty
    if origin == "DOES_NOT_QUALIFY":
        return "NOT_APPLICABLE", duty
    if duty is None:
        return GAP, None
    status = duty.get("status")
    if status == "ESTIMATED":
        return "ESTIMATED", duty
    if status in ("NO_PREFERENCE", "NEEDS_VALUE"):
        return status, duty
    return GAP, duty


# ---------- code-filled fields ----------

def fill_authorities(data: dict, pack: EvidencePack) -> None:
    """Set each procedure step's `authority` from its cited record's actor.

    Any authority the model wrote is overwritten. A record with no actor gives
    REGULATORY_GAP_DETECTED: code never guesses who acts.
    """
    steps = data.get("procedure")
    if not isinstance(steps, list):
        return
    for step in steps:
        if isinstance(step, dict):
            step["authority"] = pack.actors.get(step.get("source_id"), GAP)


def fill_tariff_line(data: dict, pack: EvidencePack) -> None:
    """Write `classification.tariff_line` as the cited record's 8 digits (Step 9.5b).

    The model sometimes copies the record ID ("TL-IN-85044030") or the display form
    ("39239090 (3923 90 90)"). Code fixes the format only when the cited record is a
    candidate line whose 8 digits appear in what the model wrote; a different line is
    left for check_researcher to report.
    """
    cls = data.get("classification")
    if not isinstance(cls, dict):
        return
    cand = next((c for c in pack.candidates if c["id"] == cls.get("source_id")), None)
    line = (cand or {}).get("tariff_line")
    if line and str(cls.get("tariff_line", "")).strip() != GAP and line in digits(cls.get("tariff_line")):
        cls["tariff_line"] = line


def fill_fixed_notes(data: dict, pack: EvidencePack) -> list[str]:
    """Write each caveat citing a fixed-note passage as that passage's KB note (Step 7.6f).

    The issuer note is printed verbatim in ELIGIBLE / NEEDS_MORE_DATA reports, so a
    reworded copy is unsafe: on 19 Oct the model wrote "doit.gov.ae" for moet.gov.ae
    twice (problem 79). The model still has to cite the passage (check_researcher);
    code only replaces the text. Returns what changed, for the phase log.
    """
    changes: list[str] = []
    caveats = data.get("caveats")
    if not isinstance(caveats, list):
        return changes
    for i, cv in enumerate(caveats):
        if not isinstance(cv, dict):
            continue
        sid = cv.get("source_id")
        kb_note = pack.fixed_notes.get(sid)
        if kb_note and cv.get("note") != kb_note:
            cv["note"] = kb_note
            changes.append(f"caveats[{i}]: note written from the KB ({sid})")
    return changes


def _same_text(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip().rstrip(".").lower()


def gap_text(g) -> str:
    """A gap's text: `gaps` items are {text, source_id} since Step 7.6g (plain strings before)."""
    return str(g.get("text") or "") if isinstance(g, dict) else str(g or "")


def normalize_gaps(data: dict) -> list[str]:
    """Read plain-string gaps (the old format) as {text, source_id: null}; return what changed."""
    gaps = data.get("gaps")
    if not isinstance(gaps, list):
        return []
    plain = [i for i, g in enumerate(gaps) if isinstance(g, str)]
    for i in plain:
        gaps[i] = {"text": gaps[i], "source_id": None}
    if not plain:
        return []
    return [f"gaps: {len(plain)} plain-text item(s) given without a source_id, read as source null "
            f"({', '.join(f'gaps[{i}]' for i in plain)})"]


NOTE_STOPWORDS = frozenset(
    "the a an of and or to in on for is are be by it its this that with as at from not no any which "
    "was were has have does do".split())


def content_words(text) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", str(text or "").lower()) if w not in NOTE_STOPWORDS}


def coverage(of, by) -> float:
    """Share of `of`'s content words that `by` also has (0..1). Used to pair a text with a KB note."""
    a = content_words(of)
    return len(a & content_words(by)) / len(a) if a else 0.0


NOTES_HEADER = "notes:"


def record_notes(pack: EvidencePack) -> dict[str, list[str]]:
    """{evidence ID: that record's `notes:` items, verbatim} from the EVIDENCE text."""
    out: dict[str, list[str]] = {}
    for rid, block in split_records(pack.text).items():
        notes, inside = [], False
        for line in block.splitlines():
            if line.strip() == NOTES_HEADER:
                inside = True
            elif inside and line.startswith("- "):
                notes.append(line[2:].strip())
            elif inside and line.strip() and not line.startswith(" "):
                inside = False
        if notes:
            out[rid] = notes
    return out


# A moved gap whose words are this much inside a caveat with the same source is that caveat again.
SAME_NOTE_COVERAGE = 0.6


def move_note_gaps(data: dict, pack: EvidencePack) -> list[str]:
    """Move `gaps` items that cite a passage with KB notes into `caveats` (Step 7.6g, G39).

    Problems 81-82 (23 Oct, windows_nodata): the model put KB notes ("'direct labour cost' is not
    defined", "no official page names the Ministry of Foreign Trade as issuer", the free-zone
    inference) into `gaps` as plain strings. QA could not see their record, called them
    unsupported, and its "fix" (MoFT confirmed as issuer) was copied by the writer. A gap whose
    cited passage has notes is a note: it goes to `caveats` with that source, where QA reads it
    beside its record. A copy of a caveat with the same source (or of the fixed issuer note) is
    dropped instead. Gaps citing a tool result (e.g. a missing value) or no record stay gaps.
    """
    gaps, caveats = data.get("gaps"), data.get("caveats")
    if not isinstance(gaps, list) or not isinstance(caveats, list):
        return []
    notes = record_notes(pack)
    keep, changes = [], []
    for i, g in enumerate(gaps):
        sid = g.get("source_id") if isinstance(g, dict) else None
        if not (isinstance(sid, str) and sid.startswith("P-") and sid in pack.allowed_ids and sid in notes):
            keep.append(g)
            continue
        same = [c for c in caveats if isinstance(c, dict) and c.get("source_id") == sid]
        if (sid in pack.fixed_notes and same) or any(
                coverage(gap_text(g), c.get("note")) >= SAME_NOTE_COVERAGE for c in same):
            changes.append(f"gaps[{i}]: dropped, already a note from {sid}: {gap_text(g)!r}")
            continue
        caveats.append({"note": gap_text(g), "source_id": sid})
        changes.append(f"gaps[{i}]: moved to caveats[{len(caveats) - 1}], a KB note from {sid}: {gap_text(g)!r}")
    data["gaps"] = keep
    return changes


# A gap citing one of these tool results with this status is data the user must supply (7.6h).
USER_DATA_TOOL_STATUS = {"TOOL:origin:": "INSUFFICIENT_DATA", "TOOL:duty:": "NEEDS_VALUE"}


def drop_user_data_gaps(data: dict, pack: EvidencePack) -> list[str]:
    """Drop `gaps` items that ask for data the user must supply (Step 7.6h, problem 85).

    On 23 Oct 20:08 (windows_nodata) "What's still needed" asked twice for the same things: the
    follow-up questions asked for a bill of materials and the shipment value, and two gaps citing
    `TOOL:origin:<line>` (INSUFFICIENT_DATA) and `TOOL:duty:<line>` (NEEDS_VALUE) said they were
    missing. For those statuses check 7 already requires follow-up questions, so such a gap only
    repeats them. A gap citing the origin tool with RULE_GAP, or the duty tool with
    REGULATORY_GAP_DETECTED, is a gap in Mansha's data and stays.
    """
    gaps = data.get("gaps")
    if not isinstance(gaps, list):
        return []
    keep, changes = [], []
    for i, g in enumerate(gaps):
        sid = g.get("source_id") if isinstance(g, dict) else None
        tool = pack.tool_results.get(sid) if isinstance(sid, str) else None
        want = next((st for pre, st in USER_DATA_TOOL_STATUS.items()
                     if isinstance(sid, str) and sid.startswith(pre)), None)
        if tool is not None and want and tool.get("status") == want:
            changes.append(f"gaps[{i}]: dropped, data the user must supply ({sid} {want}; "
                           f"asked in follow_up_questions): {gap_text(g)!r}")
            continue
        keep.append(g)
    data["gaps"] = keep
    return changes


def plain_check_names(data: dict) -> list[str]:
    """Write the origin calculator's check names in plain words in exporter text (Step 7.6j).

    "final_manufacture_in_uae: PASS - ..." -> "final manufacture check: PASS - ...". A fixed
    mapping, so code does it instead of spending the revision; any other raw name is a problem
    in check_researcher (RAW_NAME_RE).
    """
    changes: list[str] = []

    def fix(where: str, text):
        if not isinstance(text, str):
            return text
        new = text
        for raw, words in CHECK_NAME_WORDS.items():
            new = re.sub(rf"\b{raw}\b", words, new)
        if new != text:
            changes.append(f"{where}: check names written in plain words")
        return new

    res = data.get("origin_result")
    if isinstance(res, dict):
        res["basis"] = fix("origin_result.basis", res.get("basis"))
    for k, key in (("procedure", "step"), ("caveats", "note"), ("gaps", "text")):
        for i, item in enumerate(data.get(k) if isinstance(data.get(k), list) else []):
            if isinstance(item, dict):
                item[key] = fix(f"{k}[{i}].{key}", item.get(key))
    qs = data.get("follow_up_questions")
    if isinstance(qs, list):
        data["follow_up_questions"] = [fix(f"follow_up_questions[{i}]", q) for i, q in enumerate(qs)]
    return changes


# ---------- qualifiers kept (Step 7.8, G35) ----------
# What marks a record sentence (summary sentence or KB note) as less than a plain fact. Same words as
# qa.SHIELD_QUALIFIER_RE (kept separate: qa imports this module).
SOURCE_QUALIFIER_RE = re.compile(
    r"\b(?:interpretation|inference|(?:un)?likely|reportedly|unconfirmed|"
    r"not (?:confirmed|defined|verified|checked|named|stated)|no official|secondary (?:sources?|reports?)|"
    r"(?:does|do) not (?:define|confirm|state|say|name))\b", re.IGNORECASE)
# What counts as that qualifier kept in the Researcher's text: the same words plus the ways the model
# rewords them ("has not been checked", "does not specify", "Mansha's interpretation", "secondary sources").
# "may" is left out on purpose, as in document_builder.QUALIFIER_RE.
KEPT_QUALIFIER_RE = re.compile(
    r"\b(?:interpret\w*|inference|inferred|(?:un)?likely|probably|reportedly|unconfirmed|"
    r"unclear|uncertain|"
    r"secondary (?:sources?|reports?)|no official|"
    r"not (?:been |yet )?(?:confirmed|defined|verified|checked|named|stated|specified)|"
    r"(?:does|do|did) not (?:define|confirm|state|say|name|specify|address|mention))\b", re.IGNORECASE)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.;])\s+(?=[A-Z(\"'])")
CLAUSE_SPLIT_RE = re.compile(r"(?<=[.;])\s+|,\s+and\s+")   # the Researcher's text, cut into sentences and clauses
SUMMARY_HEADER = "summary:"
# A text restates a record sentence when it has this share of the sentence's content words
# (qualifier words left out, so a copy without them still matches).
QUALIFIED_MATCH = 0.6
# A clause of the Researcher's text restates a qualified sentence when this share of its words comes from it.
RESTATING_CLAUSE = 0.5


def record_sentences(pack: EvidencePack) -> dict[str, list[tuple[str, str]]]:
    """{evidence ID: [(kind, sentence)]}: the record's summary sentences ("summary") and KB notes ("note")."""
    notes = record_notes(pack)
    out: dict[str, list[tuple[str, str]]] = {}
    for rid, block in split_records(pack.text).items():
        units = []
        for line in block.splitlines():
            if line.startswith(SUMMARY_HEADER):
                units += [("summary", x.strip()) for x in
                          SENTENCE_SPLIT_RE.split(line[len(SUMMARY_HEADER):].strip()) if x.strip()]
        units += [("note", n) for n in notes.get(rid, [])]
        if units:
            out[rid] = units
    return out


def qualifier_drops(text, units: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """The qualified record sentences that `text` restates without a qualifier (Step 7.8).

    `text` is cut into sentences and clauses. A qualified sentence (its qualifier words left out) is
    restated when `text` has >= QUALIFIED_MATCH of its content words; a clause restates it when at least
    RESTATING_CLAUSE of the clause's words come from it and fewer come from any unqualified sentence of
    the same record (a clause the record also states plainly is supported as written). It is a drop when
    some clause restates it and none of those clauses keeps a qualifier.
    """
    if not isinstance(text, str) or not text.strip() or not units:
        return []
    clauses = [x for x in CLAUSE_SPLIT_RE.split(text) if x.strip()]
    plain = [u for _, u in units if not SOURCE_QUALIFIER_RE.search(u)]
    drops = []
    for kind, u in units:
        if not SOURCE_QUALIFIER_RE.search(u):
            continue
        core = SOURCE_QUALIFIER_RE.sub(" ", u)
        if coverage(core, text) < QUALIFIED_MATCH:
            continue
        restating = [c for c in clauses if coverage(c, core) >= RESTATING_CLAUSE
                     and coverage(c, core) > max((coverage(c, p) for p in plain), default=0.0)]
        if restating and not any(KEPT_QUALIFIER_RE.search(c) for c in restating):
            drops.append((kind, u))
    return drops


def restore_qualified_notes(data: dict, pack: EvidencePack) -> list[str]:
    """Write a caveat that dropped its KB note's qualifier as that note, word for word (Step 7.8, G35).

    Seen in most saved runs (16-24 Oct): "Interpretation: de minimis helps only the tariff-shift part
    ..." came back as "The de minimis tolerance helps only ...", and "Inference: SWS is charged on the
    reduced BCD" lost "Inference:" (problem 71; 24 Oct 15:58). QA approved these almost every time, so
    code restores the note instead of spending the revision. Several notes in one caveat are written
    in KB order. Fixed notes (fill_fixed_notes) and summary sentences are left to check_researcher.
    """
    changes: list[str] = []
    caveats = data.get("caveats")
    if not isinstance(caveats, list):
        return changes
    sents = record_sentences(pack)
    for i, cv in enumerate(caveats):
        if not isinstance(cv, dict):
            continue
        sid = cv.get("source_id")
        if not isinstance(sid, str) or sid in pack.fixed_notes:
            continue
        notes = [u for kind, u in qualifier_drops(cv.get("note"), sents.get(sid, [])) if kind == "note"]
        # Only a caveat that is those notes and nothing more (each of its clauses restates one of them)
        # is rewritten; one that also says other things is left to check_researcher, so nothing is lost.
        cores = [SOURCE_QUALIFIER_RE.sub(" ", n) for n in notes]
        if notes and all(any(coverage(c, core) >= RESTATING_CLAUSE for core in cores)
                         for c in CLAUSE_SPLIT_RE.split(cv.get("note")) if c.strip()):
            cv["note"] = " ".join(notes)
            changes.append(f"caveats[{i}]: note written from the KB, qualifier kept ({sid})")
    return changes


def drop_caveat_gaps(data: dict) -> list[str]:
    """Remove `gaps` items that repeat a caveat's text; return what was removed (Step 9.6e).

    Problem 52 (17 Oct): a Researcher copied four caveats word for word into `gaps`. `gaps` has
    no source, so the Builder's by-source filter (claim notes dropped when no CEPA rate applies)
    could not see them, and they reached "What's still needed" in a not-eligible report. The
    caveat itself stays (and is filtered by its source); only the copy goes.
    """
    gaps, caveats = data.get("gaps"), data.get("caveats")
    if not isinstance(gaps, list) or not isinstance(caveats, list):
        return []
    notes = {_same_text(c.get("note")) for c in caveats if isinstance(c, dict)}
    keep = [g for g in gaps if _same_text(gap_text(g)) not in notes]
    removed = [g for g in gaps if _same_text(gap_text(g)) in notes]
    data["gaps"] = keep
    return [f"gaps: dropped a copy of a caveat: {gap_text(g)!r}" for g in removed]


BRACKETED_ID_RE = re.compile(r"\s*\[\s*([^\[\]]+?)\s*\]\s*")

# Verdicts where no CEPA rate can apply on what the user gave (not eligible, excluded line):
# no follow-up questions (problem 74) and no notes about claiming the rate (problem 76).
NO_CEPA_RATE_VERDICTS = {"NOT_ELIGIBLE", "NO_PREFERENCE"}
CLAIM_PASSAGE_KINDS = {"duty", "procedure", "authority"}   # passage kinds about claiming the CEPA rate
CLAIM_TOOL_PREFIXES = ("TOOL:duty:", "TOOL:coo_fee")        # duty saving, certificate fee


def claim_source_ids(corridor: str = "india") -> set[str]:
    """IDs of the corridor's passages about claiming the CEPA rate (duty, procedure, authority)."""
    return {p["id"] for p in load_corridor(corridor)["passages"]["passages"]
            if p.get("kind") in CLAIM_PASSAGE_KINDS}


def is_claim_note(source_id, claim_ids: set[str]) -> bool:
    """A note is about claiming the CEPA rate if it cites the duty or fee tool or a claim passage.

    Matched by source, not wording, because the Researcher paraphrases notes (Steps 9.5b-c).
    Shared by the Researcher (drop_claim_caveats, before QA) and the Document Builder (build_notes).
    """
    return str(source_id).startswith(CLAIM_TOOL_PREFIXES) or source_id in claim_ids


def unbracket_ids(data: dict, pack: EvidencePack) -> list[str]:
    """Write a `source_id` "[X]" as "X" when X is an evidence ID; return what changed (Step 7.6c).

    Problem 75 (19 Oct, chargers, Dots3): the model copied the evidence headers' brackets into
    every `source_id` ("[TL-IN-85044030]"): 22 code problems that used up the single revision,
    which QA's real corrections then had to share. Only the format is fixed: an ID that is not
    in the evidence keeps its brackets and is reported by check_researcher.
    """
    fixed: list[str] = []

    def fix(where: str, obj) -> None:
        sid = obj.get("source_id") if isinstance(obj, dict) else None
        m = BRACKETED_ID_RE.fullmatch(sid) if isinstance(sid, str) else None
        if m and m.group(1) in pack.allowed_ids:
            obj["source_id"] = m.group(1)
            fixed.append(where)

    for k in OBJECT_KEYS:
        fix(k, data.get(k))
    for k in ("procedure", "caveats", "gaps"):
        items = data.get(k)
        for i, item in enumerate(items if isinstance(items, list) else []):
            fix(f"{k}[{i}]", item)
    if not fixed:
        return []
    return [f"source_id: square brackets removed around {len(fixed)} evidence ID(s) ({', '.join(fixed)})"]


def drop_follow_ups(data: dict, verdict: str) -> list[str]:
    """Empty `follow_up_questions` for NOT_ELIGIBLE / NO_PREFERENCE; return what went (Step 7.6c).

    Problem 74 (19 Oct, chargers): a not-eligible report asked for the UAE operations, the
    place of final manufacture and the FOB/CIF values, all already given, as if another
    answer could change the result (a nudge to change a declaration). QA rejected one such
    question in round 1 and approved the rest in round 2. Follow-up questions belong to
    NEEDS_MORE_DATA and NEEDS_VALUE; the "confirm the code" advice is in the Builder's
    classification text. `gaps` are left alone.
    """
    qs = data.get("follow_up_questions")
    if verdict not in NO_CEPA_RATE_VERDICTS or not isinstance(qs, list) or not qs:
        return []
    data["follow_up_questions"] = []
    return [f"follow_up_questions: dropped for verdict {verdict} (the result does not depend on "
            f"more information from the user): {q!r}" for q in qs]


def drop_claim_caveats(data: dict, verdict: str, corridor: str = "india") -> list[str]:
    """Drop caveats about claiming the CEPA rate for NOT_ELIGIBLE / NO_PREFERENCE (Step 7.6d).

    Problem 76 (19 Oct, chargers, Dots3): a not-eligible answer carried 17 caveats, among them
    the certificate issuer, fee, factory registration and importer steps. The Builder never
    shows those notes for this verdict (build_notes, same rule), but QA reviewed them all: the
    review split into 2 parts, and an invented website in the hidden issuer note ("doit.gov.ae")
    was rejected twice; the Researcher returned the same JSON, so the run ended CHECKS_FAILED
    over text the exporter would never have read. Dropping them here makes QA judge what the
    report shows. Other caveats (origin, tariff line, origin-rule passages) stay.
    """
    caveats = data.get("caveats")
    if verdict not in NO_CEPA_RATE_VERDICTS or not isinstance(caveats, list):
        return []
    claim_ids = claim_source_ids(corridor)
    keep = [c for c in caveats if not (isinstance(c, dict) and is_claim_note(c.get("source_id"), claim_ids))]
    gone = [c for c in caveats if c not in keep]
    data["caveats"] = keep
    return [f"caveats: dropped a note about claiming the CEPA rate for verdict {verdict} "
            f"({c.get('source_id')}): {c.get('note')!r}" for c in gone]


# ---------- the checks ----------

def check_researcher(data: dict, pack: EvidencePack) -> tuple[list[str], list[str], str]:
    """Return (problems, warnings, verdict). Pure code; no LLM."""
    problems: list[str] = []
    warnings: list[str] = []

    # 1. Shape
    for k in OBJECT_KEYS:
        if not isinstance(data.get(k), dict):
            problems.append(f"`{k}` must be a JSON object")
    for k in LIST_KEYS:
        if not isinstance(data.get(k), list):
            problems.append(f"`{k}` must be a JSON list")
    if problems:
        return problems, warnings, GAP
    for k in ("procedure", "caveats"):
        for i, item in enumerate(data[k]):
            if not isinstance(item, dict):
                problems.append(f"`{k}[{i}]` must be an object with a source_id")
    for i, g in enumerate(data["gaps"]):
        if not isinstance(g, dict) or not gap_text(g).strip():
            problems.append(f"`gaps[{i}]` must be an object with a `text` and a `source_id` (null when no "
                            "record covers the gap)")
    if problems:
        return problems, warnings, GAP

    # 1b. Text the exporter reads (report, or code-only fallback) has no IDs or internal words
    shown = [("origin_result.basis", data["origin_result"].get("basis"))]
    shown += [(f"procedure[{i}].step", s.get("step")) for i, s in enumerate(data["procedure"])]
    shown += [(f"caveats[{i}].note", c.get("note")) for i, c in enumerate(data["caveats"])]
    shown += [(f"follow_up_questions[{i}]", q) for i, q in enumerate(data["follow_up_questions"])]
    shown += [(f"gaps[{i}].text", gap_text(g)) for i, g in enumerate(data["gaps"])]
    for where, text in shown:
        text = str(text or "")
        found = EVIDENCE_ID_RE.search(text) or INTERNAL_WORD_RE.search(text)
        if found:
            span = text[found.start():found.start() + 25].split()[0]
            problems.append(f"{where} contains {span!r}: this text is shown to the exporter, so write it in "
                            "plain words without evidence IDs or internal words (cite only in source_id)")
        raw = RAW_NAME_RE.search(text)
        if raw and not found:
            problems.append(f"{where} contains the internal name {raw.group(0)!r}: this text is shown to the "
                            "exporter, so describe the check in plain words (e.g. 'final manufacture took "
                            "place in the UAE'), never with tool field names")

    # 1c. Confidence is high, medium or low (Step 7.6j: on 24 Oct 03:59 a QA correction made it null)
    cls = data["classification"]
    conf = str(cls.get("confidence") or "").strip().lower()
    if str(cls.get("tariff_line", "")).strip() != GAP and conf not in CONFIDENCE_VALUES:
        problems.append(f"classification.confidence must be one of {', '.join(CONFIDENCE_VALUES)} "
                        f"(got {cls.get('confidence')!r}): judge it from how well the description matches")

    # 2. Every source_id is an ID in the evidence
    allowed = set(pack.allowed_ids)
    cited = [(k, data[k].get("source_id")) for k in OBJECT_KEYS]
    cited += [(f"procedure[{i}]", s.get("source_id")) for i, s in enumerate(data["procedure"])]
    cited += [(f"caveats[{i}]", s.get("source_id")) for i, s in enumerate(data["caveats"])]
    for where, sid in cited:
        if sid not in allowed:
            problems.append(f"{where}.source_id {sid!r} is not an ID in the evidence")
    for i, g in enumerate(data["gaps"]):
        sid = g.get("source_id")
        if sid not in (None, "", "null") and sid not in allowed:
            problems.append(f"gaps[{i}].source_id {sid!r} is not an ID in the evidence "
                            "(use null when no record covers the gap)")

    # 3. Classification is a candidate (or a declared gap)
    chosen, cls_problems = find_chosen(data, pack)
    problems += cls_problems
    excluded = chosen is not None and chosen["id"] in pack.excluded_ids
    line = chosen.get("tariff_line") if chosen else None

    # 4. Preference and origin status follow the tools for the chosen line
    origin_exp = expected_origin(chosen, pack)
    origin_got = data["origin_result"].get("status")
    if origin_got != origin_exp:
        why = ("the chosen line is excluded from CEPA preference" if excluded
               else f"TOOL:origin:{line} maps to {origin_exp}" if line
               else "no tariff line was chosen")
        problems.append(f"origin_result.status is {origin_got!r} but must be {origin_exp!r} ({why})")
    if line and not excluded and data["origin_result"].get("source_id") != f"TOOL:origin:{line}":
        problems.append(f"origin_result.source_id must be TOOL:origin:{line} (the chosen line's result)")
    if excluded and str(data["tariff"].get("preferential_rate", "")).strip() != "EXCLUDED":
        problems.append("the chosen line is excluded, so tariff.preferential_rate must be \"EXCLUDED\"")

    rl = pack.tool_results.get(f"TOOL:rule_lookup:{line}") if line and not excluded else None
    rule_ids = [r["id"] for r in (rl or {}).get("rules", [])]
    if rule_ids and data["origin_rule"].get("source_id") not in rule_ids:
        problems.append(f"origin_rule.source_id must be the rule record {' or '.join(rule_ids)} "
                        f"(TOOL:rule_lookup:{line} names it, and the rule text is there)")

    # 5. Saving follows the duty tool and Agent 2 step 5
    s = data["estimated_saving"]
    saving_exp, duty = expected_saving(chosen, origin_exp, pack)
    if s.get("status") != saving_exp:
        problems.append(f"estimated_saving.status is {s.get('status')!r} but must be {saving_exp!r}")
    elif saving_exp == "ESTIMATED":
        if as_decimal(s.get("amount")) != as_decimal(duty.get("saving")):
            problems.append(f"estimated_saving.amount must be {duty.get('saving')!r}, "
                            f"copied from {duty['tool_id']}")
        if s.get("currency") != duty.get("currency"):
            problems.append(f"estimated_saving.currency must be {duty.get('currency')!r}")
        if s.get("source_id") != duty["tool_id"]:
            problems.append(f"estimated_saving.source_id must be {duty['tool_id']}")
    elif s.get("amount") is not None or s.get("currency") is not None:
        problems.append(f"estimated_saving.amount and currency must be null when status is {saving_exp}")

    # 6. Procedure only when the product can still qualify; steps come from passages
    if origin_exp in PROCEDURE_STATUSES and not data["procedure"]:
        problems.append(f"procedure must list the steps to claim the CEPA rate (status {origin_exp})")
    if origin_exp not in PROCEDURE_STATUSES and data["procedure"]:
        problems.append(f"procedure must be an empty list when the status is {origin_exp}")
    for i, step in enumerate(data["procedure"]):
        sid = str(step.get("source_id", ""))
        if not (sid.startswith("P-") or sid in PROCEDURE_TOOL_IDS):
            problems.append(f"procedure[{i}] must cite a P-... passage or TOOL:coo_fee")
    if (data["procedure"] and ISSUER_PASSAGE_ID in allowed
            and not any(cv.get("source_id") == ISSUER_PASSAGE_ID for cv in data["caveats"])):
        problems.append(f"the procedure leads to a certificate, so add a caveat citing {ISSUER_PASSAGE_ID} "
                        "(who issues the certificate, and what no source confirms)")

    # 7. Follow-up questions where the user must supply something
    if origin_exp == "NEEDS_MORE_DATA" and not data["follow_up_questions"]:
        problems.append("follow_up_questions must say what the user must provide "
                        f"(see the `missing` items in TOOL:origin:{line})")
    if saving_exp == "NEEDS_VALUE" and not data["follow_up_questions"]:
        problems.append("follow_up_questions must ask for the shipment value")

    # 8. Numbers must appear in the cited record (warnings, judged by QA).
    #    Step authorities are filled by code (fill_authorities), so only the step text is checked.
    records = split_records(pack.text)
    fields = [
        ("classification",
         f"{data['classification'].get('tariff_line', '')} {data['classification'].get('description', '')}",
         data["classification"].get("source_id")),
        ("tariff", " ".join(str(data["tariff"].get(k, "")) for k in
                            ("agreement", "mfn_rate", "preferential_rate")),
         data["tariff"].get("source_id")),
        ("origin_rule", str(data["origin_rule"].get("rule", "")), data["origin_rule"].get("source_id")),
        ("origin_result", str(data["origin_result"].get("basis", "")),
         data["origin_result"].get("source_id")),
    ]
    fields += [(f"procedure[{i}]", str(st.get("step", "")), st.get("source_id"))
               for i, st in enumerate(data["procedure"])]
    fields += [(f"caveats[{i}]", str(cv.get("note", "")), cv.get("source_id"))
               for i, cv in enumerate(data["caveats"])]
    for where, text, sid in fields:
        if sid in records:
            missing = number_keys(strip_list_markers(text)) - number_keys(records[sid])
            if missing:
                warnings.append(f"{where}: number(s) {sorted(missing)} not found in {sid}")

    # 9. A step's text names a known actor (e.g. a ministry) that its cited record does not:
    #    usually facts from two records merged into one step (warning, judged by QA).
    names = sorted({a.removeprefix("the ") for a in pack.actors.values()
                    if a.removeprefix("the ")[:1].isupper()}, key=len, reverse=True)
    for i, st in enumerate(data["procedure"]):
        text, rec = str(st.get("step", "")), records.get(st.get("source_id"), "")
        for name in names:  # longest first, so a short name inside a longer one is not matched twice
            if name in text:
                if name not in rec:
                    warnings.append(f"procedure[{i}]: names {name!r}, which {st.get('source_id')} does not; "
                                    "cite the record that states it, or split the step")
                text = text.replace(name, "")

    # 10. A text that restates a qualified record sentence keeps the qualifier (Step 7.8, G35). Caveats
    #     matching a KB note were already restored by code (restore_qualified_notes); this catches the
    #     rest, e.g. a step restating "Electronic certificates are reportedly accepted ..." as plain fact.
    sents = record_sentences(pack)
    restated = [(f"procedure[{i}].step", st.get("step"), st.get("source_id")) for i, st in enumerate(data["procedure"])]
    restated += [(f"caveats[{i}].note", cv.get("note"), cv.get("source_id")) for i, cv in enumerate(data["caveats"])]
    restated += [(f"gaps[{i}].text", gap_text(g), g.get("source_id")) for i, g in enumerate(data["gaps"])]
    for where, text, sid in restated:
        units = sents.get(sid, []) if isinstance(sid, str) else []
        if where.startswith("procedure"):  # a step restates the record's summary; its notes belong to caveats
            units = [x for x in units if x[0] == "summary"]
        drops = qualifier_drops(text, units)
        if drops:
            src = drops[0][1]
            word = SOURCE_QUALIFIER_RE.search(src).group(0)
            problems.append(f"{where} states as a plain fact what its cited record qualifies with {word!r} "
                            f"({src!r}): keep that qualifier in the text")

    verdict = VERDICT_MAP.get(origin_exp, GAP)
    return problems, warnings, verdict


# ---------- the LLM call ----------

def build_messages(intake: dict, pack: EvidencePack, *, previous: dict | None = None,
                   corrections: list[str] | None = None) -> list[dict]:
    user = ("INTAKE JSON:\n" + json.dumps(intake, ensure_ascii=False, indent=2)
            + "\n\nEVIDENCE:\n" + pack.text)
    messages = [
        {"role": "system", "content": build_system_prompt("researcher")},
        {"role": "user", "content": user},
    ]
    if corrections:
        # Send back what the model wrote: no code-filled verdict or step authorities.
        prev = copy.deepcopy({k: v for k, v in (previous or {}).items() if k != "verdict"})
        for step in prev.get("procedure") or []:
            if isinstance(step, dict):
                step.pop("authority", None)
        messages.append({"role": "assistant", "content": json.dumps(prev, ensure_ascii=False)})
        messages.append({"role": "user", "content":
                         "CORRECTIONS (apply all of them, then return the full corrected JSON only):\n"
                         + "\n".join(f"- {c}" for c in corrections)})
    return messages


def run_researcher(intake: dict, pack: EvidencePack, *, previous: dict | None = None,
                   corrections: list[str] | None = None, llm=call_llm) -> ResearcherResult:
    """One Researcher call (first pass, or a revision when corrections are given).

    llm: the call function (tests pass a fake one). An LLMCallError is not caught
    here: the caller (the orchestrator) records its attempts and stops.
    """
    if corrections and previous is None:
        raise ValueError("a revision needs the previous Researcher JSON")
    res = llm("researcher", "auto:long",
              build_messages(intake, pack, previous=previous, corrections=corrections),
              expect_json=True, required_keys=REQUIRED_KEYS)
    data = copy.deepcopy(res.data)
    data.pop("verdict", None)  # the verdict is code's job
    changes = normalize_gaps(data)  # old plain-string gaps -> {text, source_id: null} (Step 7.6g)
    changes += unbracket_ids(data, pack)  # "[ID]" -> "ID": the fills below read source_id (problem 75)
    changes += move_note_gaps(data, pack)  # KB notes put in gaps -> caveats, before the fills (G39)
    changes += drop_user_data_gaps(data, pack)  # missing user data repeated as gaps (problem 85)
    changes += plain_check_names(data)  # "final_manufacture_in_uae" -> "final manufacture check" (7.6j)
    changes += restore_qualified_notes(data, pack)  # a KB note's dropped "Interpretation:" put back (7.8)
    fill_authorities(data, pack)  # so is who acts in each step
    fill_tariff_line(data, pack)  # and the tariff code's format
    changes += fill_fixed_notes(data, pack)  # and fixed notes such as the issuer note (problem 79)
    changes += drop_caveat_gaps(data)  # caveats copied into gaps (problem 52)
    problems, warnings, verdict = check_researcher(data, pack)
    dropped = drop_follow_ups(data, verdict)  # no follow-ups once no CEPA rate can apply (problem 74)
    dropped += drop_claim_caveats(data, verdict, pack.corridor)  # nor notes about claiming it (problem 76)
    if dropped:
        changes += dropped
        problems, warnings, verdict = check_researcher(data, pack)  # checked again without them
    for c in changes:
        log.info("researcher normalized | %s", c)
    data["verdict"] = verdict
    log.info("researcher checks | served_by=%s | verdict=%s | problems=%d | warnings=%d",
             res.routed_via, verdict, len(problems), len(warnings))
    for p in problems:
        log.info("researcher problem | %s", p)
    for w in warnings:
        log.info("researcher warning | %s", w)
    return ResearcherResult(data=data, problems=problems, warnings=warnings, llm=res, changes=changes)