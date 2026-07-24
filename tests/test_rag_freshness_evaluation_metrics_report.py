from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
import steuerberater_copilot.evaluation.rag_freshness_report as report_module
from steuerberater_copilot.evaluation import (
    RAGFreshnessEvaluationCase,
    RAGFreshnessEvaluationCaseAssessment,
    RAGFreshnessEvaluationMetricsReport,
    RAGFreshnessEvaluationRunResult,
    assess_rag_freshness_evaluation_run_result,
    build_synthetic_rag_freshness_evaluation_case_library,
    run_offline_rag_freshness_evaluation_suite,
)
from steuerberater_copilot.rag import SourceDocument

CURRENT_ID = "SYNTHETIC_FRESHNESS_REPORT_CURRENT"
STALE_A_ID = "SYNTHETIC_FRESHNESS_REPORT_STALE_A"
STALE_B_ID = "SYNTHETIC_FRESHNESS_REPORT_STALE_B"
NEUTRAL_ID = "SYNTHETIC_FRESHNESS_REPORT_NEUTRAL"

EXPECTED_BASELINE_EVALUATION_IDS = (
    "EVAL_RAG_FRESHNESS_BASELINE_CURRENT_AHEAD",
    "EVAL_RAG_FRESHNESS_BASELINE_STALE_OUTSIDE_TOP_K",
    "EVAL_RAG_FRESHNESS_BASELINE_NEUTRAL_DISTRACTOR",
    "EVAL_RAG_FRESHNESS_BASELINE_MULTIPLE_STALE",
    "EVAL_RAG_FRESHNESS_BASELINE_NORMALIZED_QUERY",
)


def test_freshness_metrics_report_is_immutable_and_uses_slots() -> None:
    assessment = _assessment(retrieved_document_ids=(CURRENT_ID,))
    report = RAGFreshnessEvaluationMetricsReport(assessments=[assessment])

    with pytest.raises(FrozenInstanceError):
        report.assessments = ()

    assert report.assessments == (assessment,)
    assert report.assessments[0] is assessment
    assert not hasattr(report, "__dict__")
    assert RAGFreshnessEvaluationMetricsReport.__slots__ == ("assessments",)


def test_report_converts_sequence_to_tuple_and_preserves_identities() -> None:
    first = _assessment(
        evaluation_id="EVAL_FRESHNESS_REPORT_FIRST",
        retrieved_document_ids=(CURRENT_ID,),
    )
    second = _assessment(
        evaluation_id="EVAL_FRESHNESS_REPORT_SECOND",
        retrieved_document_ids=(CURRENT_ID, NEUTRAL_ID),
    )

    report = RAGFreshnessEvaluationMetricsReport(assessments=[first, second])

    assert isinstance(report.assessments, tuple)
    assert report.assessments == (first, second)
    assert report.assessments[0] is first
    assert report.assessments[1] is second


def test_empty_report_and_empty_suite_are_rejected() -> None:
    with pytest.raises(ValueError, match=r"^assessments must not be empty\.$"):
        RAGFreshnessEvaluationMetricsReport(assessments=())

    with pytest.raises(ValueError, match=r"^assessments must not be empty\.$"):
        run_offline_rag_freshness_evaluation_suite(())


def test_baseline_suite_has_exact_metrics() -> None:
    cases = build_synthetic_rag_freshness_evaluation_case_library()

    report = run_offline_rag_freshness_evaluation_suite(cases)

    assert report.total_case_count == 5
    assert tuple(
        assessment.evaluation_run_result.evaluation_case.evaluation_id
        for assessment in report.assessments
    ) == EXPECTED_BASELINE_EVALUATION_IDS
    assert report.passed_case_count == 5
    assert report.failed_case_count == 0
    assert report.pass_rate == 1.0
    assert report.failed_evaluation_ids == ()
    assert report.current_document_retrieval_rate == 1.0
    assert report.stale_document_retrieval_rate == 0.0
    assert report.missing_current_document_case_count == 0
    assert report.stale_document_retrieval_case_count == 0


