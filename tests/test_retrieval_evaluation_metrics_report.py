from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
import steuerberater_copilot.evaluation.retrieval_report as retrieval_report_module
from steuerberater_copilot.evaluation import (
    EvaluationMetricsReport,
    RetrievalEvaluationCase,
    RetrievalEvaluationCaseAssessment,
    RetrievalEvaluationMetricsReport,
    RetrievalEvaluationRunResult,
    assess_retrieval_evaluation_run_result,
    build_synthetic_evaluation_case_library,
    build_synthetic_retrieval_evaluation_case_library,
    run_offline_evaluation_suite,
    run_offline_retrieval_evaluation_suite,
)
from steuerberater_copilot.rag import SourceDocument

EXPECTED_BASELINE_RECALL_AT_K = (1.0, 0.5, 0.0, None)


def test_retrieval_metrics_report_is_immutable_and_uses_slots() -> None:
    assessment = _assessment(relevant_document_ids=("SYNTHETIC_SOURCE_A",))
    report = RetrievalEvaluationMetricsReport(assessments=[assessment])

    with pytest.raises(FrozenInstanceError):
        report.assessments = ()

    assert report.assessments == (assessment,)
    assert report.assessments[0] is assessment
    assert not hasattr(report, "__dict__")
    assert RetrievalEvaluationMetricsReport.__slots__ == ("assessments",)


def test_report_converts_sequence_to_tuple_and_preserves_identities() -> None:
    first = _assessment(
        evaluation_id="EVAL_RETRIEVAL_REPORT_FIRST",
        relevant_document_ids=("SYNTHETIC_SOURCE_A",),
        retrieved_document_ids=("SYNTHETIC_SOURCE_A",),
    )
    second = _assessment(
        evaluation_id="EVAL_RETRIEVAL_REPORT_SECOND",
        relevant_document_ids=(),
    )

    report = RetrievalEvaluationMetricsReport(assessments=[first, second])

    assert isinstance(report.assessments, tuple)
    assert report.assessments == (first, second)
    assert report.assessments[0] is first
    assert report.assessments[1] is second


def test_empty_report_and_empty_suite_are_rejected() -> None:
    with pytest.raises(ValueError, match=r"^assessments must not be empty\.$"):
        RetrievalEvaluationMetricsReport(assessments=())

    with pytest.raises(ValueError, match=r"^assessments must not be empty\.$"):
        run_offline_retrieval_evaluation_suite(())


def test_baseline_suite_has_exact_metrics() -> None:
    cases = build_synthetic_retrieval_evaluation_case_library()

    report = run_offline_retrieval_evaluation_suite(cases)

    assert report.total_case_count == 4
    assert report.applicable_recall_case_count == 3
    assert report.inapplicable_recall_case_count == 1
    assert tuple(assessment.recall_at_k for assessment in report.assessments) == (
        EXPECTED_BASELINE_RECALL_AT_K
    )
    assert report.mean_recall_at_k == 0.5
    assert not hasattr(report, "passed")
    assert not hasattr(report, "failed_case_count")
    assert not hasattr(report, "pass_rate")
    assert not hasattr(report, "abstained")
    assert not hasattr(report, "abstention")
    assert not hasattr(report, "failed_evaluation_ids")


def test_suite_preserves_case_order_and_identities() -> None:
    cases = build_synthetic_retrieval_evaluation_case_library()

    report = run_offline_retrieval_evaluation_suite(cases)

    assert len(report.assessments) == len(cases)
    for case, assessment in zip(cases, report.assessments, strict=True):
        assert assessment.evaluation_run_result.evaluation_case is case
        assert isinstance(assessment, RetrievalEvaluationCaseAssessment)


def test_zero_recall_is_included_in_applicable_count_and_mean() -> None:
    report = RetrievalEvaluationMetricsReport(
        assessments=(
            _assessment(
                evaluation_id="EVAL_RETRIEVAL_ZERO_ONLY",
                relevant_document_ids=("SYNTHETIC_SOURCE_RELEVANT",),
                retrieved_document_ids=("SYNTHETIC_SOURCE_OTHER",),
                source_document_ids=(
                    "SYNTHETIC_SOURCE_RELEVANT",
                    "SYNTHETIC_SOURCE_OTHER",
                ),
            ),
        )
    )

    assert report.total_case_count == 1
    assert report.applicable_recall_case_count == 1
    assert report.inapplicable_recall_case_count == 0
    assert report.assessments[0].recall_at_k == 0.0
    assert report.mean_recall_at_k == 0.0


