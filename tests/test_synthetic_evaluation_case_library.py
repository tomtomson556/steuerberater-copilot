from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.evaluation as evaluation
from steuerberater_copilot.ai import (
    FakeModelProvider,
    ModelProvider,
    ModelRequest,
    ModelResponse,
)
from steuerberater_copilot.evaluation import (
    EvaluationCase,
    ExpectedAIWorkflowOutcome,
    SyntheticEvaluationFixture,
    assess_evaluation_run_result,
    build_synthetic_evaluation_case_library,
    run_offline_evaluation_case,
)
from steuerberater_copilot.offline_mvp import (
    GatewayDecision,
    IntakeCase,
    ReviewGateStatus,
    SyntheticDocument,
)

EXPECTED_EVALUATION_IDS = (
    "EVAL_BASELINE_GATEWAY_BLOCK",
    "EVAL_BASELINE_GATEWAY_ESCALATION",
    "EVAL_BASELINE_REVIEW_GATE_STOP",
    "EVAL_BASELINE_STRUCTURED_DRAFT",
    "EVAL_BASELINE_PROVIDER_ERROR",
    "EVAL_BASELINE_PARSE_ERROR",
    "EVAL_BASELINE_VALIDATION_ERROR",
)


def test_synthetic_evaluation_fixture_is_immutable_and_uses_slots() -> None:
    fixture = _response_fixture()

    with pytest.raises(FrozenInstanceError):
        fixture.model_response = _model_response()

    assert not hasattr(fixture, "__dict__")
    assert SyntheticEvaluationFixture.__slots__ == (
        "evaluation_case",
        "model_response",
        "provider_error_message",
    )


def test_synthetic_evaluation_fixture_accepts_exactly_one_provider_reaction() -> None:
    response = _model_response()

    response_fixture = SyntheticEvaluationFixture(
        evaluation_case=_evaluation_case(),
        model_response=response,
    )
    error_fixture = SyntheticEvaluationFixture(
        evaluation_case=_evaluation_case(),
        provider_error_message="Synthetic provider failure.",
    )

    assert response_fixture.model_response is response
    assert response_fixture.provider_error_message is None
    assert error_fixture.model_response is None
    assert error_fixture.provider_error_message == "Synthetic provider failure."


def test_synthetic_evaluation_fixture_rejects_two_provider_reactions() -> None:
    with pytest.raises(
        ValueError,
        match=r"^Exactly one synthetic provider reaction is required\.$",
    ):
        SyntheticEvaluationFixture(
            evaluation_case=_evaluation_case(),
            model_response=_model_response(),
            provider_error_message="Synthetic provider failure.",
        )


def test_synthetic_evaluation_fixture_rejects_missing_provider_reaction() -> None:
    with pytest.raises(
        ValueError,
        match=r"^Exactly one synthetic provider reaction is required\.$",
    ):
        SyntheticEvaluationFixture(evaluation_case=_evaluation_case())


@pytest.mark.parametrize("error_message", ("", " \t\n"))
def test_synthetic_evaluation_fixture_rejects_blank_provider_error_message(
    error_message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"^provider_error_message must not be blank\.$",
    ):
        SyntheticEvaluationFixture(
            evaluation_case=_evaluation_case(),
            provider_error_message=error_message,
        )


def test_create_provider_returns_fresh_fake_providers_and_preserves_response() -> None:
    response = _model_response()
    original_fields = (response.content, response.provider_name, response.model_name)
    fixture = SyntheticEvaluationFixture(
        evaluation_case=_evaluation_case(),
        model_response=response,
    )

    first_provider = fixture.create_provider()
    second_provider = fixture.create_provider()
    request = _model_request()

    assert isinstance(first_provider, FakeModelProvider)
    assert isinstance(second_provider, FakeModelProvider)
    assert first_provider is not second_provider
    assert first_provider.generate(request) is response
    assert first_provider.requests == (request,)
    assert second_provider.requests == ()
    assert fixture.model_response is response
    assert (response.content, response.provider_name, response.model_name) == original_fields


