"""Build the EVIDENCE block the Researcher reads (Step 6.2).

Runs the deterministic tools for every candidate tariff line, renders their
results and the knowledge-base records as compact text (each record headed by
its ID in square brackets), and returns the IDs the Researcher may cite.

No LLM here. The origin calculator only outputs totals and percentages, so the
bill of materials (supplier names, individual input costs) never reaches a prompt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from mansha.kb import load_corridor
from mansha.tools.duty_estimate import duty_estimate
from mansha.tools.origin_calculator import origin_from_folder
from mansha.tools.rule_lookup import rule_lookup
from mansha.tools.tariff_lookup import tariff_lookup

# A record header is a line that starts with "[ID]".
HEADER_RE = re.compile(r"^\[([^\]\n]+)\]", re.MULTILINE)

EXCLUDED_TEXT = "EXCLUDED (no preferential rate; the normal MFN rate applies)"


@dataclass
class EvidencePack:
    text: str                              # the EVIDENCE block for the prompt
    allowed_ids: list[str]                 # every citable ID, in order of appearance
    id_sources: dict[str, dict[str, str]]  # evidence ID -> {source key: URL}
    tool_results: dict[str, dict]          # tool_id -> raw tool result (for code checks)
    candidates: list[dict]                 # candidates from the tariff lookup
    excluded_ids: set[str] = field(default_factory=set)  # candidate IDs with no CEPA preference


# ---------- formatting helpers ----------

def fmt_num(x) -> str:
    """Show numbers exactly as the tool gave them, without a trailing '.0'."""
    if x is None:
        return "not available"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x)


def pct(x) -> str:
    return "not available" if x is None else f"{fmt_num(x)}%"


def spaced(line: str | None) -> str:
    """'76101000' -> '7610 10 00' (display only)."""
    if line and len(line) == 8 and line.isdigit():
        return f"{line[:4]} {line[4:6]} {line[6:]}"
    return str(line)


def bullets(label: str, items) -> str:
    items = [i for i in (items or []) if i]
    if not items:
        return f"{label}: none"
    return f"{label}:\n" + "\n".join(f"- {i}" for i in items)


def kv(d: dict | None) -> str:
    if not d:
        return "none"
    return "; ".join(f"{k}: {fmt_num(v)}" for k, v in d.items())


def fmt_value(v) -> str:
    """Readable rendering for parameter values (lists, dicts, None)."""
    if v is None:
        return "none"
    if isinstance(v, list):
        if v and all(isinstance(x, dict) for x in v):
            return " | ".join(", ".join(f"{k} {fmt_value(y)}" for k, y in x.items()) for x in v)
        if v and all(isinstance(x, str) and " " in x for x in v):
            return " → ".join(v)  # ordered steps, no invented numbering
        return ", ".join(fmt_value(x) for x in v)
    if isinstance(v, dict):
        return ", ".join(f"{k} {fmt_value(y)}" for k, y in v.items())
    return fmt_num(v)


def render_params(params: dict) -> str:
    return bullets("parameters", [f"{k}: {fmt_value(v)}" for k, v in params.items()])


def is_excluded(c: dict) -> bool:
    return c.get("kind") == "heading_exclusion" or (c.get("cepa") or {}).get("status") == "EXCLUDED"


def passages_of(kb: dict) -> list[dict]:
    p = kb["passages"]
    return p if isinstance(p, list) else p.get("passages", [])


def select_passages(kb: dict, intake: dict) -> list[dict]:
    """All passages for now (one small corridor). Milestone 4: search by tags/embeddings."""
    return passages_of(kb)


# ---------- record renderers (each returns the lines under the [ID] header) ----------

def render_tariff_lookup(tl: dict) -> list[str]:
    q = tl.get("query") or {}
    ids = [c["id"] for c in tl.get("candidates", [])]
    return [
        f"status: {tl.get('status')} (method: {tl.get('method')})",
        f"query: product \"{q.get('product_description')}\", HS code given: {q.get('hs_code_given') or 'none'}",
        "candidates (best match first): " + (", ".join(ids) if ids else "none"),
        bullets("notes", tl.get("notes")),
    ]


def render_candidate(c: dict, meta: dict) -> list[str]:
    if c.get("kind") == "heading_exclusion":
        lines = [
            f"agreement: {meta.get('agreement')}",
            f"heading: {c.get('heading')}",
            f"CEPA status: {EXCLUDED_TEXT}",
        ]
        if c.get("evidence"):
            lines.append(f"evidence: {c['evidence']}")
        lines.append(bullets("notes", c.get("notes")))
        return lines

    mfn = c.get("mfn") or {}
    cepa = c.get("cepa") or {}
    lines = [
        f"agreement: {meta.get('agreement')}",
        f"tariff line: {c.get('tariff_line')} ({spaced(c.get('tariff_line'))})",
        f"description: {c.get('description')}",
        f"MFN rate: tariff {pct(mfn.get('tariff_rate_pct'))}, effective {pct(mfn.get('effective_rate_pct'))}",
    ]
    if cepa.get("status") == "EXCLUDED":
        lines.append(f"CEPA status: {EXCLUDED_TEXT}")
    else:
        lines.append(
            f"CEPA status: {cepa.get('status')}; 2026 CEPA rate {pct(cepa.get('rate_pct'))} "
            f"(table {cepa.get('table')}, S.No. {cepa.get('s_no')})"
        )
    if (c.get("staging") or {}).get("category"):
        lines.append(f"staging: {c['staging']['category']}")
    if c.get("hs2017_code"):
        lines.append(f"HS 2017 code: {c['hs2017_code']}")
    if meta.get("data_checked"):
        lines.append(f"data checked: {meta['data_checked']}")
    lines.append(f"how it matched the query: {c.get('match')}")
    lines.append(bullets("notes", c.get("notes")))
    return lines


def render_rule_lookup(r: dict) -> list[str]:
    applying = [g["id"] for g in r.get("general_rules", []) if g.get("applies_to_this_line")]
    rule_ids = [x["id"] for x in r.get("rules", [])]
    return [
        f"tariff line: {r.get('tariff_line')}",
        f"status: {r.get('status')} (level: {r.get('level')})",
        "product-specific rule: " + (", ".join(rule_ids) if rule_ids else "none"),
        "general rules applying to this line: " + (", ".join(applying) if applying else "none"),
        bullets("interpretations", r.get("interpretations")),
        bullets("notes", r.get("notes")),
    ]


def render_check(ch: dict) -> str:
    s = f"{ch.get('check')}: {ch.get('result')} - {ch.get('basis')}"
    if ch.get("values"):
        s += f" [{kv(ch['values'])}]"
    if ch.get("alternative"):  # only shown for 2nd+ alternatives (0 = the only/first one)
        s += f" (rule alternative index {ch['alternative']})"
    if ch.get("source_id"):
        s += f" (see {ch['source_id']})"
    return s


def render_origin(o: dict) -> list[str]:
    return [
        f"tariff line: {o.get('tariff_line')}",
        f"status: {o.get('status')}",
        f"rule: {o.get('rule_id') or 'none'} \"{o.get('rule_text') or ''}\"",
        bullets("checks", [render_check(ch) for ch in o.get("checks", [])]),
        f"totals: {kv(o.get('totals'))}",
        bullets("missing", o.get("missing")),
        bullets("notes", o.get("notes")),
    ]


def render_duty(d: dict) -> list[str]:
    cepa = d.get("cepa_rate_pct")
    cepa_txt = "none (excluded)" if cepa is None and d.get("status") == "NO_PREFERENCE" else pct(cepa)
    cur = d.get("currency") or ""
    lines = [
        f"tariff line: {d.get('tariff_line')}",
        f"status: {d.get('status')}",
        (
            f"rates: MFN effective {pct(d.get('mfn_rate_pct'))}, CEPA {cepa_txt}; "
            f"difference {fmt_num(d.get('rate_difference_pts'))} percentage points"
        ),
    ]
    if d.get("shipment_value") is not None:
        lines += [
            f"shipment value: {d['shipment_value']} {cur}",
            (
                f"duty without CEPA: {fmt_num(d.get('duty_without_cepa'))} {cur}; "
                f"duty with CEPA: {fmt_num(d.get('duty_with_cepa'))} {cur}; "
                f"saving: {fmt_num(d.get('saving'))} {cur}"
            ),
        ]
    else:
        lines.append("shipment value: not given")
    lines.append(bullets("notes", d.get("notes")))
    return lines


def render_psr(rule: dict) -> list[str]:
    scope = dict(rule.get("scope") or {})
    kind = scope.pop("type", "scope")
    return [
        f"row {rule.get('row')} of the product-specific rules table",
        f"applies to: {kind} {' '.join(str(v) for v in scope.values())}",
        f"rule: \"{rule.get('rule_text')}\"",
        bullets("notes", rule.get("notes")),
    ]


def render_general(g: dict) -> list[str]:
    lines = [f"text: \"{g.get('text')}\"", f"provision: {g.get('provision')}"]
    if g.get("params"):
        lines.append(render_params(g["params"]))
    return lines


def render_item(it) -> str:
    if not isinstance(it, dict):
        return str(it)
    code = it.get("code")
    rest = it.get("text") or "; ".join(str(v) for k, v in it.items() if k != "code")
    return f"({code}) {rest}" if code else rest


def render_passage(p: dict) -> list[str]:
    lines = [f"title: {p.get('title')}", f"provision: {p.get('provision')}"]
    quotes = [f"\"{q['text']}\"" if isinstance(q, dict) else f"\"{q}\"" for q in p.get("quotes", [])]
    if quotes:
        lines.append(bullets("quotes", quotes))
    if p.get("items"):
        lines.append(bullets("items", [render_item(i) for i in p["items"]]))
    lines.append(f"summary: {p.get('summary')}")
    if p.get("params"):
        lines.append(render_params(p["params"]))
    lines.append(bullets("notes", p.get("notes")))
    return lines


# ---------- builder ----------

class _Builder:
    def __init__(self, kb: dict):
        self.kb = kb
        self.parts: list[str] = []
        self.ids: list[str] = []
        self.id_sources: dict[str, dict[str, str]] = {}

    def urls(self, keys) -> dict[str, str]:
        out = {}
        for k in keys or []:
            src = self.kb["sources"].get(k)
            if src:
                out[k] = src["url"]
        return out

    def section(self, title: str) -> None:
        self.parts.append(f"=== {title} ===")

    def add(self, rid: str, lines: list[str], sources: dict[str, str]) -> None:
        if rid in self.id_sources:  # each ID appears once
            return
        self.ids.append(rid)
        self.id_sources[rid] = dict(sources or {})
        self.parts.append("\n".join([f"[{rid}]", *lines]))


def build_evidence(intake: dict, case_folder: str | Path | None = None,
                   corridor: str = "india") -> EvidencePack:
    """Run the tools for every candidate and build the EVIDENCE block.

    intake: the normalized Intake JSON (product_description, hs_code_given, shipment_value).
    case_folder: folder with bom.csv / declaration.json, or None (origin -> INSUFFICIENT_DATA).
    """
    kb = load_corridor(corridor)
    meta = kb["tariff"]["metadata"]
    b = _Builder(kb)
    tool_results: dict[str, dict] = {}
    excluded: set[str] = set()
    psr_rules: dict[str, dict] = {}

    tl = tariff_lookup(product_description=intake.get("product_description"),
                       hs_code_given=intake.get("hs_code_given"), corridor=corridor).to_dict()
    tool_results[tl["tool_id"]] = tl
    candidates = tl.get("candidates", [])

    # 1. Tariff lookup and candidate lines (classification happens from these).
    b.section("TARIFF LOOKUP")
    merged = {}
    for c in candidates:
        merged.update(c.get("sources") or {})
    b.add(tl["tool_id"], render_tariff_lookup(tl), merged)

    b.section("CANDIDATE TARIFF LINES (classify from these descriptions first)")
    for c in candidates:
        b.add(c["id"], render_candidate(c, meta), c.get("sources") or b.urls(c.get("source_keys")))
        if is_excluded(c):
            excluded.add(c["id"])

    # 2. Tool results per candidate. Excluded lines: duty only.
    b.section("TOOL RESULTS PER CANDIDATE")
    for c in candidates:
        line = c.get("tariff_line")
        if not line:
            continue
        if c["id"] not in excluded:
            r = rule_lookup(line, corridor).to_dict()
            tool_results[r["tool_id"]] = r
            b.add(r["tool_id"], render_rule_lookup(r), r.get("sources"))
            for rule in r.get("rules", []):
                psr_rules.setdefault(rule["id"], rule)

            o = origin_from_folder(line, case_folder, corridor).to_dict()
            tool_results[o["tool_id"]] = o
            b.add(o["tool_id"], render_origin(o), o.get("sources"))

        d = duty_estimate(line, intake.get("shipment_value"), corridor).to_dict()
        tool_results[d["tool_id"]] = d
        b.add(d["tool_id"], render_duty(d), d.get("sources"))

    # 3. Rules of origin (deduplicated) and the general rules.
    b.section("RULES OF ORIGIN")
    for rule in psr_rules.values():
        b.add(rule["id"], render_psr(rule), b.urls([rule.get("source_key")]))
    for g in kb["psr"]["general_rules"]:
        b.add(g["id"], render_general(g), b.urls([g.get("source_key")]))

    # 4. Passages from the agreement, India's rules and UAE service pages.
    b.section("PASSAGES")
    for p in select_passages(kb, intake):
        b.add(p["id"], render_passage(p), b.urls(p.get("source_keys")))

    return EvidencePack(
        text="\n\n".join(b.parts),
        allowed_ids=b.ids,
        id_sources=b.id_sources,
        tool_results=tool_results,
        candidates=candidates,
        excluded_ids=excluded,
    )