"""Deterministic observation of one synthetic RAG contradiction evaluation case."""

from __future__ import annotations

from dataclasses import dataclass

from steuerberater_copilot.rag import (
    ContradictionDetectionResult,
    detect_passage_contradictions,
)

from .rag_contradiction_case import RAGContradictionEvaluationCase


@dataclass(frozen=True, slots=True)
class RAGContradictionEvaluationRunResult:
    """Observed detector output for one RAG contradiction evaluation case.

    ``observed_detection_result`` is separate from the ground-truth labels on
    ``evaluation_case`` and does not imply a pass/fail assessment.
    """

    evaluation_case: RAGContradictionEvaluationCase
    observed_detection_result: ContradictionDetectionResult

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_case, RAGContradictionEvaluationCase):
            raise TypeError(
                "evaluation_case must be a RAGContradictionEvaluationCase."
            )
        if not isinstance(
            self.observed_detection_result,
            ContradictionDetectionResult,
        ):
            raise TypeError(
                "observed_detection_result must be a ContradictionDetectionResult."
            )


def run_offline_rag_contradiction_evaluation_case(
    evaluation_case: RAGContradictionEvaluationCase,
) -> RAGContradictionEvaluationRunResult:
    """Run the existing detector over one case without assessing its labels."""
    observed_detection_result = detect_passage_contradictions(
        evaluation_case.source_documents
    )
    return RAGContradictionEvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_detection_result=observed_detection_result,
    )
