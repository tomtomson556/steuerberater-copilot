from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
import steuerberater_copilot.evaluation.grounding_report as grounding_report_module
from steuerberater_copilot.evaluation import (
    EvaluationMetricsReport,
    GroundingEvaluationCase,
    GroundingEvaluationCaseAssessment,
    GroundingEvaluationMetricsReport,
    GroundingEvidenceLabel,
    RetrievalEvaluationMetricsReport,
    assess_grounding_evaluation_case,
    build_synthetic_evaluation_case_library,
    build_synthetic_grounding_evaluation_case_library,
    build_synthetic_retrieval_evaluation_case_library,
    run_offline_evaluation_suite,
    run_offline_grounding_evaluation_suite,
    run_offline_retrieval_evaluation_suite,
)
from steuerberater_copilot.offline_mvp import (
    GroundedDraft,
    StructuredDraftOutput,
)
from steuerberater_copilot.rag import SourceDocument

EXPECTED_BASELINE_RATES = (
    (1.0, 1.0, 1.0, 0.0),
    (0.5, 1.0, 1.0, 0.5),
    (1.0, 1.0, 0.0, 1.0),
    (1.0, 0.0, 0.0, 1.0),
    (0.0, None, None, 1.0),
    (1.0, 0.0, 0.0, 1.0),
    (1.0, 1.0, 1.0, 0.0),
    (1.0, 2 / 3, 1 / 3, 0.5),
    (None, None, None, None),
)


def test_grounding_metrics_report_is_immutable_and_uses_slots() -> None:
    assessment = assess_grounding_evaluation_case(_empty_draft_case())
    report = GroundingEvaluationMetricsReport(assessments=[assessment])

    with pytest.raises(FrozenInstanceError):
        report.assessments = ()

    assert report.assessments == (assessment,)
    assert report.assessments[0] is assessment
    assert not hasattr(report, "__dict__")
    assert GroundingEvaluationMetricsReport.__slots__ == ("assessments",)


def test_report_converts_sequence_to_tuple_and_preserves_identities() -> None:
    first = assess_grounding_evaluation_case(
        _empty_draft_case(evaluation_id="EVAL_GROUNDING_REPORT_FIRST")
    )
    second = assess_grounding_evaluation_case(
        _empty_draft_case(evaluation_id="EVAL_GROUNDING_REPORT_SECOND")
    )

    report = GroundingEvaluationMetricsReport(assessments=[first, second])

    assert isinstance(report.assessments, tuple)
    assert report.assessments == (first, second)
    assert report.assessments[0] is first
    assert report.assessments[1] is second


def test_empty_report_and_empty_suite_are_rejected() -> None:
    with pytest.raises(ValueError, match=r"^assessments must not be empty\.$"):
        GroundingEvaluationMetricsReport(assessments=())

    with pytest.raises(ValueError, match=r"^assessments must not be empty\.$"):
        run_offline_grounding_evaluation_suite(())


def test_baseline_suite_has_exact_metrics() -> None:
    cases = build_synthetic_grounding_evaluation_case_library()

    report = run_offline_grounding_evaluation_suite(cases)

    assert report.total_case_count == 9
    assert report.applicable_citation_coverage_case_count == 8
    assert report.inapplicable_citation_coverage_case_count == 1
    assert report.applicable_source_match_case_count == 7
    assert report.inapplicable_source_match_case_count == 2
    assert report.applicable_passage_match_case_count == 7
    assert report.inapplicable_passage_match_case_count == 2
    assert report.applicable_unsupported_summary_point_case_count == 8
    assert report.inapplicable_unsupported_summary_point_case_count == 1
    assert tuple(
        (
            assessment.citation_coverage,
            assessment.source_match_rate,
            assessment.passage_match_rate,
            assessment.unsupported_summary_point_rate,
        )
        for assessment in report.assessments
    ) == EXPECTED_BASELINE_RATES
    assert report.mean_citation_coverage == 6.5 / 8
    assert report.mean_source_match_rate == (14 / 3) / 7
    assert report.mean_passage_match_rate == (10 / 3) / 7
    assert report.mean_unsupported_summary_point_rate == 5.0 / 8
    assert not hasattr(report, "passed")
    assert not hasattr(report, "pass_rate")
    assert not hasattr(report, "abstained")
    assert not hasattr(report, "abstention")


def test_suite_preserves_case_order_and_identities() -> None:
    cases = build_synthetic_grounding_evaluation_case_library()

    report = run_offline_grounding_evaluation_suite(cases)

    assert len(report.assessments) == len(cases)
    for case, assessment in zip(cases, report.assessments, strict=True):
        assert assessment.evaluation_case is case
        assert isinstance(assessment, GroundingEvaluationCaseAssessment)


def test_zero_rates_are_included_in_applicable_counts_and_means() -> None:
    report = run_offline_grounding_evaluation_suite(
        (
            _missing_citations_case(
                evaluation_id="EVAL_GROUNDING_REPORT_ZERO_ONLY"
            ),
        )
    )

    assert report.total_case_count == 1
    assert report.assessments[0].citation_coverage == 0.0
    assert report.assessments[0].unsupported_summary_point_rate == 1.0
    assert report.assessments[0].source_match_rate is None
    assert report.assessments[0].passage_match_rate is None
    assert report.applicable_citation_coverage_case_count == 1
    assert report.mean_citation_coverage == 0.0
    assert report.mean_unsupported_summary_point_rate == 1.0
    assert report.mean_source_match_rate is None
    assert report.mean_passage_match_rate is None


