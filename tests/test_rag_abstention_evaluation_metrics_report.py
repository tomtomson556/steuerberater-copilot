import json
from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
import steuerberater_copilot.evaluation.rag_abstention_library as rag_abstention_library
import steuerberater_copilot.evaluation.rag_abstention_report as rag_abstention_report_module
from steuerberater_copilot.ai import FakeModelProvider, ModelResponse
from steuerberater_copilot.evaluation import (
    EvaluationMetricsReport,
    RAGAbstentionEvaluationCase,
    RAGAbstentionEvaluationCaseAssessment,
    RAGAbstentionEvaluationMetricsReport,
    RAGAbstentionEvaluationRunResult,
    RetrievalEvaluationMetricsReport,
    assess_rag_abstention_evaluation_run_result,
    build_synthetic_evaluation_case_library,
    build_synthetic_rag_abstention_evaluation_case_library,
    build_synthetic_retrieval_evaluation_case_library,
    run_offline_evaluation_suite,
    run_offline_rag_abstention_evaluation_suite,
    run_offline_retrieval_evaluation_suite,
)
from steuerberater_copilot.offline_mvp import IntakeCase, SyntheticDocument
from steuerberater_copilot.rag import SourceDocument

EXPECTED_BASELINE_EVALUATION_IDS = (
    "EVAL_RAG_ABSTENTION_BASELINE_MISSING_EVIDENCE",
    "EVAL_RAG_ABSTENTION_BASELINE_WITH_EVIDENCE",
    "EVAL_RAG_ABSTENTION_BASELINE_GATEWAY_STOP",
    "EVAL_RAG_ABSTENTION_BASELINE_REVIEW_GATE_STOP",
)


def test_abstention_metrics_report_is_immutable_and_uses_slots() -> None:
    assessment = _assessment(expected=True, observed=True)
    report = RAGAbstentionEvaluationMetricsReport(assessments=[assessment])

    with pytest.raises(FrozenInstanceError):
        report.assessments = ()

    assert report.assessments == (assessment,)
    assert report.assessments[0] is assessment
    assert not hasattr(report, "__dict__")
    assert RAGAbstentionEvaluationMetricsReport.__slots__ == ("assessments",)


def test_report_converts_sequence_to_tuple_and_preserves_identities() -> None:
    first = _assessment(
        evaluation_id="EVAL_ABSTENTION_REPORT_FIRST",
        expected=True,
        observed=True,
    )
    second = _assessment(
        evaluation_id="EVAL_ABSTENTION_REPORT_SECOND",
        expected=False,
        observed=False,
    )

    report = RAGAbstentionEvaluationMetricsReport(assessments=[first, second])

    assert isinstance(report.assessments, tuple)
    assert report.assessments == (first, second)
    assert report.assessments[0] is first
    assert report.assessments[1] is second


def test_empty_report_and_empty_suite_are_rejected() -> None:
    with pytest.raises(ValueError, match=r"^assessments must not be empty\.$"):
        RAGAbstentionEvaluationMetricsReport(assessments=())

    with pytest.raises(ValueError, match=r"^assessments must not be empty\.$"):
        run_offline_rag_abstention_evaluation_suite((), provider_factory=_provider_factory)


def test_baseline_suite_has_exact_metrics() -> None:
    cases = build_synthetic_rag_abstention_evaluation_case_library()

    report = run_offline_rag_abstention_evaluation_suite(
        cases,
        provider_factory=_provider_factory,
    )

    assert report.total_case_count == 4
    assert tuple(
        assessment.evaluation_run_result.evaluation_case.evaluation_id
        for assessment in report.assessments
    ) == EXPECTED_BASELINE_EVALUATION_IDS
    assert report.passed_case_count == 4
    assert report.failed_case_count == 0
    assert report.pass_rate == 1.0
    assert report.failed_evaluation_ids == ()
    assert report.expected_missing_evidence_case_count == 1
    assert report.missing_evidence_abstention_rate == 1.0
    assert report.false_negative_case_count == 0
    assert report.false_positive_case_count == 0


