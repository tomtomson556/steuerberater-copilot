"""Deterministic synthetic claim contradiction detection over source documents."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .source_document import SourceDocument

_CLAIM_PATTERN = re.compile(
    r"\[\[SYNTHETIC_CLAIM\s+(?P<key>[A-Za-z0-9_.-]+)=(?P<value>[^\]]+?)\]\]"
)


@dataclass(frozen=True, slots=True)
class DetectedClaimPassage:
    """One exact synthetic claim marker found in a source document."""

    document_id: str
    supporting_text: str
    claim_key: str
    claim_value: str

    def __post_init__(self) -> None:
        for field_name in (
            "document_id",
            "supporting_text",
            "claim_key",
            "claim_value",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string.")
            if not value or value.isspace():
                raise ValueError(f"{field_name} must not be blank.")


@dataclass(frozen=True, slots=True)
class DetectedContradictionPair:
    """Two passages with the same synthetic claim key but different values."""

    claim_key: str
    first: DetectedClaimPassage
    second: DetectedClaimPassage

    def __post_init__(self) -> None:
        if not isinstance(self.claim_key, str):
            raise TypeError("claim_key must be a string.")
        if not self.claim_key or self.claim_key.isspace():
            raise ValueError("claim_key must not be blank.")
        if not isinstance(self.first, DetectedClaimPassage):
            raise TypeError("first must be a DetectedClaimPassage.")
        if not isinstance(self.second, DetectedClaimPassage):
            raise TypeError("second must be a DetectedClaimPassage.")
        if self.first.claim_key != self.claim_key or self.second.claim_key != self.claim_key:
            raise ValueError("both passages must use the contradiction claim_key.")
        if self.first.claim_value == self.second.claim_value:
            raise ValueError("contradicting passages must have different claim values.")


@dataclass(frozen=True, slots=True)
class ContradictionDetectionResult:
    """Observed synthetic claim contradictions across source documents.

    Detection is limited to explicit ``[[SYNTHETIC_CLAIM key=value]]`` markers.
    It is not semantic NLP contradiction detection and makes no steuerliche
    correctness claim.
    """

    contradiction_present: bool
    contradictions: tuple[DetectedContradictionPair, ...]

    def __post_init__(self) -> None:
        if type(self.contradiction_present) is not bool:
            raise TypeError("contradiction_present must be a boolean.")
        if not isinstance(self.contradictions, tuple):
            raise TypeError("contradictions must be a tuple.")
        for contradiction in self.contradictions:
            if not isinstance(contradiction, DetectedContradictionPair):
                raise TypeError(
                    "contradictions must contain only DetectedContradictionPair objects."
                )
        if self.contradiction_present != bool(self.contradictions):
            raise ValueError(
                "contradiction_present must be True exactly when contradictions "
                "is non-empty."
            )


def detect_synthetic_claim_contradictions(
    documents: tuple[SourceDocument, ...],
) -> ContradictionDetectionResult:
    """Detect opposing synthetic claim markers across the provided documents."""
    if not isinstance(documents, tuple):
        raise TypeError("documents must be a tuple.")

    passages_by_key: dict[str, list[DetectedClaimPassage]] = {}
    seen_document_ids: set[str] = set()
    for document in documents:
        if not isinstance(document, SourceDocument):
            raise TypeError("documents must contain only SourceDocument objects.")
        if document.document_id in seen_document_ids:
            raise ValueError("documents must not contain duplicate document_id values.")
        seen_document_ids.add(document.document_id)
        for match in _CLAIM_PATTERN.finditer(document.content):
            passage = DetectedClaimPassage(
                document_id=document.document_id,
                supporting_text=match.group(0),
                claim_key=match.group("key"),
                claim_value=match.group("value"),
            )
            passages_by_key.setdefault(passage.claim_key, []).append(passage)

    contradictions: list[DetectedContradictionPair] = []
    for claim_key in sorted(passages_by_key):
        passages = passages_by_key[claim_key]
        first_by_value: dict[str, DetectedClaimPassage] = {}
        for passage in passages:
            if passage.claim_value not in first_by_value:
                first_by_value[passage.claim_value] = passage
        distinct_values = sorted(first_by_value)
        if len(distinct_values) < 2:
            continue
        first = first_by_value[distinct_values[0]]
        second = first_by_value[distinct_values[1]]
        contradictions.append(
            DetectedContradictionPair(
                claim_key=claim_key,
                first=first,
                second=second,
            )
        )

    return ContradictionDetectionResult(
        contradiction_present=bool(contradictions),
        contradictions=tuple(contradictions),
    )
