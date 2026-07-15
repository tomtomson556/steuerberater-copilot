from dataclasses import FrozenInstanceError, replace
from unittest.mock import Mock

import pytest
from openai import APIError

import steuerberater_copilot.evaluation as evaluation
import steuerberater_copilot.evaluation.runner as evaluation_runner
from steuerberater_copilot.ai import (
    FakeModelProvider,
    ModelInvocationPolicyViolationError,
    ModelRequest,
    ModelResponse,
    OpenAIResponsesProvider,
)
from steuerberater_copilot.evaluation import (
    EvaluationCase,
    EvaluationRunResult,
    ExpectedAIWorkflowOutcome,
    run_offline_evaluation_case,
)
from steuerberater_copilot.offline_mvp import (
    GatewayDecision,
    IntakeCase,
    ReviewGateStatus,
    StructuredDraftOutput,
    StructuredDraftOutputParseError,
    SyntheticAIWorkflowOutput,
    SyntheticDocument,
    build_synthetic_model_request,
    classify_internal_risk,
    run_human_review_gate,
)
from steuerberater_copilot.offline_mvp.workflow import run_mock_gateway

VALID_STRUCTURED_CONTENT = (
    "{"
    '"summary_points":["Synthetic summary."],'
    '"uncertainties":["Synthetic uncertainty."],'
    '"review_questions":["Synthetic review question?"]'
    "}"
)

SEMANTICALLY_INVALID_STRUCTURED_CONTENT = (
    "{"
    '"summary_points":[""],'
    '"uncertainties":["Synthetic uncertainty."],'
    '"review_questions":["Synthetic review question?"]'
    "}"
)


def test_evaluation_run_result_keeps_all_fields_unchanged() -> None:
    evaluation_case = _evaluation_case(
        expected_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
        expected_structured_draft=_structured_draft(),
    )
    structured_draft = _structured_draft()

    result = EvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_gateway_decision=GatewayDecision.ALLOW_DRAFT,
        observed_review_gate_status=(
            ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
        ),
        observed_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
        observed_structured_draft=structured_draft,
        provider_call_count=1,
    )

    assert result.evaluation_case is evaluation_case
    assert result.observed_gateway_decision is GatewayDecision.ALLOW_DRAFT
    assert (
        result.observed_review_gate_status
        is ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
    )
    assert result.observed_outcome is ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT
    assert result.observed_structured_draft is structured_draft
    assert result.provider_call_count == 1
    assert result == EvaluationRunResult(
        evaluation_case=evaluation_case,
        observed_gateway_decision=GatewayDecision.ALLOW_DRAFT,
        observed_review_gate_status=(
            ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
        ),
        observed_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
        observed_structured_draft=structured_draft,
        provider_call_count=1,
    )


def test_evaluation_run_result_is_immutable_and_uses_slots() -> None:
    result = _provider_error_result()

    with pytest.raises(FrozenInstanceError):
        result.provider_call_count = 2

    assert not hasattr(result, "__dict__")


def test_evaluation_run_result_equality_includes_all_fields() -> None:
    base = _structured_result()

    assert base != replace(
        base,
        evaluation_case=_evaluation_case(evaluation_id="EVAL_OTHER"),
    )
    assert base != replace(
        base,
        observed_gateway_decision=GatewayDecision.BLOCK,
    )
    assert base != replace(
        base,
        observed_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
    )
    assert _provider_error_result() != replace(
        _provider_error_result(),
        observed_outcome=ExpectedAIWorkflowOutcome.PARSE_ERROR,
    )
    assert base != replace(
        base,
        observed_structured_draft=StructuredDraftOutput(
            summary_points=("Different synthetic summary.",),
            uncertainties=("Synthetic uncertainty.",),
            review_questions=("Synthetic review question?",),
        ),
    )
    assert base != replace(base, provider_call_count=2)


def test_evaluation_run_result_rejects_negative_provider_call_count() -> None:
    with pytest.raises(
        ValueError,
        match=r"^provider_call_count must not be negative\.$",
    ):
        EvaluationRunResult(
            evaluation_case=_evaluation_case(),
            observed_gateway_decision=GatewayDecision.ALLOW_DRAFT,
            observed_review_gate_status=(
                ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
            ),
            observed_outcome=ExpectedAIWorkflowOutcome.PROVIDER_ERROR,
            observed_structured_draft=None,
            provider_call_count=-1,
        )


