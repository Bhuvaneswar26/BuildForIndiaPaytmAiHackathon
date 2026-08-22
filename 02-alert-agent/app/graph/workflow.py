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
from app.services.notification_service import dispatch_notification
from app.services.risk_service import classify_risk, get_checklist
from app.services.template_service import render_message


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


def render_alert_copy(state: AlertState) -> AlertState:
    state["copy"] = render_message(state["risk"], state["metrics"])
    state["context"]["language"] = state["copy"].get("language", "en")
    return state


def validate_content(state: AlertState) -> AlertState:
    metrics = state["metrics"]
    copy = state["copy"]
    issues = []

    if not copy.get("channel_title"):
        issues.append("missing_title")
    if not copy.get("body"):
        issues.append("missing_body")
    if not (metrics.get("email") or metrics.get("phone")):
        issues.append("missing_contact")
    if not metrics.get("merchant_id"):
        issues.append("missing_merchant_id")

    state["validation"] = {
        "ok": not issues,
        "missing_fields": issues,
        "language": copy.get("language", "en"),
        "risk": state["risk"],
    }
    state["context"]["validation_summary"] = state["validation"]
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
    graph.add_node("render_alert_copy", render_alert_copy)
    graph.add_node("validate_content", validate_content)
    graph.add_node("build_notification_payload", build_notification_payload)
    graph.add_node("dispatch_to_mcp", dispatch_to_mcp)
    graph.add_node("finalize_response", finalize_response)

    graph.add_edge(START, "normalize_input")
    graph.add_edge("normalize_input", "evaluate_risk")
    graph.add_edge("evaluate_risk", "render_alert_copy")
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
