"""Review summary aggregation for deterministic offline MVP workflow results."""

from __future__ import annotations

from typing import Any

from .models import GatewayDecision, ReviewGateStatus, RiskLevel, WorkflowOutput
from .review_worklist import build_review_worklist
from .serialization import workflow_to_json

GATEWAY_DECISION_COUNTS = {
    GatewayDecision.ALLOW_DRAFT.value: 0,
    GatewayDecision.ESCALATE.value: 0,
    GatewayDecision.BLOCK.value: 0,
}
RISK_LEVEL_COUNTS = {
    RiskLevel.CLASS_A.value: 0,
    RiskLevel.CLASS_B.value: 0,
    RiskLevel.CLASS_C.value: 0,
    RiskLevel.CLASS_D.value: 0,
}
REVIEW_GATE_COUNTS = {
    ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION.value: 0,
    ReviewGateStatus.REQUIRES_HUMAN_REVIEW.value: 0,
}


def build_review_summary(outputs: list[WorkflowOutput]) -> dict[str, Any]:
    """Build a local stdout-only review summary from existing workflow results."""

    summary: dict[str, Any] = {
        "total_cases": len(outputs),
        "gateway": dict(GATEWAY_DECISION_COUNTS),
        "risk": dict(RISK_LEVEL_COUNTS),
        "review_gate": dict(REVIEW_GATE_COUNTS),
        "draft_availability": {"available": 0, "unavailable": 0},
        "open_questions": {
            "total": 0,
            "cases_with_open_questions": [],
        },
        "highest_priority_cases": [],
    }

    for output in outputs:
        payload = workflow_to_json(output)
        summary["gateway"][payload["gateway"]["decision"]] += 1
        summary["risk"][payload["risk"]["level"]] += 1
        summary["review_gate"][payload["review_gate"]["status"]] += 1

        draft_availability = "available" if payload["draft"]["available"] else "unavailable"
        summary["draft_availability"][draft_availability] += 1

        open_questions = payload["draft"]["questions"]
        summary["open_questions"]["total"] += len(open_questions)
        if open_questions:
            summary["open_questions"]["cases_with_open_questions"].append(
                payload["case_id"]
            )

    summary["highest_priority_cases"] = [
        _compact_priority_case(item) for item in build_review_worklist(outputs)[:3]
    ]
    return summary


def _compact_priority_case(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": item["case_id"],
        "priority": item["priority"],
        "gateway_decision": item["gateway"]["decision"],
        "risk_level": item["risk"]["level"],
        "review_gate_status": item["review_gate"]["status"],
        "draft_available": item["draft"]["available"],
        "open_questions_count": item["open_questions_count"],
    }
