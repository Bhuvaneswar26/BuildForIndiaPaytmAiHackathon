from __future__ import annotations

from typing import Any

ALLOWED_RISKS = {"watch", "prepare", "act_soon", "imminent"}
ALLOWED_LANGUAGES = {"en", "hi", "te"}


def evaluate_policy(metrics: dict[str, Any], risk: str) -> dict[str, Any]:
    violations: list[str] = []
    allow_send = True

    if not (metrics.get("email") or metrics.get("phone")):
        violations.append("missing_contact")
        allow_send = False

    if risk not in ALLOWED_RISKS:
        violations.append("invalid_risk")
        allow_send = False

    pct = float(metrics.get("pct") or 0)
    if pct < 25:
        violations.append("under_threshold_alert_cutoff")
        allow_send = False

    lang = (metrics.get("language") or "en").split("-")[0].lower()
    if lang not in ALLOWED_LANGUAGES:
        violations.append("unsupported_language")
        allow_send = False

    return {
        "allow_send": allow_send,
        "violations": violations,
        "policy": {
            "must_not_imply_notice": True,
            "must_not_quote_owed_tax": True,
            "must_have_contact": True,
            "must_use_supported_language": True,
            "must_not_send_if_pct_below_25": True,
            "allowed_risks": sorted(ALLOWED_RISKS),
            "allowed_languages": sorted(ALLOWED_LANGUAGES),
        },
    }
