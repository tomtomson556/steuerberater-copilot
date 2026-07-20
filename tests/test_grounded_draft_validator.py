import pytest

import steuerberater_copilot.offline_mvp as offline_mvp
from steuerberater_copilot.offline_mvp import (
    GroundedDraft,
    GroundedDraftCitation,
    GroundedDraftValidationError,
    validate_grounded_draft,
)
from steuerberater_copilot.offline_mvp.structured_output import StructuredDraftOutput
from steuerberater_copilot.rag import SourceDocument


def test_validate_grounded_draft_accepts_valid_citations() -> None:
    validate_grounded_draft(
        _grounded_draft(
            summary_points=("Synthetic first summary point.",),
            citations=(
                _citation(
                    summary_point_index=0,
                    document_id="SYNTHETIC_SOURCE_001",
                    supporting_text="Exact synthetic supporting passage one.",
                ),
            ),
        ),
        retrieved_documents=(
            _source_document(
                document_id="SYNTHETIC_SOURCE_001",
                content=(
                    "Prefix. Exact synthetic supporting passage one. Suffix."
                ),
            ),
        ),
    )


def test_validate_grounded_draft_accepts_multiple_summary_points_and_citations() -> None:
    validate_grounded_draft(
        _grounded_draft(
            summary_points=(
                "Synthetic first summary point.",
                "Synthetic second summary point.",
            ),
            citations=(
                _citation(
                    summary_point_index=0,
                    document_id="SYNTHETIC_SOURCE_001",
                    supporting_text="Exact synthetic supporting passage one.",
                ),
                _citation(
                    summary_point_index=0,
                    document_id="SYNTHETIC_SOURCE_002",
                    supporting_text="Second synthetic supporting passage.",
                ),
                _citation(
                    summary_point_index=1,
                    document_id="SYNTHETIC_SOURCE_002",
                    supporting_text="Exact synthetic supporting passage two.",
                ),
            ),
        ),
        retrieved_documents=(
            _source_document(
                document_id="SYNTHETIC_SOURCE_001",
                content="Exact synthetic supporting passage one.",
            ),
            _source_document(
                document_id="SYNTHETIC_SOURCE_002",
                content=(
                    "Second synthetic supporting passage. "
                    "Exact synthetic supporting passage two."
                ),
            ),
        ),
    )


def test_validate_grounded_draft_accepts_empty_summary_points_and_citations() -> None:
    validate_grounded_draft(
        _grounded_draft(summary_points=(), citations=()),
        retrieved_documents=(),
    )


def test_validate_grounded_draft_rejects_unknown_document_reference() -> None:
    with pytest.raises(GroundedDraftValidationError) as exc_info:
        validate_grounded_draft(
            _grounded_draft(
                citations=(
                    _citation(
                        document_id="SYNTHETIC_SOURCE_UNKNOWN",
                        supporting_text="Exact synthetic supporting passage one.",
                    ),
                ),
            ),
            retrieved_documents=(
                _source_document(
                    content="Exact synthetic supporting passage one.",
                ),
            ),
        )

    error = exc_info.value
    assert error.rule == "unknown_document"
    assert error.citation_index == 0
    assert error.summary_point_index == 0
    assert "unknown_document" in str(error)
    assert "citation_index=0" in str(error)


def test_validate_grounded_draft_rejects_supporting_text_missing_from_document() -> None:
    with pytest.raises(GroundedDraftValidationError) as exc_info:
        validate_grounded_draft(
            _grounded_draft(
                citations=(
                    _citation(
                        supporting_text=(
                            "Synthetic passage absent from the referenced document."
                        ),
                    ),
                ),
            ),
            retrieved_documents=(
                _source_document(
                    content="Exact synthetic supporting passage one.",
                ),
            ),
        )

    error = exc_info.value
    assert error.rule == "supporting_text_not_found"
    assert error.citation_index == 0
    assert error.summary_point_index == 0
    assert "supporting_text_not_found" in str(error)


def test_validate_grounded_draft_requires_supporting_text_in_referenced_document_only() -> (
    None
):
    with pytest.raises(
        GroundedDraftValidationError,
        match="supporting_text_not_found",
    ) as exc_info:
        validate_grounded_draft(
            _grounded_draft(
                citations=(
                    _citation(
                        document_id="SYNTHETIC_SOURCE_001",
                        supporting_text="Exact synthetic supporting passage two.",
                    ),
                ),
            ),
            retrieved_documents=(
                _source_document(
                    document_id="SYNTHETIC_SOURCE_001",
                    content="Exact synthetic supporting passage one.",
                ),
                _source_document(
                    document_id="SYNTHETIC_SOURCE_002",
                    content="Exact synthetic supporting passage two.",
                ),
            ),
        )

    assert exc_info.value.citation_index == 0