def test_suite_with_only_inapplicable_recall_has_no_mean() -> None:
    cases = (
        RetrievalEvaluationCase(
            evaluation_id="EVAL_RETRIEVAL_INAPPLICABLE_A",
            source_documents=(_document("SYNTHETIC_SOURCE_MEADOW"),),
            retrieval_query="orchard",
            top_k=1,
            relevant_document_ids=(),
        ),
        RetrievalEvaluationCase(
            evaluation_id="EVAL_RETRIEVAL_INAPPLICABLE_B",
            source_documents=(_document("SYNTHETIC_SOURCE_RIVER"),),
            retrieval_query="quartz",
            top_k=1,
            relevant_document_ids=(),
        ),
    )

    report = run_offline_retrieval_evaluation_suite(cases)

    assert report.total_case_count == 2
    assert report.applicable_recall_case_count == 0
    assert report.inapplicable_recall_case_count == report.total_case_count
    assert tuple(assessment.recall_at_k for assessment in report.assessments) == (
        None,
        None,
    )
    assert report.mean_recall_at_k is None


def test_suite_propagates_unexpected_runner_exception(monkeypatch) -> None:
    unexpected_error = RuntimeError("Synthetic unexpected retrieval suite failure.")

    def fail_runner(*args, **kwargs):
        raise unexpected_error

    monkeypatch.setattr(
        retrieval_report_module,
        "run_offline_retrieval_evaluation_case",
        fail_runner,
    )

    with pytest.raises(RuntimeError) as exc_info:
        run_offline_retrieval_evaluation_suite(
            build_synthetic_retrieval_evaluation_case_library()[:1]
        )

    assert exc_info.value is unexpected_error


def test_evaluation_package_exports_retrieval_metrics_report_contract() -> None:
    assert (
        evaluation.RetrievalEvaluationMetricsReport
        is RetrievalEvaluationMetricsReport
    )
    assert (
        evaluation.run_offline_retrieval_evaluation_suite
        is run_offline_retrieval_evaluation_suite
    )
    assert evaluation.RetrievalEvaluationMetricsReport is (
        retrieval_report_module.RetrievalEvaluationMetricsReport
    )
    assert "RetrievalEvaluationMetricsReport" in evaluation.__all__
    assert "run_offline_retrieval_evaluation_suite" in evaluation.__all__


def test_existing_ai_evaluation_metrics_report_remains_unchanged() -> None:
    report = run_offline_evaluation_suite(build_synthetic_evaluation_case_library())

    assert evaluation.EvaluationMetricsReport is EvaluationMetricsReport
    assert evaluation.run_offline_evaluation_suite is run_offline_evaluation_suite
    assert "EvaluationMetricsReport" in evaluation.__all__
    assert "run_offline_evaluation_suite" in evaluation.__all__
    assert report.total_case_count == 7
    assert report.passed_case_count == 7
    assert report.pass_rate == 1.0
    assert report.failed_evaluation_ids == ()


def _assessment(
    *,
    evaluation_id: str = "EVAL_RETRIEVAL_REPORT_TEST",
    relevant_document_ids: tuple[str, ...] = ("SYNTHETIC_SOURCE_A",),
    retrieved_document_ids: tuple[str, ...] | None = None,
    source_document_ids: tuple[str, ...] | None = None,
    top_k: int = 1,
) -> RetrievalEvaluationCaseAssessment:
    if source_document_ids is None:
        source_document_ids = relevant_document_ids or ("SYNTHETIC_SOURCE_OTHER",)
    if retrieved_document_ids is None:
        retrieved_document_ids = source_document_ids[:1]

    documents_by_id = {
        document_id: _document(document_id) for document_id in source_document_ids
    }
    evaluation_case = RetrievalEvaluationCase(
        evaluation_id=evaluation_id,
        source_documents=tuple(
            documents_by_id[document_id] for document_id in source_document_ids
        ),
        retrieval_query="synthetic query",
        top_k=top_k,
        relevant_document_ids=relevant_document_ids,
    )
    result = RetrievalEvaluationRunResult(
        evaluation_case=evaluation_case,
        retrieved_documents=tuple(
            documents_by_id[document_id] for document_id in retrieved_document_ids
        ),
    )
    return assess_retrieval_evaluation_run_result(result)


def _document(document_id: str) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=f"Synthetic title for {document_id}",
        content=f"Synthetic content for {document_id}.",
    )