def test_evaluation_run_result_requires_draft_for_structured_outcome() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^observed_structured_draft is required for "
            r"structured_draft outcome\.$"
        ),
    ):
        EvaluationRunResult(
            evaluation_case=_evaluation_case(),
            observed_gateway_decision=GatewayDecision.ALLOW_DRAFT,
            observed_review_gate_status=(
                ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
            ),
            observed_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
            observed_structured_draft=None,
            provider_call_count=1,
        )


def test_evaluation_run_result_rejects_draft_for_other_outcome() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^observed_structured_draft must be None unless outcome is "
            r"structured_draft\.$"
        ),
    ):
        EvaluationRunResult(
            evaluation_case=_evaluation_case(),
            observed_gateway_decision=GatewayDecision.ALLOW_DRAFT,
            observed_review_gate_status=(
                ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
            ),
            observed_outcome=ExpectedAIWorkflowOutcome.PARSE_ERROR,
            observed_structured_draft=_structured_draft(),
            provider_call_count=1,
        )


def test_observed_provider_forwards_request_and_response_unchanged() -> None:
    response = _model_response(VALID_STRUCTURED_CONTENT)
    provider = FakeModelProvider(response)
    observed_provider = evaluation_runner._ObservedModelProvider(provider)
    request = ModelRequest(
        prompt_id="synthetic_observer_prompt",
        prompt_version="1",
        system_prompt="Use only synthetic data.",
        user_prompt="Return the configured synthetic response.",
    )

    result = observed_provider.generate(request)

    assert result is response
    assert provider.requests == (request,)
    assert provider.requests[0] is request
    assert observed_provider.call_count == 1
    assert observed_provider.raised_exception is None


def test_offline_evaluation_runner_observes_gateway_stop() -> None:
    intake = _synthetic_intake(
        missing_items=("Synthetic missing source reference.",),
    )
    evaluation_case = _evaluation_case(
        intake=intake,
        expected_gateway_decision=GatewayDecision.ESCALATE,
        expected_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
        expected_outcome=ExpectedAIWorkflowOutcome.GATEWAY_STOP,
    )
    provider = FakeModelProvider(_model_response(VALID_STRUCTURED_CONTENT))

    result = run_offline_evaluation_case(evaluation_case, provider=provider)

    assert result.observed_gateway_decision is GatewayDecision.ESCALATE
    assert result.observed_review_gate_status is ReviewGateStatus.REQUIRES_HUMAN_REVIEW
    assert result.observed_outcome is ExpectedAIWorkflowOutcome.GATEWAY_STOP
    assert result.observed_structured_draft is None
    assert result.provider_call_count == 0
    assert provider.requests == ()


def test_offline_evaluation_runner_observes_review_gate_stop() -> None:
    intake = _synthetic_intake(mock_risk_signals=("document_preparation",))
    evaluation_case = _evaluation_case(
        intake=intake,
        expected_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
        expected_outcome=ExpectedAIWorkflowOutcome.REVIEW_GATE_STOP,
    )
    provider = FakeModelProvider(_model_response(VALID_STRUCTURED_CONTENT))

    result = run_offline_evaluation_case(evaluation_case, provider=provider)

    assert result.observed_gateway_decision is GatewayDecision.ALLOW_DRAFT
    assert result.observed_review_gate_status is ReviewGateStatus.REQUIRES_HUMAN_REVIEW
    assert result.observed_outcome is ExpectedAIWorkflowOutcome.REVIEW_GATE_STOP
    assert result.observed_structured_draft is None
    assert result.provider_call_count == 0
    assert provider.requests == ()


def test_offline_evaluation_runner_observes_structured_draft() -> None:
    intake = _synthetic_intake()
    structured_draft = _structured_draft()
    evaluation_case = _evaluation_case(
        intake=intake,
        expected_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
        expected_structured_draft=structured_draft,
    )
    provider = FakeModelProvider(_model_response(VALID_STRUCTURED_CONTENT))

    result = run_offline_evaluation_case(evaluation_case, provider=provider)

    assert result.evaluation_case is evaluation_case
    assert result.observed_gateway_decision is GatewayDecision.ALLOW_DRAFT
    assert (
        result.observed_review_gate_status
        is ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
    )
    assert result.observed_outcome is ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT
    assert result.observed_structured_draft == structured_draft
    assert result.provider_call_count == 1
    assert provider.requests == (build_synthetic_model_request(intake),)


