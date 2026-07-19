"""Controlled synthetic AI workflow for offline MVP draft response checks."""

from __future__ import annotations

from dataclasses import dataclass

from steuerberater_copilot.ai import ModelProvider, ModelResponse

from ._response_markers import OFFLINE_DRAFT_TITLE_PREFIX
from .model_invocation import (
    SYNTHETIC_MODEL_INVOCATION_POLICY,
    invoke_model_if_allowed,
)
from .models import (
    DraftPackage,
    GatewayDecision,
    GatewayResult,
    IntakeCase,
    ReviewGateDecision,
    ReviewStatus,
    RiskClassification,
)
from .privacy_gateway import combine_gateway_results, run_response_gateway_check
from .prompt_builder import build_synthetic_model_request
from .structured_output import StructuredDraftOutput
from .structured_output_parser import parse_structured_draft_output
from .structured_output_validator import validate_structured_draft_output
from .workflow import classify_internal_risk, run_human_review_gate, run_mock_gateway


@dataclass(frozen=True)
class SyntheticAIWorkflowOutput:
    """Synthetic workflow state after response controls, without fachliche validation."""

    intake: IntakeCase
    gateway: GatewayResult
    risk_classification: RiskClassification
    review_gate: ReviewGateDecision
    model_response: ModelResponse | None
    structured_draft: StructuredDraftOutput | None


def build_synthetic_ai_workflow(
    case: IntakeCase,
    *,
    provider: ModelProvider,
) -> SyntheticAIWorkflowOutput:
    """Run the separate synthetic AI path after existing offline MVP controls."""

    gateway = run_mock_gateway(case)
    risk_classification = classify_internal_risk(case, gateway)
    review_gate = run_human_review_gate(risk_classification)

    if (
        gateway.decision is not GatewayDecision.ALLOW_DRAFT
        or not review_gate.allows_offline_mock_continuation
    ):
        return SyntheticAIWorkflowOutput(
            intake=case,
            gateway=gateway,
            risk_classification=risk_classification,
            review_gate=review_gate,
            model_response=None,
            structured_draft=None,
        )

    request = build_synthetic_model_request(case)
    model_response = invoke_model_if_allowed(
        provider=provider,
        request=request,
        gateway=gateway,
        review_gate=review_gate,
        policy=SYNTHETIC_MODEL_INVOCATION_POLICY,
    )
    structured_draft = parse_structured_draft_output(model_response.content)
    validate_structured_draft_output(structured_draft)
    response_draft_package = DraftPackage(
        title=f"{OFFLINE_DRAFT_TITLE_PREFIX} {case.case_id}",
        review_status=ReviewStatus.DRAFT,
        risk_classification=risk_classification,
        review_required=risk_classification.review_required,
        summary_points=structured_draft.summary_points,
        question_drafts=structured_draft.review_questions,
        handoff_notes=structured_draft.uncertainties,
    )
    gateway = combine_gateway_results(
        gateway,
        run_response_gateway_check(response_draft_package),
    )

    if gateway.decision is not GatewayDecision.ALLOW_DRAFT:
        structured_draft = None

    return SyntheticAIWorkflowOutput(
        intake=case,
        gateway=gateway,
        risk_classification=risk_classification,
        review_gate=review_gate,
        model_response=model_response,
        structured_draft=structured_draft,
    )
