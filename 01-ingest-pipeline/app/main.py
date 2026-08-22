from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import store
from app.config import settings
from app.ingestion import ingest_merchant, run_all, seed_merchants
from app.metrics import compute_metrics
from app.mock_paytm import router as mock_paytm_router
from app.scheduler import start_scheduler

app = FastAPI(
    title="GST Visibility — Ingest Pipeline",
    description="Mock/live Paytm passbook ingest + GST threshold metrics.",
    version="0.1.0",
)

static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Always expose the Paytm-shaped mock so local clients can hit the real path.
app.include_router(mock_paytm_router)


class OtherIncomeIn(BaseModel):
    amount: float = Field(ge=0)


@app.on_event("startup")
async def startup() -> None:
    seed_merchants()
    start_scheduler()


@app.get("/")
async def merchant_ui():
    index = static_dir / "index.html"
    if not index.exists():
        return {"ok": True, "env": settings.app_env}
    return FileResponse(index)


@app.get("/health")
async def health():
    return {
        "ok": True,
        "env": settings.app_env,
        "paytm_base_url": settings.paytm_base_url,
        "live_paytm": settings.is_live_paytm,
        "cron": f"{settings.cron_hour:02d}:{settings.cron_minute:02d}",
    }


@app.post("/v1/ingest/run")
async def ingest_now():
    return await run_all()


@app.get("/v1/merchants")
async def merchants():
    return store.list_merchants()


@app.get("/v1/merchants/{merchant_id}/dashboard")
async def dashboard(merchant_id: str, refresh: bool = False):
    merchant = store.get_merchant(merchant_id)
    if not merchant:
        raise HTTPException(404, "merchant not found")
    orders = store.orders_for_merchant(merchant_id)
    if refresh or not orders:
        return await ingest_merchant(merchant)
    metrics = compute_metrics(
        merchant=merchant,
        orders=orders,
        previous_pct=store.last_snapshot_pct(merchant_id),
    )
    metrics["advisor_url"] = (
        f"{settings.advisor_public_url.rstrip('/')}/?merchant={merchant_id}"
        f"&lang={merchant.get('language') or 'en'}"
    )
    metrics["source"] = (
        "paytm_passbook_mock" if not settings.is_live_paytm else "paytm_passbook"
    )
    return metrics


@app.post("/v1/merchants/{merchant_id}/other-income")
async def other_income(merchant_id: str, body: OtherIncomeIn):
    merchant = store.get_merchant(merchant_id)
    if not merchant:
        raise HTTPException(404, "merchant not found")
    store.update_other_income(merchant_id, body.amount)
    merchant = store.get_merchant(merchant_id)
    return await ingest_merchant(merchant)


@app.post("/v1/demo/reset-checkpoints")
async def reset_checkpoints():
    """Clear FY snapshots so the next ingest re-fires 25/60/80/95% WhatsApp nudges."""
    n = store.clear_snapshots()
    return {"ok": True, "cleared_snapshots": n}
