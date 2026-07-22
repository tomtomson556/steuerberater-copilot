from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
import steuerberater_copilot.evaluation.rag_contradiction_report as report_module
from steuerberater_copilot.evaluation import (
    ContradictionEvidenceLabel,
    RAGContradictionEvaluationCase,
    RAGContradictionEvaluationCaseAssessment,
    RAGContradictionEvaluationMetricsReport,
    RAGContradictionEvaluationRunResult,
    assess_rag_contradiction_evaluation_run_result,
    build_synthetic_rag_contradiction_evaluation_case_library,
    run_offline_rag_contradiction_evaluation_suite,
)
from steuerberater_copilot.rag import SourceDocument

RETENTION_SEVEN_YEARS = "The retention period is 7 years."
RETENTION_TEN_YEARS = "The retention period is 10 years."

EXPECTED_BASELINE_EVALUATION_IDS = (
    "EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_CONFLICT",
    "EVAL_RAG_CONTRADICTION_BASELINE_NO_CLAIM_OVERLAP",
    "EVAL_RAG_CONTRADICTION_BASELINE_SAME_FACT_PARAPHRASE",
    "EVAL_RAG_CONTRADICTION_BASELINE_DIFFERENT_SUBJECTS",
    "EVAL_RAG_CONTRADICTION_BASELINE_TEMPORAL_SCOPES",
    "EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_NEGATION",
    "EVAL_RAG_CONTRADICTION_BASELINE_ARCHIVE_NOT_REQUIRED",
    "EVAL_RAG_CONTRADICTION_BASELINE_MARKER_NOISE_IGNORED",
    "EVAL_RAG_CONTRADICTION_BASELINE_KNOWN_LIMITATION_DECADE",
)


def test_contradiction_metrics_report_is_immutable_and_uses_slots() -> None:
    assessment = _assessment(expected=True, observed=True)
    report = RAGContradictionEvaluationMetricsReport(assessments=[assessment])

    with pytest.raises(FrozenInstanceError):
        report.assessments = ()

    assert report.assessments == (assessment,)
    assert report.assessments[0] is assessment
    assert not hasattr(report, "__dict__")
    assert RAGContradictionEvaluationMetricsReport.__slots__ == ("assessments",)


def test_report_converts_sequence_to_tuple_and_preserves_identities() -> None:
    first = _assessment(
        evaluation_id="EVAL_CONTRADICTION_REPORT_FIRST",
        expected=True,
        observed=True,
    )
    second = _assessment(
        evaluation_id="EVAL_CONTRADICTION_REPORT_SECOND",
        expected=False,
        observed=False,
    )

    report = RAGContradictionEvaluationMetricsReport(assessments=[first, second])

    assert isinstance(report.assessments, tuple)
    assert report.assessments == (first, second)
    assert report.assessments[0] is first
    assert report.assessments[1] is second


def test_empty_report_and_empty_suite_are_rejected() -> None:
    with pytest.raises(ValueError, match=r"^assessments must not be empty\.$"):
        RAGContradictionEvaluationMetricsReport(assessments=())

    with pytest.raises(ValueError, match=r"^assessments must not be empty\.$"):
        run_offline_rag_contradiction_evaluation_suite(())


def test_baseline_suite_has_exact_metrics() -> None:
    cases = build_synthetic_rag_contradiction_evaluation_case_library()

    report = run_offline_rag_contradiction_evaluation_suite(cases)

    assert report.total_case_count == 9
    assert tuple(
        assessment.evaluation_run_result.evaluation_case.evaluation_id
        for assessment in report.assessments
    ) == EXPECTED_BASELINE_EVALUATION_IDS
    assert report.passed_case_count == 8
    assert report.failed_case_count == 1
    assert report.pass_rate == 8 / 9
    assert report.failed_evaluation_ids == (
        "EVAL_RAG_CONTRADICTION_BASELINE_KNOWN_LIMITATION_DECADE",
    )
    assert report.expected_contradiction_case_count == 4
    assert report.contradiction_detection_rate == 3 / 4


def test_suite_preserves_case_order_and_identities() -> None:
    cases = build_synthetic_rag_contradiction_evaluation_case_library()

    report = run_offline_rag_contradiction_evaluation_suite(cases)

    assert len(report.assessments) == len(cases)
    for case, assessment in zip(cases, report.assessments, strict=True):
        assert assessment.evaluation_run_result.evaluation_case is case
        assert isinstance(assessment, RAGContradictionEvaluationCaseAssessment)


