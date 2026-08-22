from __future__ import annotations

import base64
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import settings
from app.prompts import ANSWER_INSTRUCTIONS, SYSTEM, clean_text, extractive_answer, flatten_for_display, skill_text
from app.rag import kb
from app.sarvam import sarvam

app = FastAPI(title="GST Pulse Advisor", version="0.1.0")
static = Path(__file__).resolve().parent.parent / "static"
if static.exists():
    app.mount("/static", StaticFiles(directory=static), name="static")


class ChatIn(BaseModel):
    question: str
    language: str = "en"
    merchant_id: str | None = None
    speak: bool = False


_TOPIC_HINTS = (
    ("document", " documents proof paperwork deed certificate photo bank electricity rent lease consent PAN Aadhaar JPG PDF size"),
    ("proof", " documents proof paperwork deed certificate photo bank electricity rent lease consent PAN Aadhaar"),
    ("paperwork", " documents checklist constitution signatory principal place of business"),
    ("composition", " composition scheme 1.5 crore 50 lakh quarterly GSTR-4 input tax credit flat rate"),
    ("threshold", " aggregate turnover 40 lakh 20 lakh special category goods services registration"),
    ("register", " GST registration process TRN ARN GSTIN documents 30 days portal"),
    ("registration", " GST registration process TRN ARN GSTIN documents eligibility types"),
    ("what happens", " registration composition compliance GSTR returns input tax credit"),
)


def _retrieval_query(question: str) -> tuple[str, int]:
    q = question.lower()
    extra = []
    k = 8
    for needle, hint in _TOPIC_HINTS:
        if needle in q:
            extra.append(hint)
            k = 12
    return question + "".join(extra), k


def _bounded_context(hits: list, max_chars: int = 16000) -> str:
    parts: list[str] = []
    used = 0
    for _, chunk in hits:
        block = flatten_for_display(
            f"Source: {chunk.source}\nSection: {chunk.title}\n{chunk.text}"
        )
        if used and used + len(block) > max_chars:
            remain = max_chars - used
            if remain > 500:
                parts.append(block[:remain].rstrip() + "\n[section truncated]")
            break
        parts.append(block)
        used += len(block)
    return "\n\n---\n\n".join(parts)


async def answer_question(question: str, language: str) -> dict:
    retrieval_query, k = _retrieval_query(question)
    hits = kb().search(retrieval_query, k=k)
    sources = [c.source for _, c in hits]
    context = _bounded_context(hits)
    user = (
        f"Language: {language}\n\n"
        f"Question: {question}\n\n"
        f"{ANSWER_INSTRUCTIONS}\n\n"
        f"Retrieved GST notes:\n{context}"
    )
    llm = await sarvam.chat(SYSTEM + "\n\n" + skill_text(), user)
    text = llm or extractive_answer(question, hits)
    if sarvam.enabled and language not in ("en", "en-IN"):
        try:
            text = await sarvam.translate(text, "en", language.split("-")[0])
        except Exception:
            pass
    text = clean_text(text)
    audio_b64 = None
    if False:
        pass
    return {"answer": text, "sources": sources, "sarvam": sarvam.enabled, "audio_b64": audio_b64}


@app.get("/")
async def ui():
    return FileResponse(static / "index.html")


@app.get("/health")
async def health():
    return {"ok": True, "chunks": len(kb().chunks), "sarvam": sarvam.enabled}


@app.post("/v1/chat")
async def chat(body: ChatIn):
    result = await answer_question(body.question, body.language)
    if body.speak and sarvam.enabled:
        audio = await sarvam.tts(result["answer"], body.language.split("-")[0])
        if audio:
            result["audio_b64"] = base64.b64encode(audio).decode()
    return result


@app.post("/v1/voice")
async def voice(
    file: UploadFile = File(...),
    language: str = Form("en"),
):
    raw = await file.read()
    transcript = ""
    if sarvam.enabled:
        try:
            transcript = await sarvam.transcribe(raw, file.filename or "audio.webm", file.content_type or "audio/webm")
        except Exception as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=502)
    if not transcript:
        return {
            "ok": False,
            "error": "Sarvam API key missing — type your question, or set SARVAM_API_KEY for voice.",
            "transcript": "",
        }
    result = await answer_question(transcript, language)
    audio = await sarvam.tts(result["answer"], language.split("-")[0])
    if audio:
        result["audio_b64"] = base64.b64encode(audio).decode()
    result["transcript"] = transcript
    result["ok"] = True
    return result
