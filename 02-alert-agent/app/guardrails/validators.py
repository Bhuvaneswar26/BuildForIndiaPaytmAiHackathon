from __future__ import annotations

from typing import Any


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []

    if not payload.get("merchant_id"):
        issues.append("missing_merchant_id")
    if not (payload.get("email") or payload.get("phone")):
        issues.append("missing_contact")
    if not payload.get("title"):
        issues.append("missing_title")
    if not payload.get("body"):
        issues.append("missing_body")
    if payload.get("language") not in {"en", "hi", "te"}:
        issues.append("unsupported_language")

    return {
        "ok": not issues,
        "issues": issues,
    }


def validate_message_text(message: str) -> dict[str, Any]:
    text = (message or "").strip()
    return {
        "ok": bool(text),
        "issues": [] if text else ["empty_message"],
    }


def validate_metrics_input(metrics: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []

    if not metrics.get("merchant_id"):
        issues.append("missing_merchant_id")
    if not (metrics.get("email") or metrics.get("phone")):
        issues.append("missing_contact")
    if not metrics.get("language"):
        issues.append("missing_language")

    language = (metrics.get("language") or "en").split("-")[0].lower()
    if language not in {"en", "hi", "te"}:
        issues.append("unsupported_language")

    return {
        "ok": not issues,
        "issues": issues,
        "normalized_language": "en" if language not in {"en", "hi", "te"} else language,
    }


def normalize_notify_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload or {})
    metric_block = normalized.get("metrics") if isinstance(normalized.get("metrics"), dict) else normalized

    if not normalized.get("title"):
        risk = normalized.get("risk") or metric_block.get("risk") or "watch"
        merchant = metric_block.get("merchant_id") or normalized.get("merchant_id") or "merchant"
        normalized["title"] = f"GST Pulse Alert — {risk.upper()} / {merchant}"

    if not normalized.get("body"):
        merchant = metric_block.get("merchant_id") or normalized.get("merchant_id") or "merchant"
        pct = metric_block.get("pct") or normalized.get("pct") or 0
        normalized["body"] = (
            f"This is a GST Pulse notification for merchant {merchant}. "
            f"Current threshold usage is {pct}%. Please review the GST registration checklist and advisor guidance."
        )

    if not normalized.get("language"):
        normalized["language"] = (metric_block.get("language") or "en").split("-")[0].lower()

    if normalized["language"] not in {"en", "hi", "te"}:
        normalized["language"] = "en"

    return normalized
