from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.rag as rag
from steuerberater_copilot.rag import (
    ContradictionDetectionResult,
    DetectedClaimPassage,
    DetectedContradictionPair,
    SourceDocument,
    detect_passage_contradictions,
    detect_synthetic_claim_contradictions,
)


def test_detects_opposing_retention_sentences() -> None:
    first = _document(
        "SYNTHETIC_SOURCE_RETENTION_TEN",
        content="Synthetic orchard note. The retention period is 10 years. End.",
    )
    second = _document(
        "SYNTHETIC_SOURCE_RETENTION_SEVEN",
        content="Synthetic meadow note. The retention period is 7 years. End.",
    )

    result = detect_passage_contradictions((first, second))

    assert result.contradiction_present is True
    assert len(result.contradictions) == 1
    contradiction = result.contradictions[0]
    assert contradiction.claim_key == "retention_years"
    assert {
        (contradiction.first.document_id, contradiction.first.claim_value),
        (contradiction.second.document_id, contradiction.second.claim_value),
    } == {
        ("SYNTHETIC_SOURCE_RETENTION_TEN", "10"),
        ("SYNTHETIC_SOURCE_RETENTION_SEVEN", "7"),
    }
    assert {
        contradiction.first.supporting_text,
        contradiction.second.supporting_text,
    } == {
        "The retention period is 10 years.",
        "The retention period is 7 years.",
    }
    assert {contradiction.first.polarity, contradiction.second.polarity} == {"affirm"}


def test_subject_scoped_retention_conflicts_only_with_same_subject() -> None:
    result = detect_passage_contradictions(
        (
            _document(
                "SYNTHETIC_SOURCE_ALPHA_TEN",
                content="Client Alpha retention period is 10 years.",
            ),
            _document(
                "SYNTHETIC_SOURCE_ALPHA_SEVEN",
                content="Client Alpha retention period is 7 years.",
            ),
        )
    )

    assert result.contradiction_present is True
    assert result.contradictions[0].claim_key == "retention_years::client_alpha"


def test_different_subject_retention_sentences_do_not_collide() -> None:
    result = detect_passage_contradictions(
        (
            _document(
                "SYNTHETIC_SOURCE_ALPHA",
                content="Client Alpha retention period is 10 years.",
            ),
            _document(
                "SYNTHETIC_SOURCE_BETA",
                content="Client Beta retention period is 7 years.",
            ),
        )
    )

    assert result.contradiction_present is False
    assert result.contradictions == ()


def test_temporal_retention_sentences_are_not_unscoped_facts() -> None:
    result = detect_passage_contradictions(
        (
            _document(
                "SYNTHETIC_SOURCE_UNTIL",
                content="Until 2024, the retention period is 10 years.",
            ),
            _document(
                "SYNTHETIC_SOURCE_FROM",
                content="From 2025, the retention period is 7 years.",
            ),
        )
    )

    assert result.contradiction_present is False
    assert result.contradictions == ()


def test_negated_retention_sentence_conflicts_by_polarity() -> None:
    result = detect_passage_contradictions(
        (
            _document(
                "SYNTHETIC_SOURCE_RETENTION_AFFIRM",
                content="The retention period is 10 years.",
            ),
            _document(
                "SYNTHETIC_SOURCE_RETENTION_DENY",
                content="The retention period is not 10 years.",
            ),
        )
    )

    assert result.contradiction_present is True
    contradiction = result.contradictions[0]
    assert contradiction.claim_key == "retention_years"
    assert {
        (contradiction.first.claim_value, contradiction.first.polarity),
        (contradiction.second.claim_value, contradiction.second.polarity),
    } == {("10", "affirm"), ("10", "deny")}


def test_same_fact_paraphrase_is_not_a_contradiction() -> None:
    result = detect_passage_contradictions(
        (
            _document(
                "SYNTHETIC_SOURCE_RETENTION_DIGITS",
                content="Synthetic orchard. The retention period is 10 years.",
            ),
            _document(
                "SYNTHETIC_SOURCE_RETENTION_WORDS",
                content="Synthetic meadow. The retention period is ten years.",
            ),
            _document(
                "SYNTHETIC_SOURCE_RETENTION_GERMAN",
                content="Synthetic meadow. Die Aufbewahrungsfrist betraegt 10 Jahre.",
            ),
        )
    )

    assert result == ContradictionDetectionResult(
        contradiction_present=False,
        contradictions=(),
    )


