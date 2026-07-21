from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.evaluation import (
    GroundingEvaluationCase,
    GroundingEvaluationCaseAssessment,
    GroundingEvidenceLabel,
    assess_grounding_evaluation_case,
)
from steuerberater_copilot.offline_mvp import (
    GroundedDraft,
    GroundedDraftCitation,
    StructuredDraftOutput,
)
from steuerberater_copilot.rag import SourceDocument


def test_grounding_assessment_is_immutable_and_uses_slots() -> None:
    assessment = assess_grounding_evaluation_case(_fully_correct_case())

    with pytest.raises(FrozenInstanceError):
        assessment.evaluation_case = _fully_correct_case()

    assert not hasattr(assessment, "__dict__")
    assert GroundingEvaluationCaseAssessment.__slots__ == ("evaluation_case",)


def test_assessment_function_keeps_exact_case_instance() -> None:
    evaluation_case = _fully_correct_case()

    assessment = assess_grounding_evaluation_case(evaluation_case)

    assert isinstance(assessment, GroundingEvaluationCaseAssessment)
    assert assessment.evaluation_case is evaluation_case


def test_fully_correct_source_and_passage_matches() -> None:
    assessment = assess_grounding_evaluation_case(_fully_correct_case())

    assert assessment.citation_covered_summary_point_indices == (0, 1)
    assert assessment.source_matched_citation_indices == (0, 1)
    assert assessment.passage_matched_citation_indices == (0, 1)
    assert assessment.unsupported_summary_point_indices == ()
    assert assessment.citation_coverage == 1.0
    assert assessment.source_match_rate == 1.0
    assert assessment.passage_match_rate == 1.0
    assert assessment.unsupported_summary_point_rate == 0.0


def test_correct_source_with_wrong_passage_is_source_match_only() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content=(
                "Synthetic correct orchard passage. "
                "Synthetic other orchard passage."
            ),
        ),
    )
    evaluation_case = GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_WRONG_PASSAGE",
        source_documents=documents,
        candidate_grounded_draft=_grounded_draft(
            summary_points=("Synthetic orchard summary.",),
            citations=(
                _candidate_citation(
                    document_id="SYNTHETIC_SOURCE_001",
                    supporting_text="Synthetic other orchard passage.",
                ),
            ),
        ),
        acceptable_evidence=(
            _label(supporting_text="Synthetic correct orchard passage."),
        ),
    )

    assessment = assess_grounding_evaluation_case(evaluation_case)

    assert assessment.source_matched_citation_indices == (0,)
    assert assessment.passage_matched_citation_indices == ()
    assert assessment.citation_covered_summary_point_indices == (0,)
    assert assessment.unsupported_summary_point_indices == (0,)
    assert assessment.source_match_rate == 1.0
    assert assessment.passage_match_rate == 0.0
    assert assessment.unsupported_summary_point_rate == 1.0


def test_wrong_source_with_identical_text_is_not_a_match() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content="Synthetic shared orchard passage.",
        ),
        _document(
            "SYNTHETIC_SOURCE_002",
            content="Synthetic shared orchard passage.",
        ),
    )
    evaluation_case = GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_WRONG_SOURCE",
        source_documents=documents,
        candidate_grounded_draft=_grounded_draft(
            summary_points=("Synthetic orchard summary.",),
            citations=(
                _candidate_citation(
                    document_id="SYNTHETIC_SOURCE_002",
                    supporting_text="Synthetic shared orchard passage.",
                ),
            ),
        ),
        acceptable_evidence=(
            _label(
                document_id="SYNTHETIC_SOURCE_001",
                supporting_text="Synthetic shared orchard passage.",
            ),
        ),
    )

    assessment = assess_grounding_evaluation_case(evaluation_case)

    assert assessment.source_matched_citation_indices == ()
    assert assessment.passage_matched_citation_indices == ()
    assert assessment.citation_covered_summary_point_indices == (0,)
    assert assessment.unsupported_summary_point_indices == (0,)
    assert assessment.source_match_rate == 0.0
    assert assessment.passage_match_rate == 0.0


