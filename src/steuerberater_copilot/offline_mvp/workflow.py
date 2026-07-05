"""Deterministic offline MVP workflow using synthetic case data only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import (
    KNOWN_MOCK_RISK_SIGNALS,
    DraftPackage,
    GatewayDecision,
    GatewayResult,
    IntakeCase,
    MockRiskSignal,
    ReviewGateDecision,
    ReviewGateStatus,
    ReviewStatus,
    RiskClassification,
    RiskLevel,
    SyntheticDocument,
    WorkflowOutput,
)
from .privacy_gateway import (
    combine_gateway_results,
    privacy_gateway_request_from_case,
    run_request_gateway_check,
    run_response_gateway_check,
)

DEFAULT_FIXTURE_PATH = (
    Path(__file__).resolve().parents[3] / "fixtures" / "offline_mvp" / "cases.json"
)


def load_fixture_cases(path: Path = DEFAULT_FIXTURE_PATH) -> tuple[IntakeCase, ...]:
    """Load synthetic offline MVP cases from a local JSON fixture."""

    raw_cases = json.loads(path.read_text(encoding="utf-8"))
    return tuple(_case_from_mapping(raw_case) for raw_case in raw_cases)


def build_mock_workflow(case: IntakeCase) -> WorkflowOutput:
    """Build a draft-only workflow result without external systems."""

    gateway = run_mock_gateway(case)
    risk_classification = classify_internal_risk(case, gateway)
    review_gate = run_human_review_gate(risk_classification)
    draft_package = build_draft_package(case, gateway, risk_classification, review_gate)
    gateway = combine_gateway_results(gateway, run_response_gateway_check(draft_package))
    return WorkflowOutput(
        intake=case,
        gateway=gateway,
        risk_classification=risk_classification,
        review_gate=review_gate,
        draft_package=draft_package,
    )


def run_mock_gateway(case: IntakeCase) -> GatewayResult:
    """Apply minimal mock checks that mirror the documented gateway boundary."""

    gateway = run_request_gateway_check(privacy_gateway_request_from_case(case))
    if not case.missing_items:
        return gateway

    return combine_gateway_results(
        gateway,
        GatewayResult(
            decision=GatewayDecision.ESCALATE,
            checks=("request_missing_context",),
            escalation_reasons=("missing_context_requires_review",),
        ),
    )


def classify_internal_risk(
    case: IntakeCase, gateway: GatewayResult
) -> RiskClassification:
    """Classify internal MVP review routing from synthetic mock signals only."""

    signals = set(case.mock_risk_signals)
    basis: list[str] = []

    if gateway.decision is GatewayDecision.BLOCK:
        basis.extend(gateway.block_reasons)
    if gateway.decision is GatewayDecision.ESCALATE:
        basis.extend(gateway.escalation_reasons)
    if case.missing_items:
        basis.append("missing_fixture_context")
    basis.extend(sorted(signals))

    if (
        gateway.decision is GatewayDecision.BLOCK
        or MockRiskSignal.SYNTHETIC_STOP_REVIEW_MARKER.value in signals
    ):
        risk_level = RiskLevel.CLASS_D
    elif (
        gateway.decision is GatewayDecision.ESCALATE
        or case.missing_items
        or signals.intersection(
            {
                MockRiskSignal.CLIENT_COMMUNICATION_DRAFT.value,
                MockRiskSignal.HANDOFF_PREPARATION.value,
                MockRiskSignal.HIGH_UNCERTAINTY.value,
            }
        )
    ):
        risk_level = RiskLevel.CLASS_C
    elif signals.intersection(
        {
            MockRiskSignal.DOCUMENT_PREPARATION.value,
            MockRiskSignal.QUESTION_LIST_PREPARATION.value,
        }
    ):
        risk_level = RiskLevel.CLASS_B
    else:
        risk_level = RiskLevel.CLASS_A

    return RiskClassification(
        risk_level=risk_level,
        review_required=risk_level in {RiskLevel.CLASS_B, RiskLevel.CLASS_C, RiskLevel.CLASS_D},
        basis=tuple(basis or ("synthetic_internal_admin_fixture",)),
    )


def run_human_review_gate(
    risk_classification: RiskClassification,
) -> ReviewGateDecision:
    """Gate offline mock continuation from the existing internal risk class."""

    if risk_classification.risk_level is RiskLevel.CLASS_A:
        return ReviewGateDecision(
            status=ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION,
            allows_offline_mock_continuation=True,
            risk_classification=risk_classification,
            reason="RiskLevel A permits offline mock continuation only.",
        )

    return ReviewGateDecision(
        status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
        allows_offline_mock_continuation=False,
        risk_classification=risk_classification,
        reason=(
            f"RiskLevel {risk_classification.risk_level.value} requires human review "
            "before any offline mock continuation."
        ),
    )


def build_draft_package(
    case: IntakeCase,
    gateway: GatewayResult,
    risk_classification: RiskClassification,
    review_gate: ReviewGateDecision,
) -> DraftPackage:
    """Create internal draft material for human review."""

    if not review_gate.allows_offline_mock_continuation:
        review_status = (
            ReviewStatus.ESCALATED
            if gateway.decision is GatewayDecision.ESCALATE
            or risk_classification.risk_level is RiskLevel.CLASS_D
            else ReviewStatus.IN_REVIEW
        )
        return DraftPackage(
            title=f"Offline-MVP Human Review Gate fuer {case.case_id}",
            review_status=review_status,
            risk_classification=risk_classification,
            review_required=True,
            summary_points=(
                (
                    "Human Review Gate: automatische Offline-Mock-Fortsetzung "
                    "gestoppt."
                ),
                (
                    "Interne RiskLevel-Markierung: "
                    f"Klasse {risk_classification.risk_level.value}; "
                    "nur Routing- und Review-Grundlage."
                ),
            ),
            question_drafts=tuple(
                f"Bitte im Human Review intern klaeren: {item}."
                for item in case.missing_items
            ),
            handoff_notes=(
                "Keine automatische Rueckfragenkommunikation oder fachliche "
                "Inhaltsausgabe vor Human Review.",
                "keine Agenda-, DATEV- oder ELSTER-Uebertragung.",
            ),
        )

    review_status = (
        ReviewStatus.ESCALATED
        if gateway.decision is GatewayDecision.ESCALATE
        or risk_classification.risk_level is RiskLevel.CLASS_D
        else ReviewStatus.DRAFT
    )
    document_labels = ", ".join(document.label for document in case.documents)
    return DraftPackage(
        title=f"Offline-MVP Entwurf fuer {case.case_id}",
        review_status=review_status,
        risk_classification=risk_classification,
        review_required=risk_classification.review_required,
        summary_points=(
            f"Szenario: {case.scenario}.",
            f"Zeitraum: {case.period}.",
            f"Synthetische Dokumenthinweise: {document_labels}.",
            (
                "Interne RiskLevel-Markierung: "
                f"Klasse {risk_classification.risk_level.value}; "
                "nur Routing- und Review-Grundlage."
            ),
            "RiskLevel A erlaubt nur die Offline-Mock-Fortsetzung ohne produktive Wirkung.",
        ),
        question_drafts=tuple(
            f"Bitte im Review klaeren: {item}." for item in case.missing_items
        ),
        handoff_notes=(
            "Nur manueller Handoff-Entwurf; keine Agenda-, DATEV- oder ELSTER-Uebertragung.",
            "Vor jeder fachlichen Nutzung sind Gateway- und Kanzlei-Review zu pruefen.",
        ),
    )


def _case_from_mapping(raw_case: dict[str, Any]) -> IntakeCase:
    mock_risk_signals = tuple(raw_case.get("mock_risk_signals", ()))
    unknown_signals = sorted(set(mock_risk_signals) - KNOWN_MOCK_RISK_SIGNALS)
    if unknown_signals:
        case_id = raw_case.get("case_id", "<unknown>")
        unknown_signal_list = ", ".join(unknown_signals)
        raise ValueError(
            f"Unknown mock_risk_signals for {case_id}: {unknown_signal_list}"
        )

    documents = tuple(
        SyntheticDocument(
            document_id=document["document_id"],
            label=document["label"],
            period=document["period"],
            source_note=document["source_note"],
        )
        for document in raw_case["documents"]
    )
    return IntakeCase(
        case_id=raw_case["case_id"],
        client_ref=raw_case["client_ref"],
        scenario=raw_case["scenario"],
        period=raw_case["period"],
        documents=documents,
        notes=tuple(raw_case.get("notes", ())),
        missing_items=tuple(raw_case.get("missing_items", ())),
        mock_risk_signals=mock_risk_signals,
    )
