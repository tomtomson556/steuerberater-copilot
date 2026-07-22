from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.rag as rag
from steuerberater_copilot.rag import (
    ContradictionDetectionResult,
    DetectedClaimPassage,
    DetectedContradictionPair,
    SourceDocument,
    detect_synthetic_claim_contradictions,
)


def test_detects_opposing_synthetic_claim_markers() -> None:
    first = _document(
        "SYNTHETIC_SOURCE_ORCHARD_OPEN",
        content="Synthetic orchard note [[SYNTHETIC_CLAIM orchard_status=open]].",
    )
    second = _document(
        "SYNTHETIC_SOURCE_ORCHARD_CLOSED",
        content="Synthetic meadow note [[SYNTHETIC_CLAIM orchard_status=closed]].",
    )

    result = detect_synthetic_claim_contradictions((first, second))

    assert result.contradiction_present is True
    assert len(result.contradictions) == 1
    contradiction = result.contradictions[0]
    assert contradiction.claim_key == "orchard_status"
    assert {
        (contradiction.first.document_id, contradiction.first.claim_value),
        (contradiction.second.document_id, contradiction.second.claim_value),
    } == {
        ("SYNTHETIC_SOURCE_ORCHARD_OPEN", "open"),
        ("SYNTHETIC_SOURCE_ORCHARD_CLOSED", "closed"),
    }
    assert {
        contradiction.first.supporting_text,
        contradiction.second.supporting_text,
    } == {
        "[[SYNTHETIC_CLAIM orchard_status=open]]",
        "[[SYNTHETIC_CLAIM orchard_status=closed]]",
    }


def test_same_value_claims_are_not_contradictions() -> None:
    result = detect_synthetic_claim_contradictions(
        (
            _document(
                "SYNTHETIC_SOURCE_RETENTION_ALPHA",
                content="Synthetic orchard [[SYNTHETIC_CLAIM retention_years=10]].",
            ),
            _document(
                "SYNTHETIC_SOURCE_RETENTION_BETA",
                content="Synthetic meadow [[SYNTHETIC_CLAIM retention_years=10]].",
            ),
        )
    )

    assert result == ContradictionDetectionResult(
        contradiction_present=False,
        contradictions=(),
    )


def test_no_markers_have_no_contradiction() -> None:
    result = detect_synthetic_claim_contradictions(
        (
            _document(
                "SYNTHETIC_SOURCE_ORCHARD",
                content="Synthetic orchard content without claim markers.",
            ),
            _document(
                "SYNTHETIC_SOURCE_MEADOW",
                content="Synthetic meadow content without claim markers.",
            ),
        )
    )

    assert result.contradiction_present is False
    assert result.contradictions == ()


def test_detection_result_is_immutable_and_uses_slots() -> None:
    result = detect_synthetic_claim_contradictions(
        (
            _document(
                "SYNTHETIC_SOURCE_A",
                content="Synthetic orchard [[SYNTHETIC_CLAIM status=alpha]].",
            ),
            _document(
                "SYNTHETIC_SOURCE_B",
                content="Synthetic meadow [[SYNTHETIC_CLAIM status=beta]].",
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


def test_detected_pair_rejects_same_claim_values() -> None:
    first = DetectedClaimPassage(
        document_id="SYNTHETIC_SOURCE_ALPHA",
        supporting_text="[[SYNTHETIC_CLAIM status=open]]",
        claim_key="status",
        claim_value="open",
    )
    second = DetectedClaimPassage(
        document_id="SYNTHETIC_SOURCE_BETA",
        supporting_text="[[SYNTHETIC_CLAIM status=open]]",
        claim_key="status",
        claim_value="open",
    )

    with pytest.raises(
        ValueError,
        match=r"^contradicting passages must have different claim values\.$",
    ):
        DetectedContradictionPair(
            claim_key="status",
            first=first,
            second=second,
        )


def test_rejects_non_tuple_documents() -> None:
    with pytest.raises(TypeError, match=r"^documents must be a tuple\.$"):
        detect_synthetic_claim_contradictions([_document("SYNTHETIC_SOURCE_001")])


def test_rejects_non_source_document_entries() -> None:
    with pytest.raises(
        TypeError,
        match=r"^documents must contain only SourceDocument objects\.$",
    ):
        detect_synthetic_claim_contradictions(("not-a-document",))


def test_rejects_duplicate_document_ids() -> None:
    with pytest.raises(
        ValueError,
        match=r"^documents must not contain duplicate document_id values\.$",
    ):
        detect_synthetic_claim_contradictions(
            (
                _document("SYNTHETIC_SOURCE_DUPLICATE"),
                _document("SYNTHETIC_SOURCE_DUPLICATE"),
            )
        )


def test_rag_package_exports_contradiction_detector_contract() -> None:
    assert rag.ContradictionDetectionResult is ContradictionDetectionResult
    assert rag.DetectedClaimPassage is DetectedClaimPassage
    assert rag.DetectedContradictionPair is DetectedContradictionPair
    assert rag.detect_synthetic_claim_contradictions is (
        detect_synthetic_claim_contradictions
    )


def _document(document_id: str, *, content: str | None = None) -> SourceDocument:
    return SourceDocument(
        document_id=document_id,
        title=f"Synthetic title for {document_id}",
        content=content or f"Synthetic content for {document_id}.",
    )
