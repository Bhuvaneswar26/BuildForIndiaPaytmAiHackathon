# 01 — Ingest pipeline (Paytm mock + GST metrics)

Pulls Paytm **Order List v2** (same path and JSON shape as production), stores SUCCESS transactions, rolls them into FY / monthly turnover, and wakes the alert agent from **25%** of the GST registration threshold.

## Environments

| `APP_ENV` | Paytm host | Notes |
|---|---|---|
| `development` (default) | `http://127.0.0.1:8088` | In-process mock of `/merchant-passbook/search/list/order/v2` (port 8088 locally because 8080 is often taken) |
| `test` | same mock | Deterministic smaller fixtures |
| `production` | `https://secure.paytmpayments.com` | Real checksum + MID/key from `.env.production` |

Production swap: point `PAYTM_BASE_URL` at Paytm and set `PAYTM_SKIP_CHECKSUM=false`. After the hackathon, replace the 10pm poll with a Paytm settlement webhook.

## Run

```powershell
$env:APP_ENV="development"
cd 01-ingest-pipeline
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8088
```

- Merchant UI: http://127.0.0.1:8088
- Health: http://127.0.0.1:8088/health
- Force ingest (same as 22:00 cron): `POST /v1/ingest/run`

## Demo merchants

- Sharma Kirana (MH, goods) ~70% of ₹40L
- Lakshmi Tailors (AP, services) ~82% of ₹20L
- Borpujari Tea (AS, special-category goods) ~95% of ₹20L
- Namma Snacks (KA) ~18% — below the 25% agent wake
