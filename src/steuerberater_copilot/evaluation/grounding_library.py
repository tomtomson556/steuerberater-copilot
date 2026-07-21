"""Deterministic synthetic baseline cases for offline grounding evaluation."""

from __future__ import annotations

from steuerberater_copilot.offline_mvp import (
    GroundedDraft,
    GroundedDraftCitation,
    StructuredDraftOutput,
)
from steuerberater_copilot.rag import SourceDocument

from .grounding_case import GroundingEvaluationCase, GroundingEvidenceLabel


def build_synthetic_grounding_evaluation_case_library() -> tuple[
    GroundingEvaluationCase, ...
]:
    """Build the nine fresh synthetic grounding baseline cases in stable order.

    Order is fixed and documented:

    1. ``EVAL_GROUNDING_BASELINE_FULL_MATCH``
    2. ``EVAL_GROUNDING_BASELINE_PARTIAL_COVERAGE``
    3. ``EVAL_GROUNDING_BASELINE_WRONG_PASSAGE``
    4. ``EVAL_GROUNDING_BASELINE_WRONG_SOURCE``
    5. ``EVAL_GROUNDING_BASELINE_MISSING_CITATIONS``
    6. ``EVAL_GROUNDING_BASELINE_NO_ACCEPTABLE_EVIDENCE``
    7. ``EVAL_GROUNDING_BASELINE_ALTERNATIVE_EVIDENCE``
    8. ``EVAL_GROUNDING_BASELINE_MIXED_CITATIONS``
    9. ``EVAL_GROUNDING_BASELINE_EMPTY_DRAFT``

    Each call returns a new immutable tuple of fresh ``GroundingEvaluationCase``
    instances. Cases can be assessed directly with
    ``assess_grounding_evaluation_case``.
    """
    return (
        _full_match_case(),
        _partial_coverage_case(),
        _wrong_passage_case(),
        _wrong_source_case(),
        _missing_citations_case(),
        _no_acceptable_evidence_case(),
        _alternative_evidence_case(),
        _mixed_citations_case(),
        _empty_draft_case(),
    )


def _full_match_case() -> GroundingEvaluationCase:
    """Two summary points with fully matching citations each."""
    document_alpha = SourceDocument(
        document_id="SYNTHETIC_GROUNDING_FULL_ALPHA",
        title="Synthetic orchard reference alpha",
        content="Synthetic orchard passage alpha for full match.",
    )
    document_beta = SourceDocument(
        document_id="SYNTHETIC_GROUNDING_FULL_BETA",
        title="Synthetic orchard reference beta",
        content="Synthetic orchard passage beta for full match.",
    )
    return GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_BASELINE_FULL_MATCH",
        source_documents=(document_alpha, document_beta),
        candidate_grounded_draft=_grounded_draft(
            summary_points=(
                "Synthetic first orchard summary point.",
                "Synthetic second orchard summary point.",
            ),
            citations=(
                _citation(
                    summary_point_index=0,
                    document_id="SYNTHETIC_GROUNDING_FULL_ALPHA",
                    supporting_text="Synthetic orchard passage alpha for full match.",
                ),
                _citation(
                    summary_point_index=1,
                    document_id="SYNTHETIC_GROUNDING_FULL_BETA",
                    supporting_text="Synthetic orchard passage beta for full match.",
                ),
            ),
        ),
        acceptable_evidence=(
            GroundingEvidenceLabel(
                summary_point_index=0,
                document_id="SYNTHETIC_GROUNDING_FULL_ALPHA",
                supporting_text="Synthetic orchard passage alpha for full match.",
            ),
            GroundingEvidenceLabel(
                summary_point_index=1,
                document_id="SYNTHETIC_GROUNDING_FULL_BETA",
                supporting_text="Synthetic orchard passage beta for full match.",
            ),
        ),
    )


def _partial_coverage_case() -> GroundingEvaluationCase:
    """Two summary points; only the first has a fully correct citation."""
    document = SourceDocument(
        document_id="SYNTHETIC_GROUNDING_PARTIAL_DOC",
        title="Synthetic orchard reference",
        content=(
            "Synthetic covered orchard passage. "
            "Synthetic uncovered orchard passage."
        ),
    )
    return GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_BASELINE_PARTIAL_COVERAGE",
        source_documents=(document,),
        candidate_grounded_draft=_grounded_draft(
            summary_points=(
                "Synthetic covered orchard summary point.",
                "Synthetic uncovered orchard summary point.",
            ),
            citations=(
                _citation(
                    summary_point_index=0,
                    document_id="SYNTHETIC_GROUNDING_PARTIAL_DOC",
                    supporting_text="Synthetic covered orchard passage.",
                ),
            ),
        ),
        acceptable_evidence=(
            GroundingEvidenceLabel(
                summary_point_index=0,
                document_id="SYNTHETIC_GROUNDING_PARTIAL_DOC",
                supporting_text="Synthetic covered orchard passage.",
            ),
            GroundingEvidenceLabel(
                summary_point_index=1,
                document_id="SYNTHETIC_GROUNDING_PARTIAL_DOC",
                supporting_text="Synthetic uncovered orchard passage.",
            ),
        ),
    )