def test_failure_ids_and_detection_rate_reflect_failed_cases() -> None:
    report = RAGContradictionEvaluationMetricsReport(
        assessments=(
            _assessment(
                evaluation_id="EVAL_CONTRADICTION_FALSE_NEGATIVE",
                expected=True,
                observed=False,
            ),
            _assessment(
                evaluation_id="EVAL_CONTRADICTION_FALSE_POSITIVE",
                expected=False,
                observed=True,
                observed_passages=_labels(),
            ),
            _assessment(
                evaluation_id="EVAL_CONTRADICTION_MATCH",
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
        "EVAL_CONTRADICTION_FALSE_NEGATIVE",
        "EVAL_CONTRADICTION_FALSE_POSITIVE",
    )
    assert report.expected_contradiction_case_count == 2
    assert report.contradiction_detection_rate == 0.5


def test_detection_rate_is_none_without_expected_contradiction_cases() -> None:
    report = RAGContradictionEvaluationMetricsReport(
        assessments=(
            _assessment(
                evaluation_id="EVAL_CONTRADICTION_CONTROL_ONLY_A",
                expected=False,
                observed=False,
            ),
            _assessment(
                evaluation_id="EVAL_CONTRADICTION_CONTROL_ONLY_B",
                expected=False,
                observed=True,
                observed_passages=_labels(),
            ),
        )
    )

    assert report.expected_contradiction_case_count == 0
    assert report.contradiction_detection_rate is None
    assert report.pass_rate == 0.5


def test_suite_propagates_unexpected_runner_exception(monkeypatch) -> None:
    unexpected_error = RuntimeError("Synthetic unexpected contradiction suite failure.")

    def fail_runner(*args, **kwargs):
        raise unexpected_error

    monkeypatch.setattr(
        report_module,
        "run_offline_rag_contradiction_evaluation_case",
        fail_runner,
    )

    with pytest.raises(RuntimeError) as exc_info:
        run_offline_rag_contradiction_evaluation_suite(
            build_synthetic_rag_contradiction_evaluation_case_library()[:1]
        )

    assert exc_info.value is unexpected_error


def test_evaluation_package_exports_contradiction_metrics_report_contract() -> None:
    assert (
        evaluation.RAGContradictionEvaluationMetricsReport
        is RAGContradictionEvaluationMetricsReport
    )
    assert (
        evaluation.run_offline_rag_contradiction_evaluation_suite
        is run_offline_rag_contradiction_evaluation_suite
    )
    assert "RAGContradictionEvaluationMetricsReport" in evaluation.__all__
    assert "run_offline_rag_contradiction_evaluation_suite" in evaluation.__all__


def _assessment(
    *,
    evaluation_id: str = "EVAL_CONTRADICTION_REPORT_TEST",
    expected: bool,
    observed: bool,
    observed_passages: tuple[ContradictionEvidenceLabel, ...] | None = None,
) -> RAGContradictionEvaluationCaseAssessment:
    if observed_passages is None:
        observed_passages = _labels() if observed else ()
    evaluation_case = RAGContradictionEvaluationCase(
        evaluation_id=evaluation_id,
        source_documents=(
            _document(
                "SYNTHETIC_SOURCE_RETENTION_TEN",
                content=f"Synthetic orchard note. {RETENTION_TEN_YEARS}",
            ),
            _document(
                "SYNTHETIC_SOURCE_RETENTION_SEVEN",
                content=f"Synthetic meadow note. {RETENTION_SEVEN_YEARS}",
            ),
        ),
        expected_contradiction_present=expected,
        contradicting_passages=_labels() if expected else (),
    )
    result = RAGContradictionEvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_contradiction_present=observed,
        observed_contradicting_passages=observed_passages,
    )
    return assess_rag_contradiction_evaluation_run_result(result)


def _labels() -> tuple[ContradictionEvidenceLabel, ...]:
    return (
        ContradictionEvidenceLabel(
            document_id="SYNTHETIC_SOURCE_RETENTION_TEN",
            supporting_text=RETENTION_TEN_YEARS,
        ),
        ContradictionEvidenceLabel(
            document_id="SYNTHETIC_SOURCE_RETENTION_SEVEN",
            supporting_text=RETENTION_SEVEN_YEARS,
        ),
    )


def _document(document_id: str, *, content: str) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=f"Synthetic title for {document_id}",
        content=content,
    )
