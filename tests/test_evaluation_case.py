from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import (
    EvaluationCase,
    ExpectedAIWorkflowOutcome,
    SyntheticEvaluationFixture,
    build_synthetic_evaluation_case_library,
)
from steuerberater_copilot.offline_mvp import (
    GatewayDecision,
    IntakeCase,
    ReviewGateStatus,
    StructuredDraftOutput,
    SyntheticDocument,
)


def test_expected_ai_workflow_outcome_has_exact_values() -> None:
    assert ExpectedAIWorkflowOutcome.GATEWAY_STOP == "gateway_stop"
    assert ExpectedAIWorkflowOutcome.REVIEW_GATE_STOP == "review_gate_stop"
    assert ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT == "structured_draft"
    assert ExpectedAIWorkflowOutcome.PROVIDER_ERROR == "provider_error"
    assert ExpectedAIWorkflowOutcome.PARSE_ERROR == "parse_error"
    assert ExpectedAIWorkflowOutcome.VALIDATION_ERROR == "validation_error"
    assert list(ExpectedAIWorkflowOutcome) == [
        ExpectedAIWorkflowOutcome.GATEWAY_STOP,
        ExpectedAIWorkflowOutcome.REVIEW_GATE_STOP,
        ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
        ExpectedAIWorkflowOutcome.PROVIDER_ERROR,
        ExpectedAIWorkflowOutcome.PARSE_ERROR,
        ExpectedAIWorkflowOutcome.VALIDATION_ERROR,
    ]


def test_evaluation_case_keeps_successful_structured_expectations_unchanged() -> None:
    intake = _synthetic_intake()
    structured_draft = _structured_draft()

    case = EvaluationCase(
        evaluation_id=" EVAL_SYNTHETIC_001 ",
        intake=intake,
        expected_gateway_decision=GatewayDecision.ALLOW_DRAFT,
        expected_review_gate_status=(
            ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
        ),
        expected_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
        expected_structured_draft=structured_draft,
    )

    assert case.evaluation_id == " EVAL_SYNTHETIC_001 "
    assert case.intake is intake
    assert case.expected_gateway_decision is GatewayDecision.ALLOW_DRAFT
    assert (
        case.expected_review_gate_status
        is ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
    )
    assert case.expected_outcome is ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT
    assert case.expected_structured_draft is structured_draft
    assert case == EvaluationCase(
        evaluation_id=" EVAL_SYNTHETIC_001 ",
        intake=intake,
        expected_gateway_decision=GatewayDecision.ALLOW_DRAFT,
        expected_review_gate_status=(
            ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
        ),
        expected_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
        expected_structured_draft=structured_draft,
    )


@pytest.mark.parametrize(
    ("outcome", "gateway_decision", "review_gate_status"),
    (
        (
            ExpectedAIWorkflowOutcome.GATEWAY_STOP,
            GatewayDecision.ESCALATE,
            ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
        ),
        (
            ExpectedAIWorkflowOutcome.REVIEW_GATE_STOP,
            GatewayDecision.ALLOW_DRAFT,
            ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
        ),
        (
            ExpectedAIWorkflowOutcome.PROVIDER_ERROR,
            GatewayDecision.ALLOW_DRAFT,
            ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION,
        ),
        (
            ExpectedAIWorkflowOutcome.PARSE_ERROR,
            GatewayDecision.ALLOW_DRAFT,
            ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION,
        ),
        (
            ExpectedAIWorkflowOutcome.VALIDATION_ERROR,
            GatewayDecision.ALLOW_DRAFT,
            ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION,
        ),
    ),
)
def test_evaluation_case_accepts_stop_and_error_outcomes_without_draft(
    outcome: ExpectedAIWorkflowOutcome,
    gateway_decision: GatewayDecision,
    review_gate_status: ReviewGateStatus,
) -> None:
    case = EvaluationCase(
        evaluation_id=f"EVAL_{outcome.value}",
        intake=_synthetic_intake(),
        expected_gateway_decision=gateway_decision,
        expected_review_gate_status=review_gate_status,
        expected_outcome=outcome,
        expected_structured_draft=None,
    )

    assert case.expected_outcome is outcome
    assert case.expected_structured_draft is None


def test_evaluation_case_is_immutable_and_uses_slots() -> None:
    case = _provider_error_case()

    with pytest.raises(FrozenInstanceError):
        case.evaluation_id = "EVAL_CHANGED"

    assert not hasattr(case, "__dict__")


@pytest.mark.parametrize("evaluation_id", ("", " \t\n"))
def test_evaluation_case_rejects_blank_evaluation_id(evaluation_id: str) -> None:
    with pytest.raises(ValueError, match=r"^evaluation_id must not be blank\.$"):
        EvaluationCase(
            evaluation_id=evaluation_id,
            intake=_synthetic_intake(),
            expected_gateway_decision=GatewayDecision.ALLOW_DRAFT,
            expected_review_gate_status=(
                ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
            ),
            expected_outcome=ExpectedAIWorkflowOutcome.PROVIDER_ERROR,
            expected_structured_draft=None,
        )


