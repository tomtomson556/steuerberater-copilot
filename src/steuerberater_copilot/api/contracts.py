"""Pydantic HTTP contracts for the synthetic AI draft endpoint."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AIDraftRequest(BaseModel):
    """Request body limited to a known synthetic demo case identifier."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)


class AIDraftCitation(BaseModel):
    """One citation linking a draft summary point to synthetic source text."""

    model_config = ConfigDict(extra="forbid")

    summary_point_index: int
    document_id: str
    supporting_text: str


class AIDraftContent(BaseModel):
    """Grounded draft payload released only when workflow controls allow it."""

    model_config = ConfigDict(extra="forbid")

    review_status: str
    summary_points: list[str]
    uncertainties: list[str]
    review_questions: list[str]
    citations: list[AIDraftCitation]


class AIDraftGateway(BaseModel):
    """Gateway decision surface from the existing offline MVP semantics."""

    model_config = ConfigDict(extra="forbid")

    decision: str
    checks: list[str]
    escalation_reasons: list[str]
    block_reasons: list[str]


class AIDraftRisk(BaseModel):
    """Internal risk classification markers for routing and review."""

    model_config = ConfigDict(extra="forbid")

    level: str
    review_required: bool
    basis: list[str]


class AIDraftReviewGate(BaseModel):
    """Human-review gate status from the existing offline MVP semantics."""

    model_config = ConfigDict(extra="forbid")

    status: str
    allows_offline_mock_continuation: bool
    reason: str


class AIDraftResponse(BaseModel):
    """Structured AI draft response without raw model payloads or prompts."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    gateway: AIDraftGateway
    risk: AIDraftRisk
    review_gate: AIDraftReviewGate
    abstained_for_missing_evidence: bool
    draft: AIDraftContent | None
