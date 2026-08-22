# GST Pulse — Paytm hackathon (Theme 2)

Three services. Almost nothing is faked except **optional other income** (merchant-typed) and the **Paytm mock** (same URL path + JSON as production because you cannot hit live passbook from here).

| Project | Port | Job |
|---|---|---|
| `01-ingest-pipeline` | 8088 | Mock Paytm Order List v2, nightly ingest, FY/monthly bars, 25/60/80/95% |
| `02-alert-agent` | 8090 + MCP 8091 | Risk band, EN/HI/TE copy, WhatsApp + email tools |
| `03-gst-advisor` | 8100 | RAG explainer + Sarvam voice/translation |

```
Paytm mock (or live)  →  ingest + rules  →  alert agent  →  MCP notify (WA/email)
                                              ↓
                                    link to RAG + voice advisor
```

## One-command local demo (4 terminals)

From `1poc`, using Python 3.11+:

```powershell
# 1 — notifications
cd 02-alert-agent
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn notify_bridge.http_bridge:app --port 8091

# 2 — alert agent
cd 02-alert-agent
.\.venv\Scripts\python -m uvicorn app.main:app --port 8090

# 3 — advisor
cd 03-gst-advisor
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --port 8100

# 4 — ingest + merchant UI (starts 22:00 cron; button runs it now)
cd 01-ingest-pipeline
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
$env:APP_ENV="development"
.\.venv\Scripts\python -m uvicorn app.main:app --port 8088
```

Or: `.\scripts\run-dev.ps1` then open the four listed URLs.

1. Open http://127.0.0.1:8088 — pick **Sharma Kirana** (~70% of ₹40L).
2. Click **Run nightly ingest now**.
3. Open http://127.0.0.1:8091/tools/recent — mock WhatsApp/email with advisor link.
4. Open that link (http://127.0.0.1:8100) — ask “What is composition scheme?”
5. Switch to **Borpujari Tea** (Assam, ~95% of ₹20L) for the imminent nudge.

## Environments (ingest)

`APP_ENV=development|test|production` loads `.env.<env>`. Production points `PAYTM_BASE_URL` at `https://secure.paytmpayments.com` and uses checksum. Judge line: *today we poll a staging mock; production is a Paytm settlement webhook instead of a 10pm cron.*

## Thresholds (rules engine)

- Goods ₹40L / services ₹20L; special-category ₹20L / ₹10L
- Agent wakes at **25%**; merchant nudges at **60 / 80 / 95%**
- Composition eligibility: goods ₹1.5Cr / services ₹50L (explained, not filed)

## Adding real GST PDFs

Drop extracted text as `.md` files in `03-gst-advisor/knowledge/` (or paste PDF text). The lexical RAG reloads on process start.

## Sarvam

Put hackathon credits in `03-gst-advisor/.env` as `SARVAM_API_KEY`. Voice + translation + optional chat light up; without the key, typed RAG still demos.
