"""Deterministic synthetic baseline cases for offline RAG contradiction evaluation."""

from __future__ import annotations

from steuerberater_copilot.rag import SourceDocument

from .rag_contradiction_case import ContradictionEvidenceLabel, RAGContradictionEvaluationCase

RETENTION_TEN_YEARS = "The retention period is 10 years."
RETENTION_SEVEN_YEARS = "The retention period is 7 years."
RETENTION_TEN_YEARS_WORD = "The retention period is ten years."
RETENTION_TEN_YEARS_DE = "Die Aufbewahrungsfrist betraegt 10 Jahre."
DEADLINE_2024 = "The filing deadline is 2024-12-31."
DEADLINE_2025 = "The filing deadline is 2025-12-31."
ARCHIVE_REQUIRED = "The archive is required."
ARCHIVE_OPTIONAL = "The archive is optional."
UNRELATED_MEADOW = "Synthetic meadow baseline describes orchard irrigation schedules."
UNRELATED_ORCHARD = "Synthetic orchard baseline describes meadow soil samples."


def build_synthetic_rag_contradiction_evaluation_case_library() -> tuple[
    RAGContradictionEvaluationCase, ...
]:
    """Build synthetic contradiction cases in stable order.

    Ground truth describes real opposing facts in the synthetic corpus. Observed
    detections come only from the closed-template extractor and remain separate.

    Order:

    1. ``EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_CONFLICT``
    2. ``EVAL_RAG_CONTRADICTION_BASELINE_NO_CLAIM_OVERLAP``
    3. ``EVAL_RAG_CONTRADICTION_BASELINE_SAME_FACT_PARAPHRASE``
    4. ``EVAL_RAG_CONTRADICTION_BASELINE_DEADLINE_CONFLICT``
    5. ``EVAL_RAG_CONTRADICTION_BASELINE_DIFFERENT_ATTRIBUTES_SAME_NUMBER``
    6. ``EVAL_RAG_CONTRADICTION_BASELINE_ARCHIVE_REQUIREMENT_CONFLICT``
    7. ``EVAL_RAG_CONTRADICTION_BASELINE_MARKER_NOISE_IGNORED``
    """
    return (
        _retention_conflict_case(),
        _no_claim_overlap_case(),
        _same_fact_paraphrase_case(),
        _deadline_conflict_case(),
        _different_attributes_same_number_case(),
        _archive_requirement_conflict_case(),
        _marker_noise_ignored_case(),
    )


def _retention_conflict_case() -> RAGContradictionEvaluationCase:
    older = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_RETENTION_TEN",
        title="Synthetic retention reference ten",
        content=f"Internal orchard note. {RETENTION_TEN_YEARS} End of note.",
    )
    newer = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_RETENTION_SEVEN",
        title="Synthetic retention reference seven",
        content=f"Internal orchard note. {RETENTION_SEVEN_YEARS} End of note.",
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_CONFLICT",
        source_documents=(older, newer),
        expected_contradiction_present=True,
        contradicting_passages=(
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_RETENTION_TEN",
                supporting_text=RETENTION_TEN_YEARS,
            ),
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_RETENTION_SEVEN",
                supporting_text=RETENTION_SEVEN_YEARS,
            ),
        ),
    )


def _no_claim_overlap_case() -> RAGContradictionEvaluationCase:
    meadow = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_ABSENT_MEADOW",
        title="Synthetic meadow reference",
        content=UNRELATED_MEADOW,
    )
    orchard = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_ABSENT_ORCHARD",
        title="Synthetic orchard reference",
        content=UNRELATED_ORCHARD,
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_NO_CLAIM_OVERLAP",
        source_documents=(meadow, orchard),
        expected_contradiction_present=False,
        contradicting_passages=(),
    )


def _same_fact_paraphrase_case() -> RAGContradictionEvaluationCase:
    """Same retention fact in digit and word form must not be a contradiction."""
    digits = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_SAME_DIGITS",
        title="Synthetic retention digits",
        content=f"Policy summary. {RETENTION_TEN_YEARS}",
    )
    words = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_SAME_WORDS",
        title="Synthetic retention words",
        content=f"Policy summary. {RETENTION_TEN_YEARS_WORD}",
    )
    german = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_SAME_DE",
        title="Synthetic retention german",
        content=f"Policy summary. {RETENTION_TEN_YEARS_DE}",
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_SAME_FACT_PARAPHRASE",
        source_documents=(digits, words, german),
        expected_contradiction_present=False,
        contradicting_passages=(),
    )


def _deadline_conflict_case() -> RAGContradictionEvaluationCase:
    older = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_DEADLINE_2024",
        title="Synthetic deadline 2024",
        content=f"Calendar note. {DEADLINE_2024}",
    )
    newer = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_DEADLINE_2025",
        title="Synthetic deadline 2025",
        content=f"Calendar note. {DEADLINE_2025}",
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_DEADLINE_CONFLICT",
        source_documents=(older, newer),
        expected_contradiction_present=True,
        contradicting_passages=(
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_DEADLINE_2024",
                supporting_text=DEADLINE_2024,
            ),
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_DEADLINE_2025",
                supporting_text=DEADLINE_2025,
            ),
        ),
    )


def _different_attributes_same_number_case() -> RAGContradictionEvaluationCase:
    """Same numeric token on different attributes is not a contradiction."""
    retention = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_ATTR_RETENTION",
        title="Synthetic attribute retention",
        content="The retention period is 10 years.",
    )
    deadline = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_ATTR_DEADLINE",
        title="Synthetic attribute deadline",
        content="The filing deadline is 2010-10-10.",
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_DIFFERENT_ATTRIBUTES_SAME_NUMBER",
        source_documents=(retention, deadline),
        expected_contradiction_present=False,
        contradicting_passages=(),
    )


def _archive_requirement_conflict_case() -> RAGContradictionEvaluationCase:
    required = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_ARCHIVE_REQUIRED",
        title="Synthetic archive required",
        content=f"Storage note. {ARCHIVE_REQUIRED}",
    )
    optional = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_ARCHIVE_OPTIONAL",
        title="Synthetic archive optional",
        content=f"Storage note. {ARCHIVE_OPTIONAL}",
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_ARCHIVE_REQUIREMENT_CONFLICT",
        source_documents=(required, optional),
        expected_contradiction_present=True,
        contradicting_passages=(
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_ARCHIVE_REQUIRED",
                supporting_text=ARCHIVE_REQUIRED,
            ),
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_ARCHIVE_OPTIONAL",
                supporting_text=ARCHIVE_OPTIONAL,
            ),
        ),
    )


def _marker_noise_ignored_case() -> RAGContradictionEvaluationCase:
    """Artificial marker tags alone must not create a contradiction signal."""
    first = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_MARKER_ALPHA",
        title="Synthetic marker alpha",
        content=(
            "Synthetic meadow inventory remains unchanged. "
            "[[SYNTHETIC_CLAIM retention_years=10]]"
        ),
    )
    second = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_MARKER_BETA",
        title="Synthetic marker beta",
        content=(
            "Synthetic meadow inventory remains unchanged. "
            "[[SYNTHETIC_CLAIM retention_years=7]]"
        ),
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_MARKER_NOISE_IGNORED",
        source_documents=(first, second),
        expected_contradiction_present=False,
        contradicting_passages=(),
    )
