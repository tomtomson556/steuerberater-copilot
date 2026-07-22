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
    5. ``EVAL_RAG_FRESHNESS_BASELINE_OVERLAPPING_WINDOWS``
    6. ``EVAL_RAG_FRESHNESS_BASELINE_HIGHEST_EXPIRED_LOWER_CURRENT``
    7. ``EVAL_RAG_FRESHNESS_BASELINE_VALID_TO_EXACT_REFERENCE``
    8. ``EVAL_RAG_FRESHNESS_BASELINE_VERSION_GAP``
    """
    return (
        _superseded_case(),
        _validity_ended_case(),
        _current_despite_past_start_case(),
        _future_draft_not_outdated_case(),
        _overlapping_windows_case(),
        _highest_expired_lower_current_case(),
        _valid_to_exact_reference_case(),
        _version_gap_case(),
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


def _overlapping_windows_case() -> RAGFreshnessEvaluationCase:
    """Overlapping in-force windows: highest in-force version wins."""
    older = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_OVERLAP_V1",
        title="Synthetic overlap v1",
        content="Synthetic overlap policy version one still open.",
    )
    newer = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_OVERLAP_V2",
        title="Synthetic overlap v2",
        content="Synthetic overlap policy version two already started.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_OVERLAPPING_WINDOWS",
        source_documents=(older, newer),
        version_records=(
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_OVERLAP_V1",
                document_family="overlap_family",
                version_number=1,
                valid_from="2025-01-01",
                valid_to="2026-12-31",
            ),
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_OVERLAP_V2",
                document_family="overlap_family",
                version_number=2,
                valid_from="2026-01-01",
            ),
        ),
        reference_date=REFERENCE_DATE,
        expected_outdated_document_ids=("SYNTHETIC_FRESHNESS_OVERLAP_V1",),
    )


def _highest_expired_lower_current_case() -> RAGFreshnessEvaluationCase:
    """If the highest version already closed, a lower open version stays current."""
    lower = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_HIGHEST_EXPIRED_V1",
        title="Synthetic highest-expired lower",
        content="Synthetic lower policy still open after higher closed.",
    )
    higher = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_HIGHEST_EXPIRED_V2",
        title="Synthetic highest-expired higher",
        content="Synthetic higher policy already closed.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_HIGHEST_EXPIRED_LOWER_CURRENT",
        source_documents=(lower, higher),
        version_records=(
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_HIGHEST_EXPIRED_V1",
                document_family="highest_expired_family",
                version_number=1,
                valid_from="2024-01-01",
            ),
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_HIGHEST_EXPIRED_V2",
                document_family="highest_expired_family",
                version_number=2,
                valid_from="2025-01-01",
                valid_to="2026-01-01",
            ),
        ),
        reference_date=REFERENCE_DATE,
        expected_outdated_document_ids=("SYNTHETIC_FRESHNESS_HIGHEST_EXPIRED_V2",),
    )


def _valid_to_exact_reference_case() -> RAGFreshnessEvaluationCase:
    """valid_to equal to reference_date closes validity (inclusive closure)."""
    ended = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_VALID_TO_EXACT",
        title="Synthetic exact valid_to",
        content="Synthetic notice closing exactly on the reference date.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_VALID_TO_EXACT_REFERENCE",
        source_documents=(ended,),
        version_records=(
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_VALID_TO_EXACT",
                document_family="exact_boundary_family",
                version_number=1,
                valid_from="2025-01-01",
                valid_to=REFERENCE_DATE,
            ),
        ),
        reference_date=REFERENCE_DATE,
        expected_outdated_document_ids=("SYNTHETIC_FRESHNESS_VALID_TO_EXACT",),
    )


def _version_gap_case() -> RAGFreshnessEvaluationCase:
    """Version gaps are allowed; lower started versions are still superseded."""
    first = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_GAP_V1",
        title="Synthetic gap v1",
        content="Synthetic gap policy version one.",
    )
    third = SourceDocument(
        document_id="SYNTHETIC_FRESHNESS_GAP_V3",
        title="Synthetic gap v3",
        content="Synthetic gap policy version three.",
    )
    return RAGFreshnessEvaluationCase(
        evaluation_id="EVAL_RAG_FRESHNESS_BASELINE_VERSION_GAP",
        source_documents=(first, third),
        version_records=(
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_GAP_V1",
                document_family="gap_family",
                version_number=1,
                valid_from="2024-01-01",
            ),
            DocumentVersionRecord(
                document_id="SYNTHETIC_FRESHNESS_GAP_V3",
                document_family="gap_family",
                version_number=3,
                valid_from="2026-01-01",
            ),
        ),
        reference_date=REFERENCE_DATE,
        expected_outdated_document_ids=("SYNTHETIC_FRESHNESS_GAP_V1",),
    )