def test_completely_missing_citations_leave_all_summary_points_unsupported() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content="Synthetic orchard passage.",
        ),
    )
    evaluation_case = GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_MISSING_CITATIONS",
        source_documents=documents,
        candidate_grounded_draft=_grounded_draft(
            summary_points=(
                "Synthetic first summary point.",
                "Synthetic second summary point.",
            ),
            citations=(),
        ),
        acceptable_evidence=(
            _label(summary_point_index=0),
            _label(summary_point_index=1),
        ),
    )

    assessment = assess_grounding_evaluation_case(evaluation_case)

    assert assessment.citation_covered_summary_point_indices == ()
    assert assessment.source_matched_citation_indices == ()
    assert assessment.passage_matched_citation_indices == ()
    assert assessment.unsupported_summary_point_indices == (0, 1)
    assert assessment.citation_coverage == 0.0
    assert assessment.source_match_rate is None
    assert assessment.passage_match_rate is None
    assert assessment.unsupported_summary_point_rate == 1.0


def test_partial_citation_coverage() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content="Synthetic alpha orchard passage. Synthetic beta orchard passage.",
        ),
    )
    evaluation_case = GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_PARTIAL_COVERAGE",
        source_documents=documents,
        candidate_grounded_draft=_grounded_draft(
            summary_points=(
                "Synthetic covered summary point.",
                "Synthetic uncovered summary point.",
            ),
            citations=(
                _candidate_citation(
                    summary_point_index=0,
                    supporting_text="Synthetic alpha orchard passage.",
                ),
            ),
        ),
        acceptable_evidence=(
            _label(
                summary_point_index=0,
                supporting_text="Synthetic alpha orchard passage.",
            ),
            _label(
                summary_point_index=1,
                supporting_text="Synthetic beta orchard passage.",
            ),
        ),
    )

    assessment = assess_grounding_evaluation_case(evaluation_case)

    assert assessment.citation_covered_summary_point_indices == (0,)
    assert assessment.unsupported_summary_point_indices == (1,)
    assert assessment.citation_coverage == 0.5
    assert assessment.unsupported_summary_point_rate == 0.5


def test_citation_present_without_acceptable_evidence_is_unsupported() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content="Synthetic orchard passage.",
        ),
    )
    evaluation_case = GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_NO_ACCEPTABLE_EVIDENCE_FOR_POINT",
        source_documents=documents,
        candidate_grounded_draft=_grounded_draft(
            summary_points=(
                "Synthetic first summary point.",
                "Synthetic second summary point.",
            ),
            citations=(
                _candidate_citation(
                    summary_point_index=1,
                    supporting_text="Synthetic orchard passage.",
                ),
            ),
        ),
        acceptable_evidence=(
            _label(summary_point_index=0, supporting_text="Synthetic orchard passage."),
        ),
    )

    assessment = assess_grounding_evaluation_case(evaluation_case)

    assert assessment.citation_covered_summary_point_indices == (1,)
    assert assessment.source_matched_citation_indices == ()
    assert assessment.passage_matched_citation_indices == ()
    assert assessment.unsupported_summary_point_indices == (0, 1)
    assert assessment.unsupported_summary_point_rate == 1.0


def test_alternative_acceptable_evidence_labels_are_sufficient() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content="Synthetic orchard passage alpha.",
        ),
        _document(
            "SYNTHETIC_SOURCE_002",
            content="Synthetic orchard passage beta.",
        ),
    )
    evaluation_case = GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_ALTERNATIVE_LABEL",
        source_documents=documents,
        candidate_grounded_draft=_grounded_draft(
            summary_points=("Synthetic orchard summary.",),
            citations=(
                _candidate_citation(
                    document_id="SYNTHETIC_SOURCE_002",
                    supporting_text="Synthetic orchard passage beta.",
                ),
            ),
        ),
        acceptable_evidence=(
            _label(
                document_id="SYNTHETIC_SOURCE_001",
                supporting_text="Synthetic orchard passage alpha.",
            ),
            _label(
                document_id="SYNTHETIC_SOURCE_002",
                supporting_text="Synthetic orchard passage beta.",
            ),
        ),
    )

    assessment = assess_grounding_evaluation_case(evaluation_case)

    assert assessment.source_matched_citation_indices == (0,)
    assert assessment.passage_matched_citation_indices == (0,)
    assert assessment.unsupported_summary_point_indices == ()
    assert assessment.passage_match_rate == 1.0
    assert assessment.unsupported_summary_point_rate == 0.0