def test_suite_preserves_case_order_and_identities() -> None:
    cases = build_synthetic_rag_freshness_evaluation_case_library()

    report = run_offline_rag_freshness_evaluation_suite(cases)

    assert len(report.assessments) == len(cases)
    for case, assessment in zip(cases, report.assessments, strict=True):
        assert assessment.evaluation_run_result.evaluation_case is case
        assert isinstance(assessment, RAGFreshnessEvaluationCaseAssessment)


def test_failed_evaluation_ids_are_ordered_and_traceable() -> None:
    report = RAGFreshnessEvaluationMetricsReport(
        assessments=(
            _assessment(
                evaluation_id="EVAL_FRESHNESS_FAIL_ALPHA",
                retrieved_document_ids=(STALE_A_ID,),
            ),
            _assessment(
                evaluation_id="EVAL_FRESHNESS_PASS_BETA",
                retrieved_document_ids=(CURRENT_ID,),
            ),
            _assessment(
                evaluation_id="EVAL_FRESHNESS_FAIL_GAMMA",
                retrieved_document_ids=(NEUTRAL_ID,),
            ),
        )
    )

    assert report.pass_rate == 1 / 3
    assert report.failed_evaluation_ids == (
        "EVAL_FRESHNESS_FAIL_ALPHA",
        "EVAL_FRESHNESS_FAIL_GAMMA",
    )
    assert report.passed_case_count == 1
    assert report.failed_case_count == 2


def test_missing_current_document_case_is_counted() -> None:
    report = RAGFreshnessEvaluationMetricsReport(
        assessments=(
            _assessment(
                evaluation_id="EVAL_FRESHNESS_NO_CURRENT",
                retrieved_document_ids=(STALE_A_ID,),
            ),
            _assessment(
                evaluation_id="EVAL_FRESHNESS_CURRENT_PRESENT",
                retrieved_document_ids=(CURRENT_ID,),
            ),
        )
    )

    assert report.missing_current_document_case_count == 1
    assert report.current_document_retrieval_rate == 0.5
    assert report.pass_rate == 0.5
    assert report.stale_document_retrieval_case_count == 1
    assert report.stale_document_retrieval_rate == 0.5


def test_current_plus_stale_fails_and_counts_case_not_stale_docs() -> None:
    report = RAGFreshnessEvaluationMetricsReport(
        assessments=(
            _assessment(
                evaluation_id="EVAL_FRESHNESS_CURRENT_PLUS_STALE",
                retrieved_document_ids=(CURRENT_ID, STALE_A_ID),
            ),
            _assessment(
                evaluation_id="EVAL_FRESHNESS_CURRENT_ONLY",
                retrieved_document_ids=(CURRENT_ID,),
            ),
            _assessment(
                evaluation_id="EVAL_FRESHNESS_CURRENT_PLUS_TWO_STALE",
                retrieved_document_ids=(CURRENT_ID, STALE_A_ID, STALE_B_ID),
            ),
        )
    )

    assert report.total_case_count == 3
    assert report.passed_case_count == 1
    assert report.failed_case_count == 2
    assert report.pass_rate == 1 / 3
    assert report.missing_current_document_case_count == 0
    assert report.current_document_retrieval_rate == 1.0
    assert report.stale_document_retrieval_case_count == 2
    assert report.stale_document_retrieval_rate == 2 / 3
    assert report.failed_evaluation_ids == (
        "EVAL_FRESHNESS_CURRENT_PLUS_STALE",
        "EVAL_FRESHNESS_CURRENT_PLUS_TWO_STALE",
    )


def test_stale_without_current_fails_and_counts_as_stale_case() -> None:
    report = RAGFreshnessEvaluationMetricsReport(
        assessments=(
            _assessment(
                evaluation_id="EVAL_FRESHNESS_STALE_ONLY",
                retrieved_document_ids=(STALE_B_ID,),
            ),
            _assessment(
                evaluation_id="EVAL_FRESHNESS_CURRENT_ONLY",
                retrieved_document_ids=(CURRENT_ID,),
            ),
        )
    )

    assert report.passed_case_count == 1
    assert report.failed_case_count == 1
    assert report.pass_rate == 0.5
    assert report.missing_current_document_case_count == 1
    assert report.current_document_retrieval_rate == 0.5
    assert report.stale_document_retrieval_case_count == 1
    assert report.stale_document_retrieval_rate == 0.5
    assert report.failed_evaluation_ids == ("EVAL_FRESHNESS_STALE_ONLY",)


