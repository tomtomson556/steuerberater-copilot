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


class RiskLevel(StrEnum):
    """Internal MVP control classes from the risk classification policy."""

    CLASS_A = "A"
    CLASS_B = "B"
    CLASS_C = "C"
    CLASS_D = "D"


class MockRiskSignal(StrEnum):
    """Known synthetic fixture signals for deterministic offline MVP routing."""

    CLIENT_COMMUNICATION_DRAFT = "client_communication_draft"
    DOCUMENT_PREPARATION = "document_preparation"
    FORBIDDEN_CONFIDENTIAL_ORIGINAL_CONTENT = (
        "forbidden_confidential_original_content"
    )
    FORBIDDEN_ORIGINAL_PII = "forbidden_original_pii"
    FORBIDDEN_PRODUCTIVE_SYSTEM_CONFIGURATION = (
        "forbidden_productive_system_configuration"
    )
    FORBIDDEN_REAL_CLIENT_DATA = "forbidden_real_client_data"
    FORBIDDEN_SECRET = "forbidden_secret"
    FORBIDDEN_TOKEN_MAP = "forbidden_token_map"
    HANDOFF_PREPARATION = "handoff_preparation"
    HIGH_UNCERTAINTY = "high_uncertainty"
    INTERNAL_ADMIN_NOTE = "internal_admin_note"
    MISSING_REVIEW_PATH = "missing_review_path"
    QUESTION_LIST_PREPARATION = "question_list_preparation"
    REIDENTIFICATION_RISK = "reidentification_risk"
    SYNTHETIC_STOP_REVIEW_MARKER = "synthetic_stop_review_marker"
    UNCLEAR_PURPOSE = "unclear_purpose"


KNOWN_MOCK_RISK_SIGNALS = frozenset(signal.value for signal in MockRiskSignal)


class ReviewGateStatus(StrEnum):
    """Deterministic offline gate status after internal risk classification."""

    ALLOWED_OFFLINE_MOCK_CONTINUATION = "allowed_offline_mock_continuation"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"


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
    mock_risk_signals: tuple[str, ...] = ()


@dataclass(frozen=True)
class GatewayResult:
    """Mock gateway result used before producing draft material."""

    decision: GatewayDecision
    checks: tuple[str, ...]
    escalation_reasons: tuple[str, ...] = ()
    block_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class RiskClassification:
    """Internal offline MVP routing and review marker, not a tax assessment."""

    risk_level: RiskLevel
    review_required: bool
    basis: tuple[str, ...]
    note: str = (
        "Interne Offline-MVP Einstufung fuer Routing und Review; "
        "keine fachliche Freigabe oder steuerliche Entscheidung."
    )


@dataclass(frozen=True)
class ReviewGateDecision:
    """Human review gate decision derived from the internal risk class."""

    status: ReviewGateStatus
    allows_offline_mock_continuation: bool
    risk_classification: RiskClassification
    reason: str


@dataclass(frozen=True)
class DraftPackage:
    """Prepared internal draft material for human review."""

    title: str
    review_status: ReviewStatus
    risk_classification: RiskClassification
    review_required: bool
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
    risk_classification: RiskClassification
    review_gate: ReviewGateDecision
    draft_package: DraftPackage

    @property
    def draft_available(self) -> bool:
        return (
            self.gateway.decision is GatewayDecision.ALLOW_DRAFT
            and self.risk_classification.risk_level is RiskLevel.CLASS_A
            and self.review_gate.allows_offline_mock_continuation
        )
