"""Grade evaluation-set runs against their cases (evaluation set, sub-step 2). Pure code, no LLM.

`derive` runs the plain-Python tools for an intake (the answer key comes from code), `compare`
checks the facts against a case's key, and `grade` reads one saved pipeline run folder
(phase_log.json, intake.json, researcher_N.json, report.md / notice.md, evidence.txt) and
checks it against its case: status, verdict, intake, tools on the live intake, the
Researcher's facts, the report check, QA and prose QA coverage, privacy, case anchors.
Global anchors count known open problems as "slips" (decision D1 = A, 24 Oct): they do not
fail a case; reading confirms them.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from mansha.document_builder import saving_how
from mansha.evidence import build_evidence, is_excluded
from mansha.kb import corridor_for
from mansha.researcher import HS_QUESTION_RE, NOT_PRODUCT_CODE_RE, ORIGIN_MAP
from scripts.eval_cases import EvalCase


def _f(x):
    try:
        return float(str(x).replace(",", ""))
    except (TypeError, ValueError):
        return None


# ---------- the answer key from code ----------

def derive(case: EvalCase, intake: dict | None = None) -> dict:
    """The facts the tools produce for an intake (default: the case's expected intake)."""
    intake = case.intake if intake is None else intake
    facts: dict = {}
    if intake is None:
        return facts
    corridor = corridor_for(intake.get("destination_country"))
    facts["corridor"] = corridor
    if corridor is None:
        return facts
    if case.folder and not Path(case.folder).is_dir():
        raise FileNotFoundError(f"{case.id}: bill-of-materials folder {case.folder} is missing")
    pack = build_evidence(intake, case.folder, corridor)
    tl = pack.tool_results["TOOL:tariff_lookup"]
    facts["candidates"] = [c["id"] for c in pack.candidates]
    facts["tariff_notes"] = tl.get("notes") or []
    facts["evidence_text"] = pack.text

    line = case.key.get("line")
    cand = next((c for c in pack.candidates if c.get("tariff_line") == line), None) if line else None
    facts["line_found"] = cand is not None
    if cand:
        mfn, cepa = cand.get("mfn") or {}, cand.get("cepa") or {}
        facts.update(excluded=is_excluded(cand), hs2017=cand.get("hs2017_code"),
                     mfn_tariff=mfn.get("tariff_rate_pct"), mfn_effective=mfn.get("effective_rate_pct"),
                     cepa=cepa.get("rate_pct"), cepa_table=cepa.get("table"))
    elif pack.candidates and case.key.get("excluded") is not None:
        facts["excluded"] = all(is_excluded(c) for c in pack.candidates)

    o = pack.tool_results.get(f"TOOL:origin:{line}") if line else None
    facts["no_origin"] = o is None
    if o:
        checks: dict[str, str] = {}
        for ch in o.get("checks", []):
            checks.setdefault(ch["check"], ch["result"])
            if ch["check"] == "VA" and "va_build_down" not in facts:
                v = ch.get("values") or {}
                facts["va_build_down"], facts["va_threshold"] = v.get("build_down_pct"), v.get("threshold_pct")
        facts.update(origin=o.get("status"), checks=checks, origin_missing=o.get("missing") or [],
                     origin_notes=o.get("notes") or [])
    d = pack.tool_results.get(f"TOOL:duty:{line}") if line else None
    if d:
        facts.update(duty_status=d.get("status"), saving=_f(d.get("saving")), currency=d.get("currency"))
    fee = pack.tool_results.get("TOOL:coo_fee") or {}
    facts.update(fee_status=fee.get("status"), fee_aed=fee.get("fee_aed"))
    return facts


NUMERIC_KEYS = ("va_build_down", "va_threshold", "mfn_tariff", "mfn_effective", "cepa", "saving")
CONTAINS_KEYS = {"tariff_notes_contain": "tariff_notes", "origin_notes_contain": "origin_notes",
                 "origin_missing_contains": "origin_missing"}


def compare(case: EvalCase, facts: dict) -> list[str]:
    """Every way the tools' facts differ from the case's answer key."""
    out: list[str] = []
    for k, want in case.key.items():
        if k == "line":
            if not facts.get("line_found"):
                out.append(f"line {want} not among the candidates {facts.get('candidates')}")
        elif k == "checks":
            got = facts.get("checks") or {}
            out += [f"check {n}: expected {r}, got {got.get(n)}" for n, r in want.items() if got.get(n) != r]
        elif k in CONTAINS_KEYS:
            text = " | ".join(facts.get(CONTAINS_KEYS[k]) or [])
            out += [f"{CONTAINS_KEYS[k]} lacks {s!r}" for s in want if s not in text]
        elif k in NUMERIC_KEYS:
            if _f(facts.get(k)) != _f(want):
                out.append(f"{k}: expected {want}, got {facts.get(k)}")
        elif facts.get(k) != want:
            out.append(f"{k}: expected {want!r}, got {facts.get(k)!r}")
    return out


def bom_rows(case: EvalCase) -> list[dict]:
    if not case.folder or not (Path(case.folder) / "bom.csv").exists():
        return []
    with (Path(case.folder) / "bom.csv").open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def supplier_leaks(case: EvalCase, text: str) -> list[str]:
    """Supplier names from the bill of materials must never reach a prompt or a saved file."""
    return [f"supplier {r['supplier']!r} appears" for r in bom_rows(case)
            if r.get("supplier") and r["supplier"] in text]


def value_pattern(v: float) -> re.Pattern:
    """An input amount written with or without thousands separators, not inside a bigger number."""
    n = int(v)
    forms = {str(n), f"{n:,}"}
    alt = "|".join(re.escape(x) for x in sorted(forms, key=len, reverse=True))
    return re.compile(rf"(?<![\d.,])(?:{alt})(?:\.0+)?(?![\d,]|\.\d)")


TOOL_FIGURES_RE = re.compile(r"^\[TOOL:(?:duty:[^\]\n]+|coo_fee)\]\n(.*?)(?=^\[|^===|\Z)", re.M | re.S)
AMOUNT_RE = re.compile(r"(?<![\d.,])\d[\d,]*(?:\.\d+)?")


def tool_figures(evidence: str) -> set[float]:
    """Amounts the duty and certificate-fee tools printed. Both work only from the tariff line and the
    shipment value the user gave (never the bill of materials), so these figures are not input costs
    (25 Oct: N5's saving 10000.00 AED equals the synthetic 'Paint additives' value, AED 10,000)."""
    out = set()
    for block in TOOL_FIGURES_RE.findall(evidence or ""):
        for line in block.splitlines():
            if line.startswith(("notes:", "- ")):
                continue
            out |= {float(x.replace(",", "")) for x in AMOUNT_RE.findall(line)}
    return out


def value_leaks(case: EvalCase, text: str, message: str, allowed: set[float] = frozenset()) -> list[str]:
    """Individual bill-of-materials amounts (1,000 or more, not stated in the message) in a text.
    An amount equal to a duty/fee tool figure (`allowed`) is skipped: the grader can't tell the two
    apart, so a real leak of exactly that value would be missed (recorded limit, 25 Oct)."""
    out = []
    for r in bom_rows(case):
        v = _f(r.get("value"))
        if v is None or v < 1000 or not float(v).is_integer():
            continue
        if float(v) in allowed:
            continue
        pat = value_pattern(v)
        if pat.search(message):
            continue
        m = pat.search(text)
        if m:
            out.append(f"input amount {m.group(0)} ({r['input_description']}) appears")
    return out


# ---------- a saved run ----------

@dataclass
class Run:
    folder: Path
    status: str
    verdict: str | None
    seconds: float
    warnings: list[str]
    phases: list[dict]
    message: str
    intake: dict | None
    research: dict | None        # the last Researcher round's JSON output
    output: str                  # report.md or notice.md
    evidence: str


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def load_run(folder: str | Path) -> Run:
    folder = Path(folder)
    log = _json(folder / "phase_log.json") or {}
    rounds = sorted(folder.glob("researcher_*.json"), key=lambda p: int(re.sub(r"\D", "", p.stem) or 0))
    research = (_json(rounds[-1]) or {}).get("output") if rounds else None
    intake = (_json(folder / "intake.json") or {}).get("output")
    out = folder / ("report.md" if (folder / "report.md").exists() else "notice.md")
    txt = lambda p: p.read_text(encoding="utf-8") if p.exists() else ""
    return Run(folder, log.get("status"), log.get("verdict"), log.get("seconds") or 0.0,
               log.get("warnings") or [], log.get("phases") or [], txt(folder / "message.txt"),
               intake, research, txt(out), txt(folder / "evidence.txt"))


# ---------- anchors ----------

GLOBAL_ANCHORS = {  # open problem -> pattern on the report (counted as slips, D1 = A)
    # 72: MoFT named as the provider of the 'Certificate of Origin for India' e-service (that page is
    # MoET's), in either order within one sentence. The service name is case-sensitive: "MoFT issues
    # the certificate of origin for India" is decision C, not problem 72. Widened 25 Oct: 33 of 63 saved
    # reports, 0 false alarms, 1 known miss (a claim spread over two sentences, left to reading).
    "72": re.compile(r"Ministry of Foreign Trade(?:'s)?\b[^.\n]{0,160}?'?Certificate of Origin for India"
                     r"|Certificate of Origin for India'?[^.\n]{0,60}?\b(?:via|through|on|at) the Ministry of Foreign Trade"),
    "86": re.compile(r"\bCEPA (?:provides|sets|gives|has|specifies) (?:a|the) normal", re.I),
    "93": re.compile(r"exchange rate|(?:in|into) (?:a different|another|a second) currency|"
                     r"\bconvert(?:ed|ing)? (?:the |your )?(?:value|amount|shipment|price)", re.I),
    "94": re.compile(r"^- \[ \] (?:\*\*)?The Ministry of [^:\n]{3,50}:\s|requires the applicant to log in|"
                     r"\*Authority: Not in Mansha's sources", re.I | re.M),
    # 95: a pointer to a checklist that isn't where it says. Widened 26 Oct: "checklist and details below"
    # (N7) and any report with no checklist section (C4 NO_PREFERENCE): 90 saved reports, those 2 new hits,
    # 0 false alarms. Widened again 26 Oct: "see / refer to / consult / check / review / follow the (claim)
    # checklist" without "below" (N10 "Please see the checklist for the required information"): 1 new hit, 0 false alarms.
    "95": re.compile(r"checklist\b[^.\n]{0,20}?\bbelow|\b(?:see|refer to|consult|check|review|follow)\s+the (?:claim )?checklist\b|"
                     r"bill of materials[^.\n]{0,60}needed to estimate the (?:duty )?saving", re.I),
    "G12": re.compile(r"\bAIDC\b|Agricultur\w* Infrastructure", re.I),
    # 96: the box-8/9 KB note turned into an instruction to the exporter (added 25 Oct: 10 of 63 saved
    # reports, 0 false alarms). The KB's own "India's form say/use box 9" and the descriptive "require
    # box 9" stay unflagged (reading).
    "96": re.compile(r"\byou (?:must|should|need to) use box 9\b|(?<!form )(?<!forms )\buse box 9\b|"
                     r"\bbox 9 (?:to be completed|must be used|should be used)\b|"
                     # KB batch (27 Oct): "you must follow India's form" (163642 N5) was missed.
                     r"\byou (?:must|should|need to) follow India['\u2019]?s (?:certificate )?form\b", re.I),
}
NEEDS_MORE_DATA_ONLY = {"95"}      # "checklist below" is right in an ELIGIBLE report (it has one); also counted
                                   # in any report with no checklist section
CHECKLIST_RE = re.compile(r"^## .*(?:checklist|قائمة)", re.I | re.M)
TABLE_RE = re.compile(r"\(table (I{1,3}), S\.No\.")


def tariff_notes_from_evidence(evidence: str) -> str | None:
    """The tariff lookup record's notes ('none' when it wrote none), from the saved evidence."""
    m = re.search(r"^\[TOOL:tariff_lookup\]\n(.*?)(?=^\[|^===|\Z)", evidence, re.M | re.S)
    if not m:
        return None
    n = re.search(r"^notes:(.*)", m.group(1), re.M | re.S)
    return n.group(1).strip() if n else None


def chosen_table(run: Run) -> str | None:
    """Table I/II/III of the chosen tariff line's CEPA row, read from the saved evidence."""
    rid = ((run.research or {}).get("classification") or {}).get("source_id")
    if not rid:
        return None
    m = re.search(rf"^\[{re.escape(rid)}\]\n(.*?)(?=^\[|^===|\Z)", run.evidence, re.M | re.S)
    t = TABLE_RE.search(m.group(1)) if m else None
    return t.group(1) if t else None


def slips(run: Run) -> dict[str, list[str]]:
    """Hits of the global anchors (known open problems) in a report; empty for non-reports."""
    out: dict[str, list[str]] = {}
    if run.status != "REPORT":
        return out
    text = run.output
    for pid, pat in GLOBAL_ANCHORS.items():
        if pid in NEEDS_MORE_DATA_ONLY and run.verdict != "NEEDS_MORE_DATA" and CHECKLIST_RE.search(text):
            continue
        if pid == "G12" and chosen_table(run) != "I":
            continue
        hits = [m.group(0) for m in pat.finditer(text)]
        if hits:
            out[pid] = hits
    hits = [m.group(0) for m in saving_how(text)]
    if hits:
        out["67"] = hits
    notes = tariff_notes_from_evidence(run.evidence)
    if notes == "none":
        qs = (run.research or {}).get("follow_up_questions") or []
        hs = [q for q in qs if isinstance(q, str) and HS_QUESTION_RE.search(q) and not NOT_PRODUCT_CODE_RE.search(q)]
        if hs:
            out["92"] = hs
    return out


# Case anchors (decision D2 = A): code patterns only where a pattern is safe; the rest is reading.
NO_CLAIM_VERDICTS = {"NOT_ELIGIBLE", "NO_PREFERENCE", "REGULATORY_GAP_DETECTED"}
CASE_ANCHORS: dict[str, list[tuple[str, str, re.Pattern]]] = {
    # (label, "not" | "must", pattern)
    "N1": [("an AED amount for the shipment or saving", "not",
            re.compile(r"\d[\d,.]*\s?AED\b|\bAED\s?(?:\d{4,}|\d{1,3},\d{3})"))],  # the fee range "AED 10 to AED 200" is fine
    # 27 Oct (163642): "does not eliminate it" is the right wording, not a removal claim (negation guard;
    # saved reports: 2 negated, 0 plain)
    "N2": [("duty removed wording", "not",
            re.compile(r"duty[- ]free|(?<!not )(?<!n't )\beliminat\w*|\bno (?:customs |import )?duty\b|"
                       r"\bcannot claim\b", re.I)),
           # problem 97 (Haris option ii, 25 Oct): the free-zone doubt must reach the summary, not only a note
           ("the free-zone caution in the summary", "must",
            re.compile(r"^## (?:Summary|الملخص)[^\S\n]*\n(?:(?!## )[^\n]*\n)*?(?!## )[^\n]*free[- ]zone", re.I | re.M))],
    # problem 97 (25 Oct, same class as N2): the verdict depends on the Indian resin counting as
    # originating, so the proof condition must reach the summary, not only a note
    "N5": [("the Indian-origin proof condition in the summary", "must",
            re.compile(r"^## (?:Summary|الملخص)[^\S\n]*\n(?:(?!## )[^\n]*\n)*?(?!## )[^\n]*"
                       r"(?:\bproof\b|\bcumulat\w*|\bIndian[- ](?:input|resin|material|origin)|"
                       r"\b(?:resin|inputs?|materials?) (?:bought|sourced|made|purchased) (?:in|from) India|"
                       r"\boriginat\w* in India)", re.I | re.M))],
    # G9 (fix round, 26 Oct; Haris: re-mark A): the user attached the BOM and only row 2's HS code is
    # missing, so a whole bill of materials must not be asked for (3 of 3 repeats, baseline clean).
    # N10 only: the same ask is right when no BOM was given (C3 windows_nodata, 18 saved reports).
    "N10": [("a whole bill of materials asked for", "not",
             re.compile(r"\bbill of materials (?:with|showing|listing|including|giving) [^.\n]{0,80}?\beach input|"
                        r"\b(?:a |the )?(?:full|complete|whole|new) bill of materials", re.I))],
    "N3": [("a saving from the 15% tariff rate", "not", re.compile(r"(?<![\d,])15,?000(?:\.00)?(?![\d,])"))],
    "N4": [("45% applied as the threshold", "not",
            re.compile(r"against (?:a |the )?(?:threshold of |minimum of )?45\s?%|45\s?% threshold (?:applied|used)", re.I)),
           ("the Ex-Works threshold of 40%", "must", re.compile(r"\b40\s?%"))],
    "S3": [("the Ministry of Foreign Trade's CEPA list link", "must", re.compile(r"trade\.gov\.ae"))],
}


def case_anchor_problems(case: EvalCase, run: Run) -> list[str]:
    out = []
    for label, mode, pat in CASE_ANCHORS.get(case.id, []):
        m = pat.search(run.output)
        if mode == "not" and m:
            out.append(f"must not say {label}: {m.group(0)!r}")
        elif mode == "must" and not m:
            out.append(f"must say {label}")
    if run.status == "REPORT" and case.verdict in NO_CLAIM_VERDICTS and CHECKLIST_RE.search(run.output):
        out.append("a claim checklist in a report whose verdict allows no claim")
    return out


# ---------- grading ----------

@dataclass
class Grade:
    case: EvalCase
    run: Run
    checks: list[tuple[str, bool, str]] = field(default_factory=list)   # (name, ok, detail)
    slips: dict[str, list[str]] = field(default_factory=dict)
    cost: dict = field(default_factory=dict)

    @property
    def failed(self) -> list[tuple[str, bool, str]]:
        return [c for c in self.checks if not c[1]]

    @property
    def passed(self) -> bool:
        return not self.failed

    def add(self, name: str, problems: list[str]) -> None:
        self.checks.append((name, not problems, "; ".join(problems)))


def intake_problems(case: EvalCase, got: dict | None) -> list[str]:
    want = case.intake
    if want is None:
        return []
    if got is None:
        return ["no Intake output"]
    out = []
    digits = lambda s: re.sub(r"\D", "", s or "")
    if digits(want.get("hs_code_given")) != digits(got.get("hs_code_given")):
        out.append(f"hs_code_given {got.get('hs_code_given')!r}, expected {want.get('hs_code_given')!r}")
    wc, gc = corridor_for(want.get("destination_country")), corridor_for(got.get("destination_country"))
    if wc != gc or (wc is None and not got.get("destination_country")):
        out.append(f"destination {got.get('destination_country')!r}, expected {want.get('destination_country')!r}")
    if want.get("language") != got.get("language"):
        out.append(f"language {got.get('language')!r}, expected {want.get('language')!r}")
    wv, gv = want.get("shipment_value"), got.get("shipment_value")
    if (wv is None) != (gv is None) or (wv and (_f(wv.get("amount")) != _f(gv.get("amount"))
                                              or wv.get("currency") != gv.get("currency"))):
        out.append(f"shipment_value {gv!r}, expected {wv!r}")
    return out


def researcher_problems(case: EvalCase, research: dict | None) -> list[str]:
    if research is None:
        return ["no Researcher output"]
    out = []
    cls = research.get("classification") or {}
    line = case.key.get("line")
    if line and case.verdict != "REGULATORY_GAP_DETECTED" and cls.get("tariff_line") != line:
        out.append(f"tariff line {cls.get('tariff_line')!r}, expected {line!r}")
    o = (research.get("origin_result") or {}).get("status")
    want_o = "NOT_APPLICABLE" if case.key.get("excluded") else ORIGIN_MAP.get(case.key.get("origin"))
    if want_o and case.verdict != "REGULATORY_GAP_DETECTED" and o != want_o:
        out.append(f"origin_result {o!r}, expected {want_o!r}")
    s = research.get("estimated_saving") or {}
    if case.saving_status and s.get("status") != case.saving_status:
        out.append(f"estimated_saving {s.get('status')!r}, expected {case.saving_status!r}")
    if case.saving_status == "ESTIMATED" and case.key.get("saving") is not None \
            and _f(s.get("amount")) != _f(case.key["saving"]):
        out.append(f"saving amount {s.get('amount')!r}, expected {case.key['saving']}")
    return out


def phase_list(run: Run, prefix: str) -> list[dict]:
    return [p for p in run.phases if p["name"].startswith(prefix)]


def attempts(run: Run):
    for p in run.phases:
        for c in p.get("calls") or []:
            for a in c.get("attempts") or []:
                yield p, a


def review_problems(run: Run, prefix: str, allowed: set[str]) -> list[str]:
    """Every QA (or prose QA) phase reviewed: allowed statuses only, nothing NOT reviewed.

    A router refusal (HTTP 429) that the client's retry got past is not a failure: the review
    happened. It is counted in cost()["refusals"] and the summary (Haris, 24 Oct 19:21, E3 changed).
    A refusal the retry did not get past leaves the part NOT reviewed, which fails here."""
    out = []
    phases = phase_list(run, prefix)
    if not phases:
        return [f"no {prefix} phase"]
    for p in phases:
        if p["status"] not in allowed:
            out.append(f"{p['name']} {p['status']}")
        if "NOT reviewed" in json.dumps(p, ensure_ascii=False):
            out.append(f"{p['name']}: NOT reviewed")
    return out


ARABIC_RE, LATIN_RE = re.compile(r"[؀-ۿ]"), re.compile(r"[A-Za-z]")


def language_problems(case: EvalCase, run: Run) -> list[str]:
    want = (case.intake or {}).get("language", "en")
    body = re.sub(r"\(https?://[^)]*\)|https?://\S+", "", run.output)
    ar, la = len(ARABIC_RE.findall(body)), len(LATIN_RE.findall(body))
    if want == "ar" and ar <= la:
        return [f"expected Arabic, found {ar} Arabic and {la} Latin letters"]
    if want == "en" and ar > 0:
        return [f"{ar} Arabic letters in an English output"]
    return []


def cost(run: Run) -> dict:
    out: dict = {"refusals": 0, "paced_wait_s": 0.0}
    for p, a in attempts(run):
        ch = out.setdefault(a.get("chain") or "?", {"requests": 0, "prompt": 0, "completion": 0})
        ch["requests"] += 1
        u = a.get("usage") or {}
        ch["prompt"] += u.get("prompt") or 0
        ch["completion"] += u.get("completion") or 0
        if not a.get("ok") and a.get("http_status") == 429:
            out["refusals"] += 1
        out["paced_wait_s"] += a.get("paced_wait_s") or 0.0
    return out


SAVED_TEXTS = ("evidence.txt", "researcher_*.json", "qa_*.json", "prose_qa_*.json", "builder.json",
               "report.md", "notice.md", "phase_log.json", "phase_log.md", "intake.json")


def grade(case: EvalCase, run: Run) -> Grade:
    g = Grade(case, run)
    g.add("status", [] if run.status == case.status else [f"{run.status}, expected {case.status}"])
    if case.verdict:
        g.add("verdict", [] if run.verdict == case.verdict else [f"{run.verdict}, expected {case.verdict}"])
    if case.intake is not None:
        g.add("intake", intake_problems(case, run.intake))
        if run.intake and corridor_for(run.intake.get("destination_country")):
            g.add("tools", compare(case, derive(case, run.intake)))
    if case.status == "REPORT" and run.status == "REPORT":
        g.add("researcher", researcher_problems(case, run.research))
        check = next((p for p in run.phases if p["name"] == "Report check"), None)
        g.add("report check", ["no report check"] if check is None else
              [f"{len(check.get('problems') or [])} problem(s): " + "; ".join(check.get("problems") or [])]
              if check.get("problems") else [])
        g.add("QA", review_problems(run, "QA", {"OK", "REJECTED", "OVERRULED", "SETTLED"}))
        g.add("prose QA", review_problems(run, "Prose QA", {"OK", "REJECTED"}))
    if run.output:
        g.add("language", language_problems(case, run))
    texts = []
    for pat in SAVED_TEXTS:
        texts += [p.read_text(encoding="utf-8") for p in run.folder.glob(pat)]
    llm_side = run.evidence + json.dumps(run.research or {}, ensure_ascii=False) + run.output
    g.add("privacy", supplier_leaks(case, "\n".join(texts)) + value_leaks(case, llm_side, run.message,
                                                                                  tool_figures(run.evidence)))
    g.add("anchors", case_anchor_problems(case, run))
    g.slips = slips(run)
    g.cost = cost(run)
    return g
