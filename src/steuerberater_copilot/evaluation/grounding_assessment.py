"""Deterministic grounding assessment for one grounding evaluation case."""

from __future__ import annotations

from dataclasses import dataclass

from .grounding_case import GroundingEvaluationCase


@dataclass(frozen=True, slots=True)
class GroundingEvaluationCaseAssessment:
    """Exact source, passage, coverage, and unsupported metrics for one case.

    Matching uses only exact comparisons. Empty summary-point denominators make
    summary-point rates ``None``. Empty candidate-citation denominators make
    citation-based rates ``None``. This contract does not evaluate abstention or
    pass/fail thresholds.
    """

    evaluation_case: GroundingEvaluationCase

    @property
    def citation_covered_summary_point_indices(self) -> tuple[int, ...]:
        summary_point_count = len(
            self.evaluation_case.candidate_grounded_draft.structured_draft.summary_points
        )
        if summary_point_count == 0:
            return ()

        covered_indices = {
            citation.summary_point_index
            for citation in self.evaluation_case.candidate_grounded_draft.citations
        }
        return tuple(
            index for index in range(summary_point_count) if index in covered_indices
        )

    @property
    def source_matched_citation_indices(self) -> tuple[int, ...]:
        source_keys = {
            (label.summary_point_index, label.document_id)
            for label in self.evaluation_case.acceptable_evidence
        }
        return tuple(
            citation_index
            for citation_index, citation in enumerate(
                self.evaluation_case.candidate_grounded_draft.citations
            )
            if (citation.summary_point_index, citation.document_id) in source_keys
        )

    @property
    def passage_matched_citation_indices(self) -> tuple[int, ...]:
        passage_keys = {
            (label.summary_point_index, label.document_id, label.supporting_text)
            for label in self.evaluation_case.acceptable_evidence
        }
        return tuple(
            citation_index
            for citation_index, citation in enumerate(
                self.evaluation_case.candidate_grounded_draft.citations
            )
            if (
                citation.summary_point_index,
                citation.document_id,
                citation.supporting_text,
            )
            in passage_keys
        )

    @property
    def unsupported_summary_point_indices(self) -> tuple[int, ...]:
        summary_point_count = len(
            self.evaluation_case.candidate_grounded_draft.structured_draft.summary_points
        )
        if summary_point_count == 0:
            return ()

        passage_matched_summary_point_indices = {
            self.evaluation_case.candidate_grounded_draft.citations[
                citation_index
            ].summary_point_index
            for citation_index in self.passage_matched_citation_indices
        }
        return tuple(
            index
            for index in range(summary_point_count)
            if index not in passage_matched_summary_point_indices
        )

    @property
    def citation_coverage(self) -> float | None:
        summary_point_count = len(
            self.evaluation_case.candidate_grounded_draft.structured_draft.summary_points
        )
        if summary_point_count == 0:
            return None
        return len(self.citation_covered_summary_point_indices) / summary_point_count

    @property
    def source_match_rate(self) -> float | None:
        citation_count = len(self.evaluation_case.candidate_grounded_draft.citations)
        if citation_count == 0:
            return None
        return len(self.source_matched_citation_indices) / citation_count

    @property
    def passage_match_rate(self) -> float | None:
        citation_count = len(self.evaluation_case.candidate_grounded_draft.citations)
        if citation_count == 0:
            return None
        return len(self.passage_matched_citation_indices) / citation_count

    @property
    def unsupported_summary_point_rate(self) -> float | None:
        summary_point_count = len(
            self.evaluation_case.candidate_grounded_draft.structured_draft.summary_points
        )
        if summary_point_count == 0:
            return None
        return len(self.unsupported_summary_point_indices) / summary_point_count


def assess_grounding_evaluation_case(
    evaluation_case: GroundingEvaluationCase,
) -> GroundingEvaluationCaseAssessment:
    """Assess one grounding case without pass/fail thresholds."""
    return GroundingEvaluationCaseAssessment(evaluation_case=evaluation_case)
