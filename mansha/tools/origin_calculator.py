"""Origin calculator. Pure code, no LLM.

Applies the agreement's rules of origin for ONE tariff line to a bill of
materials (BOM) and the exporter's declaration. Returns MEETS / FAILS /
INSUFFICIENT_DATA / RULE_GAP with the totals and percentages it used.

Data protection: supplier names and individual input values never leave this
module. Results contain only totals, percentages, descriptions and HS codes.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from mansha.kb import load_corridor
from mansha.tools.rule_lookup import rule_lookup

TOOL_PREFIX = "TOOL:origin"
# The tool's fixed notes (named so the Arabic report can match them: document_builder.NOTE_AR_DRAFTS).
INDIAN_INPUTS_NOTE = ("Indian inputs count as originating only with proof of their originating status "
                      "(bilateral cumulation, Art. 3.7).")
OWN_DECLARATION_NOTE = "Operations and final manufacture are the exporter's own declaration."
FREE_ZONE_NOTE = ("Factory declared in a free zone: likely not eligible for the ministry's factory "
                  "registration; confirm with the ministry.")
PARTIES = {"AE", "IN"}  # bilateral cumulation: UAE and India inputs count as originating
NOM_BASES = {"CIF", "FIRST_PRICE"}  # Art. 3.1: CIF, else first price paid in a Party
BOM_COLUMNS = ("input_description", "hs_code", "origin_country", "value", "currency", "value_basis")
BEYOND_MINIMAL = "beyond_minimal"

P_MINIMAL = "P-AGR-3.5-MINIMAL"
P_VA = "P-AGR-3.2.2-VA"
P_NOM = "P-AGR-3.1-NOM"
P_DEMIN = "P-AGR-3.4-DEMINIMIS"

PASS, FAIL, NOT_EVALUATED = "PASS", "FAIL", "NOT_EVALUATED"


@dataclass
class OriginResult:
    tool_id: str
    tariff_line: str
    status: str  # MEETS | FAILS | INSUFFICIENT_DATA | RULE_GAP
    rule_id: str | None = None
    rule_text: str | None = None
    checks: list[dict] = field(default_factory=list)
    totals: dict = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    # Problem 97: conditions that decide whether the result can be used (FREE_ZONE, INDIAN_INPUTS).
    # The Builder's code prints a fixed caution for each in the summary; the notes above stay as they are.
    conditions: list[str] = field(default_factory=list)
    sources: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------- helpers ----------

def _num(x):
    if x is None:
        return None
    try:
        return float(str(x).replace(",", "").strip())
    except ValueError:
        return None


def _passage(kb: dict, pid: str) -> dict:
    for p in kb["passages"]["passages"]:
        if p["id"] == pid:
            return p
    raise KeyError(f"passage {pid} missing from the knowledge base")


def _minimal_ops_text(kb: dict, codes: list[str]) -> str:
    """'(b) changes of packaging ...; (l) affixing ...' from the agreement's own list (Art. 3.5.1).

    Exporters never see the bare letters. ' / ' in a stored quote marks a line break.
    """
    items = {it["code"]: it["text"] for it in _passage(kb, P_MINIMAL).get("items", [])}
    parts = []
    for code in codes:
        text = " ".join(items.get(code, "").replace(" / ", " ").split()).rstrip(";,. ")
        text = text.removesuffix("; or").removesuffix(" or").rstrip(";,. ")
        parts.append(f"({code}) {text}" if text else f"({code})")
    return "; ".join(parts)


def _passage_by_provision(kb: dict, text: str) -> str | None:
    for p in kb["passages"]["passages"]:
        if text in p.get("provision", ""):
            return p["id"]
    return None


def _pct(part: float, whole: float) -> float:
    return round(part / whole * 100, 2)


# ---------- input parsing ----------

def parse_bom(rows: list[dict], currency: str, missing: list[str]) -> list[dict]:
    items = []
    for i, row in enumerate(rows, start=1):
        r = {k: str(row.get(k) or "").strip() for k in BOM_COLUMNS}
        label = f"BOM row {i} ({r['input_description'] or 'no description'})"
        origin = r["origin_country"].upper()
        value = _num(r["value"])
        hs = "".join(ch for ch in r["hs_code"] if ch.isdigit())

        if len(origin) != 2 or not origin.isalpha():
            missing.append(f"{label}: origin_country must be a 2-letter country code")
        if value is None or value < 0:
            missing.append(f"{label}: value must be a non-negative number")
        if r["currency"].upper() != currency:
            missing.append(f"{label}: currency '{r['currency'] or 'missing'}' differs from the product "
                           f"price currency '{currency}'; values are never converted")
        originating = origin in PARTIES
        if not originating:
            if len(hs) < 6:
                missing.append(f"{label}: a 6-digit HS code is needed for every non-originating input")
            if r["value_basis"].upper() not in NOM_BASES:
                missing.append(f"{label}: non-originating inputs must be valued at CIF "
                               "(or the first price paid in the UAE)")
        items.append({"description": r["input_description"], "hs": hs, "origin": origin,
                      "value": value or 0.0, "originating": originating})
    if not items:
        missing.append("the bill of materials has no rows")
    return items


def parse_declaration(d: dict, valid_ops: set[str], missing: list[str]) -> dict:
    basis = str(d.get("price_basis") or "").upper().replace("-", "").replace(" ", "")
    basis = "EXW" if basis in ("EXW", "EXWORKS") else basis
    if basis not in ("FOB", "EXW"):
        missing.append("declaration: price_basis must be FOB or EXW (Ex-Works)")
    price = _num(d.get("price"))
    if price is None or price <= 0:
        missing.append("declaration: price of the finished product must be a positive number")
    currency = str(d.get("currency") or "").strip().upper()
    if not currency:
        missing.append("declaration: currency of the price is missing")
    fm = d.get("final_manufacture_in_uae")
    if not isinstance(fm, bool):
        missing.append("declaration: final_manufacture_in_uae must be true or false")
    ops = d.get("operations")
    if not isinstance(ops, list) or not ops:
        missing.append("declaration: list the operations done in the UAE")
        ops = []
    unknown = [o for o in ops if o not in valid_ops and o != BEYOND_MINIMAL]
    if unknown:
        missing.append(f"declaration: unknown operation codes: {', '.join(map(str, unknown))} "
                       "(use the letters of Art. 3.5.1, or 'beyond_minimal')")
    if BEYOND_MINIMAL in ops and not str(d.get("operations_description") or "").strip():
        missing.append("declaration: describe the manufacturing done beyond minimal operations")
    labour, overhead = _num(d.get("direct_labour")), _num(d.get("direct_overhead"))
    return {"price_basis": basis, "price": price, "currency": currency, "final_manufacture": fm,
            "operations": ops, "labour": labour, "overhead": overhead,
            "free_zone": d.get("factory_in_free_zone")}


# ---------- tests of the rule ----------

def _shift_test(test: str, items: list[dict], line: str, price: float, demin: dict) -> dict:
    n, level = (4, "heading") if test == "CTH" else (6, "subheading")
    nom = [it for it in items if not it["originating"]]
    same = [it for it in nom if it["hs"][:n] == line[:n]]
    check = {"check": test, "source_id": P_DEMIN if same else None}
    if not same:
        check.update(result=PASS, basis=f"All {len(nom)} non-originating input(s) are classified outside "
                                        f"{level} {line[:n]}.")
        return check
    names = ", ".join(it["description"] for it in same)
    share = _pct(sum(it["value"] for it in same), price)
    lo, hi = (int(c) for c in demin["textile_chapters"])
    if lo <= int(line[:2]) <= hi:
        check.update(result=NOT_EVALUATED, basis=f"{len(same)} input(s) in the same {level} ({names}); "
                     "textile de minimis is by weight, which this calculator does not support.")
    elif share <= demin["value_pct"]:
        check.update(result=PASS, basis=f"{len(same)} non-originating input(s) in the same {level} {line[:n]} "
                     f"({names}) total {share}% of the price, within the {demin['value_pct']}% de minimis.")
    else:
        check.update(result=FAIL, basis=f"{len(same)} non-originating input(s) are in the same {level} "
                     f"{line[:n]} as the product ({names}); together {share}% of the price, above the "
                     f"{demin['value_pct']}% de minimis.")
    return check


def _va_test(min_pct: float, items: list[dict], dec: dict, exw: dict) -> dict:
    price, basis = dec["price"], dec["price_basis"]
    nom = sum(it["value"] for it in items if not it["originating"])
    orig = sum(it["value"] for it in items if it["originating"])
    check = {"check": "VA", "source_id": P_VA}

    if basis == "EXW" and not exw["applies"]:
        check.update(result=NOT_EVALUATED, basis="This chapter must use an FOB price; an FOB price is needed.")
        return check
    threshold = min_pct - exw["points"] if basis == "EXW" else min_pct
    bd = _pct(price - nom, price)
    bu = _pct(orig + dec["labour"] + dec["overhead"], price) \
        if dec["labour"] is not None and dec["overhead"] is not None else None
    ok = bd >= threshold or (bu is not None and bu >= threshold)
    parts = [f"build-down {bd}%"] + ([f"build-up {bu}%"] if bu is not None else [])
    adj = f" ({min_pct}% minus {exw['points']} points on an Ex-Works basis)" if basis == "EXW" else ""
    check.update(result=PASS if ok else FAIL,
                 basis=f"{' and '.join(parts)} against a threshold of {threshold}%{adj}, {basis} basis.",
                 values={"build_down_pct": bd, "build_up_pct": bu, "threshold_pct": threshold})
    return check


def _wo_test(items: list[dict]) -> dict:
    n = sum(1 for it in items if not it["originating"])
    if n:
        return {"check": "WO", "result": FAIL, "source_id": None,
                "basis": f"{n} non-originating input(s) used, so the product is not wholly obtained."}
    return {"check": "WO", "result": NOT_EVALUATED, "source_id": None,
            "basis": "Wholly obtained status needs a declaration; not evaluated from a bill of materials."}


# ---------- main entry point ----------

def calculate_origin(tariff_line: str, bom_rows: list[dict] | None = None,
                     declaration: dict | None = None, corridor: str = "india") -> OriginResult:
    kb = load_corridor(corridor)
    rl = rule_lookup(tariff_line, corridor)
    res = OriginResult(tool_id=f"{TOOL_PREFIX}:{tariff_line}", tariff_line=tariff_line, status="RULE_GAP",
                       sources=dict(rl.sources))

    # 1) rule
    if rl.status != "RULE_FOUND" or len(rl.rules) != 1:
        res.notes += rl.notes or [f"REGULATORY_GAP_DETECTED: no single rule of origin for {tariff_line}."]
        return res
    rule = rl.rules[0]
    res.rule_id, res.rule_text = rule["id"], rule["rule_text"]
    res.notes += rl.notes + rl.interpretations

    # 2) inputs
    if bom_rows is None or declaration is None:
        res.status = "INSUFFICIENT_DATA"
        res.missing.append("a bill of materials (each input's description, 6-digit HS code, origin country, "
                           "value and currency) and a declaration (product price, FOB or Ex-Works basis, "
                           "final manufacture in the UAE, operations done in the UAE)")
        return res
    minimal = _passage(kb, P_MINIMAL)
    valid_ops = {it["code"] for it in minimal.get("items", [])}
    dec = parse_declaration(declaration, valid_ops, res.missing)
    items = parse_bom(bom_rows, dec["currency"], res.missing)
    if res.missing:
        res.status = "INSUFFICIENT_DATA"
        return res

    demin = _passage(kb, P_DEMIN)["params"]
    exw = {"points": 0, "applies": True}
    for g in rl.general_rules:
        params = g.get("params") or {}
        if "exworks_reduction_pts" in params:
            exw = {"points": params["exworks_reduction_pts"], "applies": g["applies_to_this_line"]}

    # 3) hard gates
    fm_ok = dec["final_manufacture"]
    res.checks.append({"check": "final_manufacture_in_uae", "result": PASS if fm_ok else FAIL,
                       "source_id": _passage_by_provision(kb, "3.2.3") or rl.tool_id,
                       "basis": "Declared: final manufacture took place in the UAE." if fm_ok else
                                "Declared: final manufacture did not take place in the UAE (Art. 3.2.3)."})
    only_minimal = BEYOND_MINIMAL not in dec["operations"]
    res.checks.append({"check": "minimal_operations", "result": FAIL if only_minimal else PASS,
                       "source_id": P_MINIMAL,
                       "basis": "Declared operations are all minimal operations under Art. 3.5.1, which "
                                f"never confer origin: {_minimal_ops_text(kb, dec['operations'])}."
                                if only_minimal else
                                "Declared manufacturing goes beyond the minimal operations of Art. 3.5.1."})

    # 4) product-specific rule: alternatives are OR, tests inside one are AND
    alt_results = []
    for a_i, alt in enumerate(rule["alternatives"]):
        results = []
        for test in alt:
            t = test["test"]
            if t in ("CTH", "CTSH"):
                c = _shift_test(t, items, tariff_line, dec["price"], demin)
            elif t == "VA":
                c = _va_test(test["min_pct"], items, dec, exw)
            else:
                c = _wo_test(items)
            c["alternative"] = a_i
            res.checks.append(c)
            results.append(c["result"])
        alt_results.append(PASS if all(r == PASS for r in results)
                           else FAIL if FAIL in results else NOT_EVALUATED)

    # 5) status
    if not fm_ok or only_minimal:
        res.status = "FAILS"
    elif PASS in alt_results:
        res.status = "MEETS"
    elif NOT_EVALUATED in alt_results:
        res.status = "INSUFFICIENT_DATA"
        res.missing.append("data for the checks marked NOT_EVALUATED")
    else:
        res.status = "FAILS"

    nom = sum(it["value"] for it in items if not it["originating"])
    orig = sum(it["value"] for it in items if it["originating"])
    res.totals = {"price_basis": dec["price_basis"], "price": dec["price"], "currency": dec["currency"],
                  "inputs_count": len(items),
                  "non_originating_inputs_count": sum(1 for it in items if not it["originating"]),
                  "non_originating_total": nom, "originating_total": orig,
                  "non_originating_share_pct": _pct(nom, dec["price"]),
                  "nom_valuation_source_id": P_NOM}

    if any(it["origin"] == "IN" for it in items):
        res.notes.append(INDIAN_INPUTS_NOTE)
        res.conditions.append("INDIAN_INPUTS")
    if dec["labour"] is not None:
        res.notes.append("'Direct labour cost' and 'direct overhead cost' are not defined in the agreement.")
    res.notes.append(OWN_DECLARATION_NOTE)
    if dec["free_zone"]:
        res.notes.append(FREE_ZONE_NOTE)
        res.conditions.append("FREE_ZONE")
    return res


def origin_from_folder(tariff_line: str, folder: str | Path | None, corridor: str = "india") -> OriginResult:
    """Read bom.csv and declaration.json from a folder (either may be absent)."""
    bom_rows = declaration = None
    if folder:
        folder = Path(folder)
        if (folder / "bom.csv").exists():
            with (folder / "bom.csv").open(encoding="utf-8-sig", newline="") as f:
                bom_rows = list(csv.DictReader(f))
        if (folder / "declaration.json").exists():
            with (folder / "declaration.json").open(encoding="utf-8") as f:
                declaration = json.load(f)
    return calculate_origin(tariff_line, bom_rows, declaration, corridor)