def test_detects_opposing_deadline_sentences() -> None:
    result = detect_passage_contradictions(
        (
            _document(
                "SYNTHETIC_SOURCE_DEADLINE_2024",
                content="Synthetic calendar. The filing deadline is 2024-12-31.",
            ),
            _document(
                "SYNTHETIC_SOURCE_DEADLINE_2025",
                content="Synthetic calendar. The filing deadline is 2025-12-31.",
            ),
        )
    )

    assert result.contradiction_present is True
    assert result.contradictions[0].claim_key == "filing_deadline"
    assert {
        result.contradictions[0].first.supporting_text,
        result.contradictions[0].second.supporting_text,
    } == {
        "The filing deadline is 2024-12-31.",
        "The filing deadline is 2025-12-31.",
    }


def test_detects_opposing_archive_requirement_sentences() -> None:
    result = detect_passage_contradictions(
        (
            _document(
                "SYNTHETIC_SOURCE_ARCHIVE_REQUIRED",
                content="Synthetic archive. The archive is required.",
            ),
            _document(
                "SYNTHETIC_SOURCE_ARCHIVE_OPTIONAL",
                content="Synthetic archive. The archive is optional.",
            ),
        )
    )

    assert result.contradiction_present is True
    assert result.contradictions[0].claim_key == "archive_requirement"
    assert {
        result.contradictions[0].first.claim_value,
        result.contradictions[0].second.claim_value,
    } == {"required", "optional"}


def test_archive_not_required_normalizes_to_optional_conflict() -> None:
    result = detect_passage_contradictions(
        (
            _document(
                "SYNTHETIC_SOURCE_ARCHIVE_REQUIRED",
                content="Synthetic archive. The archive is required.",
            ),
            _document(
                "SYNTHETIC_SOURCE_ARCHIVE_NOT_REQUIRED",
                content="Synthetic archive. The archive is not required.",
            ),
        )
    )

    assert result.contradiction_present is True
    contradiction = result.contradictions[0]
    assert contradiction.claim_key == "archive_requirement"
    assert {
        (contradiction.first.claim_value, contradiction.first.polarity),
        (contradiction.second.claim_value, contradiction.second.polarity),
    } == {("required", "affirm"), ("optional", "affirm")}


def test_sentence_final_punctuation_is_stripped_for_matching() -> None:
    result = detect_passage_contradictions(
        (
            _document(
                "SYNTHETIC_SOURCE_ARCHIVE_REQUIRED",
                content="Synthetic archive. The archive is required!",
            ),
            _document(
                "SYNTHETIC_SOURCE_ARCHIVE_OPTIONAL",
                content="Synthetic archive. The archive is optional?",
            ),
        )
    )

    assert result.contradiction_present is True
    assert {
        result.contradictions[0].first.supporting_text,
        result.contradictions[0].second.supporting_text,
    } == {"The archive is required!", "The archive is optional?"}


def test_different_attributes_with_same_number_are_not_contradictions() -> None:
    result = detect_passage_contradictions(
        (
            _document(
                "SYNTHETIC_SOURCE_RETENTION_NUMBER",
                content="Synthetic orchard. The retention period is 10 years.",
            ),
            _document(
                "SYNTHETIC_SOURCE_DEADLINE_NUMBER",
                content="Synthetic meadow. The filing deadline is 2010-10-10.",
            ),
        )
    )

    assert result.contradiction_present is False
    assert result.contradictions == ()


def test_marker_noise_alone_is_ignored() -> None:
    result = detect_passage_contradictions(
        (
            _document(
                "SYNTHETIC_SOURCE_MARKER_ALPHA",
                content=(
                    "Synthetic orchard note. "
                    "[[SYNTHETIC_CLAIM retention_years=10]]"
                ),
            ),
            _document(
                "SYNTHETIC_SOURCE_MARKER_BETA",
                content=(
                    "Synthetic meadow note. "
                    "[[SYNTHETIC_CLAIM retention_years=7]]"
                ),
            ),
        )
    )

    assert result.contradiction_present is False
    assert result.contradictions == ()


def test_no_closed_template_facts_have_no_contradiction() -> None:
    result = detect_passage_contradictions(
        (
            _document(
                "SYNTHETIC_SOURCE_ORCHARD",
                content="Synthetic orchard content without closed template facts.",
            ),
            _document(
                "SYNTHETIC_SOURCE_MEADOW",
                content="Synthetic meadow content without closed template facts.",
            ),
        )
    )

    assert result.contradiction_present is False
    assert result.contradictions == ()


