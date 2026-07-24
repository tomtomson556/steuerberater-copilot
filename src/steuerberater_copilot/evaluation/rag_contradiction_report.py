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
    """Traceable aggregate contradiction metrics from ordered assessments.

    ``pass_rate`` includes exact flag and evidence assessment. The separate
    ``contradiction_detection_rate`` uses only cases with
    ``expected_contradiction_present=True`` as denominator and counts their
    observed contradiction flags, independent of evidence matching. When no
    expected positive case is present, that rate is ``None``.
    """

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
        observed_contradiction_count = sum(
            self._observed_contradiction(assessment) for assessment in assessments
        )
        return observed_contradiction_count / len(assessments)

    @property
    def false_negative_case_count(self) -> int:
        return sum(
            1
            for assessment in self.assessments
            if self._is_false_negative(assessment)
        )

    @property
    def false_positive_case_count(self) -> int:
        return sum(
            1
            for assessment in self.assessments
            if self._is_false_positive(assessment)
        )

    @property
    def _expected_contradiction_assessments(
        self,
    ) -> tuple[RAGContradictionEvaluationCaseAssessment, ...]:
        return tuple(
            assessment
            for assessment in self.assessments
            if self._expected_contradiction(assessment)
        )

    @staticmethod
    def _expected_contradiction(
        assessment: RAGContradictionEvaluationCaseAssessment,
    ) -> bool:
        return (
            assessment.evaluation_run_result.evaluation_case.expected_contradiction_present
        )

    @staticmethod
    def _observed_contradiction(
        assessment: RAGContradictionEvaluationCaseAssessment,
    ) -> bool:
        return (
            assessment.evaluation_run_result.observed_detection_result.contradiction_present
        )

    @classmethod
    def _is_false_negative(
        cls,
        assessment: RAGContradictionEvaluationCaseAssessment,
    ) -> bool:
        return (
            cls._expected_contradiction(assessment)
            and not cls._observed_contradiction(assessment)
        )

    @classmethod
    def _is_false_positive(
        cls,
        assessment: RAGContradictionEvaluationCaseAssessment,
    ) -> bool:
        return (
            not cls._expected_contradiction(assessment)
            and cls._observed_contradiction(assessment)
        )


def run_offline_rag_contradiction_evaluation_suite(
    evaluation_cases: Sequence[RAGContradictionEvaluationCase],
) -> RAGContradictionEvaluationMetricsReport:
    """Run and assess every contradiction case in input order."""
    assessments = []
    for evaluation_case in evaluation_cases:
        result = run_offline_rag_contradiction_evaluation_case(evaluation_case)
        assessments.append(assess_rag_contradiction_evaluation_run_result(result))

    return RAGContradictionEvaluationMetricsReport(assessments=tuple(assessments))
