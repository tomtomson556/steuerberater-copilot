"""HTTP system boundary for the local FastAPI demo surface."""

from .app import create_app
from .contracts import (
    AIDraftCitation,
    AIDraftContent,
    AIDraftGateway,
    AIDraftRequest,
    AIDraftResponse,
    AIDraftReviewGate,
    AIDraftRisk,
)

__all__ = [
    "AIDraftCitation",
    "AIDraftContent",
    "AIDraftGateway",
    "AIDraftRequest",
    "AIDraftResponse",
    "AIDraftReviewGate",
    "AIDraftRisk",
    "create_app",
]