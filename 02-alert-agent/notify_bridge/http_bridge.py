from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        extra="ignore",
    )
    whatsapp_mode: str = "mock"
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "gst-pulse@example.com"
    notify_log: str = "./data/notifications.jsonl"


settings = Settings()
app = FastAPI(title="GST Pulse MCP Notification Bridge", version="0.1.0")


class NotifyIn(BaseModel):
    merchant_id: str | None = None
    phone: str | None = None
    email: str | None = None
    language: str | None = "en"
    risk: str | None = None
    title: str
    body: str
    advisor_url: str | None = None
    gst_portal: str | None = None
    checklist: list[str] | None = None
    metrics_summary: dict | None = None


def _log(event: dict) -> None:
    path = Path(settings.notify_log)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / path
    path.parent.mkdir(parents=True, exist_ok=True)
    event["ts"] = datetime.utcnow().isoformat() + "Z"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def send_whatsapp(phone: str | None, title: str, body: str) -> dict:
    text = f"{title}\n\n{body}"
    if settings.whatsapp_mode != "live" or not settings.whatsapp_token:
        _log({"channel": "whatsapp", "mode": "mock", "to": phone, "text": text})
        return {"channel": "whatsapp", "mode": "mock", "to": phone, "ok": True}
    import httpx

    url = f"https://graph.facebook.com/v20.0/{settings.whatsapp_phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": (phone or "").lstrip("+"),
        "type": "text",
        "text": {"body": text[:4000]},
    }
    resp = httpx.post(
        url,
        headers={"Authorization": f"Bearer {settings.whatsapp_token}"},
        json=payload,
        timeout=20.0,
    )
    _log({"channel": "whatsapp", "mode": "live", "status": resp.status_code, "to": phone})
    return {"channel": "whatsapp", "mode": "live", "ok": resp.is_success, "status": resp.status_code}


def send_email(to: str | None, title: str, body: str) -> dict:
    if not settings.smtp_host or not to:
        _log({"channel": "email", "mode": "mock", "to": to, "subject": title, "body": body})
        return {"channel": "email", "mode": "mock", "to": to, "ok": True}
    import smtplib
    from email.message import EmailMessage

    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg["Subject"] = title
    msg.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)
    _log({"channel": "email", "mode": "live", "to": to, "subject": title})
    return {"channel": "email", "mode": "live", "to": to, "ok": True}


@app.get("/health")
async def health():
    return {"ok": True, "whatsapp_mode": settings.whatsapp_mode}


@app.post("/tools/notify_merchant")
async def notify_merchant(body: NotifyIn):
    wa = send_whatsapp(body.phone, body.title, body.body)
    try:
        mail = send_email(body.email, body.title, body.body)
    except Exception as exc:
        _log({"channel": "email", "mode": "live", "to": body.email, "ok": False, "error": str(exc)})
        mail = {"channel": "email", "mode": "live", "to": body.email, "ok": False, "error": str(exc)}
    return {"ok": wa.get("ok", False) and mail.get("ok", False), "whatsapp": wa, "email": mail}


@app.get("/tools/recent")
async def recent():
    path = Path(settings.notify_log)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / path
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").strip().splitlines()[-20:]
    return [json.loads(x) for x in lines]