def test_offline_evaluation_runner_observes_provider_error() -> None:
    provider_error = RuntimeError("synthetic provider failure")
    provider = _FailingProvider(provider_error)

    result = run_offline_evaluation_case(_evaluation_case(), provider=provider)

    assert result.observed_outcome is ExpectedAIWorkflowOutcome.PROVIDER_ERROR
    assert result.observed_structured_draft is None
    assert result.provider_call_count == 1
    assert provider.requests == [
        build_synthetic_model_request(_synthetic_intake())
    ]


def test_offline_evaluation_runner_observes_openai_error_as_provider_error() -> None:
    client = Mock()
    client.responses.create.side_effect = APIError(
        "Synthetic OpenAI SDK failure.",
        Mock(),
        body=None,
    )
    provider = OpenAIResponsesProvider(
        client=client,
        model="gpt-synthetic-evaluation-test",
        max_output_tokens=2_000,
    )

    result = run_offline_evaluation_case(_evaluation_case(), provider=provider)

    assert result.observed_outcome is ExpectedAIWorkflowOutcome.PROVIDER_ERROR
    assert result.observed_structured_draft is None
    assert result.provider_call_count == 1
    client.responses.create.assert_called_once()


def test_provider_origin_takes_precedence_over_parse_error_type() -> None:
    provider_error = StructuredDraftOutputParseError("Synthetic provider failure.")
    provider = _FailingProvider(provider_error)

    result = run_offline_evaluation_case(_evaluation_case(), provider=provider)

    assert result.observed_outcome is ExpectedAIWorkflowOutcome.PROVIDER_ERROR
    assert result.observed_structured_draft is None
    assert result.provider_call_count == 1


def test_offline_evaluation_runner_observes_parse_error() -> None:
    provider = FakeModelProvider(_model_response('{"summary_points": []}'))

    result = run_offline_evaluation_case(_evaluation_case(), provider=provider)

    assert result.observed_outcome is ExpectedAIWorkflowOutcome.PARSE_ERROR
    assert result.observed_structured_draft is None
    assert result.provider_call_count == 1


def test_offline_evaluation_runner_observes_validation_error() -> None:
    provider = FakeModelProvider(
        _model_response(SEMANTICALLY_INVALID_STRUCTURED_CONTENT)
    )

    result = run_offline_evaluation_case(_evaluation_case(), provider=provider)

    assert result.observed_outcome is ExpectedAIWorkflowOutcome.VALIDATION_ERROR
    assert result.observed_structured_draft is None
    assert result.provider_call_count == 1


def test_offline_evaluation_runner_propagates_response_policy_violation() -> None:
    provider = FakeModelProvider(_model_response("X" * 16_001))

    with pytest.raises(ModelInvocationPolicyViolationError) as exc_info:
        run_offline_evaluation_case(_evaluation_case(), provider=provider)

    assert "observed_chars=16001" in str(exc_info.value)
    assert provider.requests == (
        build_synthetic_model_request(_synthetic_intake()),
    )


def test_offline_evaluation_runner_propagates_unexpected_internal_error(
    monkeypatch,
) -> None:
    unexpected_error = RuntimeError("synthetic unexpected workflow failure")
    provider = FakeModelProvider(_model_response(VALID_STRUCTURED_CONTENT))

    def fail_before_provider(*args, **kwargs):
        raise unexpected_error

    monkeypatch.setattr(
        evaluation_runner,
        "build_synthetic_ai_workflow",
        fail_before_provider,
    )

    with pytest.raises(RuntimeError) as exc_info:
        run_offline_evaluation_case(_evaluation_case(), provider=provider)

    assert exc_info.value is unexpected_error
    assert provider.requests == ()


def test_offline_evaluation_runner_rejects_inconsistent_workflow_output(
    monkeypatch,
) -> None:
    intake = _synthetic_intake()
    gateway = run_mock_gateway(intake)
    risk_classification = classify_internal_risk(intake, gateway)
    review_gate = run_human_review_gate(risk_classification)
    inconsistent_output = SyntheticAIWorkflowOutput(
        intake=intake,
        gateway=gateway,
        risk_classification=risk_classification,
        review_gate=review_gate,
        model_response=None,
        structured_draft=None,
    )

    def return_inconsistent_output(*args, **kwargs):
        return inconsistent_output

    monkeypatch.setattr(
        evaluation_runner,
        "build_synthetic_ai_workflow",
        return_inconsistent_output,
    )

    with pytest.raises(
        RuntimeError,
        match=(
            r"^Synthetic AI workflow returned no structured draft "
            r"after allowed continuation\.$"
        ),
    ):
        run_offline_evaluation_case(
            _evaluation_case(intake=intake),
            provider=FakeModelProvider(_model_response(VALID_STRUCTURED_CONTENT)),
        )


