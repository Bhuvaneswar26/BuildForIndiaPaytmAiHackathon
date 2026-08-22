---
name: gst-risk-classify
description: Classifies a merchant GST-threshold snapshot into watch / prepare / act_soon / imminent and decides whether to notify. Use when ingest metrics arrive or when drafting an early-warning nudge.
---

# GST risk classify

## Band definitions

| Band       | Range   | Intent                                                           |
| ---------- | ------- | ---------------------------------------------------------------- |
| `watch`    | 25%–59% | Visibility only. Calm informational update.                      |
| `prepare`  | 60%–79% | Explain registration and composition path.                       |
| `act_soon` | 80%–94% | Encourage the merchant to start the portal process this month.   |
| `imminent` | ≥95%    | Strong start-now reminder without pretending to be a GST notice. |

Do not invent a fifth band. If `pct` < 25, do not send a merchant note.

## Inputs

`pct`, `aggregate_turnover`, `threshold`, `months_to_threshold`, `composition_eligible`, `data_caveat`, `new_checkpoint`, `language`, `merchant_id`, `name`.

## Output contract

Return JSON in this exact shape:

```json
{
  "risk_category": "act_soon",
  "notify": true,
  "confidence": "high",
  "reason": "Merchant is at 88% of threshold; this is an early prompting stage.",
  "suggestions": [
    "Review the registration checklist",
    "Check composition eligibility",
    "Prepare business and identity documents"
  ]
}
```

## Rules

1. Risk category must be derived from `pct` only.
2. Never escalate risk due to fear, rumors, or a dramatic story.
3. `notify` is true only when the risk is in the watch/prepare/act_soon/imminent bands and the threshold is relevant.
4. Keep the caveat in the payload; this is Paytm + any user-entered income estimate, not complete government turnover.
5. Output must be valid JSON only.

## Few-shot examples

### Example 1

Input:

```json
{
  "pct": 42,
  "threshold": 1000000,
  "aggregate_turnover": 420000,
  "language": "en"
}
```

Output:

```json
{
  "risk_category": "watch",
  "notify": false,
  "confidence": "medium",
  "reason": "Merchant is at 42% of the GST registration threshold. This is an informational watch state.",
  "suggestions": [
    "Monitor turnover trend",
    "Keep the estimate updated",
    "Review any other income that should be included"
  ]
}
```

### Example 2

Input:

```json
{
  "pct": 67,
  "threshold": 1000000,
  "aggregate_turnover": 670000,
  "composition_eligible": true
}
```

Output:

```json
{
  "risk_category": "prepare",
  "notify": true,
  "confidence": "high",
  "reason": "Merchant has crossed 60% of the threshold and is trending toward registration within a few months.",
  "suggestions": [
    "Understand GST registration flow",
    "Check composition eligibility",
    "Prepare PAN, bank details, and address proof"
  ]
}
```

### Example 3

Input:

```json
{
  "pct": 88,
  "threshold": 1000000,
  "aggregate_turnover": 880000,
  "months_to_threshold": 2
}
```

Output:

```json
{
  "risk_category": "act_soon",
  "notify": true,
  "confidence": "high",
  "reason": "Merchant is at 88% of threshold and may cross the limit soon. A practical reminder is appropriate.",
  "suggestions": [
    "Compile the GST registration checklist",
    "Open the GST portal and start review",
    "Check whether composition remains useful"
  ]
}
```

### Example 4

Input:

```json
{
  "pct": 97,
  "threshold": 1000000,
  "aggregate_turnover": 970000,
  "language": "hi"
}
```

Output:

```json
{
  "risk_category": "imminent",
  "notify": true,
  "confidence": "high",
  "reason": "Merchant is very close to the GST limit and should begin registration without delay.",
  "suggestions": [
    "Start the registration process now",
    "Gather identity and business documents",
    "Use the advisor channel for quick clarification"
  ]
}
```

## Final rule

Do not produce freeform advisory text. Return valid JSON only.