def test_create_provider_returns_fresh_failing_providers() -> None:
    fixture = SyntheticEvaluationFixture(
        evaluation_case=_evaluation_case(),
        provider_error_message="Synthetic provider failure.",
    )

    first_provider = fixture.create_provider()
    second_provider = fixture.create_provider()

    assert isinstance(first_provider, ModelProvider)
    assert isinstance(second_provider, ModelProvider)
    assert first_provider is not second_provider
    with pytest.raises(RuntimeError, match=r"^Synthetic provider failure\.$"):
        first_provider.generate(_model_request())
    with pytest.raises(RuntimeError, match=r"^Synthetic provider failure\.$"):
        second_provider.generate(_model_request())


def test_library_has_exact_stable_baseline_cases_and_order() -> None:
    fixtures = build_synthetic_evaluation_case_library()
    evaluation_ids = tuple(
        fixture.evaluation_case.evaluation_id for fixture in fixtures
    )

    assert isinstance(fixtures, tuple)
    assert len(fixtures) == 7
    assert evaluation_ids == EXPECTED_EVALUATION_IDS
    assert len(evaluation_ids) == len(set(evaluation_ids))


def test_library_covers_all_terminal_outcomes_and_both_gateway_stops() -> None:
    cases = tuple(
        fixture.evaluation_case
        for fixture in build_synthetic_evaluation_case_library()
    )
    outcomes = {case.expected_outcome for case in cases}
    gateway_stop_decisions = {
        case.expected_gateway_decision
        for case in cases
        if case.expected_outcome is ExpectedAIWorkflowOutcome.GATEWAY_STOP
    }

    assert outcomes == set(ExpectedAIWorkflowOutcome)
    assert gateway_stop_decisions == {
        GatewayDecision.BLOCK,
        GatewayDecision.ESCALATE,
    }


def test_library_uses_only_explicitly_synthetic_references_and_content() -> None:
    for fixture in build_synthetic_evaluation_case_library():
        case = fixture.evaluation_case
        intake = case.intake
        combined_text = " ".join(
            (
                intake.scenario,
                *intake.notes,
                *intake.missing_items,
                *(document.label for document in intake.documents),
                *(document.source_note for document in intake.documents),
                fixture.model_response.content if fixture.model_response else "",
                fixture.provider_error_message or "",
            )
        ).lower()

        assert case.evaluation_id.startswith("EVAL_BASELINE_")
        assert intake.case_id.startswith("CASE_4")
        assert intake.client_ref.startswith("CLIENT_4")
        assert intake.scenario.startswith("Synthetic ")
        assert all(document.document_id.startswith("DOCUMENT_4") for document in intake.documents)
        assert all(document.label.startswith("Synthetic ") for document in intake.documents)
        assert all(document.source_note.startswith("Synthetic ") for document in intake.documents)
        assert all(note.startswith("Synthetic ") for note in intake.notes)
        assert all(item.startswith("Synthetic ") for item in intake.missing_items)
        assert all(
            forbidden_marker not in combined_text
            for forbidden_marker in (
                "@",
                "api key",
                "bank account",
                "iban",
                "password",
                "tax identifier",
            )
        )


def test_all_baseline_cases_run_and_pass_with_expected_provider_counts() -> None:
    results_by_id = {}

    for fixture in build_synthetic_evaluation_case_library():
        result = run_offline_evaluation_case(
            fixture.evaluation_case,
            provider=fixture.create_provider(),
        )
        assessment = assess_evaluation_run_result(result)
        evaluation_id = fixture.evaluation_case.evaluation_id

        assert assessment.evaluation_run_result is result
        assert assessment.passed is True, evaluation_id
        results_by_id[evaluation_id] = result

    assert results_by_id["EVAL_BASELINE_GATEWAY_BLOCK"].provider_call_count == 0
    assert (
        results_by_id["EVAL_BASELINE_GATEWAY_ESCALATION"].provider_call_count
        == 0
    )
    assert results_by_id["EVAL_BASELINE_REVIEW_GATE_STOP"].provider_call_count == 0
    for evaluation_id in EXPECTED_EVALUATION_IDS[3:]:
        assert results_by_id[evaluation_id].provider_call_count == 1


