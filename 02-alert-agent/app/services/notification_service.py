from __future__ import annotations

import json
from pathlib import Path

import httpx

from app.config import settings


async def dispatch_notification(payload: dict) -> dict:
    url = settings.mcp_notify_url.rstrip("/") + "/tools/notify_merchant"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as exc:  # pragma: no cover - network fallback
        Path(settings.notify_log).parent.mkdir(parents=True, exist_ok=True)
        with open(settings.notify_log, "a", encoding="utf-8") as file:
            file.write(json.dumps({"fallback_log": True, "error": str(exc), **payload}, ensure_ascii=False) + "\n")
        return {"ok": False, "error": str(exc), "logged": True}
