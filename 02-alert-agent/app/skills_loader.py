from __future__ import annotations

from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


def load_skills() -> str:
    chunks = []
    for skill in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        chunks.append(f"# Skill: {skill.parent.name}\n\n{skill.read_text(encoding='utf-8')}")
    return "\n\n---\n\n".join(chunks)
