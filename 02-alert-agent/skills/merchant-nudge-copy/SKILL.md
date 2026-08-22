---
name: merchant-nudge-copy
description: Writes plain-language GST early-warning copy in English, Hindi, or Telugu. Use after risk classification when composing WhatsApp or email text for kirana / small merchants.
---

# Merchant nudge copy

## Voice

- Calm, specific, adult-to-adult. No "penalty!", no red sirens, no fake legal threats.
- Fear to address: "I don't know where I stand / what registering means / I found out from a notice."
- Product job: early visibility + what to do next. Not tax filing.

## Must mention

1. Current percent and rupee amounts (Indian grouping).
2. That this is **not** a government notice.
3. PAN-India aggregate caveat (Paytm + optional other income).
4. Composition Scheme when `composition_eligible` is true (goods ~₹1.5 crore / services ~₹50 lakh; simplified rate + quarterly filing).
5. Two links: GST Pulse advisor (chat/voice) and GST portal.
6. Checklist: PAN, bank, address proof, photo, Aadhaar.

## Language

Use `language`: `en`, `hi`, or `te`. Keep numbers in Western digits. Keep URLs unchanged.

## Forbidden

- Filing a return for them
- Quoting a tax amount they "will owe"
- Saying Paytm data is complete turnover