def test_informal_decade_wording_is_not_extracted() -> None:
    result = detect_passage_contradictions(
        (
            _document(
                "SYNTHETIC_SOURCE_DECADE",
                content="Orchard guidance. Records must be kept for a decade.",
            ),
            _document(
                "SYNTHETIC_SOURCE_SEVEN",
                content="Orchard guidance. The retention period is 7 years.",
            ),
        )
    )

    assert result.contradiction_present is False
    assert result.contradictions == ()


def test_detection_result_is_immutable_and_uses_slots() -> None:
    result = detect_passage_contradictions(
        (
            _document(
                "SYNTHETIC_SOURCE_A",
                content="Synthetic orchard. The archive is required.",
            ),
            _document(
                "SYNTHETIC_SOURCE_B",
                content="Synthetic meadow. The archive is optional.",
            ),
        )
    )

    with pytest.raises(FrozenInstanceError):
        result.contradiction_present = False

    assert not hasattr(result, "__dict__")
    assert ContradictionDetectionResult.__slots__ == (
        "contradiction_present",
        "contradictions",
    )
    assert DetectedClaimPassage.__slots__ == (
        "document_id",
        "supporting_text",
        "claim_key",
        "claim_value",
        "polarity",
    )
    assert DetectedContradictionPair.__slots__ == (
        "claim_key",
        "first",
        "second",
    )


def test_detection_result_rejects_inconsistent_bool_and_pairs() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^contradiction_present must be True exactly when contradictions "
            r"is non-empty\.$"
        ),
    ):
        ContradictionDetectionResult(
            contradiction_present=True,
            contradictions=(),
        )


def test_detected_claim_passage_defaults_to_affirm_polarity() -> None:
    passage = DetectedClaimPassage(
        document_id="SYNTHETIC_SOURCE_ALPHA",
        supporting_text="The archive is required.",
        claim_key="archive_requirement",
        claim_value="required",
    )

    assert passage.polarity == "affirm"


def test_detected_claim_passage_rejects_unknown_polarity() -> None:
    with pytest.raises(ValueError, match=r"^polarity must be 'affirm' or 'deny'\.$"):
        DetectedClaimPassage(
            document_id="SYNTHETIC_SOURCE_ALPHA",
            supporting_text="The archive is required.",
            claim_key="archive_requirement",
            claim_value="required",
            polarity="unknown",
        )


def test_detected_pair_rejects_non_conflicting_claims() -> None:
    first = DetectedClaimPassage(
        document_id="SYNTHETIC_SOURCE_ALPHA",
        supporting_text="The archive is required.",
        claim_key="archive_requirement",
        claim_value="required",
    )
    second = DetectedClaimPassage(
        document_id="SYNTHETIC_SOURCE_BETA",
        supporting_text="The archive is required.",
        claim_key="archive_requirement",
        claim_value="required",
    )

    with pytest.raises(
        ValueError,
        match=r"^passages must form a contradiction under closed rules\.$",
    ):
        DetectedContradictionPair(
            claim_key="archive_requirement",
            first=first,
            second=second,
        )


def test_rejects_non_tuple_documents() -> None:
    with pytest.raises(TypeError, match=r"^documents must be a tuple\.$"):
        detect_passage_contradictions([_document("SYNTHETIC_SOURCE_001")])


def test_rejects_non_source_document_entries() -> None:
    with pytest.raises(
        TypeError,
        match=r"^documents must contain only SourceDocument objects\.$",
    ):
        detect_passage_contradictions(("not-a-document",))


def test_rejects_duplicate_document_ids() -> None:
    with pytest.raises(
        ValueError,
        match=r"^documents must not contain duplicate document_id values\.$",
    ):
        detect_passage_contradictions(
            (
                _document("SYNTHETIC_SOURCE_DUPLICATE"),
                _document("SYNTHETIC_SOURCE_DUPLICATE"),
            )
        )


def test_alias_still_points_to_passage_detector() -> None:
    assert detect_synthetic_claim_contradictions is detect_passage_contradictions


def test_rag_package_exports_contradiction_detector_contract() -> None:
    assert rag.ContradictionDetectionResult is ContradictionDetectionResult
    assert rag.DetectedClaimPassage is DetectedClaimPassage
    assert rag.DetectedContradictionPair is DetectedContradictionPair
    assert rag.detect_passage_contradictions is detect_passage_contradictions
    assert rag.detect_synthetic_claim_contradictions is (
        detect_synthetic_claim_contradictions
    )


def _document(document_id: str, *, content: str | None = None) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=f"Synthetic title for {document_id}",
        content=content or f"Synthetic content for {document_id}.",
    )
