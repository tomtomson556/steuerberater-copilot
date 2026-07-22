"""Public contracts for deterministic local document retrieval."""

from .contradiction_detector import (
    ContradictionDetectionResult,
    DetectedClaimPassage,
    DetectedContradictionPair,
    detect_synthetic_claim_contradictions,
)
from .document_freshness import DocumentVersionRecord, find_outdated_document_ids
from .local_document_retriever import LocalDocumentRetriever
from .source_document import SourceDocument

__all__ = [
    "ContradictionDetectionResult",
    "DetectedClaimPassage",
    "DetectedContradictionPair",
    "DocumentVersionRecord",
    "LocalDocumentRetriever",
    "SourceDocument",
    "detect_synthetic_claim_contradictions",
    "find_outdated_document_ids",
]
