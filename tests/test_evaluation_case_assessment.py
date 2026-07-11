from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import (
    EvaluationCase,
    EvaluationCaseAssessment,
    EvaluationRunResult,
    ExpectedAIWorkflowOutcome,
    assess_evaluation_run_result,
)
from steuerberater_copilot.offline_mvp import (
    GatewayDecision,
    IntakeCase,
    ReviewGateStatus,
    StructuredDraftOutput,
    SyntheticDocument,
)


def test_evaluation_case_assessment_is_immutable_and_uses_slots() -> None:
    result = _continuation_result()
    assessment = EvaluationCaseAssessment(result)

    with pytest.raises(FrozenInstanceError):
        assessment.evaluation_run_result = _continuation_result()

    assert not hasattr(assessment, "__dict__")
    assert EvaluationCaseAssessment.__slots__ == ("evaluation_run_result",)


def test_assessment_function_keeps_exact_evaluation_run_result_instance() -> None:
    result = _continuation_result()

    assessment = assess_evaluation_run_result(result)

    assert assessment.evaluation_run_result is result


def test_matching_structured_draft_case_passes_with_exact_dataclass_equality() -> None:
    expected_draft = _structured_draft()
    observed_draft = _structured_draft()
    case = _evaluation_case(
        expected_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
        expected_structured_draft=expected_draft,
    )
    result = _evaluation_run_result(
        evaluation_case=case,
        observed_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
        observed_structured_draft=observed_draft,
    )

    assessment = assess_evaluation_run_result(result)

    assert observed_draft is not expected_draft
    assert assessment.structured_draft_matches is True
    assert assessment.passed is True


def test_matching_gateway_stop_passes_and_expects_no_provider_call() -> None:
    case = _evaluation_case(
        expected_gateway_decision=GatewayDecision.BLOCK,
        expected_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
        expected_outcome=ExpectedAIWorkflowOutcome.GATEWAY_STOP,
    )
    result = _evaluation_run_result(
        evaluation_case=case,
        observed_gateway_decision=GatewayDecision.BLOCK,
        observed_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
        observed_outcome=ExpectedAIWorkflowOutcome.GATEWAY_STOP,
        provider_call_count=0,
    )

    assessment = assess_evaluation_run_result(result)

    assert assessment.expected_provider_call_count == 0
    assert assessment.provider_call_count_matches is True
    assert assessment.passed is True


def test_matching_review_gate_stop_passes_and_expects_no_provider_call() -> None:
    case = _evaluation_case(
        expected_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
        expected_outcome=ExpectedAIWorkflowOutcome.REVIEW_GATE_STOP,
    )
    result = _evaluation_run_result(
        evaluation_case=case,
        observed_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
        observed_outcome=ExpectedAIWorkflowOutcome.REVIEW_GATE_STOP,
        provider_call_count=0,
    )

    assessment = assess_evaluation_run_result(result)

    assert assessment.expected_provider_call_count == 0
    assert assessment.provider_call_count_matches is True
    assert assessment.passed is True


def test_allowed_continuation_expects_exactly_one_provider_call() -> None:
    assessment = assess_evaluation_run_result(_continuation_result())

    assert assessment.expected_provider_call_count == 1
    assert assessment.provider_call_count_matches is True
    assert assessment.passed is True


def test_wrong_gateway_decision_is_detected_separately() -> None:
    result = _evaluation_run_result(
        evaluation_case=_evaluation_case(),
        observed_gateway_decision=GatewayDecision.ESCALATE,
    )

    assessment = assess_evaluation_run_result(result)

    assert assessment.gateway_decision_matches is False
    assert assessment.review_gate_status_matches is True
    assert assessment.outcome_matches is True
    assert assessment.structured_draft_matches is True
    assert assessment.provider_call_count_matches is True
    assert assessment.passed is False


