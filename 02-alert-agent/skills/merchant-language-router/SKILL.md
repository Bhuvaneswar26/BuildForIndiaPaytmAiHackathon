---
name: merchant-language-router
description: Decides the final communication language, tone, and subject style for the merchant notification. Use before drafting the final email or WhatsApp message.
---

# Merchant language router

## Objective

Choose the best output language and tone for each merchant. The output must be deterministic, respectful, and safe for email/WhatsApp delivery.

## Input fields

- language: merchant preferred language, if present
- merchant_id: unique merchant id
- state_code: optional
- business_type: optional
- risk_category: category from GST risk classifier
- pct: percentage of registration threshold reached

## Output contract

Return a JSON object with exactly this shape:

```json
{
  "language": "en",
  "tone": "formal_friendly",
  "subject_prefix": "GST Pulse",
  "reasoning": "Merchant language is English; preserve professional but simple wording.",
  "notify_channel": "email",
  "if_language_missing": "fallback_to_en"
}
```

## Rules

1. Use the merchant's language when it is known and supported: en, hi, te.
2. If the merchant language is missing, unsupported, or noisy, default to en.
3. Keep subject lines short, clean, and non-scary.
4. For email, prefer a professional business tone.
5. For WhatsApp, prefer a slightly warmer and more direct tone.
6. Never switch to a language unless the merchant is clearly in that language.

## Supported languages

- en: English
- hi: Hindi
- te: Telugu

## Few-shot examples

### Example 1

Input:

```json
{
  "language": "hi",
  "risk_category": "act_soon",
  "pct": 82
}
```

Output:

```json
{
  "language": "hi",
  "tone": "formal_friendly",
  "subject_prefix": "GST Pulse",
  "reasoning": "Merchant preferred Hindi; use plain Hindi with a respectful, business-safe tone.",
  "notify_channel": "email",
  "if_language_missing": "fallback_to_en"
}
```

### Example 2

Input:

```json
{
  "language": "te",
  "risk_category": "prepare",
  "pct": 68
}
```

Output:

```json
{
  "language": "te",
  "tone": "calm_practical",
  "subject_prefix": "GST Pulse",
  "reasoning": "Merchant is Telugu-speaking; keep instructions simple and reassuring.",
  "notify_channel": "email",
  "if_language_missing": "fallback_to_en"
}
```

### Example 3

Input:

```json
{
  "language": null,
  "risk_category": "watch",
  "pct": 40
}
```

Output:

```json
{
  "language": "en",
  "tone": "formal_friendly",
  "subject_prefix": "GST Pulse",
  "reasoning": "Merchant language is missing; safe default is English for open communication.",
  "notify_channel": "email",
  "if_language_missing": "fallback_to_en"
}
```

## Final rule

The final message must be in one language only, not a mixed-language response. Return JSON only.
