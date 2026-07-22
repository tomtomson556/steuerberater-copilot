"""Deterministic observation of one synthetic RAG freshness evaluation case."""

from __future__ import annotations

from dataclasses import dataclass

from steuerberater_copilot.rag import find_outdated_document_ids

from .rag_freshness_case import RAGFreshnessEvaluationCase


@dataclass(frozen=True, slots=True)
class RAGFreshnessEvaluationRunResult:
    """Observed outdated document IDs for one freshness evaluation case."""

    evaluation_case: RAGFreshnessEvaluationCase
    observed_outdated_document_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_case, RAGFreshnessEvaluationCase):
            raise TypeError("evaluation_case must be a RAGFreshnessEvaluationCase.")
        if not isinstance(self.observed_outdated_document_ids, tuple):
            raise TypeError("observed_outdated_document_ids must be a tuple.")
        for document_id in self.observed_outdated_document_ids:
            if not isinstance(document_id, str):
                raise TypeError(
                    "observed_outdated_document_ids must contain only strings."
                )
            if not document_id or document_id.isspace():
                raise ValueError(
                    "observed_outdated_document_ids must not contain blank values."
                )


def run_offline_rag_freshness_evaluation_case(
    evaluation_case: RAGFreshnessEvaluationCase,
) -> RAGFreshnessEvaluationRunResult:
    """Detect outdated documents without assessing the case."""
    if not isinstance(evaluation_case, RAGFreshnessEvaluationCase):
        raise TypeError("evaluation_case must be a RAGFreshnessEvaluationCase.")

    observed = find_outdated_document_ids(
        evaluation_case.version_records,
        reference_date=evaluation_case.reference_date,
    )
    return RAGFreshnessEvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_outdated_document_ids=observed,
    )