def test_wrong_review_gate_status_is_detected_separately() -> None:
    result = _evaluation_run_result(
        evaluation_case=_evaluation_case(),
        observed_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
    )

    assessment = assess_evaluation_run_result(result)

    assert assessment.gateway_decision_matches is True
    assert assessment.review_gate_status_matches is False
    assert assessment.outcome_matches is True
    assert assessment.structured_draft_matches is True
    assert assessment.provider_call_count_matches is True
    assert assessment.passed is False


def test_wrong_error_outcome_class_is_detected_separately() -> None:
    result = _evaluation_run_result(
        evaluation_case=_evaluation_case(),
        observed_outcome=ExpectedAIWorkflowOutcome.PARSE_ERROR,
    )

    assessment = assess_evaluation_run_result(result)

    assert assessment.gateway_decision_matches is True
    assert assessment.review_gate_status_matches is True
    assert assessment.outcome_matches is False
    assert assessment.structured_draft_matches is True
    assert assessment.provider_call_count_matches is True
    assert assessment.passed is False


def test_different_structured_draft_is_detected_by_exact_dataclass_equality() -> None:
    expected_draft = _structured_draft()
    observed_draft = StructuredDraftOutput(
        summary_points=("Different synthetic summary.",),
        uncertainties=expected_draft.uncertainties,
        review_questions=expected_draft.review_questions,
    )
    case = _evaluation_case(
        expected_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
        expected_structured_draft=expected_draft,
    )
    result = _evaluation_run_result(
        evaluation_case=case,
        observed_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
        observed_structured_draft=observed_draft,
    )

    assessment = assess_evaluation_run_result(result)

    assert assessment.gateway_decision_matches is True
    assert assessment.review_gate_status_matches is True
    assert assessment.outcome_matches is True
    assert assessment.structured_draft_matches is False
    assert assessment.provider_call_count_matches is True
    assert assessment.passed is False


def test_no_provider_call_fails_when_one_call_is_expected() -> None:
    result = _evaluation_run_result(
        evaluation_case=_evaluation_case(),
        provider_call_count=0,
    )

    assessment = assess_evaluation_run_result(result)

    assert assessment.expected_provider_call_count == 1
    assert assessment.provider_call_count_matches is False
    assert assessment.passed is False


def test_two_provider_calls_fail_when_one_call_is_expected() -> None:
    result = _evaluation_run_result(
        evaluation_case=_evaluation_case(),
        provider_call_count=2,
    )

    assessment = assess_evaluation_run_result(result)

    assert assessment.expected_provider_call_count == 1
    assert assessment.provider_call_count_matches is False
    assert assessment.passed is False


def test_provider_call_behind_expected_gateway_stop_fails() -> None:
    case = _evaluation_case(
        expected_gateway_decision=GatewayDecision.ESCALATE,
        expected_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
        expected_outcome=ExpectedAIWorkflowOutcome.GATEWAY_STOP,
    )
    result = _evaluation_run_result(
        evaluation_case=case,
        observed_gateway_decision=GatewayDecision.ESCALATE,
        observed_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
        observed_outcome=ExpectedAIWorkflowOutcome.GATEWAY_STOP,
        provider_call_count=1,
    )

    assessment = assess_evaluation_run_result(result)

    assert assessment.expected_provider_call_count == 0
    assert assessment.provider_call_count_matches is False
    assert assessment.passed is False


def test_provider_call_behind_expected_review_gate_stop_fails() -> None:
    case = _evaluation_case(
        expected_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
        expected_outcome=ExpectedAIWorkflowOutcome.REVIEW_GATE_STOP,
    )
    result = _evaluation_run_result(
        evaluation_case=case,
        observed_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
        observed_outcome=ExpectedAIWorkflowOutcome.REVIEW_GATE_STOP,
        provider_call_count=1,
    )

    assessment = assess_evaluation_run_result(result)

    assert assessment.expected_provider_call_count == 0
    assert assessment.provider_call_count_matches is False
    assert assessment.passed is False