def test_suite_with_only_inapplicable_rates_has_no_means() -> None:
    report = run_offline_grounding_evaluation_suite(
        (
            _empty_draft_case(evaluation_id="EVAL_GROUNDING_REPORT_EMPTY_A"),
            _empty_draft_case(evaluation_id="EVAL_GROUNDING_REPORT_EMPTY_B"),
        )
    )

    assert report.total_case_count == 2
    assert report.applicable_citation_coverage_case_count == 0
    assert report.applicable_source_match_case_count == 0
    assert report.applicable_passage_match_case_count == 0
    assert report.applicable_unsupported_summary_point_case_count == 0
    assert report.inapplicable_citation_coverage_case_count == 2
    assert report.inapplicable_source_match_case_count == 2
    assert report.inapplicable_passage_match_case_count == 2
    assert report.inapplicable_unsupported_summary_point_case_count == 2
    assert report.mean_citation_coverage is None
    assert report.mean_source_match_rate is None
    assert report.mean_passage_match_rate is None
    assert report.mean_unsupported_summary_point_rate is None


def test_none_rates_are_excluded_from_means_while_zero_is_kept() -> None:
    report = run_offline_grounding_evaluation_suite(
        (
            _missing_citations_case(
                evaluation_id="EVAL_GROUNDING_REPORT_ZERO_AND_NONE"
            ),
            _empty_draft_case(evaluation_id="EVAL_GROUNDING_REPORT_NONE_ONLY"),
        )
    )

    assert report.total_case_count == 2
    assert report.applicable_citation_coverage_case_count == 1
    assert report.inapplicable_citation_coverage_case_count == 1
    assert report.mean_citation_coverage == 0.0
    assert report.mean_unsupported_summary_point_rate == 1.0
    assert report.mean_source_match_rate is None
    assert report.mean_passage_match_rate is None


def test_suite_propagates_unexpected_assessment_exception(monkeypatch) -> None:
    unexpected_error = RuntimeError("Synthetic unexpected grounding suite failure.")

    def fail_assessment(*args, **kwargs):
        raise unexpected_error

    monkeypatch.setattr(
        grounding_report_module,
        "assess_grounding_evaluation_case",
        fail_assessment,
    )

    with pytest.raises(RuntimeError) as exc_info:
        run_offline_grounding_evaluation_suite(
            build_synthetic_grounding_evaluation_case_library()[:1]
        )

    assert exc_info.value is unexpected_error


def test_evaluation_package_exports_grounding_metrics_report_contract() -> None:
    assert (
        evaluation.GroundingEvaluationMetricsReport
        is GroundingEvaluationMetricsReport
    )
    assert (
        evaluation.run_offline_grounding_evaluation_suite
        is run_offline_grounding_evaluation_suite
    )
    assert evaluation.GroundingEvaluationMetricsReport is (
        grounding_report_module.GroundingEvaluationMetricsReport
    )
    assert "GroundingEvaluationMetricsReport" in evaluation.__all__
    assert "run_offline_grounding_evaluation_suite" in evaluation.__all__


def test_existing_ai_and_retrieval_metrics_reports_remain_unchanged() -> None:
    ai_report = run_offline_evaluation_suite(build_synthetic_evaluation_case_library())
    retrieval_report = run_offline_retrieval_evaluation_suite(
        build_synthetic_retrieval_evaluation_case_library()
    )

    assert evaluation.EvaluationMetricsReport is EvaluationMetricsReport
    assert evaluation.RetrievalEvaluationMetricsReport is (
        RetrievalEvaluationMetricsReport
    )
    assert ai_report.total_case_count == 7
    assert ai_report.passed_case_count == 7
    assert ai_report.pass_rate == 1.0
    assert retrieval_report.total_case_count == 4
    assert retrieval_report.mean_recall_at_k == 0.5


def _empty_draft_case(
    *,
    evaluation_id: str = "EVAL_GROUNDING_REPORT_EMPTY",
) -> GroundingEvaluationCase:
    return GroundingEvaluationCase(
        evaluation_id=evaluation_id,
        source_documents=(),
        candidate_grounded_draft=GroundedDraft(
            structured_draft=StructuredDraftOutput(
                summary_points=(),
                uncertainties=(),
                review_questions=(),
            ),
            citations=(),
        ),
        acceptable_evidence=(),
    )


def _missing_citations_case(
    *,
    evaluation_id: str = "EVAL_GROUNDING_REPORT_MISSING",
) -> GroundingEvaluationCase:
    document = SourceDocument(
        document_id="SYNTHETIC_GROUNDING_REPORT_DOC",
        title="Synthetic orchard reference",
        content="Synthetic orchard passage for report testing.",
    )
    return GroundingEvaluationCase(
        evaluation_id=evaluation_id,
        source_documents=(document,),
        candidate_grounded_draft=GroundedDraft(
            structured_draft=StructuredDraftOutput(
                summary_points=("Synthetic unsupported orchard summary point.",),
                uncertainties=("Synthetic uncertainty.",),
                review_questions=("Synthetic review question?",),
            ),
            citations=(),
        ),
        acceptable_evidence=(
            GroundingEvidenceLabel(
                summary_point_index=0,
                document_id="SYNTHETIC_GROUNDING_REPORT_DOC",
                supporting_text="Synthetic orchard passage for report testing.",
            ),
        ),
    )
