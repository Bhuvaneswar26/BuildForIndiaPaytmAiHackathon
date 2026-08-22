from __future__ import annotations

from typing import Any

try:
    import langchain  # type: ignore

    if not hasattr(langchain, "debug"):
        langchain.debug = False
except ModuleNotFoundError:
    pass

from langgraph.graph import END, START, StateGraph

from app.domain.types import AlertState
from app.guardrails.decisions import decide_send
from app.guardrails.fallback import get_fallback_response
from app.guardrails.policy import evaluate_policy
from app.guardrails.validators import validate_message_text, validate_payload
from app.services.gemini_service import generate_alert_copy
from app.services.notification_service import dispatch_notification
from app.services.risk_service import classify_risk, get_checklist


def normalize_input(state: AlertState) -> AlertState:
    metrics = dict(state.get("metrics") or {})
    normalized = {
        "merchant_id": metrics.get("merchant_id") or "unknown_merchant",
        "name": metrics.get("name") or "merchant",
        "phone": metrics.get("phone"),
        "email": metrics.get("email"),
        "language": (metrics.get("language") or "en").split("-")[0],
        "pct": metrics.get("pct"),
        "aggregate_turnover": metrics.get("aggregate_turnover"),
        "threshold": metrics.get("threshold"),
        "fy_label": metrics.get("fy_label") or "FY2025-26",
        "advisor_url": metrics.get("advisor_url") or "",
        "gst_portal": metrics.get("gst_portal") or "",
        "data_caveat": metrics.get("data_caveat") or "Estimated from platform + declared sales.",
        "new_checkpoint": metrics.get("new_checkpoint"),
        "composition_limit": metrics.get("composition_limit"),
        "months_to_threshold": metrics.get("months_to_threshold"),
    }
    state["metrics"] = normalized
    state["context"] = {
        "merchant_name": normalized["name"],
        "merchant_id": normalized["merchant_id"],
    }
    return state


def evaluate_risk(state: AlertState) -> AlertState:
    pct = state["metrics"].get("pct")
    risk = classify_risk(pct)
    state["risk"] = risk
    threshold = state["metrics"].get("threshold")
    state["context"]["risk_reason"] = (
        f"Merchant is at {pct}% of the GST registration threshold; "
        f"risk band classified as '{risk}' for threshold {threshold}."
    )
    return state


def decide_language(state: AlertState) -> AlertState:
    metrics = state["metrics"]
    preferred = (metrics.get("language") or "en").split("-")[0].lower()
    allowed = {"en", "hi", "te"}
    chosen = preferred if preferred in allowed else "en"
    metrics["language"] = chosen

    notify_channel = "email" if metrics.get("email") else "whatsapp"
    state["context"]["language_policy"] = {
        "preferred_language": preferred,
        "selected_language": chosen,
        "notify_channel": notify_channel,
        "tone": "formal_friendly" if chosen == "en" else "calm_practical",
        "subject_prefix": "GST Pulse",
        "reasoning": (
            f"Merchant preferred language '{preferred}' but unsupported values fallback to 'en'; "
            f"the message will be written in '{chosen}' for the {notify_channel} channel."
        ),
    }
    return state


def build_merchant_guidance(state: AlertState) -> AlertState:
    metrics = state["metrics"]
    risk = state["risk"]
    pct = metrics.get("pct")
    comp_eligible = bool(metrics.get("composition_limit") and (metrics.get("aggregate_turnover") or 0) < metrics.get("composition_limit"))

    guidance_map = {
        "watch": {
            "summary": "Monitor turnover and verify whether other income should be included.",
            "suggestions": [
                "Review recent sales and cash entries",
                "Check whether other declared income should be added",
                "Keep the estimate up to date before the next review"
            ],
        },
        "prepare": {
            "summary": "Begin preparing the GST registration flow and understand whether composition may help.",
            "suggestions": [
                "Check the GST registration checklist",
                "Review composition eligibility before filing",
                "Prepare the key business documents and bank details"
            ],
        },
        "act_soon": {
            "summary": "Start the registration checklist this month and avoid leaving it for the last minute.",
            "suggestions": [
                "Open the GST registration portal and begin review",
                "Get PAN, Aadhaar, and address proof ready",
                "Use the advisor link to clarify any threshold doubts"
            ],
        },
        "imminent": {
            "summary": "This is a start-now reminder; do not wait for a notice to begin the registration flow.",
            "suggestions": [
                "Start registration immediately",
                "Gather all identity and business documents",
                "Use the advisor channel if the estimate or threshold needs a quick check"
            ],
        },
    }

    if comp_eligible and risk in {"prepare", "act_soon"}:
        guidance_map[risk]["suggestions"].append("Composition may still be available; confirm whether it suits your business model.")

    state["context"]["merchant_guidance"] = {
        "risk_category": risk,
        "pct": pct,
        "summary": guidance_map[risk]["summary"],
        "suggestions": guidance_map[risk]["suggestions"],
        "composition_eligible": comp_eligible,
    }
    return state


