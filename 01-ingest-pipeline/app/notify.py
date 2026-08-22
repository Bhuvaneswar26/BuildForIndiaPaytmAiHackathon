from __future__ import annotations

import httpx

from app.config import settings


async def push_to_alert_agent(metrics: dict) -> dict | None:
    url = settings.alert_agent_url.rstrip("/") + "/v1/evaluate"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, json={"metrics": metrics})
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:  # demo must keep running even if agent is down
        return {"error": str(exc), "skipped": True}
