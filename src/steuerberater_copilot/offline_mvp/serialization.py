"""JSON serialization for the deterministic offline MVP workflow."""

from __future__ import annotations

from typing import Any

from .models import WorkflowOutput


def workflow_to_json(output: WorkflowOutput) -> dict[str, Any]:
    draft_available = output.draft_available
    summary = list(output.draft_package.summary_points) if draft_available else []
    questions = list(output.draft_package.question_drafts)

    return {
        "case_id": output.intake.case_id,
        "gateway": {
            "decision": output.gateway.decision.value,
            "checks": list(output.gateway.checks),
            "reasons": list(output.gateway.escalation_reasons),
            "block_reasons": list(output.gateway.block_reasons),
        },
        "risk": {
            "level": output.risk_classification.risk_level.value,
            "review_required": output.risk_classification.review_required,
            "basis": list(output.risk_classification.basis),
        },
        "review_gate": {
            "status": output.review_gate.status.value,
            "decision": output.review_gate.status.value,
            "allows_offline_mock_continuation": (
                output.review_gate.allows_offline_mock_continuation
            ),
            "reason": output.review_gate.reason,
        },
        "draft": {
            "available": draft_available,
            "draft_only": True,
            "review_status": output.draft_package.review_status.value,
            "summary": summary,
            "summary_points": summary,
            "questions": questions,
            "handoff_notes": list(output.draft_package.handoff_notes),
            "disclaimers": list(output.draft_package.disclaimers),
        },
    }
