---
name: notification-format
description: Canonical JSON envelope for WhatsApp and email GST nudges sent through the MCP notify bridge. Use when calling notify_merchant or returning /v1/evaluate.
---

# Notification format

Return this object (and send it to MCP `notify_merchant`):

```json
{
  "merchant_id": "KIRANA_MH_001",
  "phone": "+91...",
  "email": "a@b.c",
  "language": "hi",
  "risk": "prepare",
  "title": "short subject, no emoji spam",
  "body": "plain text, links on their own lines",
  "advisor_url": "http://127.0.0.1:8100/?merchant=KIRANA_MH_001&lang=hi",
  "gst_portal": "https://reg.gst.gov.in/registration/",
  "checklist": ["PAN", "bank details", "address proof", "photo", "Aadhaar"],
  "metrics_summary": {
    "pct": 70.0,
    "aggregate_turnover": 2800000,
    "threshold": 4000000,
    "new_checkpoint": 0.6,
    "caveat": "Paytm + entered other income only"
  }
}
```

WhatsApp `body` max ~3500 characters. Email uses the same `title` / `body`.
The advisor URL must appear in both WhatsApp and email so the merchant can open the RAG + voice agent.
