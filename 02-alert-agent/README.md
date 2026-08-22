# 02 — Alert agent + MCP notifications

Consumes FY metrics from the ingest pipeline, classifies risk, renders formal copy (EN/HI/TE), and sends WhatsApp + email through an MCP-style tool bridge.

Skills live in `skills/` and are loaded into the agent so classification, tone, and JSON shape stay consistent with the RAG advisor.

## LangGraph architecture

The agent is structured as a single LangGraph workflow instead of a free-form script:

1. normalize input
2. classify merchant risk
3. render localized notification copy
4. assemble the outbound payload
5. dispatch through the MCP notification tool
6. finalize the API response

This keeps the business flow deterministic and makes it easy to add extra stages later, such as multi-language translation, output parsing, or data enrichment.

## Run

Terminal A — notification bridge (MCP HTTP tools):

```powershell
cd 02-alert-agent
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python -m uvicorn notify_bridge.http_bridge:app --port 8091
```

Terminal B — agent API:

```powershell
cd 02-alert-agent
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8090
```

Optional stdio MCP (Cursor):

```powershell
.\.venv\Scripts\python notify_bridge/stdio_server.py
```

## WhatsApp / email

Default `WHATSAPP_MODE=mock` writes to `data/notifications.jsonl` so the demo works without Meta/SMTP credentials. Set `WHATSAPP_MODE=live` plus Graph API token to send real WhatsApp Cloud messages.
