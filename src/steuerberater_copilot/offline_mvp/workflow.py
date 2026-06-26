"""Deterministic offline MVP workflow using synthetic case data only."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .models import (
    DraftPackage,
    GatewayDecision,
    GatewayResult,
    IntakeCase,
    ReviewStatus,
    SyntheticDocument,
    WorkflowOutput,
)


PSEUDONYM_RE = re.compile(r"^(CLIENT|CASE|DOCUMENT)_[0-9]{3}$")
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
    draft_package = build_draft_package(case, gateway)
    return WorkflowOutput(intake=case, gateway=gateway, draft_package=draft_package)


def run_mock_gateway(case: IntakeCase) -> GatewayResult:
    """Apply minimal mock checks that mirror the documented gateway boundary."""

    checks = [
        "synthetic_case_reference",
        "synthetic_client_reference",
        "synthetic_document_references",
        "offline_no_productive_integration",
    ]
    escalation_reasons: list[str] = []

    if not PSEUDONYM_RE.fullmatch(case.case_id):
        escalation_reasons.append("case_id_must_be_synthetic")
    if not PSEUDONYM_RE.fullmatch(case.client_ref):
        escalation_reasons.append("client_ref_must_be_synthetic")
    for document in case.documents:
        if not PSEUDONYM_RE.fullmatch(document.document_id):
            escalation_reasons.append("document_id_must_be_synthetic")
            break
    if case.missing_items:
        escalation_reasons.append("missing_context_requires_review")

    decision = GatewayDecision.ESCALATE if escalation_reasons else GatewayDecision.ALLOW_DRAFT
    return GatewayResult(
        decision=decision,
        checks=tuple(checks),
        escalation_reasons=tuple(escalation_reasons),
    )


def build_draft_package(case: IntakeCase, gateway: GatewayResult) -> DraftPackage:
    """Create internal draft material for human review."""

    review_status = (
        ReviewStatus.ESCALATED
        if gateway.decision is GatewayDecision.ESCALATE
        else ReviewStatus.DRAFT
    )
    document_labels = ", ".join(document.label for document in case.documents)
    missing_items = case.missing_items or ("Keine offenen Beispielpunkte im Fixture markiert.",)

    return DraftPackage(
        title=f"Offline-MVP Entwurf fuer {case.case_id}",
        review_status=review_status,
        summary_points=(
            f"Szenario: {case.scenario}.",
            f"Zeitraum: {case.period}.",
            f"Synthetische Dokumenthinweise: {document_labels}.",
            "Alle Inhalte sind interne Vorbereitung und benoetigen Human Review.",
        ),
        question_drafts=tuple(f"Bitte im Review klaeren: {item}." for item in missing_items),
        handoff_notes=(
            "Nur manueller Handoff-Entwurf; keine Agenda-, DATEV- oder ELSTER-Uebertragung.",
            "Vor jeder fachlichen Nutzung sind Gateway- und Kanzlei-Review zu pruefen.",
        ),
    )


def _case_from_mapping(raw_case: dict[str, Any]) -> IntakeCase:
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
    )
