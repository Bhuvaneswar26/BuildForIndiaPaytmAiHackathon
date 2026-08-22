---
name: merchant-action-guidance
description: Provides practical merchant-focused guidance and likely next steps based on GST threshold category and score. Use after risk classification and before final message synthesis.
---

# Merchant action guidance

## Objective

Translate the GST risk category into actionable and merchant-safe next steps. This skill is for nudging a merchant toward a clear follow-up without sounding like a legal penalty notice.

## Risk categories

- watch: 25% to 59%
- prepare: 60% to 79%
- act_soon: 80% to 94%
- imminent: 95% and above

## Output contract

Return JSON with this structure:

```json
{
  "risk_category": "act_soon",
  "suggestion_summary": "Start registration checklist this month and review whether composition is suitable.",
  "next_steps": [
    "Confirm your aggregate turnover estimate",
    "Check composition eligibility",
    "Prepare PAN, bank details, and digital documents"
  ],
  "tone": "business_helpful",
  "do_not_say": [
    "You are definitely non-compliant",
    "Penalty is automatically due"
  ]
}
```

## Rules

1. Suggestions must be practical and simple.
2. The advice must be based on category and current percentage.
3. Keep wording neutral and non-threatening.
4. If `pct` is very high, advise immediate action but never impersonate a tax notice.
5. When `composition_eligible` is true, mention composition as an option.

## Few-shot examples

### Example 1

Input:

```json
{
  "risk_category": "watch",
  "pct": 42,
  "composition_eligible": true
}
```

Output:

```json
{
  "risk_category": "watch",
  "suggestion_summary": "Keep monitoring turnover and validate the estimate with other income sources.",
  "next_steps": [
    "Review your recent sales and cash entries",
    "Check whether other income should be added to the estimate",
    "Use the advisor link if you want a quick GST explanation"
  ],
  "tone": "calm_monitoring",
  "do_not_say": ["You have broken the law", "This is an official GST notice"]
}
```

### Example 2

Input:

```json
{
  "risk_category": "prepare",
  "pct": 67,
  "composition_eligible": true
}
```

Output:

```json
{
  "risk_category": "prepare",
  "suggestion_summary": "Start understanding the GST registration flow and check whether composition can simplify filings.",
  "next_steps": [
    "Review your turnover trend for the current financial year",
    "Check composition eligibility before you register",
    "Prepare PAN, address proof, and bank details"
  ],
  "tone": "business_helpful",
  "do_not_say": ["You must file immediately", "A default tax amount is due"]
}
```

### Example 3

Input:

```json
{
  "risk_category": "act_soon",
  "pct": 88,
  "composition_eligible": false
}
```

Output:

```json
{
  "risk_category": "act_soon",
  "suggestion_summary": "Start the registration checklist this month and keep your documentation ready.",
  "next_steps": [
    "Open the GST registration portal",
    "Prepare PAN, Aadhaar, business address proof, and bank info",
    "Book a quick advisor review if there is confusion around the threshold"
  ],
  "tone": "business_helpful",
  "do_not_say": ["You are in serious default", "Government has issued a notice"]
}
```

### Example 4

Input:

```json
{
  "risk_category": "imminent",
  "pct": 97,
  "composition_eligible": false
}
```

Output:

```json
{
  "risk_category": "imminent",
  "suggestion_summary": "Act now. This is a start-now reminder, not a legal notice, but the merchant should begin registration without delay.",
  "next_steps": [
    "Start the GST registration process immediately",
    "Gather business and identity documents",
    "Use the advisor channel to clarify if any threshold assumptions need review"
  ],
  "tone": "urgent_but_safe",
  "do_not_say": [
    "You have already received a penalty",
    "This is an official GST enforcement action"
  ]
}
```

## Final rule

Suggestions should feel helpful, not frightening. Return JSON only.