def test_validate_grounded_draft_does_not_treat_title_as_citable_content() -> None:
    with pytest.raises(
        GroundedDraftValidationError,
        match="supporting_text_not_found",
    ):
        validate_grounded_draft(
            _grounded_draft(
                citations=(
                    _citation(
                        supporting_text="Exact synthetic title passage.",
                    ),
                ),
            ),
            retrieved_documents=(
                _source_document(
                    title="Exact synthetic title passage.",
                    content="Unrelated synthetic document body.",
                ),
            ),
        )


def test_validate_grounded_draft_uses_exact_whitespace_and_unicode_matching() -> None:
    supporting_text = "\nExact synthetic Cafe\u0301 supporting passage.\n"
    validate_grounded_draft(
        _grounded_draft(
            citations=(_citation(supporting_text=supporting_text),),
        ),
        retrieved_documents=(
            _source_document(
                content=f"Prefix{supporting_text}Suffix",
            ),
        ),
    )

    with pytest.raises(
        GroundedDraftValidationError,
        match="supporting_text_not_found",
    ):
        validate_grounded_draft(
            _grounded_draft(
                citations=(
                    _citation(
                        supporting_text=(
                            " Exact synthetic Cafe\u0301 supporting passage. "
                        ),
                    ),
                ),
            ),
            retrieved_documents=(
                _source_document(
                    content=f"Prefix{supporting_text}Suffix",
                ),
            ),
        )

    with pytest.raises(
        GroundedDraftValidationError,
        match="supporting_text_not_found",
    ):
        validate_grounded_draft(
            _grounded_draft(
                citations=(
                    _citation(
                        supporting_text="Exact synthetic Caf\u00e9 supporting passage.",
                    ),
                ),
            ),
            retrieved_documents=(
                _source_document(
                    content="Exact synthetic Cafe\u0301 supporting passage.",
                ),
            ),
        )


def test_validate_grounded_draft_rejects_missing_citation_coverage() -> None:
    with pytest.raises(GroundedDraftValidationError) as exc_info:
        validate_grounded_draft(
            _grounded_draft(
                summary_points=(
                    "Synthetic first summary point.",
                    "Synthetic second summary point.",
                ),
                citations=(
                    _citation(
                        summary_point_index=0,
                        supporting_text="Exact synthetic supporting passage one.",
                    ),
                ),
            ),
            retrieved_documents=(
                _source_document(
                    content="Exact synthetic supporting passage one.",
                ),
            ),
        )

    error = exc_info.value
    assert error.rule == "missing_citation_coverage"
    assert error.citation_index is None
    assert error.summary_point_index == 1
    assert "missing_citation_coverage" in str(error)
    assert "summary_point_index=1" in str(error)


def test_validate_grounded_draft_rejects_empty_citations_when_summary_points_exist() -> (
    None
):
    with pytest.raises(
        GroundedDraftValidationError,
        match="missing_citation_coverage",
    ) as exc_info:
        validate_grounded_draft(
            _grounded_draft(
                summary_points=("Synthetic first summary point.",),
                citations=(),
            ),
            retrieved_documents=(_source_document(),),
        )

    assert exc_info.value.summary_point_index == 0


def test_validate_grounded_draft_stops_at_first_citation_error() -> None:
    with pytest.raises(GroundedDraftValidationError) as exc_info:
        validate_grounded_draft(
            _grounded_draft(
                summary_points=(
                    "Synthetic first summary point.",
                    "Synthetic second summary point.",
                ),
                citations=(
                    _citation(
                        summary_point_index=0,
                        document_id="SYNTHETIC_SOURCE_UNKNOWN",
                        supporting_text="Exact synthetic supporting passage one.",
                    ),
                    _citation(
                        summary_point_index=1,
                        document_id="SYNTHETIC_SOURCE_001",
                        supporting_text="Absent synthetic supporting passage.",
                    ),
                ),
            ),
            retrieved_documents=(
                _source_document(
                    content="Exact synthetic supporting passage one.",
                ),
            ),
        )

    error = exc_info.value
    assert error.rule == "unknown_document"
    assert error.citation_index == 0
    assert "supporting_text_not_found" not in str(error)
    assert "missing_citation_coverage" not in str(error)


