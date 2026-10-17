"""Researcher Agent (Step 6.3): evidence in, cited findings out, then code checks.

The LLM picks the tariff line and explains the tool results. Code then checks
everything that can be checked mechanically:
- hard problems (certain errors) -> corrections, using the single revision
- warnings (numbers not found in the cited record) -> passed to QA to judge
Code, not the LLM, sets the final `verdict` and each procedure step's
`authority` (copied from the cited record's `actor`, Step 6.4g). Code also drops
`gaps` items that repeat a caveat (Step 9.6e, problem 52) and records that in `changes`.
"""

from __future__ import annotations

import copy
import json
import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from mansha.evidence import HEADER_RE, EvidencePack
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


def _same_text(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip().rstrip(".").lower()


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
    keep = [g for g in gaps if _same_text(g) not in notes]
    removed = [g for g in gaps if _same_text(g) in notes]
    data["gaps"] = keep
    return [f"gaps: dropped a copy of a caveat: {g!r}" for g in removed]


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
    if problems:
        return problems, warnings, GAP

    # 1b. Text the exporter reads (report, or code-only fallback) has no IDs or internal words
    shown = [("origin_result.basis", data["origin_result"].get("basis"))]
    shown += [(f"procedure[{i}].step", s.get("step")) for i, s in enumerate(data["procedure"])]
    shown += [(f"caveats[{i}].note", c.get("note")) for i, c in enumerate(data["caveats"])]
    shown += [(f"follow_up_questions[{i}]", q) for i, q in enumerate(data["follow_up_questions"])]
    shown += [(f"gaps[{i}]", g) for i, g in enumerate(data["gaps"])]
    for where, text in shown:
        text = str(text or "")
        found = EVIDENCE_ID_RE.search(text) or INTERNAL_WORD_RE.search(text)
        if found:
            span = text[found.start():found.start() + 25].split()[0]
            problems.append(f"{where} contains {span!r}: this text is shown to the exporter, so write it in "
                            "plain words without evidence IDs or internal words (cite only in source_id)")

    # 2. Every source_id is an ID in the evidence
    allowed = set(pack.allowed_ids)
    cited = [(k, data[k].get("source_id")) for k in OBJECT_KEYS]
    cited += [(f"procedure[{i}]", s.get("source_id")) for i, s in enumerate(data["procedure"])]
    cited += [(f"caveats[{i}]", s.get("source_id")) for i, s in enumerate(data["caveats"])]
    for where, sid in cited:
        if sid not in allowed:
            problems.append(f"{where}.source_id {sid!r} is not an ID in the evidence")

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
    fill_authorities(data, pack)  # so is who acts in each step
    fill_tariff_line(data, pack)  # and the tariff code's format
    changes = drop_caveat_gaps(data)  # caveats copied into gaps (problem 52)
    for c in changes:
        log.info("researcher normalized | %s", c)
    problems, warnings, verdict = check_researcher(data, pack)
    data["verdict"] = verdict
    log.info("researcher checks | served_by=%s | verdict=%s | problems=%d | warnings=%d",
             res.routed_via, verdict, len(problems), len(warnings))
    for p in problems:
        log.info("researcher problem | %s", p)
    for w in warnings:
        log.info("researcher warning | %s", w)
    return ResearcherResult(data=data, problems=problems, warnings=warnings, llm=res, changes=changes)