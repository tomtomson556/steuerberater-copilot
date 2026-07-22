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
    """Traceable aggregate freshness metrics from ordered assessments."""

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
    def expected_outdated_document_count(self) -> int:
        return sum(
            len(assessment.evaluation_run_result.evaluation_case.expected_outdated_document_ids)
            for assessment in self.assessments
        )

    @property
    def outdated_detection_rate(self) -> float | None:
        expected_ids = [
            document_id
            for assessment in self.assessments
            for document_id in (
                assessment.evaluation_run_result.evaluation_case.expected_outdated_document_ids
            )
        ]
        if not expected_ids:
            return None
        observed_hits = 0
        for assessment in self.assessments:
            expected = set(
                assessment.evaluation_run_result.evaluation_case.expected_outdated_document_ids
            )
            observed = set(assessment.evaluation_run_result.observed_outdated_document_ids)
            observed_hits += len(expected & observed)
        return observed_hits / len(expected_ids)


def run_offline_rag_freshness_evaluation_suite(
    evaluation_cases: Sequence[RAGFreshnessEvaluationCase],
) -> RAGFreshnessEvaluationMetricsReport:
    """Run and assess every freshness case in input order."""
    assessments = [
        assess_rag_freshness_evaluation_run_result(
            run_offline_rag_freshness_evaluation_case(evaluation_case)
        )
        for evaluation_case in evaluation_cases
    ]
    return RAGFreshnessEvaluationMetricsReport(assessments=tuple(assessments))
