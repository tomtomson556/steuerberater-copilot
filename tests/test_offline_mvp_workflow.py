from pathlib import Path

from steuerberater_copilot.offline_mvp.models import (
    GatewayDecision,
    IntakeCase,
    ReviewGateStatus,
    ReviewStatus,
    RiskClassification,
    RiskLevel,
    SyntheticDocument,
)
from steuerberater_copilot.offline_mvp.workflow import (
    build_mock_workflow,
    classify_internal_risk,
    load_fixture_cases,
    run_human_review_gate,
    run_mock_gateway,
)

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "offline_mvp" / "cases.json"
AUTOMATIC_FINAL_REVIEW_STATUS_MARKERS = {
    "approved",
    "final",
    "freigegeben",
    "rejected",
}


def test_fixture_cases_load_as_synthetic_intake_models():
    cases = load_fixture_cases(FIXTURE_PATH)

    assert len(cases) == 5
    assert cases[0].case_id == "CASE_001"
    assert cases[0].client_ref == "CLIENT_001"
    assert cases[0].documents[0].document_id == "DOCUMENT_001"
    assert cases[0].mock_risk_signals == ("document_preparation", "high_uncertainty")
    assert cases[-1].case_id == "CASE_005"
    assert cases[-1].mock_risk_signals == ("forbidden_original_pii",)


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
    assert output.review_gate.status == ReviewGateStatus.REQUIRES_HUMAN_REVIEW
    assert output.review_gate.allows_offline_mock_continuation is False
    assert output.review_gate.risk_classification == output.risk_classification
    assert output.draft_package.review_status == ReviewStatus.ESCALATED
    assert output.draft_package.review_required is True
    assert output.draft_package.risk_classification == output.risk_classification
    assert "Human Review Gate" in output.draft_package.title
    assert output.draft_package.question_drafts == (
        "Bitte im Human Review intern klaeren: "
        "Quellenbezug fuer Beispiel-Dokument DOCUMENT_001.",
        "Bitte im Human Review intern klaeren: "
        "Zeitraumabgrenzung fuer synthetische Zahlungsuebersicht.",
    )
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
    assert output.review_gate.status == ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
    assert output.review_gate.allows_offline_mock_continuation is True
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
    assert classifications["CASE_005"].risk_level == RiskLevel.CLASS_D
    assert classifications["CASE_005"].review_required is True


def test_human_review_gate_covers_risk_levels_a_to_d():
    classifications = {
        RiskLevel.CLASS_A: RiskClassification(
            risk_level=RiskLevel.CLASS_A,
            review_required=False,
            basis=("synthetic_internal_admin_fixture",),
        ),
        RiskLevel.CLASS_B: RiskClassification(
            risk_level=RiskLevel.CLASS_B,
            review_required=True,
            basis=("document_preparation",),
        ),
        RiskLevel.CLASS_C: RiskClassification(
            risk_level=RiskLevel.CLASS_C,
            review_required=True,
            basis=("high_uncertainty",),
        ),
        RiskLevel.CLASS_D: RiskClassification(
            risk_level=RiskLevel.CLASS_D,
            review_required=True,
            basis=("synthetic_stop_review_marker",),
        ),
    }

    decisions = {
        risk_level: run_human_review_gate(classification)
        for risk_level, classification in classifications.items()
    }

    assert decisions[RiskLevel.CLASS_A].status == (
        ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
    )
    assert classifications[RiskLevel.CLASS_A].review_required is False
    assert decisions[RiskLevel.CLASS_A].allows_offline_mock_continuation is True
    for risk_level in (RiskLevel.CLASS_B, RiskLevel.CLASS_C, RiskLevel.CLASS_D):
        assert decisions[risk_level].status == ReviewGateStatus.REQUIRES_HUMAN_REVIEW
        assert classifications[risk_level].review_required is True
        assert decisions[risk_level].allows_offline_mock_continuation is False
        assert decisions[risk_level].risk_classification == classifications[risk_level]


def test_review_gate_stops_b_c_and_d_without_substantive_output():
    cases = {case.case_id: case for case in load_fixture_cases(FIXTURE_PATH)}

    outputs = (
        build_mock_workflow(cases["CASE_003"]),
        build_mock_workflow(cases["CASE_001"]),
        build_mock_workflow(cases["CASE_004"]),
    )

    assert {output.risk_classification.risk_level for output in outputs} == {
        RiskLevel.CLASS_B,
        RiskLevel.CLASS_C,
        RiskLevel.CLASS_D,
    }
    for output in outputs:
        assert output.review_gate.status == ReviewGateStatus.REQUIRES_HUMAN_REVIEW
        assert output.review_gate.allows_offline_mock_continuation is False
        assert output.draft_package.review_required is True
        if output.intake.missing_items:
            assert output.draft_package.question_drafts
        else:
            assert output.draft_package.question_drafts == ()
        assert all("Szenario:" not in point for point in output.draft_package.summary_points)
        assert all(
            "Synthetische Dokumenthinweise:" not in point
            for point in output.draft_package.summary_points
        )
        assert any("gestoppt" in point for point in output.draft_package.summary_points)


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
    assert output.review_gate.status == ReviewGateStatus.REQUIRES_HUMAN_REVIEW
    assert output.review_gate.allows_offline_mock_continuation is False
    assert output.draft_package.review_status == ReviewStatus.ESCALATED
    assert output.draft_package.review_required is True
    assert "keine Agenda-, DATEV- oder ELSTER-Uebertragung" in combined_text
    assert "Human Review" in combined_text


def test_fixture_block_case_runs_end_to_end_without_available_draft():
    cases = {case.case_id: case for case in load_fixture_cases(FIXTURE_PATH)}

    output = build_mock_workflow(cases["CASE_005"])

    assert output.gateway.decision == GatewayDecision.BLOCK
    assert output.gateway.block_reasons == ("forbidden_data_class:original_pii",)
    assert output.risk_classification.risk_level == RiskLevel.CLASS_D
    assert output.risk_classification.review_required is True
    assert output.review_gate.status == ReviewGateStatus.REQUIRES_HUMAN_REVIEW
    assert output.review_gate.allows_offline_mock_continuation is False
    assert output.draft_package.review_required is True
    assert output.draft_package.review_status == ReviewStatus.ESCALATED
    assert output.draft_package.question_drafts == ()
    assert all("Szenario:" not in point for point in output.draft_package.summary_points)
    assert any("gestoppt" in point for point in output.draft_package.summary_points)


def test_workflow_never_auto_emits_final_or_human_review_decisions():
    outputs = [build_mock_workflow(case) for case in load_fixture_cases(FIXTURE_PATH)]

    for output in outputs:
        review_status = output.draft_package.review_status
        assert review_status is not ReviewStatus.REJECTED
        assert not any(
            marker in review_status.value.lower()
            for marker in AUTOMATIC_FINAL_REVIEW_STATUS_MARKERS
        )


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
    assert output.review_gate.status == ReviewGateStatus.REQUIRES_HUMAN_REVIEW
    assert output.draft_package.review_required is True
    assert output.draft_package.review_status == ReviewStatus.ESCALATED
    assert "case_id_must_be_synthetic" in output.gateway.escalation_reasons
