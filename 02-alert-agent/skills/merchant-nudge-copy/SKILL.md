---
name: merchant-nudge-copy
description: Writes plain-language GST early-warning copy in English, Hindi, or Telugu. Use after risk classification when composing WhatsApp or email text for kirana / small merchants.
---

# Merchant nudge copy

## Voice

- Calm, specific, adult-to-adult.
- No penalty language, no fake legal threats, no red sirens.
- The product job is early visibility and a clear next step, not tax filing or enforcement.

## Required message elements

1. Current threshold percentage and rupee totals.
2. Explicit statement that this is not a government notice.
3. PAN-India aggregate caveat: Paytm + other declared income.
4. Composition Scheme mention when eligible.
5. Two links: GST Pulse advisor and GST registration portal.
6. Checklist: PAN, bank details, address proof, photo, Aadhaar.

## Language rules

- Use `language`: `en`, `hi`, or `te` only.
- Keep numbers in Western digits.
- Keep URLs unchanged.
- Keep one language in final output, not mixed-language text.

## Few-shot examples

### Example 1: English

Input:

```json
{
  "language": "en",
  "pct": 88,
  "aggregate_turnover": 880000,
  "threshold": 1000000,
  "composition_eligible": true,
  "advisor_url": "https://advisor.example.com",
  "gst_portal": "https://reg.gst.gov.in/registration/"
}
```

Output:

```text
Namaste,

You are at 88% of the GST registration threshold (₹8,80,000 of ₹10,00,000). This is a helpful reminder and not a government notice.

GST registration is based on aggregate turnover across sales channels, not just Paytm. This estimate includes Paytm + any other income you entered.

If you are eligible, the Composition Scheme may still be useful for simpler filing. Please review the registration flow and keep your documents ready.

Talk to GST Pulse: https://advisor.example.com
Start registration: https://reg.gst.gov.in/registration/

Keep handy: PAN, bank details, address proof, photo, Aadhaar.
```

### Example 2: Hindi

Input:

```json
{
  "language": "hi",
  "pct": 72,
  "aggregate_turnover": 720000,
  "threshold": 1000000,
  "composition_eligible": true
}
```

Output:

```text
नमस्ते,

आप GST पंजीकरण सीमा के 72% पर हैं (₹10,00,000 में से ₹7,20,000)। यह सरकारी नोटिस नहीं है, बल्कि एक समय पर मदद करने वाला रिमाइंडर है।

GST की सीमा पूरे भारत की कुल बिक्री पर देखी जाती है, सिर्फ Paytm पर नहीं। यह अनुमान Paytm + आपके द्वारा दर्ज की गई अन्य आय को मिलाकर है।

अगर आप eligible हैं, तो Composition Scheme सरल फाइलिंग का विकल्प हो सकता है।

GST Pulse से बात करें: https://advisor.example.com
पंजीकरण शुरू करें: https://reg.gst.gov.in/registration/

साथ रखें: PAN, बैंक विवरण, पता प्रमाण, फोटो, Aadhaar.
```

### Example 3: Telugu

Input:

```json
{
  "language": "te",
  "pct": 90,
  "aggregate_turnover": 900000,
  "threshold": 1000000,
  "composition_eligible": false
}
```

Output:

```text
నమస్తే,

మీరు GST నమోదు పరిమితిలో 90% వద్ద ఉన్నారు (₹10,00,000 లో ₹9,00,000). ఇది ప్రభుత్వ నోటీసు కాదు, పనితీరుకు సహాయపడే రిమైండర్.

GST నమోదు మొత్తం దేశవ్యాప్త అమ్మకాల ఆధారంగా ఉంటుంది; Paytm మాత్రమే కాదు. ఈ అంచనా Paytm + మీ నమోదు చేసిన ఇతర ఆదాయాన్ని కలుపుతుంది.

మీరు ఇప్పుడు ముందుకు వెళ్లి నమోదు ప్రక్రియను ప్రారంభించడం మంచిది.

GST Pulseతో మాట్లాడండి: https://advisor.example.com
నమోదును ప్రారంభించండి: https://reg.gst.gov.in/registration/

సహాయం కోసం సిద్ధంగా ఉంచండి: PAN, బ్యాంక్ వివరాలు, చిరునామా రుజువు, ఫోటో, Aadhaar.
```

## Forbidden

- Filing a return for the merchant
- Quoting a tax amount they will owe
- Pretending the estimate is official GST data
- Using more than one language in the same message
