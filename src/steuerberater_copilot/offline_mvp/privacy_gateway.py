"""Deterministic offline Privacy Gateway checks for synthetic MVP cases."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from ._response_markers import (
    PRODUCTIVE_TRANSMISSION_MARKER,
    PRODUCTIVE_TRANSMISSION_NEGATION_MARKER,
    RESPONSE_DRAFT_VISIBILITY_MARKERS,
    RESPONSE_HUMAN_REVIEW_VISIBILITY_MARKERS,
    TAX_ADVICE_MARKER,
    TAX_ADVICE_NEGATION_MARKER,
)
from .models import DraftPackage, GatewayDecision, GatewayResult, IntakeCase, MockRiskSignal

PSEUDONYM_RE = re.compile(r"^(CLIENT|CASE|DOCUMENT)_[0-9]{3}$")


class PrivacyDataClass(StrEnum):
    """Offline MVP data class markers derived from the Privacy Gateway contract."""

    PUBLIC_DOCUMENTATION = "public_documentation"
    SYNTHETIC_FIXTURE = "synthetic_fixture"
    GENERIC_TEXT = "generic_text"
    PSEUDONYMIZED_CASE_REFERENCE = "pseudonymized_case_reference"
    PSEUDONYMIZED_DOCUMENT_REFERENCE = "pseudonymized_document_reference"
    ORIGINAL_PII = "original_pii"
    REAL_CLIENT_DATA = "real_client_data"
    CONFIDENTIAL_ORIGINAL_CONTENT = "confidential_original_content"
    SECRET = "secret"
    TOKEN_MAP = "token_map"
    PRODUCTIVE_SYSTEM_CONFIGURATION = "productive_system_configuration"


ALLOWED_DATA_CLASSES = frozenset(
    {
        PrivacyDataClass.PUBLIC_DOCUMENTATION,
        PrivacyDataClass.SYNTHETIC_FIXTURE,
        PrivacyDataClass.GENERIC_TEXT,
    }
)
PSEUDONYMIZED_DATA_CLASSES = frozenset(
    {
        PrivacyDataClass.PSEUDONYMIZED_CASE_REFERENCE,
        PrivacyDataClass.PSEUDONYMIZED_DOCUMENT_REFERENCE,
    }
)
FORBIDDEN_DATA_CLASSES = frozenset(
    {
        PrivacyDataClass.ORIGINAL_PII,
        PrivacyDataClass.REAL_CLIENT_DATA,
        PrivacyDataClass.CONFIDENTIAL_ORIGINAL_CONTENT,
        PrivacyDataClass.SECRET,
        PrivacyDataClass.TOKEN_MAP,
        PrivacyDataClass.PRODUCTIVE_SYSTEM_CONFIGURATION,
    }
)
ALLOWED_PURPOSES = frozenset(
    {
        "preparation",
        "structuring",
        "question_draft",
        "draft_creation",
        "offline_validation",
    }
)

SIGNAL_DATA_CLASSES = {
    MockRiskSignal.FORBIDDEN_ORIGINAL_PII.value: PrivacyDataClass.ORIGINAL_PII,
    MockRiskSignal.FORBIDDEN_REAL_CLIENT_DATA.value: PrivacyDataClass.REAL_CLIENT_DATA,
    MockRiskSignal.FORBIDDEN_CONFIDENTIAL_ORIGINAL_CONTENT.value: (
        PrivacyDataClass.CONFIDENTIAL_ORIGINAL_CONTENT
    ),
    MockRiskSignal.FORBIDDEN_SECRET.value: PrivacyDataClass.SECRET,
    MockRiskSignal.FORBIDDEN_TOKEN_MAP.value: PrivacyDataClass.TOKEN_MAP,
    MockRiskSignal.FORBIDDEN_PRODUCTIVE_SYSTEM_CONFIGURATION.value: (
        PrivacyDataClass.PRODUCTIVE_SYSTEM_CONFIGURATION
    ),
}


@dataclass(frozen=True)
class PrivacyGatewayRequest:
    """Request-side material inspected before offline draft preparation."""

    purpose: str
    data_classes: tuple[PrivacyDataClass, ...]
    case_refs: tuple[str, ...]
    document_refs: tuple[str, ...]
    review_path_present: bool
    reidentification_risk: bool = False


def privacy_gateway_request_from_case(case: IntakeCase) -> PrivacyGatewayRequest:
    """Build a deterministic request check input from a synthetic intake case."""

    signals = set(case.mock_risk_signals)
    data_classes = [
        PrivacyDataClass.SYNTHETIC_FIXTURE,
        PrivacyDataClass.PSEUDONYMIZED_CASE_REFERENCE,
        PrivacyDataClass.PSEUDONYMIZED_DOCUMENT_REFERENCE,
    ]
    data_classes.extend(
        data_class
        for signal, data_class in SIGNAL_DATA_CLASSES.items()
        if signal in signals
    )

    purpose = (
        "offline_validation"
        if MockRiskSignal.UNCLEAR_PURPOSE.value not in signals
        else "unclear"
    )
    return PrivacyGatewayRequest(
        purpose=purpose,
        data_classes=tuple(data_classes),
        case_refs=(case.case_id, case.client_ref),
        document_refs=tuple(document.document_id for document in case.documents),
        review_path_present=MockRiskSignal.MISSING_REVIEW_PATH.value not in signals,
        reidentification_risk=MockRiskSignal.REIDENTIFICATION_RISK.value in signals,
    )


def run_request_gateway_check(request: PrivacyGatewayRequest) -> GatewayResult:
    """Run deterministic request-side Privacy Gateway checks."""

    checks = [
        "request_purpose_documented",
        "request_data_classes_allowed",
        "request_pseudonyms_non_reidentifying",
        "request_review_path_present",
        "request_context_minimized",
    ]
    escalation_reasons: list[str] = []
    block_reasons: list[str] = []

    if request.purpose not in ALLOWED_PURPOSES:
        escalation_reasons.append("request_purpose_unclear")

    for data_class in request.data_classes:
        if data_class in FORBIDDEN_DATA_CLASSES:
            block_reasons.append(f"forbidden_data_class:{data_class.value}")

    if not request.review_path_present:
        escalation_reasons.append("review_path_missing")

    if request.reidentification_risk:
        escalation_reasons.append("reidentification_risk")

    case_ref, client_ref = request.case_refs
    if not PSEUDONYM_RE.fullmatch(case_ref):
        escalation_reasons.append("case_id_must_be_synthetic")
    if not PSEUDONYM_RE.fullmatch(client_ref):
        escalation_reasons.append("client_ref_must_be_synthetic")
    if not _all_pseudonyms_are_synthetic(request.document_refs):
        escalation_reasons.append("document_id_must_be_synthetic")

    return _gateway_result(
        checks=checks,
        escalation_reasons=escalation_reasons,
        block_reasons=block_reasons,
    )


def run_response_gateway_check(draft_package: DraftPackage) -> GatewayResult:
    """Run deterministic response-side Privacy Gateway checks for draft output."""

    checks = [
        "response_keeps_draft_status",
        "response_requires_human_review_when_needed",
        "response_no_productive_transmission",
        "response_no_tax_advice_or_calculation_claim",
    ]
    escalation_reasons: list[str] = []
    block_reasons: list[str] = []
    combined_text = " ".join(
        (
            draft_package.title,
            *draft_package.summary_points,
            *draft_package.question_drafts,
            *draft_package.handoff_notes,
            *draft_package.disclaimers,
        )
    ).lower()

    if not _contains_any(combined_text, RESPONSE_DRAFT_VISIBILITY_MARKERS):
        escalation_reasons.append("draft_character_not_visible")

    if not _contains_any(combined_text, RESPONSE_HUMAN_REVIEW_VISIBILITY_MARKERS):
        escalation_reasons.append("human_review_not_visible")

    if (
        PRODUCTIVE_TRANSMISSION_MARKER in combined_text
        and PRODUCTIVE_TRANSMISSION_NEGATION_MARKER not in combined_text
    ):
        block_reasons.append("productive_transmission_suggested")

    if TAX_ADVICE_MARKER in combined_text and TAX_ADVICE_NEGATION_MARKER not in combined_text:
        block_reasons.append("tax_advice_suggested")

    return _gateway_result(
        checks=checks,
        escalation_reasons=escalation_reasons,
        block_reasons=block_reasons,
    )


def combine_gateway_results(*results: GatewayResult) -> GatewayResult:
    """Combine request- and response-side checks into one workflow result."""

    checks: list[str] = []
    escalation_reasons: list[str] = []
    block_reasons: list[str] = []
    for result in results:
        checks.extend(result.checks)
        escalation_reasons.extend(result.escalation_reasons)
        block_reasons.extend(result.block_reasons)

    return _gateway_result(
        checks=checks,
        escalation_reasons=escalation_reasons,
        block_reasons=block_reasons,
    )


def _gateway_result(
    checks: Iterable[str],
    escalation_reasons: Iterable[str],
    block_reasons: Iterable[str],
) -> GatewayResult:
    escalation_reason_tuple = tuple(dict.fromkeys(escalation_reasons))
    block_reason_tuple = tuple(dict.fromkeys(block_reasons))
    if block_reason_tuple:
        decision = GatewayDecision.BLOCK
    elif escalation_reason_tuple:
        decision = GatewayDecision.ESCALATE
    else:
        decision = GatewayDecision.ALLOW_DRAFT

    return GatewayResult(
        decision=decision,
        checks=tuple(dict.fromkeys(checks)),
        escalation_reasons=escalation_reason_tuple,
        block_reasons=block_reason_tuple,
    )


def _all_pseudonyms_are_synthetic(references: Iterable[str]) -> bool:
    return all(PSEUDONYM_RE.fullmatch(reference) for reference in references)


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    return any(marker in text for marker in markers)
