---
name: gst-risk-classify
description: Classifies a merchant GST-threshold snapshot into watch / prepare / act_soon / imminent and decides whether to notify. Use when ingest metrics arrive or when drafting an early-warning nudge.
---

# GST risk classify

## Bands (percent of registration threshold)

| Band | Range | Intent |
|---|---|---|
| `watch` | 25%–59% | Visibility only. No scare language. |
| `prepare` | 60%–79% | Explain registration + composition. |
| `act_soon` | 80%–94% | Ask them to start the portal checklist this month. |
| `imminent` | ≥95% | Start-now reminder. Never impersonate a GST notice. |

Do not invent a fifth band. If `pct` < 25, do not send WhatsApp/email.

## Inputs you will receive

`pct`, `aggregate_turnover`, `threshold`, `state_code`, `business_type`, `is_special_category`, `months_to_threshold`, `composition_eligible`, `data_caveat`, `new_checkpoint`.

## Rules

1. Category comes only from `pct` (table above). Do not upgrade risk because of a scary story.
2. Always keep the Paytm-only caveat in the payload, even if the merchant entered other income.
3. If `new_checkpoint` is null and a message was already sent for this band, still return the classification but set `notify: false` unless the caller forced a demo.
4. Output JSON only, matching [notification-format](../notification-format/SKILL.md).