def test_evaluation_case_requires_draft_for_structured_draft_outcome() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^expected_structured_draft is required for "
            r"structured_draft outcome\.$"
        ),
    ):
        EvaluationCase(
            evaluation_id="EVAL_MISSING_DRAFT",
            intake=_synthetic_intake(),
            expected_gateway_decision=GatewayDecision.ALLOW_DRAFT,
            expected_review_gate_status=(
                ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
            ),
            expected_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
            expected_structured_draft=None,
        )


def test_evaluation_case_rejects_draft_for_non_structured_outcome() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^expected_structured_draft must be None unless outcome is "
            r"structured_draft\.$"
        ),
    ):
        EvaluationCase(
            evaluation_id="EVAL_UNEXPECTED_DRAFT",
            intake=_synthetic_intake(),
            expected_gateway_decision=GatewayDecision.ESCALATE,
            expected_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
            expected_outcome=ExpectedAIWorkflowOutcome.GATEWAY_STOP,
            expected_structured_draft=_structured_draft(),
        )


def test_evaluation_case_equality_includes_required_expectation_fields() -> None:
    intake = _synthetic_intake()
    structured_draft = _structured_draft()
    base = EvaluationCase(
        evaluation_id="EVAL_EQUALITY",
        intake=intake,
        expected_gateway_decision=GatewayDecision.ALLOW_DRAFT,
        expected_review_gate_status=(
            ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
        ),
        expected_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
        expected_structured_draft=structured_draft,
    )

    assert base != EvaluationCase(
        evaluation_id="EVAL_OTHER_ID",
        intake=intake,
        expected_gateway_decision=GatewayDecision.ALLOW_DRAFT,
        expected_review_gate_status=(
            ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
        ),
        expected_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
        expected_structured_draft=structured_draft,
    )
    assert _provider_error_case() != EvaluationCase(
        evaluation_id="EVAL_PROVIDER_ERROR",
        intake=_synthetic_intake(),
        expected_gateway_decision=GatewayDecision.ALLOW_DRAFT,
        expected_review_gate_status=(
            ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
        ),
        expected_outcome=ExpectedAIWorkflowOutcome.PARSE_ERROR,
        expected_structured_draft=None,
    )
    assert base != EvaluationCase(
        evaluation_id="EVAL_EQUALITY",
        intake=intake,
        expected_gateway_decision=GatewayDecision.ALLOW_DRAFT,
        expected_review_gate_status=(
            ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
        ),
        expected_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
        expected_structured_draft=StructuredDraftOutput(
            summary_points=("Different synthetic summary.",),
            uncertainties=structured_draft.uncertainties,
            review_questions=structured_draft.review_questions,
        ),
    )


def test_evaluation_package_has_exact_public_exports() -> None:
    assert evaluation.EvaluationCase is EvaluationCase
    assert evaluation.ExpectedAIWorkflowOutcome is ExpectedAIWorkflowOutcome
    assert evaluation.SyntheticEvaluationFixture is SyntheticEvaluationFixture
    assert (
        evaluation.build_synthetic_evaluation_case_library
        is build_synthetic_evaluation_case_library
    )
    assert evaluation.__all__ == [
        "EvaluationCase",
        "EvaluationCaseAssessment",
        "EvaluationMetricsReport",
        "EvaluationRunResult",
        "ExpectedAIWorkflowOutcome",
        "RetrievalEvaluationCase",
        "RetrievalEvaluationRunResult",
        "SyntheticEvaluationFixture",
        "assess_evaluation_run_result",
        "build_synthetic_evaluation_case_library",
        "run_offline_evaluation_case",
        "run_offline_evaluation_suite",
        "run_offline_retrieval_evaluation_case",
    ]


def _provider_error_case() -> EvaluationCase:
    return EvaluationCase(
        evaluation_id="EVAL_PROVIDER_ERROR",
        intake=_synthetic_intake(),
        expected_gateway_decision=GatewayDecision.ALLOW_DRAFT,
        expected_review_gate_status=(
            ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
        ),
        expected_outcome=ExpectedAIWorkflowOutcome.PROVIDER_ERROR,
        expected_structured_draft=None,
    )


def _synthetic_intake() -> IntakeCase:
    return IntakeCase(
        case_id="CASE_EVALUATION_TEST",
        client_ref="CLIENT_EVALUATION_TEST",
        scenario="Synthetic evaluation contract test.",
        period="2026-Q3",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_EVALUATION_TEST",
                label="Synthetic evaluation document descriptor.",
                period="2026-Q3",
                source_note="Synthetic source note without original content.",
            ),
        ),
        notes=("Synthetic test note.",),
    )


def _structured_draft() -> StructuredDraftOutput:
    return StructuredDraftOutput(
        summary_points=("Synthetic summary.",),
        uncertainties=("Synthetic uncertainty.",),
        review_questions=("Synthetic review question?",),
    )
