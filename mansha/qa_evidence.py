"""The compact evidence the QA Evaluator reads (Step 7.2).

QA judges meaning: does each claim say what its cited record says, and is the
tariff line justified by its description? For that it needs the candidate lines,
the chosen line's tool results and every record the Researcher cited, not the
whole EVIDENCE block. A smaller prompt is also cheaper and faster, and lets more
cases fit Groq's free limit of 8,000 tokens per minute (input + output), which the
router checks before it picks a model (it skips a model whose limit is too small).

Sections:
1. CANDIDATE TARIFF LINES: the tariff lookup and every candidate record (QA checks
   that the chosen line matches the product description, not its result). Lines not
   chosen are shortened to their ID, code, description and rates.
2. CHOSEN LINE: TOOL RESULTS: rule lookup, origin and duty for the chosen line only.
3. CITED RECORDS: every other record the Researcher cited, in full, in evidence order.
4. NOT CITED: one line per uncited rule or passage (ID + title), so QA can point
   at a relevant record the Researcher left out.

`research_for_qa()` is the Researcher JSON QA reads: the classification reasoning only
(the other reasoning steps repeat the findings), and without the fields code fills or
verifies exactly against the tools (`verdict`, step `authority`, `origin_result.status`,
`origin_rule`, `estimated_saving`). `checked_facts()` states those as plain facts instead,
plus what the user already gave. Why (Step 7.4, first live run): GPT-OSS "corrected" a
correct NOT_APPLICABLE saving and a correct NOT_APPLICABLE origin status, because it did not
know the mapping rules that code enforces. QA should not judge what code already proves.

Plan B (Step 7.4b): when one review is too big for Groq's limit, mansha/qa.py splits
it into parts. `qa_evidence(..., part=...)` and `research_for_qa(..., part=...)` build
each part's view from a list of keys: "findings" (candidates, chosen-line tools, records
cited by the findings, uncited index) and/or steps and notes ("procedure[2]", "caveats[0]")
with only the records they cite.

Pure code, no LLM. Built only from the EVIDENCE text the Researcher already saw, so it
carries counts and percentages only (Step 9.3) and adds nothing new.
"""

from __future__ import annotations

import copy

from mansha.evidence import EvidencePack
from mansha.researcher import digits, split_records

TOOL_PREFIXES = ("TOOL:rule_lookup:", "TOOL:origin:", "TOOL:duty:")
INDEX_PREFIXES = ("P-", "PSR-")  # records listed by title when not cited
TITLE_KEYS = ("title:", "rule:", "text:")
TITLE_MAX = 110
# Lines kept for a candidate that was not chosen (classification is judged from these).
BRIEF_KEYS = ("tariff line:", "heading:", "description:", "MFN rate:", "CEPA status:")
CODE_FILLED = ("verdict", "origin_rule", "estimated_saving")  # set or verified exactly by code
STEP_CODE_FILLED = ("authority",)
# Correction targets QA may not use: code fills or verifies them exactly (check_qa refuses them).
CODE_OWNED = ("verdict", "origin_rule", "estimated_saving", "origin_result.status")
# The fields reviewed in the "findings" part when a review is split (plan B, Step 7.4b).
FINDINGS_KEYS = ("reasoning", "classification", "tariff", "origin_result", "follow_up_questions", "gaps")


def _clean(block: str) -> str:
    """A record's text without the evidence section headers that follow it."""
    lines = [ln for ln in block.strip().splitlines() if not ln.startswith("=== ")]
    return "\n".join(lines).strip()


def _brief(block: str) -> str:
    lines = block.splitlines()
    return "\n".join([lines[0]] + [ln for ln in lines[1:] if ln.startswith(BRIEF_KEYS)])


def _title(block: str) -> str:
    for ln in block.splitlines()[1:]:
        ln = ln.strip()
        for key in TITLE_KEYS:
            if ln.startswith(key):
                t = ln[len(key):].strip()
                return t if len(t) <= TITLE_MAX else t[:TITLE_MAX - 1].rstrip() + "…"
    return ""


def cited_ids(research: dict) -> list[str]:
    """Every source_id the Researcher JSON cites (any depth), in first-seen order."""
    out: list[str] = []

    def walk(x):
        if isinstance(x, dict):
            sid = x.get("source_id")
            if isinstance(sid, str) and sid not in out:
                out.append(sid)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(research)
    return out


def item_keys(research: dict) -> list[str]:
    """The steps and notes, as field names: procedure[0], ..., caveats[0], ..."""
    return ([f"procedure[{i}]" for i in range(len(research.get("procedure") or []))]
            + [f"caveats[{i}]" for i in range(len(research.get("caveats") or []))])


def item_value(research: dict, key: str) -> dict:
    """One step or note as QA reads it (no code-filled authority)."""
    name, idx = key[:-1].split("[")
    value = copy.deepcopy(research[name][int(idx)])
    if isinstance(value, dict):
        for k in STEP_CODE_FILLED:
            value.pop(k, None)
    return value


def _split_scope(part) -> tuple[bool, list[str]]:
    """part (plan B) -> (includes the findings?, [item keys])."""
    if part is None:
        return True, []
    return "findings" in part, [k for k in part if k != "findings"]


def _part_cited(research: dict, part) -> set[str]:
    """IDs cited by the fields one review part covers (Step 7.4b, plan B)."""
    has_findings, items = _split_scope(part)
    ids = set(cited_ids([item_value(research, k) for k in items]))
    if has_findings:
        ids |= set(cited_ids({k: research.get(k) for k in FINDINGS_KEYS}))
    return ids


