"""Document Builder Agent (Step 8): approved findings in, Markdown report out.

Split of work (design D1-D4, Step 8.1; mandatory notes verbatim since 8.5):
- code builds a FACTS block and numbered optional NOTES from the approved
  Researcher JSON (no evidence IDs are sent to the model)
- the LLM writes only the prose: summary, classification, duty, origin, and a
  condensed list of the OPTIONAL notes
- MANDATORY notes (certificate issuer, duty basis, self-declaration) are never
  sent to the LLM: code prints them word for word, so no warning can be softened
- code checks the prose (numbers, note sources, no IDs or code words) and
  sends corrections once; if it still fails, code writes the prose itself
- code renders everything fixed: headings, the claim checklist, the mandatory
  notes, the sources list and the disclaimer
"""

from __future__ import annotations

import copy
import json
import logging
import re
from dataclasses import dataclass, field

from mansha.kb import load_corridor
from mansha.llm_client import LLMCallError, LLMResult, call_llm
from mansha.prompts import build_system_prompt
from mansha.researcher import GAP, number_keys

log = logging.getLogger("mansha.document_builder")

REQUIRED_KEYS = ("summary", "classification", "duty", "origin", "notes")
TEXT_KEYS = ("summary", "classification", "duty", "origin")
MAX_NOTES = 6          # notes in the report in total: mandatory (verbatim) + the LLM's items
NOT_IN_SOURCES = "not in Mansha's sources"

# D2: caveats that must always reach the reader, by the record they cite.
# Since 8.5 they are shown verbatim by code and never rewritten by the LLM (problem 25).
MANDATORY_IDS = {"P-UAE-ISSUER"}                      # who issues the certificate
MANDATORY_PREFIXES = ("TOOL:duty:", "TOOL:origin:")   # duty basis (BCD, CIF); self-declaration

# D4: verdicts that come with a claim checklist.
CHECKLIST_VERDICTS = {"ELIGIBLE", "NEEDS_MORE_DATA"}

# Fixed meanings for the TERMS line. Only terms that appear in the facts are sent.
TERMS = {
    "MFN": "MFN rate = the normal import duty rate, charged when no trade-agreement preference is claimed",
    "CEPA": "CEPA rate = the reduced rate under the trade agreement",
    "CC": "CC = change in chapter: each non-originating input must be classified in a different "
          "2-digit chapter than the product",
    "CTH": "CTH = change in tariff heading: each non-originating input must be classified in a "
           "different 4-digit heading than the product",
    "CTSH": "CTSH = change in tariff subheading: each non-originating input must be classified in a "
            "different 6-digit subheading than the product",
    "VA": "VA = value addition: the share of the product's price that does not come from "
          "non-originating materials",
    "FOB": "FOB = the price of the goods loaded on board at the UAE port",
}

# Fixed meanings for the origin check names in BASIS (problem 30: "minimal operations check
# passed" was read as "minimal operations were done"). Matched as phrases, "_" read as " ".
CHECK_TERMS = {
    "final manufacture": "final manufacture check = whether the last manufacturing step took place in "
                         "the UAE; passed means it did, failed means it did not",
    "minimal operations": "minimal operations check = whether the work done in the UAE goes beyond the "
                          "simple operations that the agreement says never give origin on their own; "
                          "passed means the work goes beyond them, failed means only such simple "
                          "operations were done",
    "de minimis": "de minimis = a small share of non-originating inputs that the tariff-shift test is "
                  "allowed to ignore",
}

# Plain words for the statuses (the model never sees a bare status word without these).
VERDICT_TEXT = {
    "ELIGIBLE": "the product meets the rule of origin, so the CEPA rate can be claimed",
    "NOT_ELIGIBLE": "the product does not meet the rule of origin, so the normal (MFN) rate applies",
    "NEEDS_MORE_DATA": "Mansha cannot confirm the result yet, because information is missing",
    "NO_PREFERENCE": "this tariff line is excluded from CEPA preference, so the normal (MFN) rate "
                     "applies whatever the product's origin",
    GAP: "Mansha's sources do not cover this product well enough to give a result",
}
ORIGIN_TEXT = {
    "QUALIFIES": "meets the rule of origin",
    "DOES_NOT_QUALIFY": "does not meet the rule of origin",
    "NEEDS_MORE_DATA": "cannot be checked yet, because information is missing",
    "NOT_APPLICABLE": "is not checked, because the line is excluded from CEPA preference",
    GAP: "cannot be checked, because the rule is not in Mansha's sources",
}

