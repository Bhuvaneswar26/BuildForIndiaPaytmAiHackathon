from __future__ import annotations

import base64
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
    paytm_logo_url: str = ""
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


def _normalize_email_text(value: str) -> str:
    text = (value or "").replace("\r\n", "\n").replace("\r", "\n")
    return text.strip()


def _resolve_paytm_logo_data_uri() -> str:
    configured = (settings.paytm_logo_url or "").strip()
    if configured:
        return configured

    candidate_paths = [
        Path(__file__).resolve().parent.parent / "Static" / "Images" / "paytm-com-logo.png",
        Path(__file__).resolve().parent.parent / "static" / "images" / "paytm-com-logo.png",
        Path(__file__).resolve().parent.parent / "Static" / "images" / "paytm-com-logo.png",
    ]

    for logo_path in candidate_paths:
        if logo_path.exists():
            encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
            return f"data:image/png;base64,{encoded}"
    return ""


def _build_logo_placeholder() -> str:
    logo_url = _resolve_paytm_logo_data_uri()
    if logo_url:
        return (
            f'<img src="{logo_url}" alt="Paytm logo" '
            'style="width:42px; height:42px; border-radius:50%; object-fit:cover; background:#ffffff; display:block;" />'
        )
    return (
        '<div style="width:42px; height:42px; border-radius:50%; background:#ffffff; display:inline-flex; '
        'align-items:center; justify-content:center; font-weight:700; color:#003d90; font-size:10px; line-height:1; '
        'letter-spacing:0.6px;">PAYTM</div>'
    )


def _build_paytm_email_html(subject: str, body: str) -> str:
    safe_subject = (subject or "GST Pulse Alert").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    clean_body = _normalize_email_text(body)
    logo_block = _build_logo_placeholder()
    paragraphs = [
        f"<p style=\"margin:0 0 14px; font-size:15px; line-height:1.7; color:#1c2331;\">{line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace(chr(10), '<br>')}</p>"
        for line in clean_body.split("\n")
        if line.strip()
    ]
    email_html = f"""
    <html>
      <body style="margin:0; background:#f3f7fb; font-family:Arial, Helvetica, sans-serif; color:#1b1d21;">
        <div style="max-width:680px; margin:28px auto; background:#ffffff; border:1px solid #e7edf5; border-radius:16px; overflow:hidden; box-shadow:0 10px 28px rgba(15, 23, 42, 0.06);">
          <div style="background:linear-gradient(90deg, #00baf2 0%, #002d7b 100%); padding:18px 28px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td align="left" valign="middle" style="width:50px;">
                  {logo_block}
                </td>
                <td align="left" valign="middle">
                  <div style="font-size:20px; font-weight:700; color:#ffffff; letter-spacing:0.2px;">Paytm</div>
                  <div style="font-size:11px; letter-spacing:0.8px; color:#dfefff; text-transform:uppercase; margin-top:2px;">GST Pulse</div>
                </td>
              </tr>
            </table>
          </div>

          <div style="padding:28px 28px 10px;">
            <div style="font-size:12px; letter-spacing:1.2px; text-transform:uppercase; color:#5a6475; font-weight:700; margin-bottom:14px;">Merchant alert</div>
            <h1 style="margin:0 0 18px; font-size:28px; line-height:1.3; color:#0f172a;">{safe_subject}</h1>
            {''.join(paragraphs) if paragraphs else '<p style="margin:0; color:#1c2331; font-size:15px;">Dear merchant,</p>'}
          </div>

          <div style="padding:0 28px 26px;">
            <div style="background:#f7fafc; border-left:4px solid #00baf2; padding:16px 18px; border-radius:10px; margin-top:8px;">
              <p style="margin:0; font-size:13px; line-height:1.7; color:#334155;">
                This is a service update from Paytm GST Pulse. Please review the details and take action via the GST registration portal when required.
              </p>
            </div>
          </div>

          <div style="padding:0 28px 30px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-top:1px solid #edf2f7; margin-top:10px;">
              <tr>
                <td style="padding-top:18px; text-align:center; color:#64748b; font-size:12px; line-height:1.7;">
                  <div style="font-weight:700; color:#1e293b;">Paytm GST Pulse</div>
                  <div>Helping merchants act before GST thresholds become a compliance issue.</div>
                </td>
              </tr>
            </table>
          </div>

          <div style="background:#0f172a; padding:18px 28px; color:#e2e8f0; font-size:12px; text-align:center;">
            <div style="font-weight:700; color:#ffffff; margin-bottom:4px;">Paytm</div>
            <div>Secure • Simple • Smart merchant support</div>
          </div>
        </div>
      </body>
    </html>
    """
    return email_html


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

    plain_text = _normalize_email_text(body)
    msg.set_content(plain_text)
    msg.add_alternative(_build_paytm_email_html(title, body), subtype="html")

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