def qa_evidence(pack: EvidencePack, research: dict, part=None) -> str:
    """The QA view of the evidence: see the module docstring.

    part: None (the whole review, one call) or, for one part of a split review (plan B),
    a list of keys: "findings" and/or item keys ("procedure[0]", "caveats[3]", ...).
    """
    records = {rid: _clean(txt) for rid, txt in split_records(pack.text).items()}
    order = [rid for rid in pack.allowed_ids if rid in records]
    has_findings, _ = _split_scope(part)
    if not has_findings:
        ids = _part_cited(research, part)
        blocks = [records[rid] for rid in order if rid in ids]
        return ("=== CITED RECORDS (for the steps and notes in this part) ===\n\n"
                + ("\n\n".join(blocks) if blocks else "none"))
    cited = set(cited_ids(research)) if part is None else _part_cited(research, part)
    cited_anywhere = set(cited_ids(research))
    line = digits((research.get("classification") or {}).get("tariff_line"))
    used: set[str] = set()
    parts: list[str] = []

    def take(ids):
        blocks = []
        for rid in ids:
            if rid in records and rid not in used:
                used.add(rid)
                blocks.append(records[rid])
        return blocks

    # 1. Candidates (always: classification is judged from them); lines not chosen in brief
    chosen_ids = {c["id"] for c in pack.candidates if digits(c.get("tariff_line")) == line}
    blocks = take(["TOOL:tariff_lookup"])
    for c in pack.candidates:
        if c["id"] in records and c["id"] not in used:
            used.add(c["id"])
            full = c["id"] in chosen_ids or c["id"] in cited
            blocks.append(records[c["id"]] if full else _brief(records[c["id"]]))
    parts.append("=== CANDIDATE TARIFF LINES ===\n\n" + "\n\n".join(blocks))

    # 2. Tool results for the chosen line (none when classification is a gap)
    chosen = [p + line for p in TOOL_PREFIXES] if len(line) == 8 else []
    blocks = take(chosen)
    parts.append("=== CHOSEN LINE: TOOL RESULTS ===\n\n"
                 + ("\n\n".join(blocks) if blocks else "none (no tariff line chosen)"))

    # 3. Everything else the Researcher cited, in evidence order
    blocks = take([rid for rid in order if rid in cited])
    parts.append("=== CITED RECORDS ===\n\n" + ("\n\n".join(blocks) if blocks else "none"))

    # 4. Rules and passages not cited: ID + title only
    index = [f"- [{rid}] {_title(records[rid])}".rstrip()
             for rid in order if rid not in used and rid not in cited_anywhere
             and rid.startswith(INDEX_PREFIXES)]
    parts.append("=== NOT CITED (titles only) ===\n" + ("\n".join(index) if index else "none"))

    return "\n\n".join(parts)


def research_for_qa(research: dict, part=None) -> dict:
    """The Researcher JSON as QA reads it: see the module docstring.

    part (plan B): a list of keys. With "findings": only the findings fields; item keys add
    those steps and notes under `items`, keyed by their field name. Without "findings":
    the items plus the origin basis as context.
    """
    has_findings, items = _split_scope(part)
    if not has_findings:
        return {"origin_basis_for_context": (research.get("origin_result") or {}).get("basis"),
                "items": {k: item_value(research, k) for k in items}}
    data = copy.deepcopy(research)
    if part is not None:
        data = {k: data[k] for k in FINDINGS_KEYS if k in data}
    for k in CODE_FILLED:
        data.pop(k, None)
    if isinstance(data.get("origin_result"), dict):
        data["origin_result"].pop("status", None)
    reasoning = data.get("reasoning")
    if isinstance(reasoning, list):
        data["reasoning"] = reasoning[:1]
    for step in data.get("procedure") or []:
        if isinstance(step, dict):
            for k in STEP_CODE_FILLED:
                step.pop(k, None)
    if items:
        data["items"] = {k: item_value(research, k) for k in items}
    return data


def checked_facts(research: dict, intake: dict, pack: EvidencePack) -> str:
    """Facts code has verified against the tools, and what the user already gave (plain text)."""
    line = digits((research.get("classification") or {}).get("tariff_line"))
    origin = (research.get("origin_result") or {}).get("status")
    rule = research.get("origin_rule") or {}
    saving = research.get("estimated_saving") or {}
    s_text = str(saving.get("status"))
    if saving.get("status") == "ESTIMATED":
        s_text += f" ({saving.get('amount')} {saving.get('currency')}, if the product qualifies)"
    lines = [
        f"- verdict: {research.get('verdict')}",
        f"- origin result status: {origin} "
        + ("(the line is excluded, so no origin check applies)" if origin == "NOT_APPLICABLE"
           else "(the origin tool's result for the chosen line, mapped by code)"),
        f"- rule of origin: {rule.get('rule')} ({rule.get('source_id')})",
        (f"- duty saving status: {s_text} (from the duty tool, by code's rule: no saving when the "
         "product does not qualify or the line is excluded)"),
    ]
    value = intake.get("shipment_value")
    gave = [f"shipment value {value.get('amount')} {value.get('currency')}" if value
            else "shipment value: NOT given"]
    tool = pack.tool_results.get(f"TOOL:origin:{line}") if line else None
    if tool is None:
        gave.append("bill of materials: not needed (no origin check for this line)")
    elif tool.get("status") == "INSUFFICIENT_DATA":
        missing = ", ".join(map(str, tool.get("missing") or [])) or "see the origin tool"
        gave.append(f"bill of materials and declaration: NOT given or incomplete (missing: {missing})")
    else:
        gave.append("bill of materials and declaration: GIVEN (the origin check already ran on them)")
    if intake.get("hs_code_given"):
        gave.append(f"HS code {intake['hs_code_given']}")
    lines.append("- the user already gave: " + "; ".join(gave))
    return "\n".join(lines)
