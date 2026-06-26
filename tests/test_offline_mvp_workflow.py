from pathlib import Path

from steuerberater_copilot.offline_mvp.models import (
    GatewayDecision,
    IntakeCase,
    RiskClassification,
    RiskLevel,
    ReviewStatus,
    SyntheticDocument,
)
from steuerberater_copilot.offline_mvp.workflow import (
    build_mock_workflow,
    classify_internal_risk,
    load_fixture_cases,
    run_mock_gateway,
)


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "offline_mvp" / "cases.json"


def test_fixture_cases_load_as_synthetic_intake_models():
    cases = load_fixture_cases(FIXTURE_PATH)

    assert len(cases) == 4
    assert cases[0].case_id == "CASE_001"
    assert cases[0].client_ref == "CLIENT_001"
    assert cases[0].documents[0].document_id == "DOCUMENT_001"
    assert cases[0].mock_risk_signals == ("document_preparation", "high_uncertainty")


def test_risk_classification_model_uses_internal_policy_classes():
    classification = RiskClassification(
        risk_level=RiskLevel.CLASS_B,
        review_required=True,
        basis=("document_preparation",),
    )

    assert classification.risk_level == RiskLevel.CLASS_B
    assert classification.review_required is True
    assert "Routing und Review" in classification.note
    assert "steuerliche Entscheidung" in classification.note


def test_mock_workflow_keeps_outputs_as_review_drafts():
    case = load_fixture_cases(FIXTURE_PATH)[0]

    output = build_mock_workflow(case)

    assert output.gateway.decision == GatewayDecision.ESCALATE
    assert output.risk_classification.risk_level == RiskLevel.CLASS_C
    assert output.risk_classification.review_required is True
    assert output.draft_package.review_status == ReviewStatus.ESCALATED
    assert output.draft_package.review_required is True
    assert output.draft_package.risk_classification == output.risk_classification
    assert "Entwurf" in output.draft_package.title
    assert output.draft_package.question_drafts
    assert any("Human Review" in point for point in output.draft_package.summary_points)
    assert any("Klasse C" in point for point in output.draft_package.summary_points)


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
    assert output.risk_classification.risk_level == RiskLevel.CLASS_A
    assert output.draft_package.review_required is False
    assert output.draft_package.review_status == ReviewStatus.DRAFT
    assert "Keine Steuerberatung" in combined_text
    assert "keine produktive Uebermittlung" in combined_text
    assert "Berechnung" in combined_text


def test_deterministic_risk_classification_covers_fixture_levels():
    cases = {case.case_id: case for case in load_fixture_cases(FIXTURE_PATH)}

    classifications = {
        case_id: classify_internal_risk(case, run_mock_gateway(case))
        for case_id, case in cases.items()
    }

    assert classifications["CASE_002"].risk_level == RiskLevel.CLASS_A
    assert classifications["CASE_002"].review_required is False
    assert classifications["CASE_003"].risk_level == RiskLevel.CLASS_B
    assert classifications["CASE_003"].review_required is True
    assert classifications["CASE_001"].risk_level == RiskLevel.CLASS_C
    assert classifications["CASE_001"].review_required is True
    assert classifications["CASE_004"].risk_level == RiskLevel.CLASS_D
    assert classifications["CASE_004"].review_required is True


def test_stop_marker_keeps_human_review_visible_without_productive_action():
    case = load_fixture_cases(FIXTURE_PATH)[3]

    output = build_mock_workflow(case)
    combined_text = " ".join(
        (
            *output.draft_package.summary_points,
            *output.draft_package.handoff_notes,
            *output.draft_package.disclaimers,
        )
    )

    assert output.gateway.decision == GatewayDecision.ALLOW_DRAFT
    assert output.risk_classification.risk_level == RiskLevel.CLASS_D
    assert output.draft_package.review_status == ReviewStatus.ESCALATED
    assert output.draft_package.review_required is True
    assert "keine Agenda-, DATEV- oder ELSTER-Uebertragung" in combined_text
    assert "Human Review" in combined_text


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
    assert output.risk_classification.risk_level == RiskLevel.CLASS_C
    assert output.draft_package.review_required is True
    assert output.draft_package.review_status == ReviewStatus.ESCALATED
    assert "case_id_must_be_synthetic" in output.gateway.escalation_reasons
