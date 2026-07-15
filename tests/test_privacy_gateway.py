from steuerberater_copilot.offline_mvp._response_markers import (
    DRAFT_REVIEW_DISCLAIMER,
    NO_TAX_ADVICE_OR_PRODUCTIVE_TRANSMISSION_DISCLAIMER,
    PRODUCTIVE_TRANSMISSION_MARKER,
    PRODUCTIVE_TRANSMISSION_NEGATION_MARKER,
    RESPONSE_DRAFT_VISIBILITY_MARKERS,
    RESPONSE_HUMAN_REVIEW_VISIBILITY_MARKERS,
    TAX_ADVICE_MARKER,
    TAX_ADVICE_NEGATION_MARKER,
)
from steuerberater_copilot.offline_mvp.models import (
    DraftPackage,
    GatewayDecision,
    IntakeCase,
    ReviewStatus,
    RiskClassification,
    RiskLevel,
    SyntheticDocument,
)
from steuerberater_copilot.offline_mvp.privacy_gateway import (
    PrivacyDataClass,
    PrivacyGatewayRequest,
    privacy_gateway_request_from_case,
    run_request_gateway_check,
    run_response_gateway_check,
)
from steuerberater_copilot.offline_mvp.workflow import build_mock_workflow, load_fixture_cases


def test_request_gateway_allows_synthetic_fixture_case():
    case = _case("CASE_101", "CLIENT_101", "DOCUMENT_101")

    gateway = run_request_gateway_check(privacy_gateway_request_from_case(case))

    assert gateway.decision == GatewayDecision.ALLOW_DRAFT
    assert gateway.escalation_reasons == ()
    assert gateway.block_reasons == ()
    assert "request_data_classes_allowed" in gateway.checks


def test_request_gateway_blocks_forbidden_data_class():
    request = PrivacyGatewayRequest(
        purpose="offline_validation",
        data_classes=(
            PrivacyDataClass.SYNTHETIC_FIXTURE,
            PrivacyDataClass.ORIGINAL_PII,
        ),
        case_refs=("CASE_102", "CLIENT_102"),
        document_refs=("DOCUMENT_102",),
        review_path_present=True,
    )

    gateway = run_request_gateway_check(request)

    assert gateway.decision == GatewayDecision.BLOCK
    assert gateway.escalation_reasons == ()
    assert gateway.block_reasons == ("forbidden_data_class:original_pii",)


def test_request_gateway_escalates_unclear_purpose():
    case = _case("CASE_103", "CLIENT_103", "DOCUMENT_103", signals=("unclear_purpose",))

    gateway = run_request_gateway_check(privacy_gateway_request_from_case(case))

    assert gateway.decision == GatewayDecision.ESCALATE
    assert gateway.escalation_reasons == ("request_purpose_unclear",)
    assert gateway.block_reasons == ()


def test_missing_review_path_stops_automatic_continuation():
    case = _case("CASE_104", "CLIENT_104", "DOCUMENT_104", signals=("missing_review_path",))

    output = build_mock_workflow(case)

    assert output.gateway.decision == GatewayDecision.ESCALATE
    assert "review_path_missing" in output.gateway.escalation_reasons
    assert output.review_gate.allows_offline_mock_continuation is False
    assert output.draft_package.question_drafts == ()
    assert all("Szenario:" not in point for point in output.draft_package.summary_points)


def test_reidentification_risk_stops_automatic_continuation():
    case = _case("CASE_105", "CLIENT_105", "DOCUMENT_105", signals=("reidentification_risk",))

    output = build_mock_workflow(case)

    assert output.gateway.decision == GatewayDecision.ESCALATE
    assert "reidentification_risk" in output.gateway.escalation_reasons
    assert output.review_gate.allows_offline_mock_continuation is False
    assert output.draft_package.question_drafts == ()
    assert all(
        "Synthetische Dokumenthinweise:" not in point
        for point in output.draft_package.summary_points
    )


def test_forbidden_data_class_blocks_workflow_without_substantive_draft_package():
    case = _case("CASE_106", "CLIENT_106", "DOCUMENT_106", signals=("forbidden_original_pii",))

    output = build_mock_workflow(case)

    assert output.gateway.decision == GatewayDecision.BLOCK
    assert output.gateway.block_reasons == ("forbidden_data_class:original_pii",)
    assert output.risk_classification.risk_level == RiskLevel.CLASS_D
    assert output.review_gate.allows_offline_mock_continuation is False
    assert output.draft_package.review_required is True
    assert output.draft_package.question_drafts == ()
    assert all("Szenario:" not in point for point in output.draft_package.summary_points)


