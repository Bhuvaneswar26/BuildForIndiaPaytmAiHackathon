from __future__ import annotations

from app.domain.types import Risk


def classify_risk(pct: float | int | str | None) -> Risk:
    value = float(pct or 0)
    if value >= 95:
        return "imminent"
    if value >= 80:
        return "act_soon"
    if value >= 60:
        return "prepare"
    return "watch"


def get_checklist() -> list[str]:
    return [
        "PAN of the business / proprietor",
        "Bank account details (cancelled cheque or passbook)",
        "Proof of principal place of business (electricity bill / rent agreement)",
        "Photograph of proprietor / authorised signatory",
        "Aadhaar of authorised signatory (OTP verification on the GST portal)",
    ]
