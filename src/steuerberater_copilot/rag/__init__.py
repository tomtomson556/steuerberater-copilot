"""Public contracts for deterministic local document retrieval."""

from .local_document_retriever import LocalDocumentRetriever
from .source_document import SourceDocument

__all__ = ["SourceDocument", "LocalDocumentRetriever"]
