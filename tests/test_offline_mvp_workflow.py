from pathlib import Path

from steuerberater_copilot.offline_mvp.models import (
    GatewayDecision,
    IntakeCase,
    ReviewStatus,
    SyntheticDocument,
)
from steuerberater_copilot.offline_mvp.workflow import (
    build_mock_workflow,
    load_fixture_cases,
)


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "offline_mvp" / "cases.json"


def test_fixture_cases_load_as_synthetic_intake_models():
    cases = load_fixture_cases(FIXTURE_PATH)

    assert len(cases) == 2
    assert cases[0].case_id == "CASE_001"
    assert cases[0].client_ref == "CLIENT_001"
    assert cases[0].documents[0].document_id == "DOCUMENT_001"


def test_mock_workflow_keeps_outputs_as_review_drafts():
    case = load_fixture_cases(FIXTURE_PATH)[0]

    output = build_mock_workflow(case)

    assert output.gateway.decision == GatewayDecision.ESCALATE
    assert output.draft_package.review_status == ReviewStatus.ESCALATED
    assert "Entwurf" in output.draft_package.title
    assert output.draft_package.question_drafts
    assert any("Human Review" in point for point in output.draft_package.summary_points)


def test_mock_workflow_has_no_productive_handoff_or_tax_calculation_claims():
    case = load_fixture_cases(FIXTURE_PATH)[1]

    output = build_mock_workflow(case)
    combined_text = " ".join(
        (
            output.draft_package.title,
            *output.draft_package.summary_points,
            *output.draft_package.question_drafts,
            *output.draft_package.handoff_notes,
            *output.draft_package.disclaimers,
        )
    )

    assert output.gateway.decision == GatewayDecision.ALLOW_DRAFT
    assert output.draft_package.review_status == ReviewStatus.DRAFT
    assert "Keine Steuerberatung" in combined_text
    assert "keine produktive Uebermittlung" in combined_text
    assert "Berechnung" in combined_text


def test_gateway_escalates_non_synthetic_references():
    case = IntakeCase(
        case_id="CASE_REAL",
        client_ref="CLIENT_001",
        scenario="ungueltiges lokales Testfixture",
        period="2026-Q1",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_001",
                label="synthetischer Platzhalter",
                period="2026-Q1",
                source_note="Test ohne Originaldaten",
            ),
        ),
    )

    output = build_mock_workflow(case)

    assert output.gateway.decision == GatewayDecision.ESCALATE
    assert output.draft_package.review_status == ReviewStatus.ESCALATED
    assert "case_id_must_be_synthetic" in output.gateway.escalation_reasons
