"""Contracts for synthetic controlled AI workflow evaluation cases."""

from dataclasses import dataclass
from enum import StrEnum

from steuerberater_copilot.offline_mvp import (
    GatewayDecision,
    IntakeCase,
    ReviewGateStatus,
    StructuredDraftOutput,
)


class ExpectedAIWorkflowOutcome(StrEnum):
    """Expected terminal outcome of one controlled synthetic AI workflow run."""

    GATEWAY_STOP = "gateway_stop"
    REVIEW_GATE_STOP = "review_gate_stop"
    STRUCTURED_DRAFT = "structured_draft"
    PROVIDER_ERROR = "provider_error"
    PARSE_ERROR = "parse_error"
    VALIDATION_ERROR = "validation_error"


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    """Expected behavior for one synthetic controlled AI workflow case."""

    evaluation_id: str
    intake: IntakeCase
    expected_gateway_decision: GatewayDecision
    expected_review_gate_status: ReviewGateStatus
    expected_outcome: ExpectedAIWorkflowOutcome
    expected_structured_draft: StructuredDraftOutput | None

    def __post_init__(self) -> None:
        if not self.evaluation_id or self.evaluation_id.isspace():
            raise ValueError("evaluation_id must not be blank.")

        if self.expected_outcome is ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT:
            if self.expected_structured_draft is None:
                raise ValueError(
                    "expected_structured_draft is required for structured_draft outcome."
                )
        elif self.expected_structured_draft is not None:
            raise ValueError(
                "expected_structured_draft must be None unless outcome is structured_draft."
            )
