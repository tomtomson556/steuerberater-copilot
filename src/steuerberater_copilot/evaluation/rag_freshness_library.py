"""Deterministic synthetic baseline cases for RAG freshness evaluation."""

from __future__ import annotations

from steuerberater_copilot.rag import SourceDocument

from .rag_freshness_case import RAGFreshnessEvaluationCase


def build_synthetic_rag_freshness_evaluation_case_library() -> tuple[
    RAGFreshnessEvaluationCase, ...
]:
    """Build five fresh freshness baseline cases in stable order.

    Order is fixed and documented:

    1. ``EVAL_RAG_FRESHNESS_BASELINE_CURRENT_AHEAD``
    2. ``EVAL_RAG_FRESHNESS_BASELINE_STALE_OUTSIDE_TOP_K``
    3. ``EVAL_RAG_FRESHNESS_BASELINE_NEUTRAL_DISTRACTOR``
    4. ``EVAL_RAG_FRESHNESS_BASELINE_MULTIPLE_STALE``
    5. ``EVAL_RAG_FRESHNESS_BASELINE_NORMALIZED_QUERY``

    Every call returns fresh case and source-document instances. Retrieval
    behavior is determined only by the existing local retriever's token
    overlap and ``top_k`` semantics; current and stale labels remain assessment
    ground truth.
    """
    return (
        _current_ahead_case(),
        _stale_outside_top_k_case(),
        _neutral_distractor_case(),
        _multiple_stale_case(),
        _normalized_query_case(),
    )


def _current_ahead_case() -> RAGFreshnessEvaluationCase:
    stale_document = _document(
        document_id="SYNTHETIC_RAG_FRESHNESS_CURRENT_AHEAD_STALE",
        title="Synthetic orchard archived reference",
        content="Synthetic neutral stored passage.",
    )
    current_document = _document(
        document_id="SYNTHETIC_RAG_FRESHNESS_CURRENT_AHEAD_CURRENT",
        title="Synthetic orchard cedar current reference",
        content="Synthetic active baseline passage.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_CURRENT_AHEAD",
        source_documents=(stale_document, current_document),
        retrieval_query="orchard cedar",
        top_k=1,
        expected_current_document_id=current_document.document_id,
        stale_document_ids=(stale_document.document_id,),
    )


def _stale_outside_top_k_case() -> RAGFreshnessEvaluationCase:
    stale_document = _document(
        document_id="SYNTHETIC_RAG_FRESHNESS_OUTSIDE_TOP_K_STALE",
        title="Synthetic harbor archived reference",
        content="Synthetic neutral stored passage.",
    )
    current_document = _document(
        document_id="SYNTHETIC_RAG_FRESHNESS_OUTSIDE_TOP_K_CURRENT",
        title="Synthetic harbor cobalt beacon reference",
        content="Synthetic active baseline passage.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_STALE_OUTSIDE_TOP_K",
        source_documents=(stale_document, current_document),
        retrieval_query="harbor cobalt beacon",
        top_k=1,
        expected_current_document_id=current_document.document_id,
        stale_document_ids=(stale_document.document_id,),
    )


def _neutral_distractor_case() -> RAGFreshnessEvaluationCase:
    stale_document = _document(
        document_id="SYNTHETIC_RAG_FRESHNESS_DISTRACTOR_STALE",
        title="Synthetic lantern archived reference",
        content="Synthetic neutral stored passage.",
    )
    distractor_document = _document(
        document_id="SYNTHETIC_RAG_FRESHNESS_DISTRACTOR_NEUTRAL",
        title="Synthetic lantern amber neutral reference",
        content="Synthetic unrelated control passage.",
    )
    current_document = _document(
        document_id="SYNTHETIC_RAG_FRESHNESS_DISTRACTOR_CURRENT",
        title="Synthetic lantern amber signal current reference",
        content="Synthetic active baseline passage.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_NEUTRAL_DISTRACTOR",
        source_documents=(
            stale_document,
            distractor_document,
            current_document,
        ),
        retrieval_query="lantern amber signal",
        top_k=2,
        expected_current_document_id=current_document.document_id,
        stale_document_ids=(stale_document.document_id,),
    )


def _multiple_stale_case() -> RAGFreshnessEvaluationCase:
    stale_document_alpha = _document(
        document_id="SYNTHETIC_RAG_FRESHNESS_MULTIPLE_STALE_ALPHA",
        title="Synthetic meadow violet archived reference",
        content="Synthetic neutral stored passage alpha.",
    )
    stale_document_beta = _document(
        document_id="SYNTHETIC_RAG_FRESHNESS_MULTIPLE_STALE_BETA",
        title="Synthetic meadow archived reference",
        content="Synthetic neutral stored passage beta.",
    )
    current_document = _document(
        document_id="SYNTHETIC_RAG_FRESHNESS_MULTIPLE_CURRENT",
        title="Synthetic meadow violet archive compass current reference",
        content="Synthetic active baseline passage.",
    )
    stale_document_gamma = _document(
        document_id="SYNTHETIC_RAG_FRESHNESS_MULTIPLE_STALE_GAMMA",
        title="Synthetic compass archived reference",
        content="Synthetic neutral stored passage gamma.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_MULTIPLE_STALE",
        source_documents=(
            stale_document_alpha,
            stale_document_beta,
            current_document,
            stale_document_gamma,
        ),
        retrieval_query="meadow violet archive compass",
        top_k=1,
        expected_current_document_id=current_document.document_id,
        stale_document_ids=(
            stale_document_alpha.document_id,
            stale_document_beta.document_id,
            stale_document_gamma.document_id,
        ),
    )


def _normalized_query_case() -> RAGFreshnessEvaluationCase:
    current_document = _document(
        document_id="SYNTHETIC_RAG_FRESHNESS_NORMALIZED_CURRENT",
        title="Synthetic Kompass current reference",
        content="Synthetic silber signal baseline passage.",
    )
    stale_document = _document(
        document_id="SYNTHETIC_RAG_FRESHNESS_NORMALIZED_STALE",
        title="Synthetic kompass archived reference",
        content="Synthetic neutral stored passage.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_NORMALIZED_QUERY",
        source_documents=(current_document, stale_document),
        retrieval_query="KOMPASS SILBER SIGNAL",
        top_k=1,
        expected_current_document_id=current_document.document_id,
        stale_document_ids=(stale_document.document_id,),
    )


def _document(*, document_id: str, title: str, content: str) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=title,
        content=content,
    )
