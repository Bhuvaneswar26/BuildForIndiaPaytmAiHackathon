from __future__ import annotations

from typing import Any, Literal, TypedDict

Risk = Literal["watch", "prepare", "act_soon", "imminent"]


class MetricsDict(TypedDict, total=False):
    merchant_id: str | None
    phone: str | None
    email: str | None
    language: str | None
    pct: float | int | str | None
    aggregate_turnover: float | int | str | None
    threshold: float | int | str | None
    fy_label: str | None
    advisor_url: str | None
    gst_portal: str | None
    data_caveat: str | None
    new_checkpoint: str | None
    composition_limit: float | int | str | None
    months_to_threshold: float | int | str | None
    name: str | None


class AlertState(TypedDict):
    metrics: dict[str, Any]
    risk: str
    copy: dict[str, Any]
    payload: dict[str, Any]
    notified: dict[str, Any]
    response: dict[str, Any]
