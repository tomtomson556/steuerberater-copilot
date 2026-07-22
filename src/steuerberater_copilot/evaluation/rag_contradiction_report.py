"""Deterministic aggregate metrics for synthetic RAG contradiction evaluation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .rag_contradiction_assessment import (
    RAGContradictionEvaluationCaseAssessment,
    assess_rag_contradiction_evaluation_run_result,
)
from .rag_contradiction_case import RAGContradictionEvaluationCase
from .rag_contradiction_runner import run_offline_rag_contradiction_evaluation_case


@dataclass(frozen=True, slots=True)
class RAGContradictionEvaluationMetricsReport:
    """Traceable aggregate contradiction metrics from ordered assessments."""

    assessments: tuple[RAGContradictionEvaluationCaseAssessment, ...]

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
    def expected_contradiction_case_count(self) -> int:
        return len(self._expected_contradiction_assessments)

    @property
    def contradiction_detection_rate(self) -> float | None:
        assessments = self._expected_contradiction_assessments
        if not assessments:
            return None
        observed_count = sum(
            assessment.evaluation_run_result.observed_contradiction_present
            for assessment in assessments
        )
        return observed_count / len(assessments)

    @property
    def _expected_contradiction_assessments(
        self,
    ) -> tuple[RAGContradictionEvaluationCaseAssessment, ...]:
        return tuple(
            assessment
            for assessment in self.assessments
            if assessment.evaluation_run_result.evaluation_case.expected_contradiction_present
        )


def run_offline_rag_contradiction_evaluation_suite(
    evaluation_cases: Sequence[RAGContradictionEvaluationCase],
) -> RAGContradictionEvaluationMetricsReport:
    """Run and assess every contradiction case in input order."""
    assessments = [
        assess_rag_contradiction_evaluation_run_result(
            run_offline_rag_contradiction_evaluation_case(evaluation_case)
        )
        for evaluation_case in evaluation_cases
    ]
    return RAGContradictionEvaluationMetricsReport(assessments=tuple(assessments))
