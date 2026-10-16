"""Automatic report check (Step 9.6b, gap G27): plain code, no LLM.

Scans the finished report (the text the exporter reads) for the kinds of mistakes
that were found only by reading on 16 Oct 2026 (problems 34-39, 44, 45, 47).

It checks FORM, not meaning: an evidence ID, a status code, a raw field name or a
number from nowhere has a shape code can find; a sentence that says the opposite of
its source does not (that is for reading and the QA Evaluator, gaps G7-G9).

Two levels:
    problems  a definite mistake (each check here passed on every good report so far)
    warnings  a likely mistake found by WORDING, so it can be wrong both ways; the
              real fix filters by source (document_builder.build_notes), this only watches it

Decision 9.6b (Haris, 17 Oct 2026): FLAG ONLY. The report is still shown; findings go to
the phase log and the runner's summary. Revisit (block the report) once the evaluation
set shows no false alarms.

Used by the orchestrator (last phase of every REPORT run) and by scripts/check_reports.py
(re-checks saved run folders).
"""

from __future__ import annotations

import re

from mansha.document_builder import (
    CODE_WORD_RE,
    DISCLAIMER,
    HEADINGS,
    ID_RE,
    NO_CEPA_RATE_VERDICTS,
)
from mansha.researcher import INTERNAL_WORD_RE, number_keys

# Status codes from the tools and the Researcher that the Builder's own list doesn't cover.
# Upper case only: real quotes in sources ("ISSUED RETROSPECTIVELY") are not in this list.
TOOL_CODE_RE = re.compile(
    r"\b(?:MEETS|FAILS?|PASS(?:ED)?|INSUFFICIENT_DATA|RULE_GAP|ESTIMATED|CURRENCY_NOT_AED|"
    r"EXCLUDED|NOT_COVERED|CHECKS_FAILED|LLM_ERROR|NEEDS_INPUT)\b")
FIELD_NAME_RE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")   # price_basis, inputs_count
PY_REPR_RE = re.compile(r"\[\s*'[^'\n]*'\s*[,\]]|\{\s*'[^'\n]*'\s*:")      # ['b', 'k'], {'a': ...}
CITATION_RE = re.compile(r"\[\d+\]")
LINK_RE = re.compile(r"\]\([^)]*\)|https?://\S+")

# Warnings, matched by wording (see the module docstring).
CLAIM_WORDS_RE = re.compile(
    r"certificates? of origin|factory registration|e-sanchit|\bissuer\b|issuing authority|"
    r"\bcertificate fee\b", re.IGNORECASE)
ESTIMATE_WORDS_RE = re.compile(r"\bthe estimate\b|\bestimate shown\b|\bduty estimate\b", re.IGNORECASE)


def sections(markdown: str) -> dict[str, str]:
    """'## Heading' -> its text (the part before the first '##' is under '')."""
    out, name, buf = {}, "", []
    for line in markdown.splitlines():
        if line.startswith("## "):
            out[name] = "\n".join(buf)
            name, buf = line[3:].strip(), []
        else:
            buf.append(line)
    out[name] = "\n".join(buf)
    return out


def reader_text(markdown: str, lang: str) -> str:
    """The report without the code-rendered Sources and Disclaimer, links and [n] markers."""
    h = HEADINGS[lang]
    parts = [t if not name else f"## {name}\n{t}" for name, t in sections(markdown).items()
             if name not in (h["sources"], h["disclaimer"])]
    text = "\n".join(parts)
    return CITATION_RE.sub("", LINK_RE.sub("]", text))


def _show(m: re.Match, text: str, width: int = 40) -> str:
    """The match with a little context, on one line."""
    a, b = max(0, m.start() - width), min(len(text), m.end() + width)
    return "…" + text[a:b].replace("\n", " ").strip() + "…"


def _all(regex: re.Pattern, text: str) -> list[re.Match]:
    seen, out = set(), []
    for m in regex.finditer(text):
        if m.group() not in seen:
            seen.add(m.group())
            out.append(m)
    return out


def check_report(markdown: str, *, research: dict, evidence_text: str, message: str,
                 language: str = "en") -> tuple[list[str], list[str]]:
    """Return (problems, warnings) for one finished report. Pure: reads nothing else."""
    lang = "ar" if language == "ar" else "en"
    problems: list[str] = []
    warnings: list[str] = []
    text = reader_text(markdown, lang)

    # 1. Evidence IDs and note numbers (problem 34)
    for m in _all(ID_RE, text):
        token = re.match(r"[^\s,;:()]+", text[m.start():]).group().rstrip(".")   # PSR-I -> PSR-IN-R118
        problems.append(f"evidence ID or note number {token!r} in the report: {_show(m, text)}")

    # 2. Internal words and status codes (problem 35, '(FAIL)' on 16 Oct 17:01)
    for regex, what in ((INTERNAL_WORD_RE, "internal word"), (CODE_WORD_RE, "status code"),
                        (TOOL_CODE_RE, "status code")):
        for m in _all(regex, text):
            problems.append(f"{what} {m.group()!r} in the report: {_show(m, text)}")

    # 3. Raw field names and Python values (problems 38, 39)
    for m in _all(FIELD_NAME_RE, text):
        problems.append(f"raw field name {m.group()!r} in the report: {_show(m, text)}")
    for m in _all(PY_REPR_RE, text)[:1]:
        problems.append(f"raw Python value in the report: {_show(m, text)}")

    # 4. The disclaimer, exactly as code renders it
    if DISCLAIMER[lang] not in markdown:
        problems.append("the disclaimer is missing or changed")

    # 5. The chosen tariff line is printed in 'Product classification' (problem 44)
    line = re.sub(r"\D", "", str((research.get("classification") or {}).get("tariff_line") or ""))
    if len(line) == 8:
        cls_text = sections(markdown).get(HEADINGS[lang]["classification"], "")
        if line not in re.sub(r"[\s.]", "", cls_text):
            problems.append(f"tariff line {line} is not printed in '{HEADINGS[lang]['classification']}'")

    # 6. Every number comes from the evidence or the user's message
    known = number_keys(evidence_text) | number_keys(message)
    unknown = sorted(number_keys(text) - known)
    if unknown:
        problems.append(f"number(s) not in the evidence or the message: {', '.join(unknown)}")

    # 7. No talk of claiming when no CEPA rate can apply (problem 47) - wording, so a warning
    verdict = research.get("verdict")
    if verdict in NO_CEPA_RATE_VERDICTS:
        for m in _all(CLAIM_WORDS_RE, text):
            warnings.append(f"{verdict} report mentions claiming ({m.group()!r}): {_show(m, text)}")

    # 8. No estimate wording when no saving is shown (problems 31, 45) - wording, so a warning
    if (research.get("estimated_saving") or {}).get("status") != "ESTIMATED":
        for m in _all(ESTIMATE_WORDS_RE, text):
            warnings.append(f"no saving shown, but the report mentions an estimate: {_show(m, text)}")

    return problems, warnings