def test_suite_preserves_case_order_and_identities() -> None:
    cases = build_synthetic_rag_abstention_evaluation_case_library()

    report = run_offline_rag_abstention_evaluation_suite(
        cases,
        provider_factory=_provider_factory,
    )

    assert len(report.assessments) == len(cases)
    for case, assessment in zip(cases, report.assessments, strict=True):
        assert assessment.evaluation_run_result.evaluation_case is case
        assert isinstance(assessment, RAGAbstentionEvaluationCaseAssessment)


def test_suite_creates_exactly_one_fresh_provider_per_case() -> None:
    cases = build_synthetic_rag_abstention_evaluation_case_library()
    created_providers: list[FakeModelProvider] = []

    def recording_factory(
        evaluation_case: RAGAbstentionEvaluationCase,
    ) -> FakeModelProvider:
        provider = _provider_factory(evaluation_case)
        created_providers.append(provider)
        return provider

    run_offline_rag_abstention_evaluation_suite(
        cases,
        provider_factory=recording_factory,
    )

    assert len(created_providers) == len(cases)
    assert len({id(provider) for provider in created_providers}) == len(cases)


def test_control_cases_do_not_inflate_missing_evidence_denominator() -> None:
    report = RAGAbstentionEvaluationMetricsReport(
        assessments=(
            _assessment(
                evaluation_id="EVAL_ABSTENTION_EXPECTED",
                expected=True,
                observed=True,
            ),
            _assessment(
                evaluation_id="EVAL_ABSTENTION_CONTROL_A",
                expected=False,
                observed=False,
            ),
            _assessment(
                evaluation_id="EVAL_ABSTENTION_CONTROL_B",
                expected=False,
                observed=False,
            ),
        )
    )

    assert report.total_case_count == 3
    assert report.expected_missing_evidence_case_count == 1
    assert report.missing_evidence_abstention_rate == 1.0
    assert report.pass_rate == 1.0


def test_false_negative_is_counted_separately_from_false_positive() -> None:
    report = RAGAbstentionEvaluationMetricsReport(
        assessments=(
            _assessment(
                evaluation_id="EVAL_ABSTENTION_FALSE_NEGATIVE",
                expected=True,
                observed=False,
            ),
            _assessment(
                evaluation_id="EVAL_ABSTENTION_FALSE_POSITIVE",
                expected=False,
                observed=True,
            ),
            _assessment(
                evaluation_id="EVAL_ABSTENTION_MATCH",
                expected=True,
                observed=True,
            ),
        )
    )

    assert report.total_case_count == 3
    assert report.passed_case_count == 1
    assert report.failed_case_count == 2
    assert report.pass_rate == 1 / 3
    assert report.failed_evaluation_ids == (
        "EVAL_ABSTENTION_FALSE_NEGATIVE",
        "EVAL_ABSTENTION_FALSE_POSITIVE",
    )
    assert report.expected_missing_evidence_case_count == 2
    assert report.missing_evidence_abstention_rate == 0.5
    assert report.false_negative_case_count == 1
    assert report.false_positive_case_count == 1


def test_missing_evidence_rate_is_none_without_expected_missing_evidence_cases() -> None:
    report = RAGAbstentionEvaluationMetricsReport(
        assessments=(
            _assessment(
                evaluation_id="EVAL_ABSTENTION_CONTROL_ONLY_A",
                expected=False,
                observed=False,
            ),
            _assessment(
                evaluation_id="EVAL_ABSTENTION_CONTROL_ONLY_B",
                expected=False,
                observed=True,
            ),
        )
    )

    assert report.total_case_count == 2
    assert report.expected_missing_evidence_case_count == 0
    assert report.missing_evidence_abstention_rate is None
    assert report.false_negative_case_count == 0
    assert report.false_positive_case_count == 1
    assert report.pass_rate == 0.5


def test_suite_propagates_unexpected_runner_exception(monkeypatch) -> None:
    unexpected_error = RuntimeError("Synthetic unexpected abstention suite failure.")

    def fail_runner(*args, **kwargs):
        raise unexpected_error

    monkeypatch.setattr(
        rag_abstention_report_module,
        "run_offline_rag_abstention_evaluation_case",
        fail_runner,
    )

    with pytest.raises(RuntimeError) as exc_info:
        run_offline_rag_abstention_evaluation_suite(
            build_synthetic_rag_abstention_evaluation_case_library()[:1],
            provider_factory=_provider_factory,
        )

    assert exc_info.value is unexpected_error