# Things the prose must never contain.
EVIDENCE_ID_RE = re.compile(r"\b(?:TL|EXC|PSR)-[A-Z0-9]|\bP-[A-Z]|TOOL:")
ID_RE = re.compile(EVIDENCE_ID_RE.pattern + r"|\b[NM]\d+\b")   # evidence IDs and note numbers
CODE_WORD_RE = re.compile(
    r"\b(?:REGULATORY_GAP_DETECTED|NOT_ELIGIBLE|ELIGIBLE|NEEDS_MORE_DATA|NO_PREFERENCE|"
    r"NOT_APPLICABLE|NEEDS_VALUE|DOES_NOT_QUALIFY|QUALIFIES|MANDATORY)\b")

HEADINGS = {
    "en": {
        "title": "Mansha origin check",
        "result": "Result",
        "summary": "Summary",
        "classification": "Product classification",
        "duty": "Duty comparison",
        "origin": "Rule of origin and result",
        "checklist": "Step-by-step checklist to claim the CEPA rate",
        "notes": "Important notes",
        "needed": "What's still needed",
        "sources": "Sources",
        "disclaimer": "Disclaimer",
        "mfn": "Normal (MFN) rate",
        "cepa": "CEPA rate",
        "saving": "Estimated saving",
        "authority": "Authority",
        "source": "Source",
    },
    "ar": {
        "title": "فحص المنشأ من منشأ",
        "result": "النتيجة",
        "summary": "الملخص",
        "classification": "تصنيف المنتج",
        "duty": "مقارنة الرسوم الجمركية",
        "origin": "قاعدة المنشأ والنتيجة",
        "checklist": "قائمة الخطوات للمطالبة بسعر الاتفاقية",
        "notes": "ملاحظات مهمة",
        "needed": "ما زال مطلوبًا",
        "sources": "المصادر",
        "disclaimer": "إخلاء المسؤولية",
        "mfn": "السعر العادي (الدولة الأولى بالرعاية)",
        "cepa": "سعر اتفاقية الشراكة الاقتصادية الشاملة",
        "saving": "التوفير التقديري",
        "authority": "الجهة المختصة",
        "source": "المصدر",
    },
}
RESULT_LABEL = {
    "en": {
        "ELIGIBLE": "Eligible for the CEPA rate",
        "NOT_ELIGIBLE": "Not eligible: the normal (MFN) rate applies",
        "NEEDS_MORE_DATA": "Cannot confirm yet: more information needed",
        "NO_PREFERENCE": "No CEPA preference for this tariff line: the normal (MFN) rate applies",
        GAP: "No result: not covered by Mansha's sources",
    },
    "ar": {
        "ELIGIBLE": "مؤهل لسعر الاتفاقية",
        "NOT_ELIGIBLE": "غير مؤهل: يطبق السعر العادي",
        "NEEDS_MORE_DATA": "لا يمكن التأكيد بعد: مطلوب مزيد من المعلومات",
        "NO_PREFERENCE": "لا تفضيل جمركي لهذا البند: يطبق السعر العادي",
        GAP: "لا توجد نتيجة: غير مشمول في مصادر منشأ",
    },
}
DISCLAIMER = {
    "en": "This report is informational only and is not an official origin ruling. Verify all "
          "details with the issuing authority and customs before shipping.",
    "ar": "هذا التقرير للعلم فقط وليس قرارًا رسميًا بشأن المنشأ. يرجى التحقق من جميع التفاصيل "
          "مع الجهة المصدرة للشهادة ومع الجمارك قبل الشحن.",
}


