"""Deterministic synthetic baseline cases for offline RAG contradiction evaluation.

Ground-truth labels are written independently of detector internals. Observed
detections come only from the closed-template extractor. One intentional
known-limitation case remains expected-positive while the detector cannot see
the conflict, so the suite is not optimized for a perfect pass rate.
"""

from __future__ import annotations

from steuerberater_copilot.rag import SourceDocument

from .rag_contradiction_case import ContradictionEvidenceLabel, RAGContradictionEvaluationCase


def build_synthetic_rag_contradiction_evaluation_case_library() -> tuple[
    RAGContradictionEvaluationCase, ...
]:
    """Build synthetic contradiction cases in stable order.

    Order:

    1. ``EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_CONFLICT``
    2. ``EVAL_RAG_CONTRADICTION_BASELINE_NO_CLAIM_OVERLAP``
    3. ``EVAL_RAG_CONTRADICTION_BASELINE_SAME_FACT_PARAPHRASE``
    4. ``EVAL_RAG_CONTRADICTION_BASELINE_DIFFERENT_SUBJECTS``
    5. ``EVAL_RAG_CONTRADICTION_BASELINE_TEMPORAL_SCOPES``
    6. ``EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_NEGATION``
    7. ``EVAL_RAG_CONTRADICTION_BASELINE_ARCHIVE_NOT_REQUIRED``
    8. ``EVAL_RAG_CONTRADICTION_BASELINE_MARKER_NOISE_IGNORED``
    9. ``EVAL_RAG_CONTRADICTION_BASELINE_KNOWN_LIMITATION_DECADE``
    """
    return (
        _retention_conflict_case(),
        _no_claim_overlap_case(),
        _same_fact_paraphrase_case(),
        _different_subjects_case(),
        _temporal_scopes_case(),
        _retention_negation_case(),
        _archive_not_required_case(),
        _marker_noise_ignored_case(),
        _known_limitation_decade_case(),
    )


def _retention_conflict_case() -> RAGContradictionEvaluationCase:
    older = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_RETENTION_TEN",
        title="Synthetic retention reference ten",
        content="Internal orchard note. The retention period is 10 years. End of note.",
    )
    newer = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_RETENTION_SEVEN",
        title="Synthetic retention reference seven",
        content="Internal orchard note. The retention period is 7 years. End of note.",
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_CONFLICT",
        source_documents=(older, newer),
        expected_contradiction_present=True,
        contradicting_passages=(
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_RETENTION_TEN",
                supporting_text="The retention period is 10 years.",
            ),
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_RETENTION_SEVEN",
                supporting_text="The retention period is 7 years.",
            ),
        ),
    )


def _no_claim_overlap_case() -> RAGContradictionEvaluationCase:
    meadow = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_ABSENT_MEADOW",
        title="Synthetic meadow reference",
        content="Synthetic meadow baseline describes orchard irrigation schedules.",
    )
    orchard = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_ABSENT_ORCHARD",
        title="Synthetic orchard reference",
        content="Synthetic orchard baseline describes meadow soil samples.",
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_NO_CLAIM_OVERLAP",
        source_documents=(meadow, orchard),
        expected_contradiction_present=False,
        contradicting_passages=(),
    )


def _same_fact_paraphrase_case() -> RAGContradictionEvaluationCase:
    digits = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_SAME_DIGITS",
        title="Synthetic retention digits",
        content="Policy summary. The retention period is 10 years.",
    )
    words = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_SAME_WORDS",
        title="Synthetic retention words",
        content="Policy summary. The retention period is ten years.",
    )
    german = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_SAME_DE",
        title="Synthetic retention german",
        content="Policy summary. Die Aufbewahrungsfrist betraegt 10 Jahre.",
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_SAME_FACT_PARAPHRASE",
        source_documents=(digits, words, german),
        expected_contradiction_present=False,
        contradicting_passages=(),
    )


def _different_subjects_case() -> RAGContradictionEvaluationCase:
    """Different client subjects must not collide on unscoped retention keys."""
    alpha = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_SUBJECT_ALPHA",
        title="Synthetic subject alpha",
        content="Client Alpha retention period is 10 years.",
    )
    beta = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_SUBJECT_BETA",
        title="Synthetic subject beta",
        content="Client Beta retention period is 7 years.",
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_DIFFERENT_SUBJECTS",
        source_documents=(alpha, beta),
        expected_contradiction_present=False,
        contradicting_passages=(),
    )


def _temporal_scopes_case() -> RAGContradictionEvaluationCase:
    """Temporally hedged retention sentences are not treated as unscoped facts."""
    until = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_TEMPORAL_UNTIL",
        title="Synthetic temporal until",
        content="Until 2024, the retention period is 10 years.",
    )
    starting = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_TEMPORAL_FROM",
        title="Synthetic temporal from",
        content="From 2025, the retention period is 7 years.",
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_TEMPORAL_SCOPES",
        source_documents=(until, starting),
        expected_contradiction_present=False,
        contradicting_passages=(),
    )


def _retention_negation_case() -> RAGContradictionEvaluationCase:
    affirmed = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_NEGATION_YES",
        title="Synthetic negation affirm",
        content="The retention period is 10 years.",
    )
    denied = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_NEGATION_NO",
        title="Synthetic negation deny",
        content="The retention period is not 10 years.",
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_NEGATION",
        source_documents=(affirmed, denied),
        expected_contradiction_present=True,
        contradicting_passages=(
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_NEGATION_YES",
                supporting_text="The retention period is 10 years.",
            ),
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_NEGATION_NO",
                supporting_text="The retention period is not 10 years.",
            ),
        ),
    )


def _archive_not_required_case() -> RAGContradictionEvaluationCase:
    required = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_ARCHIVE_REQUIRED",
        title="Synthetic archive required",
        content="Storage note. The archive is required.",
    )
    not_required = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_ARCHIVE_NOT_REQUIRED",
        title="Synthetic archive not required",
        content="Storage note. The archive is not required.",
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_ARCHIVE_NOT_REQUIRED",
        source_documents=(required, not_required),
        expected_contradiction_present=True,
        contradicting_passages=(
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_ARCHIVE_REQUIRED",
                supporting_text="The archive is required.",
            ),
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_ARCHIVE_NOT_REQUIRED",
                supporting_text="The archive is not required.",
            ),
        ),
    )


def _marker_noise_ignored_case() -> RAGContradictionEvaluationCase:
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


def _known_limitation_decade_case() -> RAGContradictionEvaluationCase:
    """Honest known limitation: informal 'decade' wording is outside templates.

    Ground truth still marks a real conflict. The closed-template detector is
    expected to miss it, so this case lowers the suite pass rate on purpose.
    """
    decade = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_LIMITATION_DECADE",
        title="Synthetic limitation decade",
        content="Orchard guidance. Records must be kept for a decade.",
    )
    seven = SourceDocument(
        document_id="SYNTHETIC_CONTRADICTION_LIMITATION_SEVEN",
        title="Synthetic limitation seven",
        content="Orchard guidance. The retention period is 7 years.",
    )
    return RAGContradictionEvaluationCase(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_KNOWN_LIMITATION_DECADE",
        source_documents=(decade, seven),
        expected_contradiction_present=True,
        contradicting_passages=(
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_LIMITATION_DECADE",
                supporting_text="Records must be kept for a decade.",
            ),
            ContradictionEvidenceLabel(
                document_id="SYNTHETIC_CONTRADICTION_LIMITATION_SEVEN",
                supporting_text="The retention period is 7 years.",
            ),
        ),
    )
