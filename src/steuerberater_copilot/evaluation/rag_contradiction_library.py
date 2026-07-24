"""Deterministic synthetic baseline cases for RAG contradiction evaluation."""

from __future__ import annotations

from steuerberater_copilot.rag import SourceDocument

from .rag_contradiction_case import (
    ContradictionEvidenceLabel,
    RAGContradictionEvaluationCase,
)


def build_synthetic_rag_contradiction_evaluation_case_library() -> tuple[
    RAGContradictionEvaluationCase, ...
]:
    """Build nine fresh contradiction baseline cases in stable order.

    Order is fixed and documented:

    1. ``EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_VALUES``
    2. ``EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_AFFIRM_NEGATION``
    3. ``EVAL_RAG_CONTRADICTION_BASELINE_SUBJECT_SCOPE``
    4. ``EVAL_RAG_CONTRADICTION_BASELINE_FILING_DEADLINES``
    5. ``EVAL_RAG_CONTRADICTION_BASELINE_ARCHIVE_REQUIREMENT``
    6. ``EVAL_RAG_CONTRADICTION_BASELINE_NORMALIZED_RETENTION``
    7. ``EVAL_RAG_CONTRADICTION_BASELINE_DIFFERENT_SUBJECTS``
    8. ``EVAL_RAG_CONTRADICTION_BASELINE_DIFFERENT_ATTRIBUTES``
    9. ``EVAL_RAG_CONTRADICTION_BASELINE_TEMPORAL_HEDGES``

    The first five cases contain exact positive evidence labels. The final four
    are negative controls. Every call returns fresh case, label, and source
    document instances for the existing closed-template detector.
    """
    return (
        _retention_values_case(),
        _retention_affirm_negation_case(),
        _subject_scope_case(),
        _filing_deadlines_case(),
        _archive_requirement_case(),
        _normalized_retention_case(),
        _different_subjects_case(),
        _different_attributes_case(),
        _temporal_hedges_case(),
    )


def _retention_values_case() -> RAGContradictionEvaluationCase:
    first_passage = "The retention period is 10 years."
    second_passage = "The retention period is 7 years."
    first_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_RETENTION_VALUES_TEN",
        title="Synthetic retention value reference ten",
        context="Synthetic retention value baseline alpha",
        passage=first_passage,
    )
    second_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_RETENTION_VALUES_SEVEN",
        title="Synthetic retention value reference seven",
        context="Synthetic retention value baseline beta",
        passage=second_passage,
    )
    return _positive_case(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_VALUES",
        first_document=first_document,
        first_passage=first_passage,
        second_document=second_document,
        second_passage=second_passage,
    )


def _retention_affirm_negation_case() -> RAGContradictionEvaluationCase:
    first_passage = "The retention period is 10 years."
    second_passage = "The retention period is not 10 years."
    first_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_RETENTION_POLARITY_AFFIRM",
        title="Synthetic retention affirmation reference",
        context="Synthetic retention affirmation baseline",
        passage=first_passage,
    )
    second_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_RETENTION_POLARITY_DENY",
        title="Synthetic retention negation reference",
        context="Synthetic retention negation baseline",
        passage=second_passage,
    )
    return _positive_case(
        evaluation_id=(
            "EVAL_RAG_CONTRADICTION_BASELINE_RETENTION_AFFIRM_NEGATION"
        ),
        first_document=first_document,
        first_passage=first_passage,
        second_document=second_document,
        second_passage=second_passage,
    )


def _subject_scope_case() -> RAGContradictionEvaluationCase:
    first_passage = "Client Alpha retention period is 10 years."
    second_passage = "Client Alpha retention period is 7 years."
    first_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_SUBJECT_ALPHA_TEN",
        title="Synthetic scoped retention reference ten",
        context="Synthetic scoped retention baseline alpha",
        passage=first_passage,
    )
    second_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_SUBJECT_ALPHA_SEVEN",
        title="Synthetic scoped retention reference seven",
        context="Synthetic scoped retention baseline beta",
        passage=second_passage,
    )
    return _positive_case(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_SUBJECT_SCOPE",
        first_document=first_document,
        first_passage=first_passage,
        second_document=second_document,
        second_passage=second_passage,
    )


def _filing_deadlines_case() -> RAGContradictionEvaluationCase:
    first_passage = "The filing deadline is 2026-09-30."
    second_passage = "The filing deadline is 2026-10-15."
    first_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_FILING_SEPTEMBER",
        title="Synthetic filing deadline reference September",
        context="Synthetic filing deadline baseline alpha",
        passage=first_passage,
    )
    second_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_FILING_OCTOBER",
        title="Synthetic filing deadline reference October",
        context="Synthetic filing deadline baseline beta",
        passage=second_passage,
    )
    return _positive_case(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_FILING_DEADLINES",
        first_document=first_document,
        first_passage=first_passage,
        second_document=second_document,
        second_passage=second_passage,
    )


