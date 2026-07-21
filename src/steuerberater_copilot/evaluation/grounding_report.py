"""Deterministic aggregate grounding metrics for synthetic evaluation cases."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .grounding_assessment import (
    GroundingEvaluationCaseAssessment,
    assess_grounding_evaluation_case,
)
from .grounding_case import GroundingEvaluationCase


@dataclass(frozen=True, slots=True)
class GroundingEvaluationMetricsReport:
    """Traceable aggregate grounding metrics from ordered assessments.

    Each mean is the unweighted arithmetic mean over assessments where that
    metric is applicable. A value of ``0.0`` is included. ``None`` means the
    metric is inapplicable for that case and is excluded from the mean. This
    report does not evaluate pass/fail thresholds or abstention.
    """

    assessments: tuple[GroundingEvaluationCaseAssessment, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "assessments", tuple(self.assessments))
        if not self.assessments:
            raise ValueError("assessments must not be empty.")

    @property
    def total_case_count(self) -> int:
        return len(self.assessments)

    @property
    def applicable_citation_coverage_case_count(self) -> int:
        return _applicable_count(
            assessment.citation_coverage for assessment in self.assessments
        )

    @property
    def inapplicable_citation_coverage_case_count(self) -> int:
        return self.total_case_count - self.applicable_citation_coverage_case_count

    @property
    def mean_citation_coverage(self) -> float | None:
        return _mean_of_applicable(
            assessment.citation_coverage for assessment in self.assessments
        )

    @property
    def applicable_source_match_case_count(self) -> int:
        return _applicable_count(
            assessment.source_match_rate for assessment in self.assessments
        )

    @property
    def inapplicable_source_match_case_count(self) -> int:
        return self.total_case_count - self.applicable_source_match_case_count

    @property
    def mean_source_match_rate(self) -> float | None:
        return _mean_of_applicable(
            assessment.source_match_rate for assessment in self.assessments
        )

    @property
    def applicable_passage_match_case_count(self) -> int:
        return _applicable_count(
            assessment.passage_match_rate for assessment in self.assessments
        )

    @property
    def inapplicable_passage_match_case_count(self) -> int:
        return self.total_case_count - self.applicable_passage_match_case_count

    @property
    def mean_passage_match_rate(self) -> float | None:
        return _mean_of_applicable(
            assessment.passage_match_rate for assessment in self.assessments
        )

    @property
    def applicable_unsupported_summary_point_case_count(self) -> int:
        return _applicable_count(
            assessment.unsupported_summary_point_rate
            for assessment in self.assessments
        )

    @property
    def inapplicable_unsupported_summary_point_case_count(self) -> int:
        return (
            self.total_case_count
            - self.applicable_unsupported_summary_point_case_count
        )

    @property
    def mean_unsupported_summary_point_rate(self) -> float | None:
        return _mean_of_applicable(
            assessment.unsupported_summary_point_rate
            for assessment in self.assessments
        )


def run_offline_grounding_evaluation_suite(
    evaluation_cases: Sequence[GroundingEvaluationCase],
) -> GroundingEvaluationMetricsReport:
    """Assess every grounding case in input order without providers."""
    assessments = tuple(
        assess_grounding_evaluation_case(evaluation_case)
        for evaluation_case in evaluation_cases
    )
    return GroundingEvaluationMetricsReport(assessments=assessments)


def _applicable_count(values: Iterable[float | None]) -> int:
    return sum(1 for value in values if value is not None)


def _mean_of_applicable(values: Iterable[float | None]) -> float | None:
    applicable_values = tuple(value for value in values if value is not None)
    if not applicable_values:
        return None
    return sum(applicable_values) / len(applicable_values)
