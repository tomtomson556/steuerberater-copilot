"""Deterministic synthetic baseline cases for offline retrieval evaluation."""

from __future__ import annotations

from steuerberater_copilot.rag import SourceDocument

from .retrieval_case import RetrievalEvaluationCase


def build_synthetic_retrieval_evaluation_case_library() -> tuple[
    RetrievalEvaluationCase, ...
]:
    """Build the four fresh synthetic retrieval baseline cases in stable order.

    Order is fixed and documented:

    1. ``EVAL_RETRIEVAL_BASELINE_FULL_RECALL``
    2. ``EVAL_RETRIEVAL_BASELINE_PARTIAL_RECALL``
    3. ``EVAL_RETRIEVAL_BASELINE_ZERO_RECALL``
    4. ``EVAL_RETRIEVAL_BASELINE_NO_EVIDENCE``

    Each call returns a new immutable tuple of fresh ``RetrievalEvaluationCase``
    and ``SourceDocument`` instances. Cases are designed for the deterministic
    token-overlap ranking of ``LocalDocumentRetriever`` and can be executed
    directly with ``run_offline_retrieval_evaluation_case`` and assessed with
    ``assess_retrieval_evaluation_run_result``.
    """
    return (
        _full_recall_case(),
        _partial_recall_case(),
        _zero_recall_case(),
        _no_evidence_case(),
    )


def _full_recall_case() -> RetrievalEvaluationCase:
    """Both relevant documents are retrieved within top_k (Recall@k = 1.0)."""
    relevant_alpha = SourceDocument(
        document_id="SYNTHETIC_RETRIEVAL_FULL_RELEVANT_ALPHA",
        title="Synthetic orchard reference alpha",
        content="Synthetic orchard baseline content for full recall.",
    )
    relevant_beta = SourceDocument(
        document_id="SYNTHETIC_RETRIEVAL_FULL_RELEVANT_BETA",
        title="Synthetic orchard reference beta",
        content="Synthetic orchard baseline content for full recall.",
    )
    distractor = SourceDocument(
        document_id="SYNTHETIC_RETRIEVAL_FULL_DISTRACTOR",
        title="Synthetic meadow reference",
        content="Synthetic meadow baseline content for full recall.",
    )
    return RetrievalEvaluationCase(
        evaluation_id="EVAL_RETRIEVAL_BASELINE_FULL_RECALL",
        source_documents=(relevant_alpha, relevant_beta, distractor),
        retrieval_query="orchard",
        top_k=2,
        relevant_document_ids=(
            "SYNTHETIC_RETRIEVAL_FULL_RELEVANT_ALPHA",
            "SYNTHETIC_RETRIEVAL_FULL_RELEVANT_BETA",
        ),
    )


def _partial_recall_case() -> RetrievalEvaluationCase:
    """Exactly one of two relevant documents is retrieved (Recall@k = 0.5)."""
    relevant_strong = SourceDocument(
        document_id="SYNTHETIC_RETRIEVAL_PARTIAL_RELEVANT_STRONG",
        title="Synthetic copper silver reference",
        content="Synthetic copper silver baseline content for partial recall.",
    )
    relevant_weak = SourceDocument(
        document_id="SYNTHETIC_RETRIEVAL_PARTIAL_RELEVANT_WEAK",
        title="Synthetic copper reference",
        content="Synthetic copper baseline content for partial recall.",
    )
    distractor = SourceDocument(
        document_id="SYNTHETIC_RETRIEVAL_PARTIAL_DISTRACTOR",
        title="Synthetic meadow reference",
        content="Synthetic meadow baseline content for partial recall.",
    )
    return RetrievalEvaluationCase(
        evaluation_id="EVAL_RETRIEVAL_BASELINE_PARTIAL_RECALL",
        source_documents=(relevant_strong, relevant_weak, distractor),
        retrieval_query="copper silver",
        top_k=1,
        relevant_document_ids=(
            "SYNTHETIC_RETRIEVAL_PARTIAL_RELEVANT_STRONG",
            "SYNTHETIC_RETRIEVAL_PARTIAL_RELEVANT_WEAK",
        ),
    )


def _zero_recall_case() -> RetrievalEvaluationCase:
    """Only an irrelevant hit is returned despite a labeled document (Recall@k = 0.0)."""
    relevant = SourceDocument(
        document_id="SYNTHETIC_RETRIEVAL_ZERO_RELEVANT",
        title="Synthetic meadow reference",
        content="Synthetic meadow baseline content for zero recall.",
    )
    irrelevant = SourceDocument(
        document_id="SYNTHETIC_RETRIEVAL_ZERO_IRRELEVANT",
        title="Synthetic orchard reference",
        content="Synthetic orchard baseline content matching the query.",
    )
    return RetrievalEvaluationCase(
        evaluation_id="EVAL_RETRIEVAL_BASELINE_ZERO_RECALL",
        source_documents=(relevant, irrelevant),
        retrieval_query="orchard",
        top_k=1,
        relevant_document_ids=("SYNTHETIC_RETRIEVAL_ZERO_RELEVANT",),
    )


def _no_evidence_case() -> RetrievalEvaluationCase:
    """No token overlap yields empty hits; empty labels make Recall@k inapplicable."""
    meadow = SourceDocument(
        document_id="SYNTHETIC_RETRIEVAL_NO_EVIDENCE_MEADOW",
        title="Synthetic meadow reference",
        content="Synthetic meadow baseline content for no evidence.",
    )
    river = SourceDocument(
        document_id="SYNTHETIC_RETRIEVAL_NO_EVIDENCE_RIVER",
        title="Synthetic river reference",
        content="Synthetic river baseline content for no evidence.",
    )
    return RetrievalEvaluationCase(
        evaluation_id="EVAL_RETRIEVAL_BASELINE_NO_EVIDENCE",
        source_documents=(meadow, river),
        retrieval_query="orchard quartz",
        top_k=2,
        relevant_document_ids=(),
    )
