from __future__ import annotations

from datetime import date, datetime

from app import store
from app.config import settings
from app.gst_rules import fy_start
from app.metrics import compute_metrics
from app.mock_paytm import DEMO_MERCHANTS, seed_passbook
from app.notify import push_to_alert_agent
from app.paytm_client import fetch_orders


def seed_merchants() -> None:
    store.init_db()
    for m in DEMO_MERCHANTS:
        store.upsert_merchant({k: m[k] for k in m if k != "target_fy_inr"})
    seed_passbook()


def _normalize_order(raw: dict, merchant_id: str) -> dict:
    return {
        "txn_id": raw["txnId"],
        "merchant_id": merchant_id,
        "merchant_order_id": raw.get("merchantOrderId"),
        "order_created_time": raw.get("orderCreatedTime"),
        "order_completed_time": raw.get("orderCompletedTime"),
        "order_search_type": raw.get("orderSearchType"),
        "order_search_status": raw.get("orderSearchStatus"),
        "mid": raw.get("mid"),
        "merchant_name": raw.get("merchantName"),
        "pay_mode": raw.get("payMode"),
        "amount": float(raw.get("amount") or 0),
        "van_id": raw.get("vanId"),
        "rrn": raw.get("rrn"),
        "van_ifsc_code": raw.get("vanIfscCode"),
        "ingested_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }


async def ingest_merchant(merchant: dict, as_of: date | None = None) -> dict:
    as_of = as_of or date.today()
    start = fy_start(as_of)
    raw = await fetch_orders(merchant["mid"], merchant.get("van_id"), start, as_of)
    store.insert_orders([_normalize_order(o, merchant["merchant_id"]) for o in raw])
    orders = store.orders_for_merchant(merchant["merchant_id"])
    prev = store.last_snapshot_pct(merchant["merchant_id"])
    metrics = compute_metrics(merchant=merchant, orders=orders, as_of=as_of, previous_pct=prev)
    metrics["advisor_url"] = (
        f"{settings.advisor_public_url.rstrip('/')}/?merchant={merchant['merchant_id']}"
        f"&lang={merchant.get('language') or 'en'}"
    )
    metrics["source"] = "paytm_passbook_mock" if not settings.is_live_paytm else "paytm_passbook"
    store.save_snapshot(
        {
            "merchant_id": merchant["merchant_id"],
            "fy_label": metrics["fy_label"],
            "paytm_turnover": metrics["paytm_turnover"],
            "other_income": metrics["other_income"],
            "aggregate_turnover": metrics["aggregate_turnover"],
            "threshold": metrics["threshold"],
            "pct": metrics["pct"],
            "monthly": metrics["monthly"],
            "checkpoint": metrics["new_checkpoint"],
        }
    )
    # Wake the alert agent from 25% onwards (or whenever a new checkpoint is crossed).
    if metrics["pct"] >= 25:
        await push_to_alert_agent(metrics)
    return metrics


async def run_all() -> dict:
    seed_merchants()
    results = []
    for m in store.list_merchants():
        results.append(await ingest_merchant(m))
    store.log_run("ok", f"ingested {len(results)} merchants")
    return {"env": settings.app_env, "merchants": results}