@dataclass
class BuilderResult:
    markdown: str
    prose: dict                      # the text placed in the report (LLM or code fallback)
    notes: list[dict]                # all notes (with nid, source_id and mandatory flag)
    used_fallback: bool
    problems: list[str] = field(default_factory=list)   # left over when the fallback was used
    llm_calls: list[LLMResult] = field(default_factory=list)


# ---------- FACTS and NOTES (code, before the call) ----------

def plain(x) -> str:
    """A field value for FACTS: the gap marker becomes plain words."""
    s = str(x if x is not None else "").strip()
    return NOT_IN_SOURCES if not s or s == GAP else s


def saving_text(research: dict) -> str:
    s = research["estimated_saving"]
    status = s.get("status")
    if status == "ESTIMATED":
        text = f"{s.get('amount')} {s.get('currency')}"
        if research["verdict"] != "ELIGIBLE":
            text += " (only if the product qualifies)"
        return text
    return {
        "NOT_APPLICABLE": "none, because the product does not qualify",
        "NO_PREFERENCE": "none, because the tariff line is excluded from CEPA preference",
        "NEEDS_VALUE": "cannot be estimated without the shipment value",
    }.get(status, NOT_IN_SOURCES)


def rule_text(research: dict) -> str:
    r = plain(research["origin_rule"].get("rule"))
    return "does not apply, because the line is excluded from CEPA preference" if r == "NOT_APPLICABLE" else r


def is_mandatory(source_id: str) -> bool:
    return source_id in MANDATORY_IDS or str(source_id).startswith(MANDATORY_PREFIXES)


def build_notes(research: dict) -> list[dict]:
    """The Researcher's caveats (duplicate texts kept once).

    Mandatory notes are numbered M1, M2, ... and are shown verbatim by code (never sent
    to the LLM). Optional notes are numbered N1, N2, ... and are what the LLM condenses.
    """
    notes, seen, count = [], set(), {True: 0, False: 0}
    for cv in research.get("caveats") or []:
        text = str(cv.get("note", "")).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        sid = cv.get("source_id")
        mand = is_mandatory(sid)
        count[mand] += 1
        notes.append({"nid": f"{'M' if mand else 'N'}{count[mand]}", "text": text,
                      "source_id": sid, "mandatory": mand})
    return notes


def max_llm_notes(notes: list[dict]) -> int:
    """How many items the LLM may write: the total cap minus the mandatory notes."""
    return max(0, MAX_NOTES - sum(n["mandatory"] for n in notes))


def sent_notes(notes: list[dict]) -> list[dict]:
    """The notes the LLM sees: the optional ones (none if there is no room for them)."""
    return [n for n in notes if not n["mandatory"]] if max_llm_notes(notes) else []


def terms_for(text: str) -> list[str]:
    keys = ["MFN", "CEPA"] + [k for k in ("CC", "CTH", "CTSH", "VA", "FOB")
                              if re.search(rf"\b{k}\b", text)]
    low = text.lower().replace("_", " ")
    return [TERMS[k] for k in keys] + [t for phrase, t in CHECK_TERMS.items() if phrase in low]


def shipment_text(intake: dict) -> str:
    v = intake.get("shipment_value")
    if isinstance(v, dict) and v.get("amount") is not None:
        return f"{v.get('amount')} {v.get('currency')}"
    return "not given"


