"""Certificate-of-origin fee (Step 6.4f): pick the ministry fee band for the shipment value.

Pure Python, no LLM. The fee bands come from the knowledge-base passage for the
corridor's certificate service. Bands are in AED; Mansha never converts
currencies, so a value in another currency gets the fee range only.
The fee's `actor` (who charges it) is copied from that passage (Step 6.4g).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation

from mansha.kb import load_corridor

TOOL_ID = "TOOL:coo_fee"
GAP = "REGULATORY_GAP_DETECTED"
# Passage that holds the fee bands of each corridor's certificate service.
FEE_PASSAGE = {"india": "P-MOET-COO-INDIA"}


@dataclass
class FeeResult:
    tool_id: str
    status: str                        # ESTIMATED | NEEDS_VALUE | CURRENCY_NOT_AED | REGULATORY_GAP_DETECTED
    passage_id: str | None
    invoice_value: str | None = None   # the value used, as a 2-decimal string
    currency: str | None = None
    fee_aed: int | None = None
    band_max_aed: int | None = None    # upper limit of the chosen band (None = top band)
    fee_range_aed: dict | None = None  # {"min": ..., "max": ...} over all bands
    actor: str | None = None           # who charges the fee, from the passage's actor
    notes: list[str] = field(default_factory=list)
    sources: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _passages(kb: dict) -> list[dict]:
    p = kb["passages"]
    return p if isinstance(p, list) else p.get("passages", [])


def _value_and_currency(shipment_value) -> tuple[Decimal | None, str | None]:
    if not isinstance(shipment_value, dict):
        return None, None
    cur = shipment_value.get("currency")
    cur = str(cur).strip().upper() if cur else None
    raw = shipment_value.get("amount")
    if raw is None or not cur:
        return None, cur
    try:
        value = Decimal(str(raw).replace(",", ""))
    except InvalidOperation:
        return None, cur
    return (value if value > 0 else None), cur


def certificate_fee(shipment_value: dict | None = None, corridor: str = "india") -> FeeResult:
    kb = load_corridor(corridor)
    pid = FEE_PASSAGE.get(corridor)
    passage = next((p for p in _passages(kb) if p.get("id") == pid), None)
    bands = ((passage or {}).get("params") or {}).get("fee_bands_aed")
    if not passage or not bands:
        return FeeResult(TOOL_ID, GAP, pid, notes=["No certificate fee bands are loaded for this corridor."])

    actor = passage.get("actor")
    sources = {k: kb["sources"][k]["url"] for k in passage.get("source_keys", []) if k in kb["sources"]}
    fees = [b["fee_aed"] for b in bands]
    rng = {"min": min(fees), "max": max(fees)}
    base = (f"Fee bands are those of the ministry's certificate service ({passage.get('title')}), "
            "charged on the invoice value in AED.")
    range_txt = f"AED {rng['min']} to AED {rng['max']}"

    value, cur = _value_and_currency(shipment_value)
    if value is None:
        return FeeResult(TOOL_ID, "NEEDS_VALUE", pid, currency=cur, fee_range_aed=rng, actor=actor,
                         sources=sources,
                         notes=[base, f"No usable shipment value, so only the fee range {range_txt} is given."])
    if cur != "AED":
        return FeeResult(TOOL_ID, "CURRENCY_NOT_AED", pid, invoice_value=f"{value:.2f}", currency=cur,
                         fee_range_aed=rng, actor=actor, sources=sources,
                         notes=[base, (f"The shipment value is in {cur}; fee bands are in AED and Mansha never "
                                       f"converts currencies, so only the fee range {range_txt} is given.")])

    for band in bands:
        limit = band.get("max_aed")
        if limit is None or value <= Decimal(str(limit)):
            return FeeResult(TOOL_ID, "ESTIMATED", pid, invoice_value=f"{value:.2f}", currency="AED",
                             fee_aed=band["fee_aed"], band_max_aed=limit, fee_range_aed=rng, actor=actor,
                             sources=sources,
                             notes=[base, "Assumes the certificate's invoice value equals the shipment value given."])
    return FeeResult(TOOL_ID, GAP, pid, fee_range_aed=rng, actor=actor, sources=sources,
                     notes=["The fee bands have no top band; the fee for this value is unknown."])