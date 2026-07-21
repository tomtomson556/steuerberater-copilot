"""Deterministic observation of one synthetic RAG abstention evaluation case."""

from __future__ import annotations

from dataclasses import dataclass

from steuerberater_copilot.ai import ModelProvider
from steuerberater_copilot.offline_mvp import build_synthetic_rag_workflow
from steuerberater_copilot.rag import LocalDocumentRetriever

from .rag_abstention_case import RAGAbstentionEvaluationCase


@dataclass(frozen=True, slots=True)
class RAGAbstentionEvaluationRunResult:
    """Observed missing-evidence abstention for one RAG abstention case.

    ``observed_abstained_for_missing_evidence`` is the workflow observation.
    It is not the ground-truth ``expected_abstained_for_missing_evidence`` and
    does not imply a pass/fail assessment.
    """

    evaluation_case: RAGAbstentionEvaluationCase
    observed_abstained_for_missing_evidence: bool

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_case, RAGAbstentionEvaluationCase):
            raise TypeError("evaluation_case must be a RAGAbstentionEvaluationCase.")
        if type(self.observed_abstained_for_missing_evidence) is not bool:
            raise TypeError(
                "observed_abstained_for_missing_evidence must be a boolean."
            )


def run_offline_rag_abstention_evaluation_case(
    evaluation_case: RAGAbstentionEvaluationCase,
    *,
    provider: ModelProvider,
) -> RAGAbstentionEvaluationRunResult:
    """Run one abstention case through the existing RAG workflow without assessing it."""
    retriever = LocalDocumentRetriever(documents=evaluation_case.source_documents)
    workflow_output = build_synthetic_rag_workflow(
        evaluation_case.intake,
        provider=provider,
        retriever=retriever,
        retrieval_query=evaluation_case.retrieval_query,
        top_k=evaluation_case.top_k,
    )
    return RAGAbstentionEvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_abstained_for_missing_evidence=(
            workflow_output.abstained_for_missing_evidence
        ),
    )