def test_multiple_citations_per_summary_point_are_assessed_individually() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content=(
                "Synthetic first orchard passage. "
                "Synthetic second orchard passage."
            ),
        ),
    )
    evaluation_case = GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_MULTIPLE_CITATIONS",
        source_documents=documents,
        candidate_grounded_draft=_grounded_draft(
            summary_points=("Synthetic orchard summary.",),
            citations=(
                _candidate_citation(
                    supporting_text="Synthetic first orchard passage.",
                ),
                _candidate_citation(
                    supporting_text="Synthetic second orchard passage.",
                ),
            ),
        ),
        acceptable_evidence=(
            _label(supporting_text="Synthetic first orchard passage."),
            _label(supporting_text="Synthetic second orchard passage."),
        ),
    )

    assessment = assess_grounding_evaluation_case(evaluation_case)

    assert assessment.source_matched_citation_indices == (0, 1)
    assert assessment.passage_matched_citation_indices == (0, 1)
    assert assessment.citation_covered_summary_point_indices == (0,)
    assert assessment.unsupported_summary_point_indices == ()
    assert assessment.source_match_rate == 1.0
    assert assessment.passage_match_rate == 1.0


def test_mix_of_correct_and_incorrect_citations() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content=(
                "Synthetic correct orchard passage. "
                "Synthetic wrong orchard passage."
            ),
        ),
        _document(
            "SYNTHETIC_SOURCE_002",
            content="Synthetic other document passage.",
        ),
    )
    evaluation_case = GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_MIXED_CITATIONS",
        source_documents=documents,
        candidate_grounded_draft=_grounded_draft(
            summary_points=(
                "Synthetic first summary point.",
                "Synthetic second summary point.",
            ),
            citations=(
                _candidate_citation(
                    summary_point_index=0,
                    document_id="SYNTHETIC_SOURCE_001",
                    supporting_text="Synthetic correct orchard passage.",
                ),
                _candidate_citation(
                    summary_point_index=1,
                    document_id="SYNTHETIC_SOURCE_002",
                    supporting_text="Synthetic other document passage.",
                ),
            ),
        ),
        acceptable_evidence=(
            _label(
                summary_point_index=0,
                document_id="SYNTHETIC_SOURCE_001",
                supporting_text="Synthetic correct orchard passage.",
            ),
            _label(
                summary_point_index=1,
                document_id="SYNTHETIC_SOURCE_001",
                supporting_text="Synthetic wrong orchard passage.",
            ),
        ),
    )

    assessment = assess_grounding_evaluation_case(evaluation_case)

    assert assessment.source_matched_citation_indices == (0,)
    assert assessment.passage_matched_citation_indices == (0,)
    assert assessment.citation_covered_summary_point_indices == (0, 1)
    assert assessment.unsupported_summary_point_indices == (1,)
    assert assessment.source_match_rate == 0.5
    assert assessment.passage_match_rate == 0.5
    assert assessment.unsupported_summary_point_rate == 0.5


def test_correct_citation_plus_additional_incorrect_citation() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content="Synthetic correct orchard passage.",
        ),
        _document(
            "SYNTHETIC_SOURCE_002",
            content="Synthetic incorrect orchard passage.",
        ),
    )
    evaluation_case = GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_CORRECT_PLUS_INCORRECT",
        source_documents=documents,
        candidate_grounded_draft=_grounded_draft(
            summary_points=("Synthetic orchard summary.",),
            citations=(
                _candidate_citation(
                    document_id="SYNTHETIC_SOURCE_001",
                    supporting_text="Synthetic correct orchard passage.",
                ),
                _candidate_citation(
                    document_id="SYNTHETIC_SOURCE_002",
                    supporting_text="Synthetic incorrect orchard passage.",
                ),
            ),
        ),
        acceptable_evidence=(
            _label(
                document_id="SYNTHETIC_SOURCE_001",
                supporting_text="Synthetic correct orchard passage.",
            ),
        ),
    )

    assessment = assess_grounding_evaluation_case(evaluation_case)

    assert assessment.source_matched_citation_indices == (0,)
    assert assessment.passage_matched_citation_indices == (0,)
    assert assessment.citation_covered_summary_point_indices == (0,)
    assert assessment.unsupported_summary_point_indices == ()
    assert assessment.source_match_rate == 0.5
    assert assessment.passage_match_rate == 0.5
    assert assessment.unsupported_summary_point_rate == 0.0


