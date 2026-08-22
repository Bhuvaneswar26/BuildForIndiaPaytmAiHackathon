from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from app.classifier import checklist, classify
from app.mcp_client import dispatch
from app.skills_loader import SKILLS_DIR, load_skills
from app.templates import render

app = FastAPI(title="GST Pulse — Alert Agent", version="0.1.0")


class EvaluateIn(BaseModel):
    metrics: dict


@app.get("/health")
async def health():
    return {"ok": True, "skills": [p.parent.name for p in SKILLS_DIR.glob("*/SKILL.md")]}


@app.get("/v1/skills")
async def skills():
    return {"markdown": load_skills()}


@app.post("/v1/evaluate")
async def evaluate(body: EvaluateIn):
    m = body.metrics
    risk = classify(float(m.get("pct") or 0))
    copy = render(risk, m)
    payload = {
        "merchant_id": m.get("merchant_id"),
        "phone": m.get("phone"),
        "email": m.get("email"),
        "language": copy["language"],
        "risk": risk,
        "title": copy["channel_title"],
        "body": copy["body"],
        "advisor_url": m.get("advisor_url"),
        "gst_portal": m.get("gst_portal"),
        "checklist": checklist(),
        "metrics_summary": {
            "pct": m.get("pct"),
            "aggregate_turnover": m.get("aggregate_turnover"),
            "threshold": m.get("threshold"),
            "new_checkpoint": m.get("new_checkpoint"),
            "caveat": m.get("data_caveat"),
        },
    }
    notified = await dispatch(payload)
    return {"risk": risk, "message": copy, "notified": notified, "payload": payload}
