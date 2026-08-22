"""Rule-based risk classification. LLM may refine copy; categories stay deterministic."""

from __future__ import annotations

from typing import Literal

Risk = Literal["watch", "prepare", "act_soon", "imminent"]


def classify(pct: float) -> Risk:
    if pct >= 95:
        return "imminent"
    if pct >= 80:
        return "act_soon"
    if pct >= 60:
        return "prepare"
    return "watch"


def checklist() -> list[str]:
    return [
        "PAN of the business / proprietor",
        "Bank account details (cancelled cheque or passbook)",
        "Proof of principal place of business (electricity bill / rent agreement)",
        "Photograph of proprietor / authorised signatory",
        "Aadhaar of authorised signatory (OTP verification on the GST portal)",
    ]
