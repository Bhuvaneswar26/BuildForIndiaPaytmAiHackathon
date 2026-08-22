from __future__ import annotations

import json
from pathlib import Path

import httpx

from app.config import settings


async def dispatch(channels: dict) -> dict:
    url = settings.mcp_notify_url.rstrip("/") + "/tools/notify_merchant"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=channels)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        Path(settings.notify_log).parent.mkdir(parents=True, exist_ok=True)
        with open(settings.notify_log, "a", encoding="utf-8") as f:
            f.write(json.dumps({"fallback_log": True, "error": str(exc), **channels}, ensure_ascii=False) + "\n")
        return {"ok": False, "error": str(exc), "logged": True}
