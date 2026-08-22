from __future__ import annotations

from typing import Any


def decide_send(policy_result: dict[str, Any], validation_result: dict[str, Any]) -> dict[str, Any]:
    allow_send = bool(policy_result.get("allow_send")) and bool(validation_result.get("ok"))
    return {
        "allow_send": allow_send,
        "reasons": {
            "policy_violations": policy_result.get("violations", []),
            "validation_issues": validation_result.get("issues", []),
        },
    }
