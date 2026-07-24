from dataclasses import FrozenInstanceError, replace

import pytest

import steuerberater_copilot.evaluation as evaluation
import steuerberater_copilot.evaluation.report as evaluation_report
from steuerberater_copilot.evaluation import (
    EvaluationCase,
    EvaluationCaseAssessment,
    EvaluationMetricsReport,
    EvaluationRunResult,
    ExpectedAIWorkflowOutcome,
    SyntheticEvaluationFixture,
    assess_evaluation_run_result,
    build_synthetic_evaluation_case_library,
    run_offline_evaluation_suite,
)
from steuerberater_copilot.offline_mvp import (
    GatewayDecision,
    IntakeCase,
    ReviewGateStatus,
    StructuredDraftOutput,
    SyntheticDocument,
)


def test_evaluation_metrics_report_is_immutable_and_uses_slots() -> None:
    assessment = _assessment()
    report = EvaluationMetricsReport(assessments=[assessment])

    with pytest.raises(FrozenInstanceError):
        report.assessments = ()

    assert report.assessments == (assessment,)
    assert not hasattr(report, "__dict__")
    assert EvaluationMetricsReport.__slots__ == ("assessments",)


def test_empty_report_and_empty_suite_are_rejected() -> None:
    with pytest.raises(ValueError, match=r"^assessments must not be empty\.$"):
        EvaluationMetricsReport(assessments=())

    with pytest.raises(ValueError, match=r"^assessments must not be empty\.$"):
        run_offline_evaluation_suite(())


def test_baseline_suite_has_exact_metrics() -> None:
    report = run_offline_evaluation_suite(build_synthetic_evaluation_case_library())

    assert report.total_case_count == 7
    assert report.passed_case_count == 7
    assert report.failed_case_count == 0
    assert report.pass_rate == 1.0
    assert report.gateway_decision_match_rate == 1.0
    assert report.review_gate_status_match_rate == 1.0
    assert report.outcome_match_rate == 1.0
    assert report.provider_call_count_match_rate == 1.0
    assert report.structured_draft_case_count == 1
    assert report.structured_draft_match_rate == 1.0
    assert report.total_provider_call_count == 4
    assert report.unexpected_provider_call_count == 0
    assert report.failed_evaluation_ids == ()


def test_suite_preserves_fixture_order() -> None:
    fixtures = tuple(reversed(build_synthetic_evaluation_case_library()))

    report = run_offline_evaluation_suite(fixtures)

    assert tuple(
        assessment.evaluation_run_result.evaluation_case.evaluation_id
        for assessment in report.assessments
    ) == tuple(fixture.evaluation_case.evaluation_id for fixture in fixtures)


def test_suite_continues_after_normal_assessment_mismatch() -> None:
    fixtures = build_synthetic_evaluation_case_library()
    mismatching_fixture = replace(
        fixtures[0],
        evaluation_case=replace(
            fixtures[0].evaluation_case,
            expected_gateway_decision=GatewayDecision.ALLOW_DRAFT,
        ),
    )

    report = run_offline_evaluation_suite((mismatching_fixture, fixtures[1]))

    assert report.total_case_count == 2
    assert report.passed_case_count == 1
    assert report.failed_evaluation_ids == (mismatching_fixture.evaluation_case.evaluation_id,)


def test_suite_creates_exactly_one_fresh_provider_per_fixture(monkeypatch) -> None:
    fixtures = build_synthetic_evaluation_case_library()
    original_create_provider = SyntheticEvaluationFixture.create_provider
    created_providers = []

    def record_provider(fixture):
        provider = original_create_provider(fixture)
        created_providers.append(provider)
        return provider

    monkeypatch.setattr(SyntheticEvaluationFixture, "create_provider", record_provider)

    run_offline_evaluation_suite(fixtures)

    assert len(created_providers) == len(fixtures)
    assert len({id(provider) for provider in created_providers}) == len(fixtures)


def test_pass_rate_and_failed_ids_preserve_assessment_order() -> None:
    report = EvaluationMetricsReport(
        assessments=(
            _assessment(evaluation_id="EVAL_PASS"),
            _assessment(
                evaluation_id="EVAL_FAIL_FIRST",
                observed_outcome=ExpectedAIWorkflowOutcome.PARSE_ERROR,
            ),
            _assessment(
                evaluation_id="EVAL_FAIL_SECOND",
                provider_call_count=0,
            ),
        )
    )

    assert report.passed_case_count == 1
    assert report.failed_case_count == 2
    assert report.pass_rate == 1 / 3
    assert report.failed_evaluation_ids == (
        "EVAL_FAIL_FIRST",
        "EVAL_FAIL_SECOND",
    )


