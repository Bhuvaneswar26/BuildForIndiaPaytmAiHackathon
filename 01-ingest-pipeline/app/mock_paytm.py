"""Staging mock of Paytm VAN Order List API (same path + payload shape as production)."""

from __future__ import annotations

import hashlib
import hmac
import json
import random
from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.gst_rules import fy_start

router = APIRouter()

# Demo merchants — amounts are tuned so judges can see 25 / 60 / 80 / 95% in one click.
DEMO_MERCHANTS = [
    {
        "merchant_id": "KIRANA_MH_001",
        "mid": "INTEGR77698636129383",
        "name": "Sharma Kirana — Pune",
        "state_code": "MH",
        "business_type": "goods",
        "phone": "+919876543210",
        "email": "stevensonr289@gmail.com",
        "language": "te",
        "other_income_inr": 0,
        "van_id": "PYI3831611899004",
        "scenario": "goods_normal_70pct",
        "target_fy_inr": 28_00_000,  # 70% of ₹40L
    }
    # {
    #     "merchant_id": "TAILOR_AP_002",
    #     "mid": "INTEGR77698636129383",
    #     "name": "Lakshmi Tailors — Vijayawada",
    #     "state_code": "AP",
    #     "business_type": "services",
    #     "phone": "+919812345678",
    #     "email": "lakshmi.tailors@example.com",
    #     "language": "te",
    #     "other_income_inr": 50_000,
    #     "van_id": "PYI3831611899005",
    #     "scenario": "services_normal_82pct",
    #     "target_fy_inr": 16_40_000,  # 82% of ₹20L (+ other income later)
    # },
    # {
    #     "merchant_id": "TEA_AS_003",
    #     "mid": "INTEGR77698636129383",
    #     "name": "Borpujari Tea Stall — Guwahati",
    #     "state_code": "AS",
    #     "business_type": "goods",
    #     "phone": "+919700112233",
    #     "email": "borpujari.tea@example.com",
    #     "language": "hi",
    #     "other_income_inr": 0,
    #     "van_id": "PYI3831611899006",
    #     "scenario": "goods_special_95pct",
    #     "target_fy_inr": 19_00_000,  # 95% of ₹20L special-category
    # },
    # {
    #     "merchant_id": "NEW_KA_004",
    #     "mid": "INTEGR77698636129383",
    #     "name": "Namma Snacks — Bengaluru",
    #     "state_code": "KA",
    #     "business_type": "goods",
    #     "phone": "+919900112244",
    #     "email": "namma.snacks@example.com",
    #     "language": "en",
    #     "other_income_inr": 0,
    #     "van_id": "PYI3831611899007",
    #     "scenario": "goods_normal_18pct",
    #     "target_fy_inr": 7_20_000,  # 18% of ₹40L — below 25% agent wake
    # },
]


def _checksum(body: dict, key: str) -> str:
    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
    digest = hmac.new(key.encode(), raw.encode(), hashlib.sha256).digest()
    import base64

    return base64.b64encode(digest).decode()