def _archive_requirement_case() -> RAGContradictionEvaluationCase:
    first_passage = "The archive is required."
    second_passage = "The archive is optional."
    first_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_ARCHIVE_REQUIRED",
        title="Synthetic required archive reference",
        context="Synthetic archive requirement baseline alpha",
        passage=first_passage,
    )
    second_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_ARCHIVE_OPTIONAL",
        title="Synthetic optional archive reference",
        context="Synthetic archive requirement baseline beta",
        passage=second_passage,
    )
    return _positive_case(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_ARCHIVE_REQUIREMENT",
        first_document=first_document,
        first_passage=first_passage,
        second_document=second_document,
        second_passage=second_passage,
    )


def _normalized_retention_case() -> RAGContradictionEvaluationCase:
    first_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_NORMALIZED_DIGITS",
        title="Synthetic normalized retention reference digits",
        context="Synthetic normalized retention baseline alpha",
        passage="The retention period is 10 years.",
    )
    second_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_NORMALIZED_WORDS",
        title="Synthetic normalized retention reference words",
        context="Synthetic normalized retention baseline beta",
        passage="The retention period is ten years.",
    )
    return _negative_case(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_NORMALIZED_RETENTION",
        source_documents=(first_document, second_document),
    )


def _different_subjects_case() -> RAGContradictionEvaluationCase:
    first_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_SUBJECT_DIFFERENT_ALPHA",
        title="Synthetic client Alpha retention reference",
        context="Synthetic different subject baseline alpha",
        passage="Client Alpha retention period is 10 years.",
    )
    second_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_SUBJECT_DIFFERENT_BETA",
        title="Synthetic client Beta retention reference",
        context="Synthetic different subject baseline beta",
        passage="Client Beta retention period is 7 years.",
    )
    return _negative_case(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_DIFFERENT_SUBJECTS",
        source_documents=(first_document, second_document),
    )


def _different_attributes_case() -> RAGContradictionEvaluationCase:
    first_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_ATTRIBUTE_RETENTION",
        title="Synthetic retention attribute reference",
        context="Synthetic different attribute baseline retention",
        passage="The retention period is 10 years.",
    )
    second_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_ATTRIBUTE_FILING",
        title="Synthetic filing attribute reference",
        context="Synthetic different attribute baseline filing",
        passage="The filing deadline is 2026-10-10.",
    )
    return _negative_case(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_DIFFERENT_ATTRIBUTES",
        source_documents=(first_document, second_document),
    )


def _temporal_hedges_case() -> RAGContradictionEvaluationCase:
    first_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_TEMPORAL_UNTIL",
        title="Synthetic temporally bounded retention reference",
        context="Synthetic temporal hedge baseline alpha",
        passage="Until 2025, the retention period is 10 years.",
    )
    second_document = _document(
        document_id="SYNTHETIC_RAG_CONTRADICTION_TEMPORAL_FROM",
        title="Synthetic temporally effective retention reference",
        context="Synthetic temporal hedge baseline beta",
        passage="From 2026, the retention period is 7 years.",
    )
    return _negative_case(
        evaluation_id="EVAL_RAG_CONTRADICTION_BASELINE_TEMPORAL_HEDGES",
        source_documents=(first_document, second_document),
    )


def _positive_case(
    *,
    evaluation_id: str,
    first_document: SourceDocument,
    first_passage: str,
    second_document: SourceDocument,
    second_passage: str,
) -> RAGContradictionEvaluationCase:
    return RAGContradictionEvaluationCase(
        evaluation_id=evaluation_id,
        source_documents=(first_document, second_document),
        expected_contradiction_present=True,
        contradicting_passages=(
            ContradictionEvidenceLabel(
                document_id=first_document.document_id,
                supporting_text=first_passage,
            ),
            ContradictionEvidenceLabel(
                document_id=second_document.document_id,
                supporting_text=second_passage,
            ),
        ),
    )


def _negative_case(
    *,
    evaluation_id: str,
    source_documents: tuple[SourceDocument, ...],
) -> RAGContradictionEvaluationCase:
    return RAGContradictionEvaluationCase(
        evaluation_id=evaluation_id,
        source_documents=source_documents,
        expected_contradiction_present=False,
        contradicting_passages=(),
    )


def _document(
    *,
    document_id: str,
    title: str,
    context: str,
    passage: str,
) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=title,
        content=f"{context}. {passage}",
    )
