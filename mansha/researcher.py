"""Researcher Agent (Step 6.3): evidence in, cited findings out, then code checks.

The LLM picks the tariff line and explains the tool results. Code then checks
everything that can be checked mechanically:
- hard problems (certain errors) -> corrections, using the single revision
- warnings (numbers not found in the cited record) -> passed to QA to judge
Code, not the LLM, sets the final `verdict`.
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


@dataclass
class ResearcherResult:
    data: dict                      # LLM JSON + code-added "verdict"
    problems: list[str]             # hard failures -> corrections
    warnings: list[str] = field(default_factory=list)  # for QA to judge
    llm: LLMResult | None = None

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
        if not str(step.get("source_id", "")).startswith("P-"):
            problems.append(f"procedure[{i}] must cite a P-... passage")
        if (data["procedure"] and ISSUER_PASSAGE_ID in allowed
            and not any(cv.get("source_id") == ISSUER_PASSAGE_ID for cv in data["caveats"])):
            problems.append(f"the procedure leads to a certificate, so add a caveat citing {ISSUER_PASSAGE_ID} "
                        "(verify the current issuing ministry)")

    # 7. Follow-up questions where the user must supply something
    if origin_exp == "NEEDS_MORE_DATA" and not data["follow_up_questions"]:
        problems.append("follow_up_questions must say what the user must provide "
                        f"(see the `missing` items in TOOL:origin:{line})")
    if saving_exp == "NEEDS_VALUE" and not data["follow_up_questions"]:
        problems.append("follow_up_questions must ask for the shipment value")

    # 8. Numbers must appear in the cited record (warnings, judged by QA)
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
    fields += [(f"procedure[{i}]", f"{st.get('step', '')} {st.get('authority', '')}", st.get("source_id"))
               for i, st in enumerate(data["procedure"])]
    fields += [(f"caveats[{i}]", str(cv.get("note", "")), cv.get("source_id"))
               for i, cv in enumerate(data["caveats"])]
    for where, text, sid in fields:
        if sid in records:
            missing = number_keys(text) - number_keys(records[sid])
            if missing:
                warnings.append(f"{where}: number(s) {sorted(missing)} not found in {sid}")

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
        prev = {k: v for k, v in (previous or {}).items() if k != "verdict"}
        messages.append({"role": "assistant", "content": json.dumps(prev, ensure_ascii=False)})
        messages.append({"role": "user", "content":
                         "CORRECTIONS (apply all of them, then return the full corrected JSON only):\n"
                         + "\n".join(f"- {c}" for c in corrections)})
    return messages


def run_researcher(intake: dict, pack: EvidencePack, *, previous: dict | None = None,
                   corrections: list[str] | None = None) -> ResearcherResult:
    """One Researcher call (first pass, or a revision when corrections are given)."""
    if corrections and previous is None:
        raise ValueError("a revision needs the previous Researcher JSON")
    llm = call_llm("researcher", "auto:long",
                   build_messages(intake, pack, previous=previous, corrections=corrections),
                   expect_json=True, required_keys=REQUIRED_KEYS)
    data = copy.deepcopy(llm.data)
    data.pop("verdict", None)  # the verdict is code's job
    problems, warnings, verdict = check_researcher(data, pack)
    data["verdict"] = verdict
    log.info("researcher checks | served_by=%s | verdict=%s | problems=%d | warnings=%d",
             llm.routed_via, verdict, len(problems), len(warnings))
    for p in problems:
        log.info("researcher problem | %s", p)
    for w in warnings:
        log.info("researcher warning | %s", w)
    return ResearcherResult(data=data, problems=problems, warnings=warnings, llm=llm)