def test_success_and_error_baselines_remain_exactly_distinguishable() -> None:
    results_by_id = {
        fixture.evaluation_case.evaluation_id: run_offline_evaluation_case(
            fixture.evaluation_case,
            provider=fixture.create_provider(),
        )
        for fixture in build_synthetic_evaluation_case_library()
    }
    structured_result = results_by_id["EVAL_BASELINE_STRUCTURED_DRAFT"]

    assert (
        structured_result.observed_structured_draft
        == structured_result.evaluation_case.expected_structured_draft
    )
    assert (
        results_by_id["EVAL_BASELINE_PROVIDER_ERROR"].observed_outcome
        is ExpectedAIWorkflowOutcome.PROVIDER_ERROR
    )
    assert (
        results_by_id["EVAL_BASELINE_PARSE_ERROR"].observed_outcome
        is ExpectedAIWorkflowOutcome.PARSE_ERROR
    )
    assert (
        results_by_id["EVAL_BASELINE_VALIDATION_ERROR"].observed_outcome
        is ExpectedAIWorkflowOutcome.VALIDATION_ERROR
    )


def test_separate_library_builds_share_no_fixtures_cases_or_providers() -> None:
    first_library = build_synthetic_evaluation_case_library()
    second_library = build_synthetic_evaluation_case_library()

    assert first_library is not second_library
    for first_fixture, second_fixture in zip(
        first_library,
        second_library,
        strict=True,
    ):
        assert first_fixture is not second_fixture
        assert first_fixture.evaluation_case is not second_fixture.evaluation_case
        assert first_fixture.create_provider() is not second_fixture.create_provider()


def test_evaluation_package_exports_synthetic_library_contract() -> None:
    assert evaluation.SyntheticEvaluationFixture is SyntheticEvaluationFixture
    assert (
        evaluation.build_synthetic_evaluation_case_library
        is build_synthetic_evaluation_case_library
    )
    assert "SyntheticEvaluationFixture" in evaluation.__all__
    assert "build_synthetic_evaluation_case_library" in evaluation.__all__


def _response_fixture() -> SyntheticEvaluationFixture:
    return SyntheticEvaluationFixture(
        evaluation_case=_evaluation_case(),
        model_response=_model_response(),
    )


def _evaluation_case() -> EvaluationCase:
    return EvaluationCase(
        evaluation_id="EVAL_SYNTHETIC_FIXTURE_TEST",
        intake=IntakeCase(
            case_id="CASE_490",
            client_ref="CLIENT_490",
            scenario="Synthetic fixture contract test.",
            period="2026-Q3",
            documents=(
                SyntheticDocument(
                    document_id="DOCUMENT_490",
                    label="Synthetic fixture document descriptor.",
                    period="2026-Q3",
                    source_note="Synthetic source note without original content.",
                ),
            ),
        ),
        expected_gateway_decision=GatewayDecision.ALLOW_DRAFT,
        expected_review_gate_status=(
            ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
        ),
        expected_outcome=ExpectedAIWorkflowOutcome.PROVIDER_ERROR,
        expected_structured_draft=None,
    )


def _model_response() -> ModelResponse:
    return ModelResponse(
        content=(
            "{"
            '"summary_points":["Synthetic summary."],'
            '"uncertainties":["Synthetic uncertainty."],'
            '"review_questions":["Synthetic review question?"]'
            "}"
        ),
        provider_name="synthetic-fixture-test",
        model_name="synthetic-fixture-model",
    )


def _model_request() -> ModelRequest:
    return ModelRequest(
        prompt_id="synthetic_fixture_test_prompt",
        prompt_version="1",
        system_prompt="Use only synthetic fixture data.",
        user_prompt="Return the configured synthetic response.",
    )
