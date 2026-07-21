"""Deterministic aggregate metrics for synthetic RAG abstention evaluation."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from steuerberater_copilot.ai import ModelProvider

from .rag_abstention_assessment import (
    RAGAbstentionEvaluationCaseAssessment,
    assess_rag_abstention_evaluation_run_result,
)
from .rag_abstention_case import RAGAbstentionEvaluationCase
from .rag_abstention_runner import run_offline_rag_abstention_evaluation_case


@dataclass(frozen=True, slots=True)
class RAGAbstentionEvaluationMetricsReport:
    """Traceable aggregate abstention metrics from ordered assessments.

    ``pass_rate`` is the overall exact match rate across all assessments.
    ``missing_evidence_abstention_rate`` uses only cases with
    ``expected_abstained_for_missing_evidence=True`` as denominator. Control
    cases with ``False`` never increase that denominator. When no expected
    missing-evidence case is present, the rate is ``None``.
    """

    assessments: tuple[RAGAbstentionEvaluationCaseAssessment, ...]

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
    def expected_missing_evidence_case_count(self) -> int:
        return len(self._expected_missing_evidence_assessments)

    @property
    def missing_evidence_abstention_rate(self) -> float | None:
        assessments = self._expected_missing_evidence_assessments
        if not assessments:
            return None
        observed_abstention_count = sum(
            assessment.evaluation_run_result.observed_abstained_for_missing_evidence
            for assessment in assessments
        )
        return observed_abstention_count / len(assessments)

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
    def _expected_missing_evidence_assessments(
        self,
    ) -> tuple[RAGAbstentionEvaluationCaseAssessment, ...]:
        return tuple(
            assessment
            for assessment in self.assessments
            if self._expected_abstained(assessment)
        )

    @staticmethod
    def _expected_abstained(
        assessment: RAGAbstentionEvaluationCaseAssessment,
    ) -> bool:
        evaluation_case = assessment.evaluation_run_result.evaluation_case
        return evaluation_case.expected_abstained_for_missing_evidence

    @staticmethod
    def _observed_abstained(
        assessment: RAGAbstentionEvaluationCaseAssessment,
    ) -> bool:
        return assessment.evaluation_run_result.observed_abstained_for_missing_evidence

    @classmethod
    def _is_false_negative(
        cls,
        assessment: RAGAbstentionEvaluationCaseAssessment,
    ) -> bool:
        return cls._expected_abstained(assessment) and not cls._observed_abstained(
            assessment
        )

    @classmethod
    def _is_false_positive(
        cls,
        assessment: RAGAbstentionEvaluationCaseAssessment,
    ) -> bool:
        return (not cls._expected_abstained(assessment)) and cls._observed_abstained(
            assessment
        )


def run_offline_rag_abstention_evaluation_suite(
    evaluation_cases: Sequence[RAGAbstentionEvaluationCase],
    *,
    provider_factory: Callable[[RAGAbstentionEvaluationCase], ModelProvider],
) -> RAGAbstentionEvaluationMetricsReport:
    """Run and assess every abstention case in input order with a fresh provider."""
    assessments = []
    for evaluation_case in evaluation_cases:
        provider = provider_factory(evaluation_case)
        result = run_offline_rag_abstention_evaluation_case(
            evaluation_case,
            provider=provider,
        )
        assessments.append(assess_rag_abstention_evaluation_run_result(result))

    return RAGAbstentionEvaluationMetricsReport(assessments=tuple(assessments))
