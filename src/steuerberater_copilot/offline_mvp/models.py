"""Models for the offline MVP draft workflow.

The models intentionally represent preparation state only. They do not model
tax calculations, filings, productive handoffs, or professional approvals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ReviewStatus(StrEnum):
    """Human-review states visible in the offline MVP."""

    DRAFT = "Draft"
    IN_REVIEW = "In review"
    REJECTED = "Rejected"
    ESCALATED = "Escalated"


class GatewayDecision(StrEnum):
    """Policy and privacy gateway outcome for mock workflow inputs."""

    ALLOW_DRAFT = "allow_draft"
    BLOCK = "block"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class SyntheticDocument:
    """A synthetic document descriptor, not an original document."""

    document_id: str
    label: str
    period: str
    source_note: str


@dataclass(frozen=True)
class IntakeCase:
    """Synthetic intake case for local offline validation."""

    case_id: str
    client_ref: str
    scenario: str
    period: str
    documents: tuple[SyntheticDocument, ...]
    notes: tuple[str, ...] = ()
    missing_items: tuple[str, ...] = ()


@dataclass(frozen=True)
class GatewayResult:
    """Mock gateway result used before producing draft material."""

    decision: GatewayDecision
    checks: tuple[str, ...]
    escalation_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class DraftPackage:
    """Prepared internal draft material for human review."""

    title: str
    review_status: ReviewStatus
    summary_points: tuple[str, ...]
    question_drafts: tuple[str, ...]
    handoff_notes: tuple[str, ...]
    disclaimers: tuple[str, ...] = field(
        default=(
            "Entwurf: fachliche Pruefung durch die Kanzlei erforderlich.",
            "Keine Steuerberatung, keine Berechnung und keine produktive Uebermittlung.",
        )
    )


@dataclass(frozen=True)
class WorkflowOutput:
    """Complete offline MVP workflow result."""

    intake: IntakeCase
    gateway: GatewayResult
    draft_package: DraftPackage
