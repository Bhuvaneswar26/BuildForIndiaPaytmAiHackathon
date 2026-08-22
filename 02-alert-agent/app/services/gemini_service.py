from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.config import settings
from app.services.template_service import render_message


def _normalize_language(value: str | None) -> str:
    lang = (value or "en").split("-")[0].lower()
    return {"en": "en", "hi": "hi", "te": "te", "tel": "te", "ta": "en"}.get(lang, "en")


def _language_instruction(language: str) -> str:
    return {
        "en": "Write in clear, natural English.",
        "hi": "Write entirely in natural Hindi using Devanagari script.",
        "te": "తెలుగులో మాత్రమే సహజమైన తెలుగు లిపిలో రాయండి. ఇంగ్లీష్ లేదా తెలుగు transliteration ఉపయోగించవద్దు.",
    }.get(language, "Write in clear, natural English.")


def _build_prompt(risk: str, metrics: dict[str, Any]) -> str:
    merchant_name = metrics.get("name") or "merchant"
    merchant_id = metrics.get("merchant_id") or "merchant"
    pct = metrics.get("pct") or 0
    aggregate = metrics.get("aggregate_turnover") or 0
    threshold = metrics.get("threshold") or 0
    language = _normalize_language(metrics.get("language"))
    advisor_url = metrics.get("advisor_url") or ""
    gst_portal = metrics.get("gst_portal") or ""
    return (
        "You are writing a GST compliance alert for a Paytm merchant.\n\n"
        "Rules:\n"
        "- Do not imply a government notice or tax demand.\n"
        "- Keep it helpful, concise, and business-friendly.\n"
        f"- Language requirement: {_language_instruction(language)}\n"
        "- The title and body must use the same requested language.\n"
        "- Return ONE valid JSON object only with exactly these keys: title and body.\n"
        "- title should be short and crisp.\n"
        "- body should be 1-3 paragraphs, polite and practical plain text.\n"
        f"- Include merchant name {merchant_name}, merchant id {merchant_id}, pct {pct}%, aggregate turnover {aggregate}, threshold {threshold}, advisor URL {advisor_url}, GST portal {gst_portal}.\n"
        f"- Risk category: {risk}.\n"
        "- No extra text before or after the JSON."
    )


def _decode_escaped_value(value: str) -> str:
    if not value:
        return value
    if "\\u" in value or "\\x" in value:
        try:
            return value.encode("utf-8").decode("unicode_escape")
        except Exception:
            return value
    return value


def _extract_partial_json_fields(text: str) -> dict[str, str]:
    title_match = re.search(r'"title"\s*:\s*"((?:\\.|[^"\\])*)', text)
    body_match = re.search(r'"body"\s*:\s*"((?:\\.|[^"\\])*)', text)
    title = _decode_escaped_value(title_match.group(1)) if title_match else ""
    body = _decode_escaped_value(body_match.group(1)) if body_match else ""
    if title.strip() and body.strip():
        return {"title": title.strip(), "body": body.strip()}
    return {}


def _safe_json_parse(raw: str) -> dict[str, str]:
    text = (raw or "").strip()
    if not text:
        return {"title": "GST Pulse Alert", "body": "Please review your GST registration status."}
    cleaned = text.replace("```json", "").replace("```", "").strip()
    candidates = [cleaned]
    if "\n" in cleaned:
        candidates.append(cleaned.split("\n", 1)[0].strip())
    if "\r" in cleaned:
        candidates.append(cleaned.split("\r", 1)[0].strip())
    for candidate in candidates:
        if not candidate or not candidate.startswith("{"):
            continue
        try:
            parsed = json.loads(candidate)
        except Exception:
            continue
        if isinstance(parsed, dict):
            title = parsed.get("title")
            body = parsed.get("body")
            if isinstance(title, str) and title.strip() and isinstance(body, str) and body.strip():
                return {"title": title.strip(), "body": body.strip()}
    partial = _extract_partial_json_fields(cleaned)
    if partial.get("title"):
        return partial
    if cleaned.startswith("{") and '"title"' in cleaned:
        extracted_title = re.search(r'"title"\s*:\s*"((?:\\.|[^"\\])*)', cleaned)
        if extracted_title:
            title = _decode_escaped_value(extracted_title.group(1))
            return {"title": title.strip() or "GST Pulse Alert", "body": ""}
    return {"title": "GST Pulse Alert", "body": ""}


def _matches_language(text: str, language: str) -> bool:
    if language == "te":
        return bool(re.search(r"[\u0C00-\u0C7F]", text))
    if language == "hi":
        return bool(re.search(r"[\u0900-\u097F]", text))
    return True


def _configured_api_key(value: str | None) -> str:
    key = (value or "").strip()
    if not key or key.upper().startswith("REPLACE_WITH_"):
        return ""
    return key


def generate_alert_copy(risk: str, metrics: dict[str, Any]) -> dict[str, Any]:
    fallback = render_message(risk, metrics)
    api_key = _configured_api_key(settings.sarvam_api_key)
    fallback["source"] = "template"
    fallback["debug"] = {"sarvam_key_present": bool(api_key)}
    if not api_key:
        print("[SARVAM_DEBUG] missing api key; using template fallback")
        return fallback

    model_name = (settings.sarvam_model or "sarvam-105b").strip() or "sarvam-105b"
    url = (settings.sarvam_base_url or "https://api.sarvam.ai/v1/chat/completions").strip()
    prompt = _build_prompt(risk, metrics)
    print("[SARVAM_DEBUG] key_present=True model=", model_name)
    print("[SARVAM_DEBUG] url=", url)
    try:
        response = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "api-subscription-key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "Follow the requested output language exactly. Return only a JSON object with title and body. Never substitute English for an Indic language. For Telugu, write both fields in Telugu script, for example: {\"title\":\"GST నమోదు\",\"body\":\"నమస్తే\"}.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 500,
                "response_format": {"type": "json_object"},
                "reasoning_effort": "low",
            },
            timeout=20.0,
        )
        print("[SARVAM_DEBUG] response_status=", response.status_code)
        response.raise_for_status()
        message = response.json()["choices"][0]["message"]
        text = message.get("content") or message.get("reasoning_content") or ""
        parsed = _safe_json_parse(text)
        title = (parsed.get("title") or "").strip()
        body = (parsed.get("body") or "").strip()
        language = _normalize_language(metrics.get("language"))
        if not title or not body or not _matches_language(f"{title} {body}", language):
            return {
                "channel_title": fallback.get("channel_title") or "GST Pulse Alert",
                "body": fallback.get("body") or "Please review your GST registration status.",
                "language": language,
                "source": "template_fallback",
                "debug": {"sarvam_key_present": True, "model": model_name, "reason": "invalid_or_wrong_language"},
            }
        return {
            "channel_title": title,
            "body": body,
            "language": language,
            "source": "sarvam",
            "debug": {"sarvam_key_present": True, "model": model_name},
        }
    except Exception as exc:
        print("[SARVAM_DEBUG] exception=", type(exc).__name__, str(exc))
        fallback["source"] = "template_fallback"
        fallback["debug"] = {"sarvam_key_present": True, "error": str(exc)}
        return fallback
