"""Public contracts for deterministic local document retrieval."""

from .contradiction_detector import (
    ContradictionDetectionResult,
    DetectedClaimPassage,
    DetectedContradictionPair,
    detect_passage_contradictions,
)
from .local_document_retriever import LocalDocumentRetriever
from .source_document import SourceDocument

__all__ = [
    "ContradictionDetectionResult",
    "DetectedClaimPassage",
    "DetectedContradictionPair",
    "LocalDocumentRetriever",
    "SourceDocument",
    "detect_passage_contradictions",
]