def test_validate_grounded_draft_checks_citations_before_coverage() -> None:
    with pytest.raises(GroundedDraftValidationError) as exc_info:
        validate_grounded_draft(
            _grounded_draft(
                summary_points=(
                    "Synthetic first summary point.",
                    "Synthetic second summary point.",
                ),
                citations=(
                    _citation(
                        summary_point_index=0,
                        supporting_text="Absent synthetic supporting passage.",
                    ),
                ),
            ),
            retrieved_documents=(
                _source_document(
                    content="Exact synthetic supporting passage one.",
                ),
            ),
        )

    error = exc_info.value
    assert error.rule == "supporting_text_not_found"
    assert error.citation_index == 0
    assert "missing_citation_coverage" not in str(error)


def test_validate_grounded_draft_reports_first_uncovered_summary_point() -> None:
    with pytest.raises(GroundedDraftValidationError) as exc_info:
        validate_grounded_draft(
            _grounded_draft(
                summary_points=(
                    "Synthetic first summary point.",
                    "Synthetic second summary point.",
                    "Synthetic third summary point.",
                ),
                citations=(
                    _citation(
                        summary_point_index=1,
                        supporting_text="Exact synthetic supporting passage one.",
                    ),
                ),
            ),
            retrieved_documents=(
                _source_document(
                    content="Exact synthetic supporting passage one.",
                ),
            ),
        )

    error = exc_info.value
    assert error.rule == "missing_citation_coverage"
    assert error.summary_point_index == 0


def test_validate_grounded_draft_rejects_non_grounded_draft_input() -> None:
    with pytest.raises(TypeError, match=r"^grounded_draft must be a GroundedDraft\.$"):
        validate_grounded_draft(  # type: ignore[arg-type]
            "not a grounded draft",
            retrieved_documents=(),
        )


def test_validate_grounded_draft_rejects_non_tuple_retrieved_documents() -> None:
    with pytest.raises(TypeError, match=r"^retrieved_documents must be a tuple\.$"):
        validate_grounded_draft(
            _grounded_draft(summary_points=(), citations=()),
            retrieved_documents=[_source_document()],  # type: ignore[arg-type]
        )


def test_validate_grounded_draft_rejects_foreign_retrieved_document_entries() -> None:
    with pytest.raises(
        TypeError,
        match=r"^retrieved_documents must contain only SourceDocument objects\.$",
    ):
        validate_grounded_draft(
            _grounded_draft(summary_points=(), citations=()),
            retrieved_documents=("not a source document",),  # type: ignore[arg-type]
        )


def test_validate_grounded_draft_rejects_duplicate_retrieved_document_ids() -> None:
    with pytest.raises(
        ValueError,
        match=r"^retrieved_documents must not contain duplicate document_id values\.$",
    ):
        validate_grounded_draft(
            _grounded_draft(summary_points=(), citations=()),
            retrieved_documents=(
                _source_document(content="First synthetic body."),
                _source_document(content="Second synthetic body."),
            ),
        )


def test_validate_grounded_draft_public_export() -> None:
    assert offline_mvp.GroundedDraftValidationError is GroundedDraftValidationError
    assert offline_mvp.validate_grounded_draft is validate_grounded_draft
    assert "GroundedDraftValidationError" in offline_mvp.__all__
    assert "validate_grounded_draft" in offline_mvp.__all__


def _grounded_draft(
    *,
    summary_points: tuple[str, ...] = ("Synthetic first summary point.",),
    citations: tuple[GroundedDraftCitation, ...] = (),
) -> GroundedDraft:
    return GroundedDraft(
        structured_draft=StructuredDraftOutput(
            summary_points=summary_points,
            uncertainties=("Synthetic uncertainty remains for review.",),
            review_questions=("Which synthetic assumption requires review?",),
        ),
        citations=citations,
    )


def _citation(
    *,
    summary_point_index: int = 0,
    document_id: str = "SYNTHETIC_SOURCE_001",
    supporting_text: str = "Exact synthetic supporting passage one.",
) -> GroundedDraftCitation:
    return GroundedDraftCitation(
        summary_point_index=summary_point_index,
        document_id=document_id,
        supporting_text=supporting_text,
    )


def _source_document(
    *,
    document_id: str = "SYNTHETIC_SOURCE_001",
    title: str = "Synthetic source title",
    content: str = "Exact synthetic supporting passage one.",
) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=title,
        content=content,
    )