def test_stale_rate_counts_cases_not_individual_stale_documents() -> None:
    report = RAGFreshnessEvaluationMetricsReport(
        assessments=(
            _assessment(
                evaluation_id="EVAL_FRESHNESS_SINGLE_STALE",
                retrieved_document_ids=(CURRENT_ID, STALE_A_ID),
            ),
            _assessment(
                evaluation_id="EVAL_FRESHNESS_DOUBLE_STALE_SAME_CASE",
                retrieved_document_ids=(CURRENT_ID, STALE_A_ID, STALE_B_ID),
            ),
        )
    )

    assert report.stale_document_retrieval_case_count == 2
    assert report.stale_document_retrieval_rate == 1.0
    assert report.pass_rate == 0.0


def test_suite_is_deterministic() -> None:
    cases = build_synthetic_rag_freshness_evaluation_case_library()

    first = run_offline_rag_freshness_evaluation_suite(cases)
    second = run_offline_rag_freshness_evaluation_suite(cases)

    assert first.total_case_count == second.total_case_count
    assert first.passed_case_count == second.passed_case_count
    assert first.pass_rate == second.pass_rate
    assert first.current_document_retrieval_rate == second.current_document_retrieval_rate
    assert first.stale_document_retrieval_rate == second.stale_document_retrieval_rate
    assert first.failed_evaluation_ids == second.failed_evaluation_ids
    assert first.missing_current_document_case_count == second.missing_current_document_case_count
    assert first.stale_document_retrieval_case_count == second.stale_document_retrieval_case_count


def test_suite_propagates_unexpected_runner_exception(monkeypatch) -> None:
    unexpected_error = RuntimeError("Synthetic unexpected freshness suite failure.")

    def fail_runner(*args, **kwargs):
        raise unexpected_error

    monkeypatch.setattr(
        report_module,
        "run_offline_rag_freshness_evaluation_case",
        fail_runner,
    )

    with pytest.raises(RuntimeError) as exc_info:
        run_offline_rag_freshness_evaluation_suite(
            build_synthetic_rag_freshness_evaluation_case_library()[:1]
        )

    assert exc_info.value is unexpected_error


def test_evaluation_package_exports_freshness_metrics_report_contract() -> None:
    assert (
        evaluation.RAGFreshnessEvaluationMetricsReport
        is RAGFreshnessEvaluationMetricsReport
    )
    assert (
        evaluation.run_offline_rag_freshness_evaluation_suite
        is run_offline_rag_freshness_evaluation_suite
    )
    assert evaluation.RAGFreshnessEvaluationMetricsReport is (
        report_module.RAGFreshnessEvaluationMetricsReport
    )
    assert "RAGFreshnessEvaluationMetricsReport" in evaluation.__all__
    assert "run_offline_rag_freshness_evaluation_suite" in evaluation.__all__


def _assessment(
    *,
    evaluation_id: str = "EVAL_RAG_FRESHNESS_REPORT_TEST",
    retrieved_document_ids: tuple[str, ...],
    top_k: int | None = None,
) -> RAGFreshnessEvaluationCaseAssessment:
    documents = _documents()
    documents_by_id = {document.document_id: document for document in documents}
    evaluation_case = RAGFreshnessEvaluationCase(
        evaluation_id=evaluation_id,
        source_documents=documents,
        retrieval_query="synthetic freshness report query",
        top_k=top_k if top_k is not None else max(len(retrieved_document_ids), 1),
        expected_current_document_id=CURRENT_ID,
        stale_document_ids=(STALE_A_ID, STALE_B_ID),
    )
    result = RAGFreshnessEvaluationRunResult(
        evaluation_case=evaluation_case,
        retrieved_documents=tuple(
            documents_by_id[document_id]
            for document_id in retrieved_document_ids
        ),
    )
    return assess_rag_freshness_evaluation_run_result(result)


def _documents() -> tuple[SourceDocument, ...]:
    return (
        _document(CURRENT_ID),
        _document(STALE_A_ID),
        _document(STALE_B_ID),
        _document(NEUTRAL_ID),
    )


def _document(document_id: str) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=f"Synthetic title for {document_id}",
        content=f"Synthetic content for {document_id}.",
    )
