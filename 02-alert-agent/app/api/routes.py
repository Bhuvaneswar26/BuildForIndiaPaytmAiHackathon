from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.graph.workflow import run_alert_workflow
from app.skills_loader import SKILLS_DIR, load_skills

router = APIRouter()


class EvaluateIn(BaseModel):
    metrics: dict


@router.get("/health")
async def health():
    return {"ok": True, "skills": [p.parent.name for p in SKILLS_DIR.glob("*/SKILL.md")]}


@router.get("/v1/skills")
async def skills():
    return {"markdown": load_skills()}


@router.post("/v1/evaluate")
async def evaluate(body: EvaluateIn):
    return await run_alert_workflow(body.metrics)