def test_response_gateway_blocks_productive_transmission_suggestion():
    package = DraftPackage(
        title="Offline-MVP Entwurf fuer CASE_107",
        review_status=ReviewStatus.DRAFT,
        risk_classification=RiskClassification(
            risk_level=RiskLevel.CLASS_A,
            review_required=False,
            basis=("synthetic_internal_admin_fixture",),
        ),
        review_required=False,
        summary_points=("Entwurf mit Human Review sichtbar.",),
        question_drafts=(),
        handoff_notes=("produktive uebermittlung vorbereitet.",),
        disclaimers=("Entwurf mit Human Review sichtbar.",),
    )

    gateway = run_response_gateway_check(package)

    assert gateway.decision == GatewayDecision.BLOCK
    assert gateway.block_reasons == ("productive_transmission_suggested",)


def test_response_gateway_blocks_tax_advice_suggestion():
    package = DraftPackage(
        title="Offline-MVP Entwurf fuer CASE_108",
        review_status=ReviewStatus.DRAFT,
        risk_classification=RiskClassification(
            risk_level=RiskLevel.CLASS_A,
            review_required=False,
            basis=("synthetic_internal_admin_fixture",),
        ),
        review_required=False,
        summary_points=("Entwurf mit Human Review sichtbar.",),
        question_drafts=(),
        handoff_notes=(TAX_ADVICE_MARKER,),
        disclaimers=(DRAFT_REVIEW_DISCLAIMER,),
    )

    gateway = run_response_gateway_check(package)

    assert gateway.decision == GatewayDecision.BLOCK
    assert gateway.block_reasons == ("tax_advice_suggested",)


def test_productive_transmission_is_not_masked_by_standard_disclaimer():
    package = _response_draft_package(
        handoff_notes=("Die produktive Übermittlung wurde vorbereitet.",),
    )

    gateway = run_response_gateway_check(package)

    assert gateway.decision == GatewayDecision.BLOCK
    assert gateway.block_reasons == ("productive_transmission_suggested",)


def test_tax_advice_in_summary_is_not_masked_by_standard_disclaimer():
    package = _response_draft_package(
        summary_points=("Entwurf mit Human Review: Steuerberatung wurde vorbereitet.",),
    )

    gateway = run_response_gateway_check(package)

    assert gateway.decision == GatewayDecision.BLOCK
    assert gateway.block_reasons == ("tax_advice_suggested",)


def test_marker_in_title_is_not_masked_by_disclaimer_negation():
    package = _response_draft_package(
        title="Entwurf: Steuerberatung für den synthetischen Fall.",
    )

    gateway = run_response_gateway_check(package)

    assert gateway.decision == GatewayDecision.BLOCK
    assert gateway.block_reasons == ("tax_advice_suggested",)


def test_marker_in_question_is_not_masked_by_negation_in_another_field():
    package = _response_draft_package(
        question_drafts=("Soll die produktive Übermittlung vorbereitet werden?",),
        handoff_notes=("Keine produktive Übermittlung.",),
    )

    gateway = run_response_gateway_check(package)

    assert gateway.decision == GatewayDecision.BLOCK
    assert gateway.block_reasons == ("productive_transmission_suggested",)


def test_exact_tax_advice_negation_in_fragment_remains_allowed():
    package = _response_draft_package(disclaimers=("Keine Steuerberatung.",))

    gateway = run_response_gateway_check(package)

    assert gateway.decision == GatewayDecision.ALLOW_DRAFT
    assert gateway.block_reasons == ()


def test_exact_productive_transmission_negation_in_fragment_remains_allowed():
    package = _response_draft_package(
        disclaimers=("Keine produktive Übermittlung.",)
    )

    gateway = run_response_gateway_check(package)

    assert gateway.decision == GatewayDecision.ALLOW_DRAFT
    assert gateway.block_reasons == ()


def test_second_tax_advice_occurrence_in_negated_fragment_is_blocked():
    package = _response_draft_package(
        handoff_notes=("Keine Steuerberatung. Wir leisten Steuerberatung.",),
    )

    gateway = run_response_gateway_check(package)

    assert gateway.decision == GatewayDecision.BLOCK
    assert gateway.block_reasons == ("tax_advice_suggested",)


def test_second_transmission_occurrence_in_negated_fragment_is_blocked():
    package = _response_draft_package(
        handoff_notes=(
            "Keine produktive Übermittlung. Produktive Übermittlung vorbereitet.",
        ),
    )

    gateway = run_response_gateway_check(package)

    assert gateway.decision == GatewayDecision.BLOCK
    assert gateway.block_reasons == ("productive_transmission_suggested",)


def test_uppercase_productive_transmission_with_umlaut_is_blocked():
    package = _response_draft_package(
        handoff_notes=("PRODUKTIVE ÜBERMITTLUNG WURDE VORBEREITET.",),
    )

    gateway = run_response_gateway_check(package)

    assert gateway.decision == GatewayDecision.BLOCK
    assert gateway.block_reasons == ("productive_transmission_suggested",)


def test_response_marker_with_mixed_unicode_whitespace_is_blocked():
    package = _response_draft_package(
        handoff_notes=("produktive\u00a0 \t\nÜbermittlung vorbereitet.",),
    )

    gateway = run_response_gateway_check(package)

    assert gateway.decision == GatewayDecision.BLOCK
    assert gateway.block_reasons == ("productive_transmission_suggested",)


