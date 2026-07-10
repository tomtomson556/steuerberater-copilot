"""Deterministic observation of one synthetic offline evaluation case."""

from dataclasses import dataclass

from steuerberater_copilot.ai import ModelProvider, ModelRequest, ModelResponse
from steuerberater_copilot.offline_mvp import (
    GatewayDecision,
    ReviewGateStatus,
    StructuredDraftOutput,
    StructuredDraftOutputParseError,
    StructuredDraftOutputValidationError,
    build_synthetic_ai_workflow,
    classify_internal_risk,
    run_human_review_gate,
)
from steuerberater_copilot.offline_mvp.workflow import run_mock_gateway

from .case import EvaluationCase, ExpectedAIWorkflowOutcome


@dataclass(frozen=True, slots=True)
class EvaluationRunResult:
    """Observed result of one synthetic offline evaluation case."""

    evaluation_case: EvaluationCase
    observed_gateway_decision: GatewayDecision
    observed_review_gate_status: ReviewGateStatus
    observed_outcome: ExpectedAIWorkflowOutcome
    observed_structured_draft: StructuredDraftOutput | None
    provider_call_count: int

    def __post_init__(self) -> None:
        if self.provider_call_count < 0:
            raise ValueError("provider_call_count must not be negative.")

        if self.observed_outcome is ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT:
            if self.observed_structured_draft is None:
                raise ValueError(
                    "observed_structured_draft is required for structured_draft outcome."
                )
        elif self.observed_structured_draft is not None:
            raise ValueError(
                "observed_structured_draft must be None unless outcome is structured_draft."
            )


class _ObservedModelProvider:
    def __init__(self, provider: ModelProvider) -> None:
        self._provider = provider
        self.call_count = 0
        self.raised_exception: Exception | None = None

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.call_count += 1
        try:
            return self._provider.generate(request)
        except Exception as exc:
            self.raised_exception = exc
            raise


def run_offline_evaluation_case(
    evaluation_case: EvaluationCase,
    *,
    provider: ModelProvider,
) -> EvaluationRunResult:
    """Run one case and return observations without evaluating expectations."""
    gateway = run_mock_gateway(evaluation_case.intake)
    risk_classification = classify_internal_risk(evaluation_case.intake, gateway)
    review_gate = run_human_review_gate(risk_classification)
    observed_provider = _ObservedModelProvider(provider)

    try:
        output = build_synthetic_ai_workflow(
            evaluation_case.intake,
            provider=observed_provider,
        )
    except Exception as exc:
        if observed_provider.raised_exception is exc:
            observed_outcome = ExpectedAIWorkflowOutcome.PROVIDER_ERROR
        elif isinstance(exc, StructuredDraftOutputParseError):
            observed_outcome = ExpectedAIWorkflowOutcome.PARSE_ERROR
        elif isinstance(exc, StructuredDraftOutputValidationError):
            observed_outcome = ExpectedAIWorkflowOutcome.VALIDATION_ERROR
        else:
            raise

        return EvaluationRunResult(
            evaluation_case=evaluation_case,
            observed_gateway_decision=gateway.decision,
            observed_review_gate_status=review_gate.status,
            observed_outcome=observed_outcome,
            observed_structured_draft=None,
            provider_call_count=observed_provider.call_count,
        )

    if output.structured_draft is not None:
        observed_outcome = ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT
    elif output.gateway.decision is not GatewayDecision.ALLOW_DRAFT:
        observed_outcome = ExpectedAIWorkflowOutcome.GATEWAY_STOP
    elif not output.review_gate.allows_offline_mock_continuation:
        observed_outcome = ExpectedAIWorkflowOutcome.REVIEW_GATE_STOP
    else:
        raise RuntimeError(
            "Synthetic AI workflow returned no structured draft after allowed continuation."
        )

    return EvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_gateway_decision=output.gateway.decision,
        observed_review_gate_status=output.review_gate.status,
        observed_outcome=observed_outcome,
        observed_structured_draft=output.structured_draft,
        provider_call_count=observed_provider.call_count,
    )
