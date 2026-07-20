"""Deterministic aggregate Recall@k metrics for synthetic retrieval evaluation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .retrieval_assessment import (
    RetrievalEvaluationCaseAssessment,
    assess_retrieval_evaluation_run_result,
)
from .retrieval_case import RetrievalEvaluationCase
from .retrieval_runner import run_offline_retrieval_evaluation_case


@dataclass(frozen=True, slots=True)
class RetrievalEvaluationMetricsReport:
    """Traceable aggregate Recall@k metrics from ordered retrieval assessments.

    ``mean_recall_at_k`` is the unweighted arithmetic mean over assessments with
    applicable Recall@k only. A Recall of ``0.0`` is included. Empty relevance
    labels make Recall inapplicable and are excluded from the mean. This report
    does not evaluate pass/fail thresholds or abstention.
    """

    assessments: tuple[RetrievalEvaluationCaseAssessment, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "assessments", tuple(self.assessments))
        if not self.assessments:
            raise ValueError("assessments must not be empty.")

    @property
    def total_case_count(self) -> int:
        return len(self.assessments)

    @property
    def applicable_recall_case_count(self) -> int:
        return sum(
            1 for assessment in self.assessments if assessment.recall_at_k is not None
        )

    @property
    def inapplicable_recall_case_count(self) -> int:
        return self.total_case_count - self.applicable_recall_case_count

    @property
    def mean_recall_at_k(self) -> float | None:
        applicable_recalls = tuple(
            assessment.recall_at_k
            for assessment in self.assessments
            if assessment.recall_at_k is not None
        )
        if not applicable_recalls:
            return None
        return sum(applicable_recalls) / len(applicable_recalls)


def run_offline_retrieval_evaluation_suite(
    evaluation_cases: Sequence[RetrievalEvaluationCase],
) -> RetrievalEvaluationMetricsReport:
    """Run and assess every retrieval case in input order without providers."""
    assessments = []
    for evaluation_case in evaluation_cases:
        result = run_offline_retrieval_evaluation_case(evaluation_case)
        assessments.append(assess_retrieval_evaluation_run_result(result))

    return RetrievalEvaluationMetricsReport(assessments=tuple(assessments))