def build_facts(research: dict, intake: dict) -> tuple[str, list[dict]]:
    """Return (FACTS + optional NOTES text for the prompt, all notes). No evidence IDs inside."""
    cls, tar = research["classification"], research["tariff"]
    res, verdict = research["origin_result"], research["verdict"]
    pref = plain(tar.get("preferential_rate"))
    if pref == "EXCLUDED":
        pref = "excluded (no CEPA rate for this line)"
    rule = rule_text(research)

    lines = [
        f"VERDICT: {verdict} ({VERDICT_TEXT.get(verdict, VERDICT_TEXT[GAP])})",
        f"PRODUCT: {plain(intake.get('product_description'))}",
        f"DESTINATION: {plain(intake.get('destination_country'))}",
        f"EXPORTER ROLE: {intake.get('exporter_role') or 'not given'}",
        f"SHIPMENT VALUE: {shipment_text(intake)}",
        f"TARIFF LINE: {plain(cls.get('tariff_line'))}, {plain(cls.get('description'))} "
        f"(Mansha's confidence: {cls.get('confidence') or 'not given'})",
        f"AGREEMENT: {plain(tar.get('agreement'))}",
        f"NORMAL (MFN) RATE: {plain(tar.get('mfn_rate'))}",
        f"CEPA RATE: {pref}",
        f"ESTIMATED SAVING: {saving_text(research)}",
        f"RULE OF ORIGIN: {rule}",
        f"ORIGIN RESULT: the product {ORIGIN_TEXT.get(res.get('status'), NOT_IN_SOURCES)}",
        f"BASIS: {plain(res.get('basis'))}",
    ]
    needed = list(research.get("follow_up_questions") or []) + list(research.get("gaps") or [])
    lines.append("STILL NEEDED:" + ("".join(f"\n- {n}" for n in needed) if needed else " nothing"))
    lines.append("TERMS:" + "".join(f"\n- {t}" for t in terms_for(rule + " " + str(res.get("basis", "")))))

    notes = build_notes(research)
    sent = sent_notes(notes)
    if sent:
        notes_text = (f"NOTES (at most {max_llm_notes(notes)} items in your `notes` list):\n"
                      + "\n".join(f"{n['nid']}: {n['text']}" for n in sent))
    else:
        notes_text = "NOTES: none (return an empty `notes` list)"
    return "FACTS:\n" + "\n".join(lines) + "\n\n" + notes_text, notes


# ---------- checks (code, after the call) ----------

def check_prose(prose: dict, facts_text: str, notes: list[dict]) -> list[str]:
    """Return problems (each one becomes a correction). Pure code."""
    problems: list[str] = []
    facts_numbers = number_keys(facts_text.split("\n\nNOTES")[0])
    by_nid = {n["nid"]: n for n in sent_notes(notes)}
    limit = max_llm_notes(notes) if by_nid else 0

    for k in TEXT_KEYS:
        if not isinstance(prose.get(k), str) or not prose[k].strip():
            problems.append(f"`{k}` must be a non-empty string")
    if not isinstance(prose.get("notes"), list):
        problems.append("`notes` must be a JSON list")
    if problems:
        return problems

    def text_problems(where: str, text: str, allowed_numbers: set[str]) -> None:
        extra = number_keys(text) - allowed_numbers
        if extra:
            problems.append(f"{where}: number(s) {sorted(extra)} are not in the input; "
                            "copy numbers exactly as given and never compute new ones")
        if ID_RE.search(text):
            problems.append(f"{where}: remove evidence IDs and note numbers "
                            f"(found {ID_RE.search(text).group(0)!r})")
        if CODE_WORD_RE.search(text):
            problems.append(f"{where}: replace the code word {CODE_WORD_RE.search(text).group(0)!r} "
                            "with plain words")

    for k in TEXT_KEYS:
        text_problems(f"`{k}`", prose[k], facts_numbers)

    if len(prose["notes"]) > limit:
        problems.append(f"`notes` has {len(prose['notes'])} items; merge or drop notes "
                        f"to keep at most {limit}")
    for i, item in enumerate(prose["notes"]):
        where = f"notes[{i}]"
        if not isinstance(item, dict) or not isinstance(item.get("text"), str) or not item["text"].strip():
            problems.append(f"{where} must be an object with a non-empty `text`")
            continue
        src = item.get("from")
        if not isinstance(src, list) or not src:
            problems.append(f"{where}.from must list the note numbers it is based on")
            continue
        unknown = [s for s in src if s not in by_nid]
        if unknown:
            problems.append(f"{where}.from has unknown note numbers {unknown}")
        allowed = set(facts_numbers)
        for s in src:
            if s in by_nid:
                allowed |= number_keys(by_nid[s]["text"])
        text_problems(where, item["text"], allowed)
    return problems


# ---------- fallback (code writes the prose) ----------