@pytest.mark.parametrize(
    ("result_changes", "mismatched_metric"),
    (
        (
            {"observed_gateway_decision": GatewayDecision.BLOCK},
            "gateway_decision_match_rate",
        ),
        (
            {"observed_review_gate_status": (ReviewGateStatus.REQUIRES_HUMAN_REVIEW)},
            "review_gate_status_match_rate",
        ),
        (
            {"observed_outcome": ExpectedAIWorkflowOutcome.PARSE_ERROR},
            "outcome_match_rate",
        ),
        ({"provider_call_count": 0}, "provider_call_count_match_rate"),
    ),
)
def test_each_general_mismatch_changes_only_its_own_metric(
    result_changes: dict[str, object],
    mismatched_metric: str,
) -> None:
    matching_result = _assessment().evaluation_run_result
    report = EvaluationMetricsReport(
        assessments=(assess_evaluation_run_result(replace(matching_result, **result_changes)),)
    )
    general_metrics = (
        "gateway_decision_match_rate",
        "review_gate_status_match_rate",
        "outcome_match_rate",
        "provider_call_count_match_rate",
    )

    assert report.pass_rate == 0.0
    for metric in general_metrics:
        assert getattr(report, metric) == (0.0 if metric == mismatched_metric else 1.0)


def test_missing_provider_call_is_mismatch_but_not_unexpected_call() -> None:
    report = EvaluationMetricsReport(assessments=(_assessment(provider_call_count=0),))

    assert report.provider_call_count_match_rate == 0.0
    assert report.total_provider_call_count == 0
    assert report.unexpected_provider_call_count == 0


def test_additional_provider_call_is_counted_as_unexpected() -> None:
    report = EvaluationMetricsReport(assessments=(_assessment(provider_call_count=2),))

    assert report.provider_call_count_match_rate == 0.0
    assert report.total_provider_call_count == 2
    assert report.unexpected_provider_call_count == 1


def test_different_draft_reduces_structured_draft_match_rate() -> None:
    expected_draft = _structured_draft()
    observed_draft = replace(
        expected_draft,
        summary_points=("Different synthetic summary.",),
    )
    report = EvaluationMetricsReport(
        assessments=(
            _assessment(
                expected_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
                expected_structured_draft=expected_draft,
                observed_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
                observed_structured_draft=observed_draft,
            ),
        )
    )

    assert report.structured_draft_case_count == 1
    assert report.structured_draft_match_rate == 0.0


def test_non_draft_cases_do_not_enter_structured_draft_denominator() -> None:
    structured_draft = _structured_draft()
    report = EvaluationMetricsReport(
        assessments=(
            _assessment(),
            _assessment(
                evaluation_id="EVAL_DRAFT",
                expected_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
                expected_structured_draft=structured_draft,
                observed_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
                observed_structured_draft=structured_draft,
            ),
        )
    )

    assert report.structured_draft_case_count == 1
    assert report.structured_draft_match_rate == 1.0


def test_report_without_expected_draft_marks_rate_not_applicable() -> None:
    report = EvaluationMetricsReport(assessments=(_assessment(),))

    assert report.structured_draft_case_count == 0
    assert report.structured_draft_match_rate is None


def test_suite_propagates_unexpected_runner_exception(monkeypatch) -> None:
    unexpected_error = RuntimeError("Synthetic unexpected suite failure.")

    def fail_runner(*args, **kwargs):
        raise unexpected_error

    monkeypatch.setattr(
        evaluation_report,
        "run_offline_evaluation_case",
        fail_runner,
    )

    with pytest.raises(RuntimeError) as exc_info:
        run_offline_evaluation_suite(build_synthetic_evaluation_case_library()[:1])

    assert exc_info.value is unexpected_error


