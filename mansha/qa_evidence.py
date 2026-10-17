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
(the other reasoning steps repeat the findings) and no code-filled fields (`verdict`,
step `authority`), which code sets and QA does not judge.

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
CODE_FILLED = ("verdict",)
STEP_CODE_FILLED = ("authority",)


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


def qa_evidence(pack: EvidencePack, research: dict) -> str:
    """The QA view of the evidence: see the module docstring."""
    records = {rid: _clean(txt) for rid, txt in split_records(pack.text).items()}
    order = [rid for rid in pack.allowed_ids if rid in records]
    cited = set(cited_ids(research))
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
             for rid in order if rid not in used and rid.startswith(INDEX_PREFIXES)]
    parts.append("=== NOT CITED (titles only) ===\n" + ("\n".join(index) if index else "none"))

    return "\n\n".join(parts)


def research_for_qa(research: dict) -> dict:
    """The Researcher JSON as QA reads it: see the module docstring."""
    data = copy.deepcopy(research)
    for k in CODE_FILLED:
        data.pop(k, None)
    reasoning = data.get("reasoning")
    if isinstance(reasoning, list):
        data["reasoning"] = reasoning[:1]
    for step in data.get("procedure") or []:
        if isinstance(step, dict):
            for k in STEP_CODE_FILLED:
                step.pop(k, None)
    return data