def apply_guardrails(state: AlertState) -> AlertState:
    metrics = state["metrics"]
    risk = state["risk"]

    policy_result = evaluate_policy(metrics, risk)
    state["context"]["guardrails"] = {
        "allow_send": policy_result["allow_send"],
        "blocked_reasons": policy_result["violations"],
        "policy": policy_result["policy"],
        "risk_category": risk,
    }

    if not policy_result["allow_send"]:
        state["context"]["guardrails"]["fallback"] = get_fallback_response()
    return state


def render_alert_copy(state: AlertState) -> AlertState:
    state["copy"] = generate_alert_copy(state["risk"], state["metrics"])
    if not state["copy"].get("channel_title"):
        state["copy"] = {
            "channel_title": "GST Pulse Alert",
            "body": "Please review your GST registration status.",
            "language": state["metrics"].get("language", "en"),
        }
    state["context"]["language"] = state["copy"].get("language", "en")
    return state


def validate_content(state: AlertState) -> AlertState:
    metrics = state["metrics"]
    copy = state["copy"]
    payload = {
        "merchant_id": metrics.get("merchant_id"),
        "phone": metrics.get("phone"),
        "email": metrics.get("email"),
        "title": copy.get("channel_title"),
        "body": copy.get("body"),
        "language": copy.get("language", "en"),
    }

    payload_validation = validate_payload(payload)
    message_validation = validate_message_text(copy.get("body", ""))
    combined = {
        "ok": payload_validation["ok"] and message_validation["ok"],
        "issues": payload_validation["issues"] + message_validation["issues"],
        "language": copy.get("language", "en"),
        "risk": state["risk"],
    }

    state["validation"] = combined
    state["context"]["validation_summary"] = combined
    return state


def build_notification_payload(state: AlertState) -> AlertState:
    metrics = state["metrics"]
    copy = state["copy"]
    payload = {
        "merchant_id": metrics.get("merchant_id"),
        "phone": metrics.get("phone"),
        "email": metrics.get("email"),
        "language": copy["language"],
        "risk": state["risk"],
        "title": copy["channel_title"],
        "body": copy["body"],
        "advisor_url": metrics.get("advisor_url"),
        "gst_portal": metrics.get("gst_portal"),
        "checklist": get_checklist(),
        "metrics_summary": {
            "pct": metrics.get("pct"),
            "aggregate_turnover": metrics.get("aggregate_turnover"),
            "threshold": metrics.get("threshold"),
            "new_checkpoint": metrics.get("new_checkpoint"),
            "caveat": metrics.get("data_caveat"),
        },
    }
    state["payload"] = payload
    return state


async def dispatch_to_mcp(state: AlertState) -> AlertState:
    state["notified"] = await dispatch_notification(state["payload"])
    return state


def finalize_response(state: AlertState) -> AlertState:
    state["response"] = {
        "risk": state["risk"],
        "message": state["copy"],
        "notified": state["notified"],
        "payload": state["payload"],
        "validation": state["validation"],
        "context": state["context"],
    }
    return state


def build_graph() -> Any:
    graph = StateGraph(AlertState)
    graph.add_node("normalize_input", normalize_input)
    graph.add_node("evaluate_risk", evaluate_risk)
    graph.add_node("decide_language", decide_language)
    graph.add_node("build_merchant_guidance", build_merchant_guidance)
    graph.add_node("apply_guardrails", apply_guardrails)
    graph.add_node("render_alert_copy", render_alert_copy)
    graph.add_node("validate_content", validate_content)
    graph.add_node("build_notification_payload", build_notification_payload)
    graph.add_node("dispatch_to_mcp", dispatch_to_mcp)
    graph.add_node("finalize_response", finalize_response)

    graph.add_edge(START, "normalize_input")
    graph.add_edge("normalize_input", "evaluate_risk")
    graph.add_edge("evaluate_risk", "decide_language")
    graph.add_edge("decide_language", "build_merchant_guidance")
    graph.add_edge("build_merchant_guidance", "apply_guardrails")
    graph.add_edge("apply_guardrails", "render_alert_copy")
    graph.add_edge("render_alert_copy", "validate_content")
    graph.add_edge("validate_content", "build_notification_payload")
    graph.add_edge("build_notification_payload", "dispatch_to_mcp")
    graph.add_edge("dispatch_to_mcp", "finalize_response")
    graph.add_edge("finalize_response", END)

    return graph.compile()


alert_workflow = build_graph()


async def run_alert_workflow(metrics: dict[str, Any]) -> dict[str, Any]:
    state: AlertState = {
        "metrics": metrics,
        "risk": "",
        "copy": {},
        "payload": {},
        "notified": {},
        "validation": {},
        "context": {},
        "response": {},
    }
    result = await alert_workflow.ainvoke(state)
    return result["response"]