def test_evaluation_package_has_exact_report_exports() -> None:
    assert evaluation.EvaluationMetricsReport is EvaluationMetricsReport
    assert evaluation.run_offline_evaluation_suite is run_offline_evaluation_suite
    assert evaluation.__all__ == [
        "ContradictionEvidenceLabel",
        "EvaluationCase",
        "EvaluationCaseAssessment",
        "EvaluationMetricsReport",
        "EvaluationRunResult",
        "ExpectedAIWorkflowOutcome",
        "GroundingEvaluationCase",
        "GroundingEvaluationCaseAssessment",
        "GroundingEvaluationMetricsReport",
        "GroundingEvidenceLabel",
        "RAGAbstentionEvaluationCase",
        "RAGAbstentionEvaluationCaseAssessment",
        "RAGAbstentionEvaluationMetricsReport",
        "RAGAbstentionEvaluationRunResult",
        "RAGContradictionEvaluationCase",
        "RAGContradictionEvaluationCaseAssessment",
        "RAGContradictionEvaluationMetricsReport",
        "RAGContradictionEvaluationRunResult",
        "RAGFreshnessEvaluationCase",
        "RAGFreshnessEvaluationRunResult",
        "RetrievalEvaluationCase",
        "RetrievalEvaluationCaseAssessment",
        "RetrievalEvaluationMetricsReport",
        "RetrievalEvaluationRunResult",
        "SyntheticEvaluationFixture",
        "assess_evaluation_run_result",
        "assess_grounding_evaluation_case",
        "assess_rag_abstention_evaluation_run_result",
        "assess_rag_contradiction_evaluation_run_result",
        "assess_retrieval_evaluation_run_result",
        "build_synthetic_evaluation_case_library",
        "build_synthetic_grounding_evaluation_case_library",
        "build_synthetic_rag_abstention_evaluation_case_library",
        "build_synthetic_rag_contradiction_evaluation_case_library",
        "build_synthetic_retrieval_evaluation_case_library",
        "run_offline_evaluation_case",
        "run_offline_evaluation_suite",
        "run_offline_grounding_evaluation_suite",
        "run_offline_rag_abstention_evaluation_case",
        "run_offline_rag_abstention_evaluation_suite",
        "run_offline_rag_contradiction_evaluation_case",
        "run_offline_rag_contradiction_evaluation_suite",
        "run_offline_rag_freshness_evaluation_case",
        "run_offline_retrieval_evaluation_case",
        "run_offline_retrieval_evaluation_suite",
    ]


def _assessment(
    *,
    evaluation_id: str = "EVAL_REPORT_TEST",
    expected_outcome: ExpectedAIWorkflowOutcome = (ExpectedAIWorkflowOutcome.PROVIDER_ERROR),
    expected_structured_draft: StructuredDraftOutput | None = None,
    observed_outcome: ExpectedAIWorkflowOutcome = (ExpectedAIWorkflowOutcome.PROVIDER_ERROR),
    observed_structured_draft: StructuredDraftOutput | None = None,
    provider_call_count: int = 1,
) -> EvaluationCaseAssessment:
    evaluation_case = EvaluationCase(
        evaluation_id=evaluation_id,
        intake=_synthetic_intake(evaluation_id),
        expected_gateway_decision=GatewayDecision.ALLOW_DRAFT,
        expected_review_gate_status=(ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION),
        expected_outcome=expected_outcome,
        expected_structured_draft=expected_structured_draft,
    )
    result = EvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_gateway_decision=GatewayDecision.ALLOW_DRAFT,
        observed_review_gate_status=(ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION),
        observed_outcome=observed_outcome,
        observed_structured_draft=observed_structured_draft,
        provider_call_count=provider_call_count,
    )
    return assess_evaluation_run_result(result)


def _synthetic_intake(evaluation_id: str) -> IntakeCase:
    return IntakeCase(
        case_id=f"CASE_{evaluation_id}",
        client_ref=f"CLIENT_{evaluation_id}",
        scenario="Synthetic evaluation metrics report test.",
        period="2026-Q3",
        documents=(
            SyntheticDocument(
                document_id=f"DOCUMENT_{evaluation_id}",
                label="Synthetic report document descriptor.",
                period="2026-Q3",
                source_note="Synthetic source note without original content.",
            ),
        ),
    )


def _structured_draft() -> StructuredDraftOutput:
    return StructuredDraftOutput(
        summary_points=("Synthetic summary.",),
        uncertainties=("Synthetic uncertainty.",),
        review_questions=("Synthetic review question?",),
    )
