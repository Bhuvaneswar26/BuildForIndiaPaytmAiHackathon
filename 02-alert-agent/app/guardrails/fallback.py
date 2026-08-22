from __future__ import annotations


def get_fallback_response() -> dict[str, str | bool]:
    return {
        "allow_send": False,
        "reason": "blocked_by_guardrails",
        "message": "Merchant notification blocked because the payload does not meet policy and validation rules.",
    }