def fallback_prose(research: dict, notes: list[dict]) -> dict:
    """Prose built from the facts alone, used when the LLM's text fails its checks.

    `notes` holds the optional notes verbatim; render_report adds the mandatory ones.
    """
    cls, tar = research["classification"], research["tariff"]
    res, verdict = research["origin_result"], research["verdict"]
    summary = VERDICT_TEXT.get(verdict, VERDICT_TEXT[GAP])
    summary = summary[0].upper() + summary[1:] + "."
    if research["estimated_saving"].get("status") == "ESTIMATED":
        summary += f" Estimated saving: {saving_text(research)}."
    return {
        "summary": summary,
        "classification": (f"Tariff line {plain(cls.get('tariff_line'))}: {plain(cls.get('description'))} "
                           f"(Mansha's confidence: {cls.get('confidence') or 'not given'}). Confirm the "
                           "code with Indian customs or a customs broker before shipping."),
        "duty": (f"Agreement: {plain(tar.get('agreement'))}. Estimated saving: {saving_text(research)}."),
        "origin": (f"Rule of origin: {rule_text(research)}. Result: the product "
                   f"{ORIGIN_TEXT.get(res.get('status'), NOT_IN_SOURCES)}. {plain(res.get('basis'))}"),
        "notes": [{"text": n["text"], "from": [n["nid"]]} for n in notes if not n["mandatory"]],
    }


# ---------- rendering (code) ----------

class SourceList:
    """Numbers each source (by KB source key) in order of first citation."""

    def __init__(self, id_sources: dict[str, dict[str, str]], kb_sources: dict[str, dict]):
        self.id_sources = id_sources
        self.kb_sources = kb_sources
        self.order: list[tuple[str, str]] = []   # (source key, url)
        self.index: dict[str, int] = {}

    def refs(self, *evidence_ids) -> list[int]:
        nums = []
        for eid in evidence_ids:
            for key, url in (self.id_sources.get(eid) or {}).items():
                if key not in self.index:
                    self.order.append((key, url))
                    self.index[key] = len(self.order)
                if self.index[key] not in nums:
                    nums.append(self.index[key])
        return nums

    def lines(self) -> list[str]:
        out = []
        for i, (key, url) in enumerate(self.order, 1):
            title = (self.kb_sources.get(key) or {}).get("title") or key
            out.append(f"{i}. [{title}]({url})")
        return out


def cite(nums: list[int]) -> str:
    return (" " + "".join(f"[{n}]" for n in nums)) if nums else ""


def cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def render_report(research: dict, intake: dict, prose: dict, notes: list[dict],
                  id_sources: dict[str, dict[str, str]], kb_sources: dict[str, dict]) -> str:
    lang = "ar" if intake.get("language") == "ar" else "en"
    h, verdict = HEADINGS[lang], research["verdict"]
    src = SourceList(id_sources, kb_sources)
    cls, tar = research["classification"], research["tariff"]
    needed = list(research.get("follow_up_questions") or []) + list(research.get("gaps") or [])

    def needed_section() -> list[str]:
        return [f"## {h['needed']}", "", *[f"- {n}" for n in needed], ""] if needed else []

    out = [
        f"# {h['title']}: {plain(intake.get('product_description'))}",
        "",
        f"**{h['result']}: {RESULT_LABEL[lang].get(verdict, RESULT_LABEL[lang][GAP])}**",
        "",
        f"## {h['summary']}", "", prose["summary"].strip(), "",
    ]
    if verdict == "NEEDS_MORE_DATA":   # D4: lead with what the user must provide
        out += needed_section()

    out += [f"## {h['classification']}", "",
            prose["classification"].strip() + cite(src.refs(cls.get("source_id"))), ""]

    pref = plain(tar.get("preferential_rate"))
    if pref == "EXCLUDED":
        pref = "Excluded" if lang == "en" else "مستثنى"
    out += [f"## {h['duty']}", "",
            f"| {h['mfn']} | {h['cepa']} | {h['saving']} |",
            "|---|---|---|",
            f"| {plain(tar.get('mfn_rate'))} | {pref} | {saving_text(research)} |",
            "",
            prose["duty"].strip() + cite(src.refs(tar.get("source_id"),
                                                 research["estimated_saving"].get("source_id"))),
            ""]

    out += [f"## {h['origin']}", "",
            prose["origin"].strip() + cite(src.refs(research["origin_rule"].get("source_id"),
                                                   research["origin_result"].get("source_id"))),
            ""]

    steps = research.get("procedure") or []
    if verdict in CHECKLIST_VERDICTS and steps:   # D4: no checklist when no preference can be claimed
        out += [f"## {h['checklist']}", ""]
        for st in steps:
            authority = plain(st.get("authority"))
            nums = src.refs(st.get("source_id"))
            out.append(f"- [ ] {str(st.get('step', '')).strip()}  \n"
                       f"  *{h['authority']}: {cap(authority)}.*{cite(nums)}")
        out.append("")

    # 8.5: mandatory notes first, word for word; then the LLM's condensed optional notes.
    mandatory = [n for n in notes if n["mandatory"]]
    by_nid = {n["nid"]: n for n in notes if not n["mandatory"]}
    if mandatory or prose.get("notes"):
        out += [f"## {h['notes']}", ""]
        for n in mandatory:
            out.append(f"- {n['text']}{cite(src.refs(n['source_id']))}")
        for item in prose.get("notes") or []:
            nums = src.refs(*[by_nid[s]["source_id"] for s in item.get("from", []) if s in by_nid])
            out.append(f"- {item['text'].strip()}{cite(nums)}")
        out.append("")

    if verdict != "NEEDS_MORE_DATA":
        out += needed_section()

    out += [f"## {h['sources']}", "", *src.lines(), "",
            f"## {h['disclaimer']}", "", f"*{DISCLAIMER[lang]}*", ""]
    return "\n".join(out)


# ---------- the LLM call ----------

def build_messages(facts_text: str, language: str | None, *, previous: dict | None = None,
                   corrections: list[str] | None = None) -> list[dict]:
    messages = [
        {"role": "system", "content": build_system_prompt("document_builder", language)},
        {"role": "user", "content": facts_text},
    ]
    if corrections:
        messages.append({"role": "assistant", "content": json.dumps(previous, ensure_ascii=False)})
        messages.append({"role": "user", "content":
                         "CORRECTIONS (apply all of them, then return the full corrected JSON only):\n"
                         + "\n".join(f"- {c}" for c in corrections)})
    return messages


def run_document_builder(research: dict, intake: dict, id_sources: dict[str, dict[str, str]],
                         *, corridor: str = "india", llm=call_llm) -> BuilderResult:
    """Write the report for APPROVED Researcher output. Always returns a report.

    llm: the call function (tests pass a fake one).
    """
    research = copy.deepcopy(research)
    facts_text, notes = build_facts(research, intake)
    language = intake.get("language")
    calls: list[LLMResult] = []
    prose, problems = None, []

    for round_no in (1, 2):   # first pass, then at most one correction round
        try:
            res = llm("document_builder", "auto:long",
                      build_messages(facts_text, language, previous=prose,
                                     corrections=problems if round_no == 2 else None),
                      expect_json=True, required_keys=REQUIRED_KEYS)
        except LLMCallError as exc:
            log.warning("document builder | LLM call failed: %s", exc)
            problems = [f"LLM call failed: {exc}"]
            break
        calls.append(res)
        prose = res.data
        problems = check_prose(prose, facts_text, notes)
        log.info("document builder checks | round=%d | served_by=%s | problems=%d",
                 round_no, res.routed_via, len(problems))
        for p in problems:
            log.info("document builder problem | %s", p)
        if not problems:
            break

    used_fallback = bool(problems)
    if used_fallback:
        log.warning("document builder | using the code-only report (%d problem(s) left)", len(problems))
        prose = fallback_prose(research, notes)

    kb_sources = load_corridor(corridor)["sources"]
    md = render_report(research, intake, prose, notes, id_sources, kb_sources)
    return BuilderResult(markdown=md, prose=prose, notes=notes, used_fallback=used_fallback,
                         problems=problems if used_fallback else [], llm_calls=calls)
