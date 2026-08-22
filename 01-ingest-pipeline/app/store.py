from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from app.config import settings


def _connect() -> sqlite3.Connection:
    path = Path(settings.sqlite_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS merchants (
                merchant_id TEXT PRIMARY KEY,
                mid TEXT NOT NULL,
                name TEXT NOT NULL,
                state_code TEXT NOT NULL,
                business_type TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                language TEXT DEFAULT 'en',
                other_income_inr REAL DEFAULT 0,
                van_id TEXT,
                scenario TEXT
            );

            CREATE TABLE IF NOT EXISTS orders (
                txn_id TEXT PRIMARY KEY,
                merchant_id TEXT NOT NULL,
                merchant_order_id TEXT,
                order_created_time TEXT,
                order_completed_time TEXT,
                order_search_type TEXT,
                order_search_status TEXT,
                mid TEXT,
                merchant_name TEXT,
                pay_mode TEXT,
                amount REAL NOT NULL,
                van_id TEXT,
                rrn TEXT,
                van_ifsc_code TEXT,
                ingested_at TEXT
            );

            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merchant_id TEXT NOT NULL,
                fy_label TEXT NOT NULL,
                paytm_turnover REAL,
                other_income REAL,
                aggregate_turnover REAL,
                threshold REAL,
                pct REAL,
                monthly_json TEXT,
                checkpoint REAL,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS ingest_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT,
                finished_at TEXT,
                status TEXT,
                detail TEXT
            );
            """
        )


def upsert_merchant(row: dict) -> None:
    with db() as conn:
        conn.execute(
            """
            INSERT INTO merchants (
                merchant_id, mid, name, state_code, business_type,
                phone, email, language, other_income_inr, van_id, scenario
            ) VALUES (
                :merchant_id, :mid, :name, :state_code, :business_type,
                :phone, :email, :language, :other_income_inr, :van_id, :scenario
            )
            ON CONFLICT(merchant_id) DO UPDATE SET
                name=excluded.name,
                state_code=excluded.state_code,
                business_type=excluded.business_type,
                phone=excluded.phone,
                email=excluded.email,
                language=excluded.language,
                other_income_inr=excluded.other_income_inr,
                van_id=excluded.van_id,
                scenario=excluded.scenario
            """,
            row,
        )


def list_merchants() -> list[dict]:
    with db() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM merchants").fetchall()]


def get_merchant(merchant_id: str) -> dict | None:
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM merchants WHERE merchant_id = ?", (merchant_id,)
        ).fetchone()
        return dict(row) if row else None


def insert_orders(orders: list[dict]) -> int:
    if not orders:
        return 0
    inserted = 0
    with db() as conn:
        for o in orders:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO orders (
                    txn_id, merchant_id, merchant_order_id, order_created_time,
                    order_completed_time, order_search_type, order_search_status,
                    mid, merchant_name, pay_mode, amount, van_id, rrn,
                    van_ifsc_code, ingested_at
                ) VALUES (
                    :txn_id, :merchant_id, :merchant_order_id, :order_created_time,
                    :order_completed_time, :order_search_type, :order_search_status,
                    :mid, :merchant_name, :pay_mode, :amount, :van_id, :rrn,
                    :van_ifsc_code, :ingested_at
                )
                """,
                o,
            )
            inserted += cur.rowcount
    return inserted


def orders_for_merchant(merchant_id: str) -> list[dict]:
    with db() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM orders WHERE merchant_id = ? ORDER BY order_completed_time",
                (merchant_id,),
            ).fetchall()
        ]


def last_snapshot_pct(merchant_id: str) -> float | None:
    with db() as conn:
        row = conn.execute(
            "SELECT pct FROM snapshots WHERE merchant_id = ? ORDER BY id DESC LIMIT 1",
            (merchant_id,),
        ).fetchone()
        return float(row["pct"]) if row else None


def save_snapshot(payload: dict) -> None:
    with db() as conn:
        conn.execute(
            """
            INSERT INTO snapshots (
                merchant_id, fy_label, paytm_turnover, other_income,
                aggregate_turnover, threshold, pct, monthly_json, checkpoint, created_at
            ) VALUES (
                :merchant_id, :fy_label, :paytm_turnover, :other_income,
                :aggregate_turnover, :threshold, :pct, :monthly_json, :checkpoint, :created_at
            )
            """,
            {
                **payload,
                "monthly_json": json.dumps(payload.get("monthly") or {}),
                "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            },
        )


def log_run(status: str, detail: str) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    with db() as conn:
        conn.execute(
            "INSERT INTO ingest_runs (started_at, finished_at, status, detail) VALUES (?,?,?,?)",
            (now, now, status, detail),
        )


def update_other_income(merchant_id: str, amount: float) -> None:
    with db() as conn:
        conn.execute(
            "UPDATE merchants SET other_income_inr = ? WHERE merchant_id = ?",
            (amount, merchant_id),
        )


def clear_snapshots() -> int:
    with db() as conn:
        cur = conn.execute("DELETE FROM snapshots")
        return cur.rowcount