def _wrong_passage_case() -> GroundingEvaluationCase:
    """Correct source with a non-accepted passage from the same document."""
    document = SourceDocument(
        document_id="SYNTHETIC_GROUNDING_WRONG_PASSAGE_DOC",
        title="Synthetic orchard reference",
        content=(
            "Synthetic accepted orchard passage. "
            "Synthetic rejected orchard passage."
        ),
    )
    return GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_BASELINE_WRONG_PASSAGE",
        source_documents=(document,),
        candidate_grounded_draft=_grounded_draft(
            summary_points=("Synthetic orchard summary point.",),
            citations=(
                _citation(
                    document_id="SYNTHETIC_GROUNDING_WRONG_PASSAGE_DOC",
                    supporting_text="Synthetic rejected orchard passage.",
                ),
            ),
        ),
        acceptable_evidence=(
            GroundingEvidenceLabel(
                summary_point_index=0,
                document_id="SYNTHETIC_GROUNDING_WRONG_PASSAGE_DOC",
                supporting_text="Synthetic accepted orchard passage.",
            ),
        ),
    )


def _wrong_source_case() -> GroundingEvaluationCase:
    """Wrong source with identical supporting text yields no match."""
    accepted = SourceDocument(
        document_id="SYNTHETIC_GROUNDING_WRONG_SOURCE_ACCEPTED",
        title="Synthetic orchard reference accepted",
        content="Synthetic shared orchard passage for wrong source.",
    )
    observed = SourceDocument(
        document_id="SYNTHETIC_GROUNDING_WRONG_SOURCE_OBSERVED",
        title="Synthetic orchard reference observed",
        content="Synthetic shared orchard passage for wrong source.",
    )
    return GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_BASELINE_WRONG_SOURCE",
        source_documents=(accepted, observed),
        candidate_grounded_draft=_grounded_draft(
            summary_points=("Synthetic orchard summary point.",),
            citations=(
                _citation(
                    document_id="SYNTHETIC_GROUNDING_WRONG_SOURCE_OBSERVED",
                    supporting_text=(
                        "Synthetic shared orchard passage for wrong source."
                    ),
                ),
            ),
        ),
        acceptable_evidence=(
            GroundingEvidenceLabel(
                summary_point_index=0,
                document_id="SYNTHETIC_GROUNDING_WRONG_SOURCE_ACCEPTED",
                supporting_text="Synthetic shared orchard passage for wrong source.",
            ),
        ),
    )


def _missing_citations_case() -> GroundingEvaluationCase:
    """Summary points with acceptable evidence but no candidate citations."""
    document = SourceDocument(
        document_id="SYNTHETIC_GROUNDING_MISSING_DOC",
        title="Synthetic orchard reference",
        content="Synthetic orchard passage for missing citations.",
    )
    return GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_BASELINE_MISSING_CITATIONS",
        source_documents=(document,),
        candidate_grounded_draft=_grounded_draft(
            summary_points=("Synthetic unsupported orchard summary point.",),
            citations=(),
        ),
        acceptable_evidence=(
            GroundingEvidenceLabel(
                summary_point_index=0,
                document_id="SYNTHETIC_GROUNDING_MISSING_DOC",
                supporting_text="Synthetic orchard passage for missing citations.",
            ),
        ),
    )


def _no_acceptable_evidence_case() -> GroundingEvaluationCase:
    """Citation present, but empty acceptable evidence makes the claim unsupported."""
    document = SourceDocument(
        document_id="SYNTHETIC_GROUNDING_NO_EVIDENCE_DOC",
        title="Synthetic orchard reference",
        content="Synthetic orchard passage without acceptable evidence.",
    )
    return GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_BASELINE_NO_ACCEPTABLE_EVIDENCE",
        source_documents=(document,),
        candidate_grounded_draft=_grounded_draft(
            summary_points=("Synthetic orchard summary point.",),
            citations=(
                _citation(
                    document_id="SYNTHETIC_GROUNDING_NO_EVIDENCE_DOC",
                    supporting_text=(
                        "Synthetic orchard passage without acceptable evidence."
                    ),
                ),
            ),
        ),
        acceptable_evidence=(),
    )