def test_empty_acceptable_evidence_marks_all_summary_points_unsupported() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content="Synthetic orchard passage.",
        ),
    )
    evaluation_case = GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_EMPTY_EVIDENCE",
        source_documents=documents,
        candidate_grounded_draft=_grounded_draft(
            summary_points=("Synthetic unsupported summary point.",),
            citations=(
                _candidate_citation(supporting_text="Synthetic orchard passage."),
            ),
        ),
        acceptable_evidence=(),
    )

    assessment = assess_grounding_evaluation_case(evaluation_case)

    assert assessment.citation_covered_summary_point_indices == (0,)
    assert assessment.source_matched_citation_indices == ()
    assert assessment.passage_matched_citation_indices == ()
    assert assessment.unsupported_summary_point_indices == (0,)
    assert assessment.citation_coverage == 1.0
    assert assessment.source_match_rate == 0.0
    assert assessment.passage_match_rate == 0.0
    assert assessment.unsupported_summary_point_rate == 1.0


def test_empty_grounded_draft_without_summary_points() -> None:
    evaluation_case = GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_EMPTY_DRAFT",
        source_documents=(),
        candidate_grounded_draft=_grounded_draft(summary_points=(), citations=()),
        acceptable_evidence=(),
    )

    assessment = assess_grounding_evaluation_case(evaluation_case)

    assert assessment.citation_covered_summary_point_indices == ()
    assert assessment.source_matched_citation_indices == ()
    assert assessment.passage_matched_citation_indices == ()
    assert assessment.unsupported_summary_point_indices == ()
    assert assessment.citation_coverage is None
    assert assessment.source_match_rate is None
    assert assessment.passage_match_rate is None
    assert assessment.unsupported_summary_point_rate is None


def test_result_indices_are_deterministic() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content=(
                "Synthetic alpha orchard passage. "
                "Synthetic beta orchard passage. "
                "Synthetic gamma orchard passage."
            ),
        ),
        _document(
            "SYNTHETIC_SOURCE_002",
            content="Synthetic delta orchard passage.",
        ),
    )
    evaluation_case = GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_INDEX_ORDER",
        source_documents=documents,
        candidate_grounded_draft=_grounded_draft(
            summary_points=(
                "Synthetic first summary point.",
                "Synthetic second summary point.",
                "Synthetic third summary point.",
            ),
            citations=(
                _candidate_citation(
                    summary_point_index=2,
                    document_id="SYNTHETIC_SOURCE_001",
                    supporting_text="Synthetic gamma orchard passage.",
                ),
                _candidate_citation(
                    summary_point_index=0,
                    document_id="SYNTHETIC_SOURCE_002",
                    supporting_text="Synthetic delta orchard passage.",
                ),
                _candidate_citation(
                    summary_point_index=2,
                    document_id="SYNTHETIC_SOURCE_001",
                    supporting_text="Synthetic beta orchard passage.",
                ),
                _candidate_citation(
                    summary_point_index=0,
                    document_id="SYNTHETIC_SOURCE_001",
                    supporting_text="Synthetic alpha orchard passage.",
                ),
            ),
        ),
        acceptable_evidence=(
            _label(
                summary_point_index=0,
                document_id="SYNTHETIC_SOURCE_001",
                supporting_text="Synthetic alpha orchard passage.",
            ),
            _label(
                summary_point_index=2,
                document_id="SYNTHETIC_SOURCE_001",
                supporting_text="Synthetic gamma orchard passage.",
            ),
        ),
    )

    assessment = assess_grounding_evaluation_case(evaluation_case)

    assert assessment.citation_covered_summary_point_indices == (0, 2)
    assert assessment.source_matched_citation_indices == (0, 2, 3)
    assert assessment.passage_matched_citation_indices == (0, 3)
    assert assessment.unsupported_summary_point_indices == (1,)


