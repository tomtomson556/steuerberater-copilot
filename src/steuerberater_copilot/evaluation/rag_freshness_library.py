"""Deterministic synthetic baseline cases for offline RAG freshness evaluation."""

from __future__ import annotations

from steuerberater_copilot.rag import DocumentVersionRecord, SourceDocument

from .rag_freshness_case import RAGFreshnessEvaluationCase

REFERENCE_DATE = "2026-07-01"


def build_synthetic_rag_freshness_evaluation_case_library() -> tuple[
    RAGFreshnessEvaluationCase, ...
]:
    """Build synthetic freshness cases in stable order.

    Order:

    1. ``EVAL_RAG_FRESHNESS_BASELINE_SUPERSEDED``
    2. ``EVAL_RAG_FRESHNESS_BASELINE_VALIDITY_ENDED``
    3. ``EVAL_RAG_FRESHNESS_BASELINE_CURRENT_DESPITE_PAST_START``
    4. ``EVAL_RAG_FRESHNESS_BASELINE_FUTURE_DRAFT_NOT_OUTDATED``
    5. ``EVAL_RAG_FRESHNESS_BASELINE_MIXED``
    6. ``EVAL_RAG_FRESHNESS_BASELINE_SAME_FAMILY_NOT_YET_SUPERSEDING``
    """
    return (
        _superseded_case(),
        _validity_ended_case(),
        _current_despite_past_start_case(),
        _future_draft_not_outdated_case(),
        _mixed_case(),
        _same_family_not_yet_superseding_case(),
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
                valid_from="2025-01-01",
            ),
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_SUPERSEDED_V2",
                document_family="retention_policy",
                version_number=2,
                valid_from="2026-01-01",
            ),
        ),
        reference_date=REFERENCE_DATE,
        expected_outdated_document_ids=("SYNTHETIC_FRESHNESS_SUPERSEDED_V1",),
    )


def _validity_ended_case() -> RAGFreshnessEvaluationCase:
    ended = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_VALIDITY_ENDED",
        title="Synthetic seasonal notice",
        content="Synthetic meadow seasonal notice with closed validity window.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_VALIDITY_ENDED",
        source_documents=(ended,),
        version_records=(
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_VALIDITY_ENDED",
                document_family="seasonal_notice",
                version_number=1,
                valid_from="2025-01-01",
                valid_to="2026-01-01",
            ),
        ),
        reference_date=REFERENCE_DATE,
        expected_outdated_document_ids=("SYNTHETIC_FRESHNESS_VALIDITY_ENDED",),
    )


def _current_despite_past_start_case() -> RAGFreshnessEvaluationCase:
    """Past valid_from alone must not mark the only in-force version outdated."""
    current = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_CURRENT_GUIDE",
        title="Synthetic current guide",
        content="Synthetic orchard guide that remains current.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_CURRENT_DESPITE_PAST_START",
        source_documents=(current,),
        version_records=(
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_CURRENT_GUIDE",
                document_family="orchard_guide",
                version_number=3,
                valid_from="2024-01-01",
            ),
        ),
        reference_date=REFERENCE_DATE,
        expected_outdated_document_ids=(),
    )


def _future_draft_not_outdated_case() -> RAGFreshnessEvaluationCase:
    """A future-dated draft is not outdated; the past in-force version stays current."""
    current = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_FUTURE_CURRENT",
        title="Synthetic current policy",
        content="Synthetic orchard policy currently in force.",
    )
    future = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_FUTURE_DRAFT",
        title="Synthetic future draft policy",
        content="Synthetic orchard policy draft for a later start date.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_FUTURE_DRAFT_NOT_OUTDATED",
        source_documents=(current, future),
        version_records=(
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_FUTURE_CURRENT",
                document_family="future_policy",
                version_number=1,
                valid_from="2025-01-01",
            ),
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_FUTURE_DRAFT",
                document_family="future_policy",
                version_number=2,
                valid_from="2026-12-01",
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
    ended = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_MIXED_ENDED",
        title="Synthetic mixed ended",
        content="Synthetic mixed validity-ended singleton family.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_MIXED",
        source_documents=(superseded, current, ended),
        version_records=(
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_MIXED_OLD",
                document_family="mixed_family",
                version_number=1,
                valid_from="2025-01-01",
            ),
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_MIXED_NEW",
                document_family="mixed_family",
                version_number=2,
                valid_from="2026-01-01",
            ),
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_MIXED_ENDED",
                document_family="ended_family",
                version_number=1,
                valid_from="2024-01-01",
                valid_to="2025-12-31",
            ),
        ),
        reference_date=REFERENCE_DATE,
        expected_outdated_document_ids=(
            "SYNTHETIC_FRESHNESS_MIXED_ENDED",
            "SYNTHETIC_FRESHNESS_MIXED_OLD",
        ),
    )


def _same_family_not_yet_superseding_case() -> RAGFreshnessEvaluationCase:
    """Higher version that is not yet in force must not supersede the current one."""
    current = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_PENDING_CURRENT",
        title="Synthetic pending current",
        content="Synthetic meadow policy still in force.",
    )
    pending = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_PENDING_NEXT",
        title="Synthetic pending next",
        content="Synthetic meadow policy waiting for a future valid_from.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_SAME_FAMILY_NOT_YET_SUPERSEDING",
        source_documents=(current, pending),
        version_records=(
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_PENDING_CURRENT",
                document_family="pending_family",
                version_number=4,
                valid_from="2025-06-01",
            ),
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_PENDING_NEXT",
                document_family="pending_family",
                version_number=5,
                valid_from="2027-01-01",
            ),
        ),
        reference_date=REFERENCE_DATE,
        expected_outdated_document_ids=(),
    )
