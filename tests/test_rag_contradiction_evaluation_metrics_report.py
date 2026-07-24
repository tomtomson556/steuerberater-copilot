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
from steuerberater_copilot.rag import (
    ContradictionDetectionResult,
    DetectedClaimPassage,
    DetectedContradictionPair,
    SourceDocument,
)

EXPECTED_BASELINE_EVALUATION_IDS = (
    "EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_VALUES",
    "EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_AFFIRM_NEGATION",
    "EVAL_RAG_CONTRADICTION_BASELINE_SUBJECT_SCOPE",
    "EVAL_RAG_CONTRADICTION_BASELINE_FILING_DEADLINES",
    "EVAL_RAG_CONTRADICTION_BASELINE_ARCHIVE_REQUIREMENT",
    "EVAL_RAG_CONTRADICTION_BASELINE_NORMALIZED_RETENTION",
    "EVAL_RAG_CONTRADICTION_BASELINE_DIFFERENT_SUBJECTS",
    "EVAL_RAG_CONTRADICTION_BASELINE_DIFFERENT_ATTRIBUTES",
    "EVAL_RAG_CONTRADICTION_BASELINE_TEMPORAL_HEDGES",
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


def test_nine_case_baseline_suite_has_exact_metrics() -> None:
    cases = build_synthetic_rag_contradiction_evaluation_case_library()

    report = run_offline_rag_contradiction_evaluation_suite(cases)

    assert report.total_case_count == 9
    assert tuple(
        assessment.evaluation_run_result.evaluation_case.evaluation_id
        for assessment in report.assessments
    ) == EXPECTED_BASELINE_EVALUATION_IDS
    assert report.passed_case_count == 9
    assert report.failed_case_count == 0
    assert report.pass_rate == 1.0
    assert report.failed_evaluation_ids == ()
    assert report.expected_contradiction_case_count == 5
    assert report.contradiction_detection_rate == 1.0
    assert report.false_negative_case_count == 0
    assert report.false_positive_case_count == 0


def test_suite_preserves_case_order_and_identities() -> None:
    cases = build_synthetic_rag_contradiction_evaluation_case_library()

    report = run_offline_rag_contradiction_evaluation_suite(cases)

    assert len(report.assessments) == len(cases)
    for case, assessment in zip(cases, report.assessments, strict=True):
        assert assessment.evaluation_run_result.evaluation_case is case
        assert isinstance(assessment, RAGContradictionEvaluationCaseAssessment)


def test_negative_controls_do_not_inflate_detection_rate_denominator() -> None:
    report = RAGContradictionEvaluationMetricsReport(
        assessments=(
            _assessment(
                evaluation_id="EVAL_CONTRADICTION_EXPECTED",
                expected=True,
                observed=True,
            ),
            _assessment(
                evaluation_id="EVAL_CONTRADICTION_CONTROL_A",
                expected=False,
                observed=False,
            ),
            _assessment(
                evaluation_id="EVAL_CONTRADICTION_CONTROL_B",
                expected=False,
                observed=False,
            ),
        )
    )

    assert report.total_case_count == 3
    assert report.expected_contradiction_case_count == 1
    assert report.contradiction_detection_rate == 1.0
    assert report.pass_rate == 1.0


def test_false_negative_is_counted_separately_from_false_positive() -> None:
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
    assert report.false_negative_case_count == 1
    assert report.false_positive_case_count == 1


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
            ),
        )
    )

    assert report.total_case_count == 2
    assert report.expected_contradiction_case_count == 0
    assert report.contradiction_detection_rate is None
    assert report.false_negative_case_count == 0
    assert report.false_positive_case_count == 1
    assert report.pass_rate == 0.5


def test_wrong_evidence_fails_without_becoming_bool_false_negative() -> None:
    report = RAGContradictionEvaluationMetricsReport(
        assessments=(
            _assessment(
                evaluation_id="EVAL_CONTRADICTION_WRONG_EVIDENCE",
                expected=True,
                observed=True,
                evidence_matches=False,
            ),
        )
    )

    assert report.passed_case_count == 0
    assert report.failed_case_count == 1
    assert report.failed_evaluation_ids == ("EVAL_CONTRADICTION_WRONG_EVIDENCE",)
    assert report.expected_contradiction_case_count == 1
    assert report.contradiction_detection_rate == 1.0
    assert report.false_negative_case_count == 0
    assert report.false_positive_case_count == 0


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
    assert evaluation.RAGContradictionEvaluationMetricsReport is (
        report_module.RAGContradictionEvaluationMetricsReport
    )
    assert "RAGContradictionEvaluationMetricsReport" in evaluation.__all__
    assert "run_offline_rag_contradiction_evaluation_suite" in evaluation.__all__


def _assessment(
    *,
    evaluation_id: str = "EVAL_CONTRADICTION_REPORT_TEST",
    expected: bool,
    observed: bool,
    evidence_matches: bool = True,
) -> RAGContradictionEvaluationCaseAssessment:
    first_passage = "The retention period is 10 years."
    second_passage = "The retention period is 7 years."
    source_documents = (
        SourceDocument(
            document_id="SYNTHETIC_CONTRADICTION_REPORT_TEN",
            title="Synthetic contradiction report reference ten",
            content=f"Synthetic report context alpha. {first_passage}",
        ),
        SourceDocument(
            document_id="SYNTHETIC_CONTRADICTION_REPORT_SEVEN",
            title="Synthetic contradiction report reference seven",
            content=f"Synthetic report context beta. {second_passage}",
        ),
    )
    contradicting_passages: tuple[ContradictionEvidenceLabel, ...] = ()
    if expected:
        contradicting_passages = (
            ContradictionEvidenceLabel(
                document_id=source_documents[0].document_id,
                supporting_text=first_passage,
            ),
            ContradictionEvidenceLabel(
                document_id=source_documents[1].document_id,
                supporting_text=second_passage,
            ),
        )
    evaluation_case = RAGContradictionEvaluationCase(
        evaluation_id=evaluation_id,
        source_documents=source_documents,
        expected_contradiction_present=expected,
        contradicting_passages=contradicting_passages,
    )
    detection_result = ContradictionDetectionResult(
        contradiction_present=observed,
        contradictions=(
            _contradiction_pair(evidence_matches=evidence_matches),
        )
        if observed
        else (),
    )
    result = RAGContradictionEvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_detection_result=detection_result,
    )
    return assess_rag_contradiction_evaluation_run_result(result)


def _contradiction_pair(
    *,
    evidence_matches: bool,
) -> DetectedContradictionPair:
    first_supporting_text = (
        "The retention period is 10 years."
        if evidence_matches
        else "Synthetic wrong observed passage for ten years."
    )
    second_supporting_text = (
        "The retention period is 7 years."
        if evidence_matches
        else "Synthetic wrong observed passage for seven years."
    )
    return DetectedContradictionPair(
        claim_key="retention_years",
        first=DetectedClaimPassage(
            document_id="SYNTHETIC_CONTRADICTION_REPORT_TEN",
            supporting_text=first_supporting_text,
            claim_key="retention_years",
            claim_value="10",
        ),
        second=DetectedClaimPassage(
            document_id="SYNTHETIC_CONTRADICTION_REPORT_SEVEN",
            supporting_text=second_supporting_text,
            claim_key="retention_years",
            claim_value="7",
        ),
    )
