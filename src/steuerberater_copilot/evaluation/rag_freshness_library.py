"""Deterministic synthetic baseline cases for offline RAG freshness evaluation."""

from __future__ import annotations

from steuerberater_copilot.rag import DocumentVersionRecord, SourceDocument

from .rag_freshness_case import RAGFreshnessEvaluationCase

REFERENCE_DATE = "2026-07-01"


def build_synthetic_rag_freshness_evaluation_case_library() -> tuple[
    RAGFreshnessEvaluationCase, ...
]:
    """Build the four fresh synthetic freshness baseline cases in stable order.

    Order is fixed and documented:

    1. ``EVAL_RAG_FRESHNESS_BASELINE_SUPERSEDED``
    2. ``EVAL_RAG_FRESHNESS_BASELINE_EXPIRED``
    3. ``EVAL_RAG_FRESHNESS_BASELINE_CURRENT``
    4. ``EVAL_RAG_FRESHNESS_BASELINE_MIXED``
    """
    return (
        _superseded_case(),
        _expired_case(),
        _current_case(),
        _mixed_case(),
    )


def _superseded_case() -> RAGFreshnessEvaluationCase:
    older = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_SUPERSEDED_V1",
        title="Synthetic retention policy v1",
        content="Synthetic orchard retention policy version one.",
    )
    newer = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_SUPERSEDED_V2",
        title="Synthetic retention policy v2",
        content="Synthetic orchard retention policy version two.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_SUPERSEDED",
        source_documents=(older, newer),
        version_records=(
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_SUPERSEDED_V1",
                document_family="retention_policy",
                version_number=1,
                effective_date=REFERENCE_DATE,
            ),
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_SUPERSEDED_V2",
                document_family="retention_policy",
                version_number=2,
                effective_date=REFERENCE_DATE,
            ),
        ),
        reference_date=REFERENCE_DATE,
        expected_outdated_document_ids=("SYNTHETIC_FRESHNESS_SUPERSEDED_V1",),
    )


def _expired_case() -> RAGFreshnessEvaluationCase:
    expired = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_EXPIRED_NOTICE",
        title="Synthetic seasonal notice",
        content="Synthetic meadow seasonal notice with expired effective date.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_EXPIRED",
        source_documents=(expired,),
        version_records=(
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_EXPIRED_NOTICE",
                document_family="seasonal_notice",
                version_number=1,
                effective_date="2025-06-01",
            ),
        ),
        reference_date=REFERENCE_DATE,
        expected_outdated_document_ids=("SYNTHETIC_FRESHNESS_EXPIRED_NOTICE",),
    )


def _current_case() -> RAGFreshnessEvaluationCase:
    current = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_CURRENT_GUIDE",
        title="Synthetic current guide",
        content="Synthetic orchard guide that remains current.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_CURRENT",
        source_documents=(current,),
        version_records=(
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_CURRENT_GUIDE",
                document_family="orchard_guide",
                version_number=3,
                effective_date="2026-07-01",
            ),
        ),
        reference_date=REFERENCE_DATE,
        expected_outdated_document_ids=(),
    )


def _mixed_case() -> RAGFreshnessEvaluationCase:
    superseded = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_MIXED_OLD",
        title="Synthetic mixed old",
        content="Synthetic mixed family older version.",
    )
    current = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_MIXED_NEW",
        title="Synthetic mixed new",
        content="Synthetic mixed family newer version.",
    )
    expired = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_MIXED_EXPIRED",
        title="Synthetic mixed expired",
        content="Synthetic mixed expired singleton family.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_MIXED",
        source_documents=(superseded, current, expired),
        version_records=(
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_MIXED_OLD",
                document_family="mixed_family",
                version_number=1,
                effective_date=REFERENCE_DATE,
            ),
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_MIXED_NEW",
                document_family="mixed_family",
                version_number=2,
                effective_date=REFERENCE_DATE,
            ),
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_MIXED_EXPIRED",
                document_family="expired_family",
                version_number=1,
                effective_date="2024-01-01",
            ),
        ),
        reference_date=REFERENCE_DATE,
        expected_outdated_document_ids=(
            "SYNTHETIC_FRESHNESS_MIXED_EXPIRED",
            "SYNTHETIC_FRESHNESS_MIXED_OLD",
        ),
    )