def generate_orders(merchant: dict, today: date | None = None) -> list[dict]:
    today = today or date.today()
    start = fy_start(today)
    days = max((today - start).days, 1)
    rng = random.Random(merchant["merchant_id"])  # deterministic per merchant
    target = float(merchant["target_fy_inr"])
    n_orders = 80 if settings.app_env != "test" else 24
    amounts = [max(50.0, rng.gauss(target / n_orders, target / n_orders / 4)) for _ in range(n_orders)]
    scale = target / sum(amounts)
    amounts = [round(a * scale, 2) for a in amounts]
    amounts[-1] = round(amounts[-1] + (target - sum(amounts)), 2)

    orders = []
    for i, amt in enumerate(amounts):
        day_offset = int(i * days / n_orders)
        dt = datetime.combine(start + timedelta(days=day_offset), datetime.min.time()) + timedelta(
            hours=rng.randint(8, 20), minutes=rng.randint(0, 59)
        )
        stamp = dt.strftime("%Y%m%d%H%M%S")
        txn = f"{stamp}{rng.randint(10**16, 10**17 - 1)}"[:35]
        orders.append(
            {
                "txnId": txn,
                "merchantOrderId": f"PPBL{100000 + i}",
                "orderCreatedTime": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "orderCompletedTime": (dt + timedelta(seconds=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "orderSearchType": "TRANSACTION",
                "orderSearchStatus": "SUCCESS",
                "mid": merchant["mid"],
                "merchantName": merchant["name"],
                "payMode": "BANK_TRANSFER",
                "txnAmt": None,
                "amount": f"{amt:.2f}",
                "vanId": f"vanId-{merchant['van_id']}",
                "rrn": f"rrnCode-{rng.randint(10**11, 10**12 - 1)}",
                "vanIfscCode": "PYTM0123456",
            }
        )
    return orders


# In-memory passbook keyed by VAN / merchant
_PASSBOOK: dict[str, list[dict]] = {}


def seed_passbook() -> None:
    if _PASSBOOK:
        return
    for m in DEMO_MERCHANTS:
        _PASSBOOK[m["van_id"]] = generate_orders(m)
        _PASSBOOK[m["merchant_id"]] = _PASSBOOK[m["van_id"]]


@router.post("/merchant-passbook/search/list/order/v2")
async def order_list(request: Request) -> JSONResponse:
    seed_passbook()
    payload: dict[str, Any] = await request.json()
    head = payload.get("head") or {}
    body = payload.get("body") or {}

    if not settings.paytm_skip_checksum:
        expected = _checksum(body, settings.paytm_merchant_key)
        if head.get("signature") != expected:
            return JSONResponse(
                {
                    "head": {"requestTimestamp": str(int(datetime.utcnow().timestamp() * 1000)), "version": "v1"},
                    "body": {
                        "orders": [],
                        "resultInfo": {
                            "resultStatus": "CHECKSUM_VALIDATION_FAILED",
                            "resultCodeId": "4009",
                            "resultCode": "FAILURE",
                            "resultMsg": "Checksum validation failed",
                        },
                    },
                }
            )

    for field in ("mid", "fromDate", "toDate", "orderSearchType", "orderSearchStatus"):
        if field not in body:
            return JSONResponse(
                {
                    "head": {"version": "v1"},
                    "body": {
                        "orders": [],
                        "resultInfo": {
                            "resultStatus": "MANDATORY_PARAM_MISSING",
                            "resultCodeId": "4002",
                            "resultCode": "FAILURE",
                            "resultMsg": "Mandatory Param Missing",
                        },
                    },
                }
            )

    van = None
    for cond in body.get("searchConditions") or []:
        if cond.get("searchKey") == "VAN_ID":
            van = cond.get("searchValue")

    all_orders: list[dict] = []
    if van and van in _PASSBOOK:
        all_orders = list(_PASSBOOK[van])
    else:
        for m in DEMO_MERCHANTS:
            if m["mid"] == body.get("mid"):
                all_orders.extend(_PASSBOOK.get(m["van_id"], []))

    from_s = str(body.get("fromDate", ""))[:10]
    to_s = str(body.get("toDate", ""))[:10]
    filtered = []
    for o in all_orders:
        d = o["orderCreatedTime"][:10]
        if (not from_s or d >= from_s) and (not to_s or d <= to_s):
            if o["orderSearchStatus"] == body.get("orderSearchStatus") or body.get("orderSearchStatus") == "ALL":
                filtered.append(o)

    page = int(body.get("pageNumber") or 1)
    size = int(body.get("pageSize") or 50)
    start = (page - 1) * size
    chunk = filtered[start : start + size]

    return JSONResponse(
        {
            "head": {
                "requestTimestamp": str(int(datetime.utcnow().timestamp() * 1000)),
                "version": "v1",
                "clientId": None,
                "signature": None,
            },
            "body": {
                "orders": chunk,
                "pageNum": str(page),
                "pageSize": str(size),
                "resultInfo": {
                    "resultStatus": "SUCCESS",
                    "resultCodeId": "1001",
                    "resultCode": "SUCCESS",
                    "resultMsg": "Success",
                },
            },
        }
    )