def _alternative_evidence_case() -> GroundingEvaluationCase:
    """Candidate citation matches the second of two acceptable evidence labels."""
    document_alpha = SourceDocument(
        document_id="SYNTHETIC_GROUNDING_ALT_ALPHA",
        title="Synthetic orchard reference alpha",
        content="Synthetic orchard passage alpha for alternative evidence.",
    )
    document_beta = SourceDocument(
        document_id="SYNTHETIC_GROUNDING_ALT_BETA",
        title="Synthetic orchard reference beta",
        content="Synthetic orchard passage beta for alternative evidence.",
    )
    return GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_BASELINE_ALTERNATIVE_EVIDENCE",
        source_documents=(document_alpha, document_beta),
        candidate_grounded_draft=_grounded_draft(
            summary_points=("Synthetic orchard summary point.",),
            citations=(
                _citation(
                    document_id="SYNTHETIC_GROUNDING_ALT_BETA",
                    supporting_text=(
                        "Synthetic orchard passage beta for alternative evidence."
                    ),
                ),
            ),
        ),
        acceptable_evidence=(
            GroundingEvidenceLabel(
                summary_point_index=0,
                document_id="SYNTHETIC_GROUNDING_ALT_ALPHA",
                supporting_text=(
                    "Synthetic orchard passage alpha for alternative evidence."
                ),
            ),
            GroundingEvidenceLabel(
                summary_point_index=0,
                document_id="SYNTHETIC_GROUNDING_ALT_BETA",
                supporting_text=(
                    "Synthetic orchard passage beta for alternative evidence."
                ),
            ),
        ),
    )


def _mixed_citations_case() -> GroundingEvaluationCase:
    """Two summary points with three mixed correct and incorrect citations."""
    accepted = SourceDocument(
        document_id="SYNTHETIC_GROUNDING_MIXED_ACCEPTED",
        title="Synthetic orchard reference accepted",
        content=(
            "Synthetic accepted orchard passage. "
            "Synthetic rejected orchard passage."
        ),
    )
    wrong_source = SourceDocument(
        document_id="SYNTHETIC_GROUNDING_MIXED_WRONG_SOURCE",
        title="Synthetic meadow reference",
        content="Synthetic meadow passage for mixed citations.",
    )
    return GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_BASELINE_MIXED_CITATIONS",
        source_documents=(accepted, wrong_source),
        candidate_grounded_draft=_grounded_draft(
            summary_points=(
                "Synthetic first orchard summary point.",
                "Synthetic second orchard summary point.",
            ),
            citations=(
                _citation(
                    summary_point_index=0,
                    document_id="SYNTHETIC_GROUNDING_MIXED_ACCEPTED",
                    supporting_text="Synthetic accepted orchard passage.",
                ),
                _citation(
                    summary_point_index=0,
                    document_id="SYNTHETIC_GROUNDING_MIXED_ACCEPTED",
                    supporting_text="Synthetic rejected orchard passage.",
                ),
                _citation(
                    summary_point_index=1,
                    document_id="SYNTHETIC_GROUNDING_MIXED_WRONG_SOURCE",
                    supporting_text="Synthetic meadow passage for mixed citations.",
                ),
            ),
        ),
        acceptable_evidence=(
            GroundingEvidenceLabel(
                summary_point_index=0,
                document_id="SYNTHETIC_GROUNDING_MIXED_ACCEPTED",
                supporting_text="Synthetic accepted orchard passage.",
            ),
            GroundingEvidenceLabel(
                summary_point_index=1,
                document_id="SYNTHETIC_GROUNDING_MIXED_ACCEPTED",
                supporting_text="Synthetic rejected orchard passage.",
            ),
        ),
    )


def _empty_draft_case() -> GroundingEvaluationCase:
    """Empty grounded draft without summary points, citations, or evidence."""
    return GroundingEvaluationCase(
        evaluation_id="EVAL_GROUNDING_BASELINE_EMPTY_DRAFT",
        source_documents=(),
        candidate_grounded_draft=_grounded_draft(summary_points=(), citations=()),
        acceptable_evidence=(),
    )


def _grounded_draft(
    *,
    summary_points: tuple[str, ...],
    citations: tuple[GroundedDraftCitation, ...],
) -> GroundedDraft:
    return GroundedDraft(
        structured_draft=StructuredDraftOutput(
            summary_points=summary_points,
            uncertainties=("Synthetic uncertainty.",) if summary_points else (),
            review_questions=(
                ("Synthetic review question?",) if summary_points else ()
            ),
        ),
        citations=citations,
    )


def _citation(
    *,
    summary_point_index: int = 0,
    document_id: str,
    supporting_text: str,
) -> GroundedDraftCitation:
    return GroundedDraftCitation(
        summary_point_index=summary_point_index,
        document_id=document_id,
        supporting_text=supporting_text,
    )