def test_offline_evaluation_runner_does_not_compare_expectations() -> None:
    evaluation_case = _evaluation_case(
        expected_gateway_decision=GatewayDecision.BLOCK,
        expected_review_gate_status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
        expected_outcome=ExpectedAIWorkflowOutcome.PROVIDER_ERROR,
    )

    result = run_offline_evaluation_case(
        evaluation_case,
        provider=FakeModelProvider(_model_response(VALID_STRUCTURED_CONTENT)),
    )

    assert result.evaluation_case is evaluation_case
    assert result.observed_gateway_decision is GatewayDecision.ALLOW_DRAFT
    assert (
        result.observed_review_gate_status
        is ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
    )
    assert result.observed_outcome is ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT
    assert not hasattr(result, "passed")
    assert not hasattr(result, "is_success")


def test_evaluation_package_exports_offline_runner_contract() -> None:
    assert evaluation.EvaluationCase is EvaluationCase
    assert evaluation.EvaluationRunResult is EvaluationRunResult
    assert evaluation.ExpectedAIWorkflowOutcome is ExpectedAIWorkflowOutcome
    assert evaluation.run_offline_evaluation_case is run_offline_evaluation_case
    assert "EvaluationCase" in evaluation.__all__
    assert "EvaluationRunResult" in evaluation.__all__
    assert "ExpectedAIWorkflowOutcome" in evaluation.__all__
    assert "run_offline_evaluation_case" in evaluation.__all__


class _FailingProvider:
    def __init__(self, error: Exception) -> None:
        self.error = error
        self.requests: list[ModelRequest] = []

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        raise self.error


def _evaluation_case(
    *,
    evaluation_id: str = "EVAL_RUNNER_TEST",
    intake: IntakeCase | None = None,
    expected_gateway_decision: GatewayDecision = GatewayDecision.ALLOW_DRAFT,
    expected_review_gate_status: ReviewGateStatus = (
        ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
    ),
    expected_outcome: ExpectedAIWorkflowOutcome = (
        ExpectedAIWorkflowOutcome.PROVIDER_ERROR
    ),
    expected_structured_draft: StructuredDraftOutput | None = None,
) -> EvaluationCase:
    return EvaluationCase(
        evaluation_id=evaluation_id,
        intake=intake or _synthetic_intake(),
        expected_gateway_decision=expected_gateway_decision,
        expected_review_gate_status=expected_review_gate_status,
        expected_outcome=expected_outcome,
        expected_structured_draft=expected_structured_draft,
    )


def _structured_result() -> EvaluationRunResult:
    structured_draft = _structured_draft()
    return EvaluationRunResult(
        evaluation_case=_evaluation_case(
            expected_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
            expected_structured_draft=structured_draft,
        ),
        observed_gateway_decision=GatewayDecision.ALLOW_DRAFT,
        observed_review_gate_status=(
            ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
        ),
        observed_outcome=ExpectedAIWorkflowOutcome.STRUCTURED_DRAFT,
        observed_structured_draft=structured_draft,
        provider_call_count=1,
    )


def _provider_error_result() -> EvaluationRunResult:
    return EvaluationRunResult(
        evaluation_case=_evaluation_case(),
        observed_gateway_decision=GatewayDecision.ALLOW_DRAFT,
        observed_review_gate_status=(
            ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION
        ),
        observed_outcome=ExpectedAIWorkflowOutcome.PROVIDER_ERROR,
        observed_structured_draft=None,
        provider_call_count=1,
    )


def _synthetic_intake(
    *,
    missing_items: tuple[str, ...] = (),
    mock_risk_signals: tuple[str, ...] = (),
) -> IntakeCase:
    return IntakeCase(
        case_id="CASE_300",
        client_ref="CLIENT_300",
        scenario="Synthetic offline evaluation runner test.",
        period="2026-Q3",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_300",
                label="Synthetic runner document descriptor.",
                period="2026-Q3",
                source_note="Synthetic source note without original content.",
            ),
        ),
        missing_items=missing_items,
        mock_risk_signals=mock_risk_signals,
    )


def _structured_draft() -> StructuredDraftOutput:
    return StructuredDraftOutput(
        summary_points=("Synthetic summary.",),
        uncertainties=("Synthetic uncertainty.",),
        review_questions=("Synthetic review question?",),
    )


def _model_response(content: str) -> ModelResponse:
    return ModelResponse(
        content=content,
        provider_name="fake",
        model_name="fake-model",
    )
