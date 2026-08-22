from __future__ import annotations

import base64
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import settings
from app.prompts import SYSTEM, clean_text, extractive_answer, skill_text
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


async def answer_question(question: str, language: str) -> dict:
    document_query = any(term in question.lower().split() for term in ("document", "documents", "proof", "paperwork", "upload", "uploads"))
    retrieval_query = question
    if document_query:
        retrieval_query += " deed certificate photo bank electricity rent lease consent PAN Aadhaar JPG PDF"
    hits = kb().search(retrieval_query, k=8 if document_query else 4)
    sources = [c.source for _, c in hits]
    context = "\n\n---\n\n".join(c.text for _, c in hits)
    user = f"Language: {language}\n\nQuestion: {question}\n\nRetrieved GST notes:\n{context}"
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