def test_response_marker_with_decomposed_unicode_umlaut_is_blocked():
    package = _response_draft_package(
        handoff_notes=("produktive U\u0308bermittlung vorbereitet.",),
    )

    gateway = run_response_gateway_check(package)

    assert gateway.decision == GatewayDecision.BLOCK
    assert gateway.block_reasons == ("productive_transmission_suggested",)


def test_human_review_visibility_accepts_uppercase_german_umlaut_spelling():
    package = _response_draft_package(
        summary_points=("FACHLICHE PRÜFUNG ERFORDERLICH.",),
    )

    gateway = run_response_gateway_check(package)

    assert gateway.decision == GatewayDecision.ALLOW_DRAFT
    assert gateway.escalation_reasons == ()


def test_response_gateway_keeps_missing_draft_character_escalation():
    package = _response_draft_package(
        title="Interne synthetische Notiz",
        summary_points=("Human Review erforderlich.",),
    )

    gateway = run_response_gateway_check(package)

    assert gateway.decision == GatewayDecision.ESCALATE
    assert gateway.escalation_reasons == ("draft_character_not_visible",)


def test_response_gateway_keeps_missing_human_review_escalation():
    package = _response_draft_package(
        summary_points=("Interner synthetischer Entwurf.",),
    )

    gateway = run_response_gateway_check(package)

    assert gateway.decision == GatewayDecision.ESCALATE
    assert gateway.escalation_reasons == ("human_review_not_visible",)


def test_response_gateway_keeps_both_block_reasons_in_stable_order():
    package = _response_draft_package(
        handoff_notes=("Produktive Übermittlung und Steuerberatung vorbereitet.",),
    )

    gateway = run_response_gateway_check(package)

    assert gateway.decision == GatewayDecision.BLOCK
    assert gateway.block_reasons == (
        "productive_transmission_suggested",
        "tax_advice_suggested",
    )


def test_generated_draft_text_keeps_response_gateway_markers_visible():
    for case in load_fixture_cases():
        output = build_mock_workflow(case)
        combined_text = _draft_package_text(output.draft_package).lower()

        assert any(
            marker in combined_text for marker in RESPONSE_DRAFT_VISIBILITY_MARKERS
        )
        assert any(
            marker in combined_text
            for marker in RESPONSE_HUMAN_REVIEW_VISIBILITY_MARKERS
        )
        assert PRODUCTIVE_TRANSMISSION_MARKER in combined_text
        assert PRODUCTIVE_TRANSMISSION_NEGATION_MARKER in combined_text
        assert TAX_ADVICE_MARKER in combined_text
        assert TAX_ADVICE_NEGATION_MARKER in combined_text
        assert DRAFT_REVIEW_DISCLAIMER in output.draft_package.disclaimers
        assert (
            NO_TAX_ADVICE_OR_PRODUCTIVE_TRANSMISSION_DISCLAIMER
            in output.draft_package.disclaimers
        )

        gateway = run_response_gateway_check(output.draft_package)
        assert gateway.decision == GatewayDecision.ALLOW_DRAFT
        assert gateway.escalation_reasons == ()
        assert gateway.block_reasons == ()


def _case(
    case_id: str,
    client_ref: str,
    document_id: str,
    signals: tuple[str, ...] = (),
) -> IntakeCase:
    return IntakeCase(
        case_id=case_id,
        client_ref=client_ref,
        scenario="synthetischer Offline-Gateway-Test",
        period="2026-Q4",
        documents=(
            SyntheticDocument(
                document_id=document_id,
                label="synthetischer Gateway-Platzhalter",
                period="2026-Q4",
                source_note="Synthetisches Testfixture ohne Originaldaten.",
            ),
        ),
        mock_risk_signals=signals,
    )


def _draft_package_text(package: DraftPackage) -> str:
    return " ".join(
        (
            package.title,
            *package.summary_points,
            *package.question_drafts,
            *package.handoff_notes,
            *package.disclaimers,
        )
    )


def _response_draft_package(
    *,
    title: str = "Offline-MVP Entwurf fuer CASE_109",
    summary_points: tuple[str, ...] = ("Human Review erforderlich.",),
    question_drafts: tuple[str, ...] = (),
    handoff_notes: tuple[str, ...] = (),
    disclaimers: tuple[str, ...] = (
        NO_TAX_ADVICE_OR_PRODUCTIVE_TRANSMISSION_DISCLAIMER,
    ),
) -> DraftPackage:
    return DraftPackage(
        title=title,
        review_status=ReviewStatus.DRAFT,
        risk_classification=RiskClassification(
            risk_level=RiskLevel.CLASS_A,
            review_required=False,
            basis=("synthetic_internal_admin_fixture",),
        ),
        review_required=False,
        summary_points=summary_points,
        question_drafts=question_drafts,
        handoff_notes=handoff_notes,
        disclaimers=disclaimers,
    )
