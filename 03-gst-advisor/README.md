# 03 — GST Pulse advisor (RAG + voice)

Independent of the forecast loop. A merchant can open the link in WhatsApp and ask “what happens if I register?” any time.

- **RAG** over markdown in `knowledge/` (stand-in for GST PDFs; drop extra `.md` or extracted PDF text here).
- **Same facts** as the alert agent (`skills/gst-explainer-consistency`).
- **Sarvam**: translation, STT (`saaras:v3`), TTS (`bulbul`), optional chat. Without `SARVAM_API_KEY`, text RAG still works.

```powershell
cd 03-gst-advisor
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8100
```

Open http://127.0.0.1:8100/?merchant=KIRANA_MH_001&lang=hi
