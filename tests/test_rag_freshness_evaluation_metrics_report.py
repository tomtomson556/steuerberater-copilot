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
from steuerberater_copilot.rag import DocumentVersionRecord, SourceDocument

EXPECTED_BASELINE_EVALUATION_IDS = (
    "EVAL_RAG_FRESHNESS_BASELINE_SUPERSEDED",
    "EVAL_RAG_FRESHNESS_BASELINE_EXPIRED",
    "EVAL_RAG_FRESHNESS_BASELINE_CURRENT",
    "EVAL_RAG_FRESHNESS_BASELINE_MIXED",
)


def test_freshness_metrics_report_is_immutable_and_uses_slots() -> None:
    assessment = _assessment(
        expected=("SYNTHETIC_SOURCE_ORCHARD_V1",),
        observed=("SYNTHETIC_SOURCE_ORCHARD_V1",),
    )
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
        expected=("SYNTHETIC_SOURCE_ORCHARD_V1",),
        observed=("SYNTHETIC_SOURCE_ORCHARD_V1",),
    )
    second = _assessment(
        evaluation_id="EVAL_FRESHNESS_REPORT_SECOND",
        expected=(),
        observed=(),
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

    assert report.total_case_count == 4
    assert tuple(
        assessment.evaluation_run_result.evaluation_case.evaluation_id
        for assessment in report.assessments
    ) == EXPECTED_BASELINE_EVALUATION_IDS
    assert report.passed_case_count == 4
    assert report.failed_case_count == 0
    assert report.pass_rate == 1.0
    assert report.failed_evaluation_ids == ()
    assert report.expected_outdated_document_count == 4
    assert report.outdated_detection_rate == 1.0


def test_suite_preserves_case_order_and_identities() -> None:
    cases = build_synthetic_rag_freshness_evaluation_case_library()

    report = run_offline_rag_freshness_evaluation_suite(cases)

    assert len(report.assessments) == len(cases)
    for case, assessment in zip(cases, report.assessments, strict=True):
        assert assessment.evaluation_run_result.evaluation_case is case
        assert isinstance(assessment, RAGFreshnessEvaluationCaseAssessment)


def test_failure_ids_and_detection_rate_reflect_failed_cases() -> None:
    report = RAGFreshnessEvaluationMetricsReport(
        assessments=(
            _assessment(
                evaluation_id="EVAL_FRESHNESS_MISSED",
                expected=("SYNTHETIC_SOURCE_ORCHARD_V1",),
                observed=(),
            ),
            _assessment(
                evaluation_id="EVAL_FRESHNESS_UNEXPECTED",
                expected=(),
                observed=("SYNTHETIC_SOURCE_ORCHARD_V1",),
            ),
            _assessment(
                evaluation_id="EVAL_FRESHNESS_MATCH",
                expected=(
                    "SYNTHETIC_SOURCE_ORCHARD_V1",
                    "SYNTHETIC_SOURCE_MEADOW_EXPIRED",
                ),
                observed=("SYNTHETIC_SOURCE_ORCHARD_V1",),
            ),
        )
    )

    assert report.total_case_count == 3
    assert report.passed_case_count == 0
    assert report.failed_case_count == 3
    assert report.pass_rate == 0.0
    assert report.failed_evaluation_ids == (
        "EVAL_FRESHNESS_MISSED",
        "EVAL_FRESHNESS_UNEXPECTED",
        "EVAL_FRESHNESS_MATCH",
    )
    assert report.expected_outdated_document_count == 3
    assert report.outdated_detection_rate == 1 / 3


def test_detection_rate_is_none_without_expected_outdated_documents() -> None:
    report = RAGFreshnessEvaluationMetricsReport(
        assessments=(
            _assessment(
                evaluation_id="EVAL_FRESHNESS_CONTROL_ONLY_A",
                expected=(),
                observed=(),
            ),
            _assessment(
                evaluation_id="EVAL_FRESHNESS_CONTROL_ONLY_B",
                expected=(),
                observed=("SYNTHETIC_SOURCE_ORCHARD_V1",),
            ),
        )
    )

    assert report.expected_outdated_document_count == 0
    assert report.outdated_detection_rate is None
    assert report.pass_rate == 0.5


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
    assert "RAGFreshnessEvaluationMetricsReport" in evaluation.__all__
    assert "run_offline_rag_freshness_evaluation_suite" in evaluation.__all__


def _assessment(
    *,
    evaluation_id: str = "EVAL_FRESHNESS_REPORT_TEST",
    expected: tuple[str, ...],
    observed: tuple[str, ...],
) -> RAGFreshnessEvaluationCaseAssessment:
    evaluation_case = RAGFreshnessEvaluationCase(
        evaluation_id=evaluation_id,
        source_documents=(
            _document("SYNTHETIC_SOURCE_ORCHARD_V1"),
            _document("SYNTHETIC_SOURCE_ORCHARD_V2"),
            _document("SYNTHETIC_SOURCE_MEADOW_EXPIRED"),
        ),
        version_records=(
            _record("SYNTHETIC_SOURCE_ORCHARD_V1", family="orchard", version=1),
            _record("SYNTHETIC_SOURCE_ORCHARD_V2", family="orchard", version=2),
            _record(
                "SYNTHETIC_SOURCE_MEADOW_EXPIRED",
                family="meadow",
                version=1,
                effective_date="2026-01-01",
            ),
        ),
        reference_date="2026-07-01",
        expected_outdated_document_ids=expected,
    )
    result = RAGFreshnessEvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_outdated_document_ids=observed,
    )
    return assess_rag_freshness_evaluation_run_result(result)


def _document(document_id: str) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=f"Synthetic title for {document_id}",
        content=f"Synthetic orchard content for {document_id}.",
    )


def _record(
    document_id: str,
    *,
    family: str,
    version: int,
    effective_date: str = "2026-07-01",
) -> DocumentVersionRecord:
    return DocumentVersionRecord(
        document_id=document_id,
        document_family=family,
        version_number=version,
        effective_date=effective_date,
    )
