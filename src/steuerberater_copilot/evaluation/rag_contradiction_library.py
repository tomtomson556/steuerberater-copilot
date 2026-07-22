"""Deterministic synthetic baseline cases for offline RAG contradiction evaluation."""

from __future__ import annotations

from steuerberater_copilot.rag import SourceDocument

from .rag_contradiction_case import ContradictionEvidenceLabel, RAGContradictionEvaluationCase

CLAIM_DEADLINE_2024 = "[[SYNTHETIC_CLAIM deadline=2024-12-31]]"
CLAIM_DEADLINE_2025 = "[[SYNTHETIC_CLAIM deadline=2025-12-31]]"
CLAIM_RETENTION_10 = "[[SYNTHETIC_CLAIM retention_years=10]]"
CLAIM_RETENTION_10_AGAIN = "[[SYNTHETIC_CLAIM retention_years=10]]"


def build_synthetic_rag_contradiction_evaluation_case_library() -> tuple[
    RAGContradictionEvaluationCase, ...
]:
    """Build the four fresh synthetic contradiction baseline cases in stable order.

    Order is fixed and documented:

    1. ``EVAL_RAG_CONTRADICTION_BASELINE_PRESENT``
    2. ``EVAL_RAG_CONTRADICTION_BASELINE_ABSENT``
    3. ``EVAL_RAG_CONTRADICTION_BASELINE_SAME_VALUE``
    4. ``EVAL_RAG_CONTRADICTION_BASELINE_MULTI_KEY``
    """
    return (
        _present_case(),
        _absent_case(),
        _same_value_case(),
        _multi_key_case(),
    )


def _present_case() -> RAGContradictionEvaluationCase:
    older = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_DEADLINE_2024",
        title="Synthetic deadline reference 2024",
        content=f"Synthetic orchard note. {CLAIM_DEADLINE_2024} End.",
    )
    newer = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_DEADLINE_2025",
        title="Synthetic deadline reference 2025",
        content=f"Synthetic orchard note. {CLAIM_DEADLINE_2025} End.",
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_PRESENT",
        source_documents=(older, newer),
        expected_contradiction_present=True,
        contradicting_passages=(
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_DEADLINE_2024",
                supporting_text=CLAIM_DEADLINE_2024,
            ),
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_DEADLINE_2025",
                supporting_text=CLAIM_DEADLINE_2025,
            ),
        ),
    )


def _absent_case() -> RAGContradictionEvaluationCase:
    meadow = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_ABSENT_MEADOW",
        title="Synthetic meadow reference",
        content="Synthetic meadow baseline without claim markers.",
    )
    orchard = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_ABSENT_ORCHARD",
        title="Synthetic orchard reference",
        content="Synthetic orchard baseline without claim markers.",
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_ABSENT",
        source_documents=(meadow, orchard),
        expected_contradiction_present=False,
        contradicting_passages=(),
    )


def _same_value_case() -> RAGContradictionEvaluationCase:
    first = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_SAME_ALPHA",
        title="Synthetic retention alpha",
        content=f"Synthetic retention note. {CLAIM_RETENTION_10} End.",
    )
    second = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_SAME_BETA",
        title="Synthetic retention beta",
        content=f"Synthetic retention note. {CLAIM_RETENTION_10_AGAIN} End.",
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_SAME_VALUE",
        source_documents=(first, second),
        expected_contradiction_present=False,
        contradicting_passages=(),
    )


def _multi_key_case() -> RAGContradictionEvaluationCase:
    """Only the first contradicting key pair is reported by the runner baseline."""
    deadline_old = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_MULTI_DEADLINE_OLD",
        title="Synthetic multi deadline old",
        content=f"Synthetic multi note. {CLAIM_DEADLINE_2024}",
    )
    deadline_new = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_MULTI_DEADLINE_NEW",
        title="Synthetic multi deadline new",
        content=f"Synthetic multi note. {CLAIM_DEADLINE_2025}",
    )
    retention = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_MULTI_RETENTION",
        title="Synthetic multi retention",
        content=f"Synthetic multi note. {CLAIM_RETENTION_10}",
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_MULTI_KEY",
        source_documents=(deadline_old, deadline_new, retention),
        expected_contradiction_present=True,
        contradicting_passages=(
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_MULTI_DEADLINE_OLD",
                supporting_text=CLAIM_DEADLINE_2024,
            ),
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_MULTI_DEADLINE_NEW",
                supporting_text=CLAIM_DEADLINE_2025,
            ),
        ),
    )
