"""Deterministic synthetic baseline cases for offline evaluation."""

from dataclasses import dataclass

from steuerberater_copilot.ai import (
    FakeModelProvider,
    ModelProvider,
    ModelRequest,
    ModelResponse,
)
from steuerberater_copilot.offline_mvp import (
    GatewayDecision,
    IntakeCase,
    ReviewGateStatus,
    StructuredDraftOutput,
    SyntheticDocument,
)
from steuerberater_copilot.offline_mvp.models import MockRiskSignal

from .case import EvaluationCase, ExpectedAIWorkflowOutcome


@dataclass(frozen=True, slots=True)
class SyntheticEvaluationFixture:
    """One synthetic evaluation case with a fresh deterministic provider source."""

    evaluation_case: EvaluationCase
    model_response: ModelResponse | None = None
    provider_error_message: str | None = None

    def __post_init__(self) -> None:
        if (self.model_response is None) == (self.provider_error_message is None):
            raise ValueError("Exactly one synthetic provider reaction is required.")
        if self.provider_error_message is not None and (
            not self.provider_error_message or self.provider_error_message.isspace()
        ):
            raise ValueError("provider_error_message must not be blank.")

    def create_provider(self) -> ModelProvider:
        """Create a fresh deterministic provider for one evaluation run."""
        if self.model_response is not None:
            return FakeModelProvider(self.model_response)

        if self.provider_error_message is None:
            raise RuntimeError("Synthetic evaluation fixture has no provider reaction.")
        return _FailingSyntheticModelProvider(self.provider_error_message)


class _FailingSyntheticModelProvider:
    def __init__(self, error_message: str) -> None:
        self._error_message = error_message

    def generate(self, request: ModelRequest) -> ModelResponse:
        raise RuntimeError(self._error_message)


def build_synthetic_evaluation_case_library(
) -> tuple[SyntheticEvaluationFixture, ...]:
    """Build the seven fresh synthetic baseline fixtures in stable order."""
    return (
        _gateway_block_fixture(),
        _gateway_escalation_fixture(),
        _review_gate_stop_fixture(),
        _structured_draft_fixture(),
        _provider_error_fixture(),
        _parse_error_fixture(),
        _validation_error_fixture(),
    )


def _gateway_block_fixture() -> SyntheticEvaluationFixture:
    return SyntheticEvaluationFixture(
        evaluation_case=EvaluationCase(
            evaluation_id="EVAL_BASELINE_GATEWAY_BLOCK",
            intake=_synthetic_intake(
                case_number="401",
                scenario="Synthetic gateway block baseline.",
                mock_risk_signals=(MockRiskSignal.FORBIDDEN_ORIGINAL_PII.value,),
            ),
            expected_gateway_decision=GatewayDecision.BLOCK,
            expected_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
            expected_outcome=ExpectedAIWorkflowOutcome.GATEWAY_STOP,
            expected_structured_draft=None,
        ),
        model_response=_valid_model_response(),
    )


def _gateway_escalation_fixture() -> SyntheticEvaluationFixture:
    return SyntheticEvaluationFixture(
        evaluation_case=EvaluationCase(
            evaluation_id="EVAL_BASELINE_GATEWAY_ESCALATION",
            intake=_synthetic_intake(
                case_number="402",
                scenario="Synthetic gateway escalation baseline.",
                missing_items=("Synthetic missing context marker.",),
            ),
            expected_gateway_decision=GatewayDecision.ESCALATE,
            expected_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
            expected_outcome=ExpectedAIWorkflowOutcome.GATEWAY_STOP,
            expected_structured_draft=None,
        ),
        model_response=_valid_model_response(),
    )


def _review_gate_stop_fixture() -> SyntheticEvaluationFixture:
    return SyntheticEvaluationFixture(
        evaluation_case=EvaluationCase(
            evaluation_id="EVAL_BASELINE_REVIEW_GATE_STOP",
            intake=_synthetic_intake(
                case_number="403",
                scenario="Synthetic review gate stop baseline.",
                mock_risk_signals=(MockRiskSignal.DOCUMENT_PREPARATION.value,),
            ),
            expected_gateway_decision=GatewayDecision.ALLOW_DRAFT,
            expected_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
            expected_outcome=ExpectedAIWorkflowOutcome.REVIEW_GATE_STOP,
            expected_structured_draft=None,
        ),
        model_response=_valid_model_response(),
    )


