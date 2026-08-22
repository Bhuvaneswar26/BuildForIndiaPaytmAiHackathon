from __future__ import annotations

TEMPLATES = {
    "watch": {
        "en": {
            "title": "GST Pulse: you are at {pct}% of the registration limit",
            "body": (
                "Namaste {name},\n\n"
                "Your Paytm + entered other income for {fy_label} is {aggregate} of {threshold} "
                "({pct}%). This is an early heads-up, not a tax notice.\n\n"
                "GST looks at all-India sales, not only Paytm. You can add cash/other-app sales in the app "
                "for a truer picture.\n\n"
                "Ask questions anytime: {advisor_url}\n"
                "When you are ready, registration starts here: {gst_portal}\n"
                "Keep handy: PAN, bank details, address proof, photo, Aadhaar.\n"
            ),
        },
        "hi": {
            "title": "GST Pulse: आप पंजीकरण सीमा के {pct}% पर हैं",
            "body": (
                "नमस्ते {name},\n\n"
                "{fy_label} में आपका Paytm + दर्ज अन्य आय {aggregate} है, सीमा {threshold} "
                "({pct}%)। यह कर नोटिस नहीं, पहले से जानकारी है।\n\n"
                "GST पूरे भारत की बिक्री देखता है, सिर्फ Paytm नहीं।\n\n"
                "सवाल पूछें: {advisor_url}\n"
                "पंजीकरण शुरू करें: {gst_portal}\n"
            ),
        },
        "te": {
            "title": "GST Pulse: మీరు నమోదు పరిమితిలో {pct}% వద్ద ఉన్నారు",
            "body": (
                "నమస్తే {name},\n\n"
                "{fy_label}లో మీ Paytm + ఇతర ఆదాయం {aggregate} / {threshold} ({pct}%). "
                "ఇది పన్ను నోటీసు కాదు — ముందస్తు సమాచారం.\n\n"
                "ప్రశ్నలు: {advisor_url}\n"
                "నమోదు: {gst_portal}\n"
            ),
        },
    },
    "prepare": {
        "en": {
            "title": "GST Pulse: {pct}% — start understanding registration",
            "body": (
                "Namaste {name},\n\n"
                "You are at {pct}% of the GST registration limit ({aggregate} of {threshold} in {fy_label}). "
                "At this pace you may cross it in about {months} months.\n\n"
                "Registering does not automatically mean high tax. Many small sellers of goods can use the "
                "Composition Scheme (simplified flat rate, quarterly filing) if turnover stays under the "
                "composition cap.\n\n"
                "Talk it through: {advisor_url}\n"
                "Portal: {gst_portal}\n"
                "This estimate is from Paytm data plus any other income you entered.\n"
            ),
        },
        "hi": {
            "title": "GST Pulse: {pct}% — पंजीकरण समझना शुरू करें",
            "body": (
                "नमस्ते {name},\n\n"
                "आप GST सीमा के {pct}% पर हैं ({aggregate} / {threshold}). मौजूदा रफ्तार से लगभग {months} महीने में सीमा पार हो सकती है।\n\n"
                "पंजीकरण का मतलब हमेशा ज्यादा टैक्स नहीं। कंपोजीशन स्कीम एक सरल विकल्प हो सकता है।\n\n"
                "पूछें: {advisor_url}\n"
                "पोर्टल: {gst_portal}\n"
            ),
        },
        "te": {
            "title": "GST Pulse: {pct}% — నమోదును అర్థం చేసుకోండి",
            "body": (
                "నమస్తే {name},\n\n"
                "మీరు GST పరిమితిలో {pct}% వద్ద ఉన్నారు. ఇప్పటి వేగంతో సుమారు {months} నెలల్లో దాటవచ్చు.\n\n"
                "నమోదు అంటే ఎక్కువ పన్ను కాదు. Composition Scheme సులభ మార్గం కావచ్చు.\n\n"
                "{advisor_url}\n"
                "{gst_portal}\n"
            ),
        },
    },
    "act_soon": {
        "en": {
            "title": "GST Pulse: {pct}% — plan registration this month",
            "body": (
                "Namaste {name},\n\n"
                "You are at {pct}% ({aggregate} of {threshold}). Crossing the limit without registration "
                "can lead to notices later. Starting on the GST portal now is usually calmer than reacting to a notice.\n\n"
                "Ask GST Pulse what filing looks like: {advisor_url}\n"
                "Start registration: {gst_portal}\n"
            ),
        },
        "hi": {
            "title": "GST Pulse: {pct}% — इस महीने पंजीकरण की योजना बनाएँ",
            "body": (
                "नमस्ते {name},\n\n"
                "आप {pct}% पर हैं। सीमा पार होने से पहले पोर्टल पर शुरू करना नोटिस के बाद भागने से आसान है।\n\n"
                "{advisor_url}\n"
                "{gst_portal}\n"
            ),
        },
        "te": {
            "title": "GST Pulse: {pct}% — ఈ నెలలో నమోదు ప్లాన్ చేయండి",
            "body": (
                "నమస్తే {name},\n\n"
                "మీరు {pct}% వద్ద ఉన్నారు. నోటీసు రాకముందే పోర్టల్‌లో మొదలుపెట్టండి.\n\n"
                "{advisor_url}\n"
                "{gst_portal}\n"
            ),
        },
    },
    "imminent": {
        "en": {
            "title": "GST Pulse: {pct}% — you are at the GST limit",
            "body": (
                "Namaste {name},\n\n"
                "Your estimated aggregate turnover is {pct}% of the registration threshold "
                "({aggregate} of {threshold} in {fy_label}). Please treat this as a start-now reminder, "
                "not a government notice.\n\n"
                "Composition Scheme may still apply if you stay under {composition_limit}.\n"
                "Clarify doubts (chat or voice): {advisor_url}\n"
                "GST portal: {gst_portal}\n"
            ),
        },
        "hi": {
            "title": "GST Pulse: {pct}% — आप सीमा के पास हैं",
            "body": (
                "नमस्ते {name},\n\n"
                "अनुमानित टर्नओवर सीमा का {pct}% है। यह सरकारी नोटिस नहीं है, अभी शुरू करने का रिमाइंडर है।\n\n"
                "{advisor_url}\n"
                "{gst_portal}\n"
            ),
        },
        "te": {
            "title": "GST Pulse: {pct}% — మీరు పరిమితి దగ్గర ఉన్నారు",
            "body": (
                "నమస్తే {name},\n\n"
                "మీ టర్నోవర్ పరిమితిలో {pct}%. ఇది ప్రభుత్వ నోటీసు కాదు.\n\n"
                "{advisor_url}\n"
                "{gst_portal}\n"
            ),
        },
    },
}


def inr(value: float | int | str | None) -> str:
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        return "₹0"
    return "₹" + f"{int(round(amount)):,}"


def render_message(risk: str, metrics: dict) -> dict:
    lang = (metrics.get("language") or "en").split("-")[0]
    pack = TEMPLATES[risk]
    template = pack.get(lang) or pack["en"]
    fields = {
        "name": metrics.get("name") or "merchant",
        "pct": metrics.get("pct"),
        "fy_label": metrics.get("fy_label"),
        "aggregate": inr(metrics.get("aggregate_turnover") or 0),
        "threshold": inr(metrics.get("threshold") or 0),
        "months": metrics.get("months_to_threshold") if metrics.get("months_to_threshold") is not None else "—",
        "advisor_url": metrics.get("advisor_url") or "",
        "gst_portal": metrics.get("gst_portal") or "",
        "composition_limit": inr(metrics.get("composition_limit") or 0),
    }
    return {
        "channel_title": template["title"].format(**fields),
        "body": template["body"].format(**fields),
        "language": lang if lang in pack else "en",
    }