def test_duplicate_observed_citations_are_assessed_individually() -> None:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content="Synthetic orchard passage.",
        ),
    )
    duplicate_citation = _candidate_citation(
        supporting_text="Synthetic orchard passage.",
    )
    evaluation_case = GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_DUPLICATE_CITATIONS",
        source_documents=documents,
        candidate_grounded_draft=_grounded_draft(
            summary_points=("Synthetic orchard summary.",),
            citations=(duplicate_citation, duplicate_citation),
        ),
        acceptable_evidence=(
            _label(supporting_text="Synthetic orchard passage."),
        ),
    )

    assessment = assess_grounding_evaluation_case(evaluation_case)

    assert assessment.source_matched_citation_indices == (0, 1)
    assert assessment.passage_matched_citation_indices == (0, 1)
    assert assessment.source_match_rate == 1.0
    assert assessment.passage_match_rate == 1.0


def test_evaluation_package_exports_grounding_assessment_contract() -> None:
    assert (
        evaluation.GroundingEvaluationCaseAssessment
        is GroundingEvaluationCaseAssessment
    )
    assert (
        evaluation.assess_grounding_evaluation_case is assess_grounding_evaluation_case
    )
    assert "GroundingEvaluationCaseAssessment" in evaluation.__all__
    assert "assess_grounding_evaluation_case" in evaluation.__all__
    assert "GroundingEvaluationCase" in evaluation.__all__
    assert "GroundingEvidenceLabel" in evaluation.__all__


def test_assessment_has_no_pass_fail_thresholds_or_abstention() -> None:
    assessment = assess_grounding_evaluation_case(_fully_correct_case())

    assert not hasattr(assessment, "passed")
    assert not hasattr(assessment, "threshold")
    assert not hasattr(assessment, "thresholds")
    assert not hasattr(assessment, "abstained")
    assert not hasattr(assessment, "abstention")


def _fully_correct_case() -> GroundingEvaluationCase:
    documents = (
        _document(
            "SYNTHETIC_SOURCE_001",
            content="Synthetic alpha orchard passage.",
        ),
        _document(
            "SYNTHETIC_SOURCE_002",
            content="Synthetic beta orchard passage.",
        ),
    )
    return GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_FULLY_CORRECT",
        source_documents=documents,
        candidate_grounded_draft=_grounded_draft(
            summary_points=(
                "Synthetic first summary point.",
                "Synthetic second summary point.",
            ),
            citations=(
                _candidate_citation(
                    summary_point_index=0,
                    document_id="SYNTHETIC_SOURCE_001",
                    supporting_text="Synthetic alpha orchard passage.",
                ),
                _candidate_citation(
                    summary_point_index=1,
                    document_id="SYNTHETIC_SOURCE_002",
                    supporting_text="Synthetic beta orchard passage.",
                ),
            ),
        ),
        acceptable_evidence=(
            _label(
                summary_point_index=0,
                document_id="SYNTHETIC_SOURCE_001",
                supporting_text="Synthetic alpha orchard passage.",
            ),
            _label(
                summary_point_index=1,
                document_id="SYNTHETIC_SOURCE_002",
                supporting_text="Synthetic beta orchard passage.",
            ),
        ),
    )


def _grounded_draft(
    *,
    summary_points: tuple[str, ...] = ("Synthetic summary point.",),
    citations: tuple[GroundedDraftCitation, ...] = (),
) -> GroundedDraft:
    return GroundedDraft(
        structured_draft=StructuredDraftOutput(
            summary_points=summary_points,
            uncertainties=("Synthetic uncertainty.",) if summary_points else (),
            review_questions=(
                ("Synthetic review question?",) if summary_points else ()
            ),
        ),
        citations=citations,
    )


def _candidate_citation(
    *,
    summary_point_index: int = 0,
    document_id: str = "SYNTHETIC_SOURCE_001",
    supporting_text: str = "Synthetic supporting text.",
) -> GroundedDraftCitation:
    return GroundedDraftCitation(
        summary_point_index=summary_point_index,
        document_id=document_id,
        supporting_text=supporting_text,
    )


def _label(
    *,
    summary_point_index: int = 0,
    document_id: str = "SYNTHETIC_SOURCE_001",
    supporting_text: str = "Synthetic orchard passage.",
) -> GroundingEvidenceLabel:
    return GroundingEvidenceLabel(
        summary_point_index=summary_point_index,
        document_id=document_id,
        supporting_text=supporting_text,
    )


def _document(
    document_id: str,
    *,
    title: str = "Synthetic source title",
    content: str = "Synthetic orchard passage.",
) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=title,
        content=content,
    )
