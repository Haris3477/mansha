"""Duty estimate tool. Pure code, no LLM.

Shipment value x (MFN rate - CEPA rate), on Basic Customs Duty (BCD) only, in
the shipment's own currency (never converted). Uses Decimal so money figures
are exact. Every result carries the caveats that make it an estimate.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from mansha.kb import load_corridor

TOOL_PREFIX = "TOOL:duty"
CENT = Decimal("0.01")


@dataclass
class DutyResult:
    tool_id: str
    tariff_line: str
    status: str  # ESTIMATED | NO_PREFERENCE | NEEDS_VALUE | REGULATORY_GAP_DETECTED
    line_id: str | None = None
    mfn_rate_pct: float | None = None
    cepa_rate_pct: float | None = None
    rate_difference_pts: float | None = None
    currency: str | None = None
    shipment_value: str | None = None
    duty_without_cepa: str | None = None
    duty_with_cepa: str | None = None
    saving: str | None = None
    notes: list[str] = field(default_factory=list)
    sources: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _dec(x) -> Decimal | None:
    try:
        d = Decimal(str(x))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return d if d.is_finite() else None


def _money(d: Decimal) -> str:
    return str(d.quantize(CENT, rounding=ROUND_HALF_UP))


def _num(d: Decimal) -> float:
    return float(d.normalize())


def duty_estimate(tariff_line: str, shipment_value: dict | None = None, corridor: str = "india") -> DutyResult:
    kb = load_corridor(corridor)
    res = DutyResult(tool_id=f"{TOOL_PREFIX}:{tariff_line}", tariff_line=tariff_line,
                     status="REGULATORY_GAP_DETECTED")
    line = next((l for l in kb["tariff"]["lines"] if l["tariff_line"] == tariff_line), None)
    if line is None:
        res.notes.append(f"REGULATORY_GAP_DETECTED: tariff line {tariff_line} is not in the knowledge base, "
                         "so no rates are available.")
        return res

    mfn, cepa = line["mfn"], line["cepa"]
    res.line_id = line["id"]
    keys = sorted(set(mfn["source_keys"]) | set(cepa["source_keys"]))
    res.sources = {k: kb["sources"][k]["url"] for k in keys}

    mfn_rate = _dec(mfn["effective_rate_pct"])
    res.mfn_rate_pct = _num(mfn_rate)
    if mfn["tariff_rate_pct"] != mfn["effective_rate_pct"]:
        res.notes.append(f"The tariff schedule prints {mfn['tariff_rate_pct']}%, but an exemption notification "
                         f"lowers the duty actually charged to {mfn['effective_rate_pct']}%; the effective rate "
                         "is used.")

    excluded = cepa["status"] == "EXCLUDED"
    cepa_rate = mfn_rate if excluded else _dec(cepa["rate_pct"])
    res.cepa_rate_pct = None if excluded else _num(cepa_rate)
    res.rate_difference_pts = _num(mfn_rate - cepa_rate)
    if excluded:
        res.notes.append("This line is excluded from India's CEPA concessions: no preferential rate, the normal "
                         "(MFN) duty applies whatever the origin.")
    elif cepa.get("table") == "II":
        res.notes.append("Table II line: the CEPA also changes the Agriculture Infrastructure and Development "
                         "Cess (AIDC), which this estimate does not include.")
    elif cepa.get("table") == "III":
        res.notes.append("Table III line (tariff-rate quota): the CEPA rate applies only within the quota and "
                         "with a quota authorisation; otherwise normal duty applies.")

    # shipment value: positive amount and a currency, kept exactly as given
    amount = _dec((shipment_value or {}).get("amount"))
    currency = str((shipment_value or {}).get("currency") or "").strip().upper()
    if amount is None or amount <= 0 or not currency:
        res.status = "NO_PREFERENCE" if excluded else "NEEDS_VALUE"
        res.notes.append("No usable shipment value (positive amount and currency), so only rates are given.")
    else:
        without = amount * mfn_rate / 100
        with_cepa = amount * cepa_rate / 100
        res.status = "NO_PREFERENCE" if excluded else "ESTIMATED"
        res.currency = currency
        res.shipment_value = _money(amount)
        res.duty_without_cepa = _money(without)
        res.duty_with_cepa = _money(with_cepa)
        res.saving = _money(without - with_cepa)
        res.notes.append("Estimate on the shipment value given. India charges duty on the assessable (CIF) "
                         "value at import, so actual amounts will differ. Shown in the shipment's own currency; "
                         "never converted.")

    # "CEPA rates reduce BCD only" holds for Table I lines. Table II lines also change AIDC (note above);
    # an excluded line has no CEPA rate, so a note about what the CEPA rate reduces would not apply.
    if not excluded and cepa.get("table") != "II":
        res.notes.append(kb["tariff"]["metadata"].get("duty_scope", "CEPA rates reduce Basic Customs Duty only."))
    if not excluded:
        res.notes.append("The CEPA rate applies only if the product qualifies under the rules of origin and a "
                         "valid certificate of origin is presented.")
    return res