def test_passed_is_exact_conjunction_of_all_five_matches() -> None:
    passing_assessment = assess_evaluation_run_result(_continuation_result())
    failing_assessment = assess_evaluation_run_result(
        _evaluation_run_result(
            evaluation_case=_evaluation_case(),
            observed_gateway_decision=GatewayDecision.BLOCK,
            observed_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
            observed_outcome=ExpectedAIWorkflowOutcome.VALIDATION_ERROR,
            provider_call_count=2,
        )
    )

    for assessment in (passing_assessment, failing_assessment):
        assert assessment.passed is all(
            (
                assessment.gateway_decision_matches,
                assessment.review_gate_status_matches,
                assessment.outcome_matches,
                assessment.structured_draft_matches,
                assessment.provider_call_count_matches,
            )
        )

    assert passing_assessment.passed is True
    assert failing_assessment.passed is False


def test_evaluation_package_exports_assessment_contract() -> None:
    assert evaluation.EvaluationCaseAssessment is EvaluationCaseAssessment
    assert evaluation.assess_evaluation_run_result is assess_evaluation_run_result
    assert evaluation.__all__ == [
        "EvaluationCase",
        "EvaluationCaseAssessment",
        "EvaluationRunResult",
        "ExpectedAIWorkflowOutcome",
        "assess_evaluation_run_result",
        "run_offline_evaluation_case",
    ]


def _continuation_result() -> EvaluationRunResult:
    return _evaluation_run_result(evaluation_case=_evaluation_case())


def _evaluation_case(
    *,
    expected_gateway_decision: GatewayDecision = GatewayDecision.ALLOW_DRAFT,
    expected_review_gate_status: ReviewGateStatus = (
        ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
    ),
    expected_outcome: ExpectedAIWorkflowOutcome = (
        ExpectedAIWorkflowOutcome.PROVIDER_ERROR
    ),
    expected_structured_draft: StructuredDraftOutput | None = None,
) -> EvaluationCase:
    return EvaluationCase(
        evaluation_id="EVAL_ASSESSMENT_TEST",
        intake=_synthetic_intake(),
        expected_gateway_decision=expected_gateway_decision,
        expected_review_gate_status=expected_review_gate_status,
        expected_outcome=expected_outcome,
        expected_structured_draft=expected_structured_draft,
    )


def _evaluation_run_result(
    *,
    evaluation_case: EvaluationCase,
    observed_gateway_decision: GatewayDecision = GatewayDecision.ALLOW_DRAFT,
    observed_review_gate_status: ReviewGateStatus = (
        ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
    ),
    observed_outcome: ExpectedAIWorkflowOutcome = (
        ExpectedAIWorkflowOutcome.PROVIDER_ERROR
    ),
    observed_structured_draft: StructuredDraftOutput | None = None,
    provider_call_count: int = 1,
) -> EvaluationRunResult:
    return EvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_gateway_decision=observed_gateway_decision,
        observed_review_gate_status=observed_review_gate_status,
        observed_outcome=observed_outcome,
        observed_structured_draft=observed_structured_draft,
        provider_call_count=provider_call_count,
    )


def _synthetic_intake() -> IntakeCase:
    return IntakeCase(
        case_id="CASE_ASSESSMENT_TEST",
        client_ref="CLIENT_ASSESSMENT_TEST",
        scenario="Synthetic evaluation assessment test.",
        period="2026-Q3",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_ASSESSMENT_TEST",
                label="Synthetic assessment document descriptor.",
                period="2026-Q3",
                source_note="Synthetic source note without original content.",
            ),
        ),
        notes=("Synthetic assessment test note.",),
    )


def _structured_draft() -> StructuredDraftOutput:
    return StructuredDraftOutput(
        summary_points=("Synthetic summary.",),
        uncertainties=("Synthetic uncertainty.",),
        review_questions=("Synthetic review question?",),
    )
