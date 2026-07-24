"""Deterministic aggregate metrics for synthetic RAG freshness evaluation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .rag_freshness_assessment import (
    RAGFreshnessEvaluationCaseAssessment,
    assess_rag_freshness_evaluation_run_result,
)
from .rag_freshness_case import RAGFreshnessEvaluationCase
from .rag_freshness_runner import run_offline_rag_freshness_evaluation_case


@dataclass(frozen=True, slots=True)
class RAGFreshnessEvaluationMetricsReport:
    """Traceable aggregate freshness metrics from ordered assessments.

    ``pass_rate`` covers simultaneous current-without-stale retrieval.
    ``current_document_retrieval_rate`` and ``stale_document_retrieval_rate``
    are independent of pass/fail and always use all cases as denominator.

    The per-case ``stale_document_retrieval_rate`` counts a case once as soon
    as at least one labeled stale document was observed within top_k, regardless
    of how many individual stale documents were retrieved.
    """

    assessments: tuple[RAGFreshnessEvaluationCaseAssessment, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "assessments", tuple(self.assessments))
        if not self.assessments:
            raise ValueError("assessments must not be empty.")

    @property
    def total_case_count(self) -> int:
        return len(self.assessments)

    @property
    def passed_case_count(self) -> int:
        return sum(assessment.passed for assessment in self.assessments)

    @property
    def failed_case_count(self) -> int:
        return self.total_case_count - self.passed_case_count

    @property
    def pass_rate(self) -> float:
        return self.passed_case_count / self.total_case_count

    @property
    def failed_evaluation_ids(self) -> tuple[str, ...]:
        return tuple(
            assessment.evaluation_run_result.evaluation_case.evaluation_id
            for assessment in self.assessments
            if not assessment.passed
        )

    @property
    def current_document_retrieval_rate(self) -> float:
        if not self.assessments:
            return 0.0
        current_retrieved_count = sum(
            assessment.current_document_retrieved
            for assessment in self.assessments
        )
        return current_retrieved_count / self.total_case_count

    @property
    def stale_document_retrieval_rate(self) -> float:
        if not self.assessments:
            return 0.0
        stale_case_count = sum(
            assessment.stale_document_retrieved
            for assessment in self.assessments
        )
        return stale_case_count / self.total_case_count

    @property
    def missing_current_document_case_count(self) -> int:
        return sum(
            not assessment.current_document_retrieved
            for assessment in self.assessments
        )

    @property
    def stale_document_retrieval_case_count(self) -> int:
        return sum(
            assessment.stale_document_retrieved
            for assessment in self.assessments
        )


def run_offline_rag_freshness_evaluation_suite(
    evaluation_cases: Sequence[RAGFreshnessEvaluationCase],
) -> RAGFreshnessEvaluationMetricsReport:
    """Run and assess every freshness case in input order."""
    if not evaluation_cases:
        raise ValueError("assessments must not be empty.")

    assessments = []
    for evaluation_case in evaluation_cases:
        result = run_offline_rag_freshness_evaluation_case(evaluation_case)
        assessments.append(assess_rag_freshness_evaluation_run_result(result))

    return RAGFreshnessEvaluationMetricsReport(assessments=tuple(assessments))