def test_evaluation_package_exports_abstention_metrics_report_contract() -> None:
    assert (
        evaluation.RAGAbstentionEvaluationMetricsReport
        is RAGAbstentionEvaluationMetricsReport
    )
    assert (
        evaluation.run_offline_rag_abstention_evaluation_suite
        is run_offline_rag_abstention_evaluation_suite
    )
    assert evaluation.RAGAbstentionEvaluationMetricsReport is (
        rag_abstention_report_module.RAGAbstentionEvaluationMetricsReport
    )
    assert "RAGAbstentionEvaluationMetricsReport" in evaluation.__all__
    assert "run_offline_rag_abstention_evaluation_suite" in evaluation.__all__


def test_existing_ai_and_retrieval_metrics_reports_remain_unchanged() -> None:
    ai_report = run_offline_evaluation_suite(build_synthetic_evaluation_case_library())
    retrieval_report = run_offline_retrieval_evaluation_suite(
        build_synthetic_retrieval_evaluation_case_library()
    )

    assert evaluation.EvaluationMetricsReport is EvaluationMetricsReport
    assert evaluation.RetrievalEvaluationMetricsReport is RetrievalEvaluationMetricsReport
    assert "EvaluationMetricsReport" in evaluation.__all__
    assert "RetrievalEvaluationMetricsReport" in evaluation.__all__
    assert ai_report.total_case_count == 7
    assert ai_report.pass_rate == 1.0
    assert retrieval_report.total_case_count == 4
    assert retrieval_report.mean_recall_at_k == 0.5


def _assessment(
    *,
    evaluation_id: str = "EVAL_ABSTENTION_REPORT_TEST",
    expected: bool,
    observed: bool,
) -> RAGAbstentionEvaluationCaseAssessment:
    evaluation_case = RAGAbstentionEvaluationCase(
        evaluation_id=evaluation_id,
        intake=_allowed_intake(evaluation_id),
        source_documents=(
            SourceDocument(
                document_id="SYNTHETIC_ABSTENTION_REPORT_SOURCE",
                title="Synthetic orchard reference",
                content="Synthetic orchard content for abstention report testing.",
            ),
        ),
        retrieval_query="orchard",
        top_k=1,
        expected_abstained_for_missing_evidence=expected,
    )
    result = RAGAbstentionEvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_abstained_for_missing_evidence=observed,
    )
    return assess_rag_abstention_evaluation_run_result(result)


def _provider_factory(
    evaluation_case: RAGAbstentionEvaluationCase,
) -> FakeModelProvider:
    return FakeModelProvider(_grounded_model_response(evaluation_case))


def _grounded_model_response(
    evaluation_case: RAGAbstentionEvaluationCase,
) -> ModelResponse:
    document = evaluation_case.source_documents[0]
    supporting_text = (
        rag_abstention_library.WITH_EVIDENCE_PASSAGE
        if (
            evaluation_case.evaluation_id
            == "EVAL_RAG_ABSTENTION_BASELINE_WITH_EVIDENCE"
        )
        else document.content
    )
    return ModelResponse(
        content=json.dumps(
            {
                "summary_points": ["Synthetic grounded orchard summary."],
                "uncertainties": ["Synthetic grounded uncertainty."],
                "review_questions": ["Synthetic grounded review question?"],
                "citations": [
                    {
                        "summary_point_index": 0,
                        "document_id": document.document_id,
                        "supporting_text": supporting_text,
                    }
                ],
            }
        ),
        provider_name="fake",
        model_name="fake-model",
    )


def _allowed_intake(evaluation_id: str) -> IntakeCase:
    return IntakeCase(
        case_id=f"CASE_{evaluation_id}",
        client_ref=f"CLIENT_{evaluation_id}",
        scenario="Synthetic RAG abstention metrics report fixture.",
        period="2026-Q3",
        documents=(
            SyntheticDocument(
                document_id=f"DOCUMENT_{evaluation_id}",
                label="Synthetic abstention metrics report document descriptor.",
                period="2026-Q3",
                source_note="Synthetic source note without original content.",
            ),
        ),
        notes=("Synthetic abstention metrics report note.",),
    )
