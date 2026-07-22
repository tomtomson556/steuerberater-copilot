"""Deterministic observation of one synthetic RAG contradiction evaluation case."""

from __future__ import annotations

from dataclasses import dataclass

from steuerberater_copilot.rag import detect_passage_contradictions

from .rag_contradiction_case import ContradictionEvidenceLabel, RAGContradictionEvaluationCase


@dataclass(frozen=True, slots=True)
class RAGContradictionEvaluationRunResult:
    """Observed contradiction signal for one contradiction evaluation case.

    Observations come only from the closed-template passage extractor. They are
    not the ground-truth ``expected_contradiction_present`` labels and do not
    imply a pass/fail assessment by themselves.
    """

    evaluation_case: RAGContradictionEvaluationCase
    observed_contradiction_present: bool
    observed_contradicting_passages: tuple[ContradictionEvidenceLabel, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_case, RAGContradictionEvaluationCase):
            raise TypeError(
                "evaluation_case must be a RAGContradictionEvaluationCase."
            )
        if type(self.observed_contradiction_present) is not bool:
            raise TypeError("observed_contradiction_present must be a boolean.")
        if not isinstance(self.observed_contradicting_passages, tuple):
            raise TypeError("observed_contradicting_passages must be a tuple.")
        for label in self.observed_contradicting_passages:
            if not isinstance(label, ContradictionEvidenceLabel):
                raise TypeError(
                    "observed_contradicting_passages must contain only "
                    "ContradictionEvidenceLabel objects."
                )
        if self.observed_contradiction_present != bool(
            self.observed_contradicting_passages
        ):
            raise ValueError(
                "observed_contradiction_present must be True exactly when "
                "observed_contradicting_passages is non-empty."
            )


def run_offline_rag_contradiction_evaluation_case(
    evaluation_case: RAGContradictionEvaluationCase,
) -> RAGContradictionEvaluationRunResult:
    """Detect passage contradictions without assessing the case."""
    if not isinstance(evaluation_case, RAGContradictionEvaluationCase):
        raise TypeError("evaluation_case must be a RAGContradictionEvaluationCase.")

    detection = detect_passage_contradictions(evaluation_case.source_documents)
    observed_passages: list[ContradictionEvidenceLabel] = []
    if detection.contradictions:
        # Report the first contradicting attribute pair as two evidence labels.
        first_pair = detection.contradictions[0]
        observed_passages.extend(
            (
                ContradictionEvidenceLabel(
                    document_id=first_pair.first.document_id,
                    supporting_text=first_pair.first.supporting_text,
                ),
                ContradictionEvidenceLabel(
                    document_id=first_pair.second.document_id,
                    supporting_text=first_pair.second.supporting_text,
                ),
            )
        )

    return RAGContradictionEvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_contradiction_present=detection.contradiction_present,
        observed_contradicting_passages=tuple(observed_passages),
    )
