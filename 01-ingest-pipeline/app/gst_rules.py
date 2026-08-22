"""GST threshold rules engine — public CGST Act / notification numbers, no API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

BusinessType = Literal["goods", "services"]

# Special-category states under GST (lower registration threshold)
SPECIAL_CATEGORY_STATES = {
    "AR",  # Arunachal Pradesh
    "AS",  # Assam
    "MN",  # Manipur
    "ML",  # Meghalaya
    "MZ",  # Mizoram
    "NL",  # Nagaland
    "SK",  # Sikkim
    "TR",  # Tripura
    "HP",  # Himachal Pradesh
    "UK",  # Uttarakhand
    "UT",  # Uttarakhand alt
    "JK",  # Jammu & Kashmir
    "LA",  # Ladakh
}

# Aggregate turnover thresholds for compulsory registration (INR)
GOODS_NORMAL = 40_00_000
GOODS_SPECIAL = 20_00_000
SERVICES_NORMAL = 20_00_000
SERVICES_SPECIAL = 10_00_000

COMPOSITION_GOODS = 1_50_00_000  # ₹1.5 crore
COMPOSITION_SERVICES = 50_00_000  # ₹50 lakh

# Early-warning checkpoints. 25% wakes the alert agent; 60/80/95% are merchant nudges.
CHECKPOINTS = (0.25, 0.60, 0.80, 0.95)

GST_PORTAL = "https://reg.gst.gov.in/registration/"


@dataclass(frozen=True)
class ThresholdProfile:
    state_code: str
    business_type: BusinessType
    is_special_category: bool
    registration_limit_inr: int
    composition_limit_inr: int
    composition_rate_hint: str


def financial_year(d: date) -> tuple[int, int]:
    if d.month >= 4:
        return d.year, d.year + 1
    return d.year - 1, d.year


def fy_start(d: date) -> date:
    start_year, _ = financial_year(d)
    return date(start_year, 4, 1)


def fy_label(d: date) -> str:
    a, b = financial_year(d)
    return f"FY {a}-{str(b)[2:]}"


def profile(state_code: str, business_type: BusinessType) -> ThresholdProfile:
    code = state_code.upper()
    special = code in SPECIAL_CATEGORY_STATES
    if business_type == "goods":
        limit = GOODS_SPECIAL if special else GOODS_NORMAL
        composition = COMPOSITION_GOODS
        rate = "1% (manufacturer / trader composition — confirm current rate)"
    else:
        limit = SERVICES_SPECIAL if special else SERVICES_NORMAL
        composition = COMPOSITION_SERVICES
        rate = "6% (services composition — confirm current rate)"
    return ThresholdProfile(
        state_code=code,
        business_type=business_type,
        is_special_category=special,
        registration_limit_inr=limit,
        composition_limit_inr=composition,
        composition_rate_hint=rate,
    )


def checkpoint_hit(pct: float, previous_pct: float | None) -> float | None:
    """Return the highest new checkpoint crossed since previous_pct."""
    hit = None
    for c in CHECKPOINTS:
        if pct >= c * 100 and (previous_pct is None or previous_pct < c * 100):
            hit = c
    return hit


def months_to_limit(current: float, limit: float, fy_elapsed_days: int) -> float | None:
    if fy_elapsed_days <= 0 or current <= 0:
        return None
    daily = current / fy_elapsed_days
    remaining = limit - current
    if remaining <= 0:
        return 0.0
    return round(remaining / daily / 30.44, 1)