def _structured_draft_fixture() -> SyntheticEvaluationFixture:
    structured_draft = StructuredDraftOutput(
        summary_points=("Synthetic baseline summary point.",),
        uncertainties=("Synthetic baseline uncertainty requires review.",),
        review_questions=("Which synthetic assumption requires human review?",),
    )
    return SyntheticEvaluationFixture(
        evaluation_case=EvaluationCase(
            evaluation_id="EVAL_BASELINE_STRUCTURED_DRAFT",
            intake=_synthetic_intake(
                case_number="404",
                scenario="Synthetic structured draft baseline.",
            ),
            expected_gateway_decision=GatewayDecision.ALLOW_DRAFT,
            expected_review_gate_status=(
                ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
            ),
            expected_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
            expected_structured_draft=structured_draft,
        ),
        model_response=_valid_model_response(),
    )


def _provider_error_fixture() -> SyntheticEvaluationFixture:
    return SyntheticEvaluationFixture(
        evaluation_case=_allowed_error_case(
            evaluation_id="EVAL_BASELINE_PROVIDER_ERROR",
            case_number="405",
            outcome=ExpectedAIWorkflowOutcome.PROVIDER_ERROR,
        ),
        provider_error_message="Synthetic evaluation provider failure.",
    )


def _parse_error_fixture() -> SyntheticEvaluationFixture:
    return SyntheticEvaluationFixture(
        evaluation_case=_allowed_error_case(
            evaluation_id="EVAL_BASELINE_PARSE_ERROR",
            case_number="406",
            outcome=ExpectedAIWorkflowOutcome.PARSE_ERROR,
        ),
        model_response=_model_response('{"summary_points":[]}'),
    )


def _validation_error_fixture() -> SyntheticEvaluationFixture:
    return SyntheticEvaluationFixture(
        evaluation_case=_allowed_error_case(
            evaluation_id="EVAL_BASELINE_VALIDATION_ERROR",
            case_number="407",
            outcome=ExpectedAIWorkflowOutcome.VALIDATION_ERROR,
        ),
        model_response=_model_response(
            "{"
            '"summary_points":["The draft is finally approved."],'
            '"uncertainties":["Synthetic validation uncertainty."],'
            '"review_questions":["Which synthetic claim requires review?"]'
            "}"
        ),
    )


def _allowed_error_case(
    *,
    evaluation_id: str,
    case_number: str,
    outcome: ExpectedAIWorkflowOutcome,
) -> EvaluationCase:
    return EvaluationCase(
        evaluation_id=evaluation_id,
        intake=_synthetic_intake(
            case_number=case_number,
            scenario=f"Synthetic {outcome.value} baseline.",
        ),
        expected_gateway_decision=GatewayDecision.ALLOW_DRAFT,
        expected_review_gate_status=(
            ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
        ),
        expected_outcome=outcome,
        expected_structured_draft=None,
    )


def _synthetic_intake(
    *,
    case_number: str,
    scenario: str,
    missing_items: tuple[str, ...] = (),
    mock_risk_signals: tuple[str, ...] = (),
) -> IntakeCase:
    return IntakeCase(
        case_id=f"CASE_{case_number}",
        client_ref=f"CLIENT_{case_number}",
        scenario=scenario,
        period="2026-Q3",
        documents=(
            SyntheticDocument(
                document_id=f"DOCUMENT_{case_number}",
                label="Synthetic evaluation document descriptor.",
                period="2026-Q3",
                source_note="Synthetic source note without original content.",
            ),
        ),
        notes=("Synthetic evaluation baseline note.",),
        missing_items=missing_items,
        mock_risk_signals=mock_risk_signals,
    )


def _valid_model_response() -> ModelResponse:
    return _model_response(
        "{"
        '"summary_points":["Synthetic baseline summary point."],'
        '"uncertainties":["Synthetic baseline uncertainty requires review."],'
        '"review_questions":["Which synthetic assumption requires human review?"]'
        "}"
    )


def _model_response(content: str) -> ModelResponse:
    return ModelResponse(
        content=content,
        provider_name="synthetic-evaluation-fake",
        model_name="synthetic-evaluation-model",
    )
