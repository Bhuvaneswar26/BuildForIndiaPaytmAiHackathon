"""Paytm passbook client. Hits mock in dev/test, live host in production."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import date, datetime, timedelta

import httpx

from app.config import settings


def checksum(body: dict) -> str:
    import base64

    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
    digest = hmac.new(settings.paytm_merchant_key.encode(), raw.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def _date_chunks(start: date, end: date, max_days: int = 30) -> list[tuple[date, date]]:
    chunks = []
    cur = start
    while cur <= end:
        nxt = min(cur + timedelta(days=max_days - 1), end)
        chunks.append((cur, nxt))
        cur = nxt + timedelta(days=1)
    return chunks


async def fetch_orders(
    mid: str,
    van_id: str | None,
    from_date: date,
    to_date: date,
) -> list[dict]:
    orders: list[dict] = []
    url = settings.paytm_base_url.rstrip("/") + "/merchant-passbook/search/list/order/v2"
    async with httpx.AsyncClient(timeout=30.0) as client:
        for start, end in _date_chunks(from_date, to_date):
            page = 1
            while True:
                body = {
                    "mid": mid,
                    "fromDate": f"{start.isoformat()}T00:00:00+05:30",
                    "toDate": f"{end.isoformat()}T23:59:59+05:30",
                    "orderSearchType": "TRANSACTION",
                    "orderSearchStatus": "SUCCESS",
                    "pageNumber": str(page),
                    "pageSize": "50",
                }
                if van_id:
                    body["searchConditions"] = [{"searchKey": "VAN_ID", "searchValue": van_id}]
                payload = {
                    "body": body,
                    "head": {
                        "requestTimestamp": str(int(datetime.utcnow().timestamp() * 1000)),
                        "tokenType": "CHECKSUM",
                        "signature": checksum(body),
                    },
                }
                resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                resp.raise_for_status()
                data = resp.json()
                info = (data.get("body") or {}).get("resultInfo") or {}
                if info.get("resultStatus") != "SUCCESS":
                    raise RuntimeError(info.get("resultMsg") or "Paytm order list failed")
                batch = (data.get("body") or {}).get("orders") or []
                orders.extend(batch)
                if len(batch) < 50:
                    break
                page += 1
    return orders
