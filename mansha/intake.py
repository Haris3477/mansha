"""Intake Agent: turn the user's message into checked, normalized JSON.

The LLM understands the message; code checks and normalizes every field.
`normalize()` is pure code, so it can be tested without calling a model.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from typing import Any

from mansha.llm_client import LLMResult, call_llm
from mansha.prompts import build_system_prompt

logger = logging.getLogger(__name__)

AGENT = "intake"
CHAIN = "auto:qa"

FIELDS = (
    "product_description",
    "hs_code_given",
    "destination_country",
    "exporter_role",
    "uae_processing",
    "shipment_value",
)
REQUIRED_KEYS = FIELDS + ("language", "missing_fields")
BLOCKING_FIELDS = ("product_description", "destination_country")

NULL_LIKE = {
    "", "null", "none", "nil", "unknown", "n/a", "na", "-",
    "not provided", "not specified", "not mentioned", "غير معروف",
}

# Arabic-Indic and Persian digits -> ASCII digits.
DIGIT_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

# Spelling/alias normalization ONLY. Being listed here says nothing about
# whether the UAE has a CEPA with that country: the knowledge base decides that.
COUNTRY_ALIASES = {
    "india": "India", "republic of india": "India", "bharat": "India", "الهند": "India",
    "indonesia": "Indonesia", "إندونيسيا": "Indonesia",
    "turkey": "Türkiye", "turkiye": "Türkiye", "türkiye": "Türkiye", "تركيا": "Türkiye",
    "korea": "South Korea", "south korea": "South Korea", "republic of korea": "South Korea",
    "malaysia": "Malaysia", "ماليزيا": "Malaysia",
    "australia": "Australia", "أستراليا": "Australia",
    "new zealand": "New Zealand",
    "georgia": "Georgia", "mauritius": "Mauritius", "kenya": "Kenya",
    "jordan": "Jordan", "الأردن": "Jordan",
    "egypt": "Egypt", "مصر": "Egypt",
    "saudi arabia": "Saudi Arabia", "ksa": "Saudi Arabia", "السعودية": "Saudi Arabia",
    "china": "China", "prc": "China", "الصين": "China",
    "brazil": "Brazil", "البرازيل": "Brazil",
    "usa": "United States", "us": "United States", "united states": "United States",
    "united states of america": "United States", "الولايات المتحدة": "United States",
    "uk": "United Kingdom", "united kingdom": "United Kingdom",
    "great britain": "United Kingdom", "المملكة المتحدة": "United Kingdom",
}

# Currency NAME -> ISO code. This renames; it never converts amounts.
# Ambiguous symbols like "$" are deliberately not mapped.
CURRENCY_ALIASES = {
    "aed": "AED", "dhs": "AED", "dh": "AED", "dirham": "AED", "dirhams": "AED",
    "uae dirham": "AED", "درهم": "AED", "درهم إماراتي": "AED", "دراهم": "AED",
    "usd": "USD", "us dollar": "USD", "us dollars": "USD", "دولار أمريكي": "USD",
    "inr": "INR", "rupee": "INR", "rupees": "INR", "indian rupee": "INR",
    "indian rupees": "INR", "روبية": "INR", "روبية هندية": "INR",
    "eur": "EUR", "euro": "EUR", "euros": "EUR", "يورو": "EUR",
}

ROLE_ALIASES = {
    "manufacturer": "manufacturer", "producer": "manufacturer", "maker": "manufacturer",
    "factory": "manufacturer",
    "trader": "trader", "reseller": "trader", "re-exporter": "trader",
    "reexporter": "trader", "distributor": "trader", "wholesaler": "trader",
}


@dataclass
class IntakeResult:
    data: dict[str, Any]
    changes: list[str]
    llm: LLMResult

    @property
    def blocking_missing(self) -> list[str]:
        """Fields the orchestrator must ask the user for before continuing."""
        return [f for f in BLOCKING_FIELDS if self.data.get(f) is None]


# ---------- small helpers ----------

def detect_language(text: str) -> str:
    """'ar' if there are more Arabic letters than Latin letters, else 'en'."""
    arabic = len(re.findall(r"[\u0600-\u06FF]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    return "ar" if arabic > latin else "en"


def _clean_text(value: Any) -> str | None:
    if value is None or isinstance(value, (dict, list, bool)):
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return None if text.lower() in NULL_LIKE else text


def _digits_only(text: str) -> str:
    return re.sub(r"\D", "", text.translate(DIGIT_MAP))


def _normalize_hs(value: Any, message: str) -> tuple[str | None, str]:
    text = _clean_text(value)
    if text is None:
        return None, "empty"
    digits = _digits_only(text)
    if not 4 <= len(digits) <= 10:
        return None, "not 4-10 digits"
    # Join digits split by '.', ' ' or '-' (e.g. "8504.40" or "8504 40").
    compact = re.sub(r"(?<=\d)[.\s-](?=\d)", "", message.translate(DIGIT_MAP))
    if digits not in compact:
        return None, "digits not found in the user's message (possible invented code)"
    return digits, "digits only"


def _parse_amount(value: Any) -> int | float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    else:
        text = str(value).translate(DIGIT_MAP).replace("٫", ".")
        text = re.sub(r"[,\s٬]", "", text)
        try:
            number = float(text)
        except ValueError:
            return None
    if not math.isfinite(number) or number <= 0:
        return None
    return int(number) if number.is_integer() else number


def _normalize_currency(value: Any) -> str | None:
    text = _clean_text(value)
    if text is None:
        return None
    return CURRENCY_ALIASES.get(text.lower(), text.upper())


# ---------- main normalization (pure code, no LLM) ----------

def normalize(raw: dict[str, Any], message: str) -> tuple[dict[str, Any], list[str]]:
    """Check and clean the model's JSON. Returns (data, list of changes made)."""
    changes: list[str] = []

    def record(field: str, before: Any, after: Any, why: str) -> None:
        if before != after:
            changes.append(f"{field}: {before!r} -> {after!r} ({why})")

    extra = sorted(set(raw) - set(REQUIRED_KEYS))
    if extra:
        changes.append(f"dropped unexpected keys: {extra}")

    data: dict[str, Any] = {}

    for name in ("product_description", "uae_processing"):
        before = raw.get(name)
        data[name] = _clean_text(before)
        record(name, before, data[name], "cleaned")

    before = raw.get("destination_country")
    country = _clean_text(before)
    if country is not None:
        country = COUNTRY_ALIASES.get(country.lower().removeprefix("the "), country)
    data["destination_country"] = country
    record("destination_country", before, country, "canonical name; unknown names kept")

    before = raw.get("hs_code_given")
    data["hs_code_given"], why = _normalize_hs(before, message)
    record("hs_code_given", before, data["hs_code_given"], why)

    before = raw.get("exporter_role")
    role = _clean_text(before)
    data["exporter_role"] = ROLE_ALIASES.get(role.lower()) if role else None
    record("exporter_role", before, data["exporter_role"], "only manufacturer/trader/null")

    before = raw.get("shipment_value")
    shipment = None
    if isinstance(before, dict):
        amount = _parse_amount(before.get("amount"))
        if amount is not None:
            shipment = {"amount": amount, "currency": _normalize_currency(before.get("currency"))}
    data["shipment_value"] = shipment
    record("shipment_value", before, shipment, "amount > 0 as a number; currency renamed, never converted")

    before = raw.get("language")
    lang = str(before).strip().lower() if before is not None else ""
    data["language"] = lang if lang in ("ar", "en") else detect_language(message)
    record("language", before, data["language"], "ar/en, else detected from script")

    missing = [f for f in FIELDS if data[f] is None]
    if shipment is not None and shipment["currency"] is None:
        missing.append("shipment_value.currency")
    model_missing = raw.get("missing_fields")
    if not isinstance(model_missing, list) or set(model_missing) != set(missing):
        changes.append(f"missing_fields: model said {model_missing!r}, code computed {missing!r}")
    data["missing_fields"] = missing

    return data, changes


# ---------- the agent ----------

def run_intake(message: str) -> IntakeResult:
    """Call the Intake LLM, then normalize its JSON with code."""
    message = message.strip()
    if not message:
        raise ValueError("Empty user message")

    messages = [
        {"role": "system", "content": build_system_prompt(AGENT)},
        {"role": "user", "content": message},
    ]
    result = call_llm(AGENT, CHAIN, messages, expect_json=True, required_keys=REQUIRED_KEYS)

    data, changes = normalize(result.data, message)
    for change in changes:
        logger.info("intake normalize | %s", change)
    return IntakeResult(data=data, changes=changes, llm=result)