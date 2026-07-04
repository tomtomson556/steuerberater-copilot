"""Review worklist aggregation for deterministic offline MVP workflow results."""

from __future__ import annotations

from typing import Any

from .models import GatewayDecision, RiskLevel, WorkflowOutput
from .serialization import workflow_to_json

RISK_PRIORITY = {
    RiskLevel.CLASS_D.value: 80,
    RiskLevel.CLASS_C.value: 60,
    RiskLevel.CLASS_B.value: 40,
    RiskLevel.CLASS_A.value: 20,
}
BLOCK_PRIORITY = 100
REVIEW_REQUIRED_PRIORITY_BONUS = 5
RISK_FILTER_RANK = {
    RiskLevel.CLASS_A.value: 1,
    RiskLevel.CLASS_B.value: 2,
    RiskLevel.CLASS_C.value: 3,
    RiskLevel.CLASS_D.value: 4,
}


def build_review_worklist(outputs: list[WorkflowOutput]) -> list[dict[str, Any]]:
    """Build a local review worklist from existing workflow results only."""

    items = [_worklist_item(output) for output in outputs]
    return sorted(items, key=lambda item: (-item["priority"], item["case_id"]))


def filter_review_worklist(
    items: list[dict[str, Any]],
    *,
    limit: int | None = None,
    min_risk: str | None = None,
    gateway_decision: str | None = None,
    open_questions_only: bool = False,
) -> list[dict[str, Any]]:
    """Filter an existing worklist without changing item structure or order."""

    filtered = list(items)

    if min_risk is not None:
        minimum_rank = RISK_FILTER_RANK[min_risk]
        filtered = [
            item
            for item in filtered
            if RISK_FILTER_RANK[item["risk"]["level"]] >= minimum_rank
        ]

    if gateway_decision is not None:
        filtered = [
            item
            for item in filtered
            if item["gateway"]["decision"] == gateway_decision
        ]

    if open_questions_only:
        filtered = [
            item for item in filtered if item["open_questions_count"] > 0
        ]

    if limit is not None:
        filtered = filtered[:limit]

    return filtered


def _worklist_item(output: WorkflowOutput) -> dict[str, Any]:
    payload = workflow_to_json(output)
    open_questions = payload["draft"]["questions"]
    return {
        "case_id": payload["case_id"],
        "priority": review_priority(output),
        "gateway": {
            "decision": payload["gateway"]["decision"],
            "reasons": payload["gateway"]["reasons"],
            "block_reasons": payload["gateway"]["block_reasons"],
        },
        "risk": {
            "level": payload["risk"]["level"],
            "review_required": payload["risk"]["review_required"],
            "basis": payload["risk"]["basis"],
        },
        "review_gate": {
            "status": payload["review_gate"]["status"],
            "allows_offline_mock_continuation": (
                payload["review_gate"]["allows_offline_mock_continuation"]
            ),
            "reason": payload["review_gate"]["reason"],
        },
        "draft": {
            "available": payload["draft"]["available"],
            "review_status": payload["draft"]["review_status"],
        },
        "open_questions_count": len(open_questions),
        "open_questions": open_questions,
    }


def review_priority(output: WorkflowOutput) -> int:
    """Return a deterministic review priority from existing workflow markers."""

    if output.gateway.decision is GatewayDecision.BLOCK:
        return BLOCK_PRIORITY

    priority = RISK_PRIORITY[output.risk_classification.risk_level.value]
    if output.risk_classification.review_required:
        priority += REVIEW_REQUIRED_PRIORITY_BONUS
    return priority
