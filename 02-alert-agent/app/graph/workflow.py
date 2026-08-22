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
    state["metrics"] = metrics
    return state


def evaluate_risk(state: AlertState) -> AlertState:
    state["risk"] = classify_risk(state["metrics"].get("pct"))
    return state


def render_alert_copy(state: AlertState) -> AlertState:
    state["copy"] = render_message(state["risk"], state["metrics"])
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
    }
    return state


def build_graph() -> Any:
    graph = StateGraph(AlertState)
    graph.add_node("normalize_input", normalize_input)
    graph.add_node("evaluate_risk", evaluate_risk)
    graph.add_node("render_alert_copy", render_alert_copy)
    graph.add_node("build_notification_payload", build_notification_payload)
    graph.add_node("dispatch_to_mcp", dispatch_to_mcp)
    graph.add_node("finalize_response", finalize_response)

    graph.add_edge(START, "normalize_input")
    graph.add_edge("normalize_input", "evaluate_risk")
    graph.add_edge("evaluate_risk", "render_alert_copy")
    graph.add_edge("render_alert_copy", "build_notification_payload")
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
        "response": {},
    }
    result = await alert_workflow.ainvoke(state)
    return result["response"]
