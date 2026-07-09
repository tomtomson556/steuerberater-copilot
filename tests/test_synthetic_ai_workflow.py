import pytest

import steuerberater_copilot.offline_mvp as offline_mvp
import steuerberater_copilot.offline_mvp.ai_workflow as ai_workflow
from steuerberater_copilot.ai import FakeModelProvider, ModelRequest, ModelResponse
from steuerberater_copilot.offline_mvp.ai_workflow import (
    SyntheticAIWorkflowOutput,
    build_synthetic_ai_workflow,
)
from steuerberater_copilot.offline_mvp.models import (
    GatewayDecision,
    IntakeCase,
    MockRiskSignal,
    RiskLevel,
    SyntheticDocument,
)
from steuerberater_copilot.offline_mvp.prompt_builder import (
    build_synthetic_model_request,
)
from steuerberater_copilot.offline_mvp.structured_output import StructuredDraftOutput
from steuerberater_copilot.offline_mvp.structured_output_parser import (
    StructuredDraftOutputParseError,
)
from steuerberater_copilot.offline_mvp.structured_output_validator import (
    StructuredDraftOutputValidationError,
)

VALID_STRUCTURED_CONTENT = (
    "{"
    '"summary_points":["Synthetic summary"],'
    '"uncertainties":["Synthetic uncertainty"],'
    '"review_questions":["Synthetic review question"]'
    "}"
)

SEMANTICALLY_INVALID_STRUCTURED_CONTENT = (
    "{"
    '"summary_points":[""],'
    '"uncertainties":["Synthetic uncertainty"],'
    '"review_questions":["Synthetic review question"]'
    "}"
)


def test_synthetic_ai_workflow_runs_successful_controlled_path() -> None:
    case = _allowed_class_a_case()
    response = _model_response(VALID_STRUCTURED_CONTENT)
    provider = FakeModelProvider(response)

    result = build_synthetic_ai_workflow(case, provider=provider)

    assert result.intake is case
    assert result.gateway.decision is GatewayDecision.ALLOW_DRAFT
    assert result.risk_classification.risk_level is RiskLevel.CLASS_A
    assert result.review_gate.allows_offline_mock_continuation is True
    assert provider.requests == (build_synthetic_model_request(case),)
    assert result.model_response is response
    assert result.structured_draft == StructuredDraftOutput(
        summary_points=("Synthetic summary",),
        uncertainties=("Synthetic uncertainty",),
        review_questions=("Synthetic review question",),
    )


def test_synthetic_ai_workflow_uses_invocation_boundary(monkeypatch) -> None:
    case = _allowed_class_a_case()
    response = _model_response(VALID_STRUCTURED_CONTENT)
    provider = FakeModelProvider(response)
    calls: list[ModelRequest] = []

    def invoke_spy(**kwargs):
        calls.append(kwargs["request"])
        return provider.generate(kwargs["request"])

    monkeypatch.setattr(ai_workflow, "invoke_model_if_allowed", invoke_spy)

    result = build_synthetic_ai_workflow(case, provider=provider)

    assert calls == [build_synthetic_model_request(case)]
    assert provider.requests == (build_synthetic_model_request(case),)
    assert result.model_response is response


def test_synthetic_ai_workflow_gateway_stop_skips_prompt_and_provider(
    monkeypatch,
) -> None:
    case = _missing_context_case()
    provider = FakeModelProvider(_model_response(VALID_STRUCTURED_CONTENT))

    def fail_if_called(_case: IntakeCase) -> ModelRequest:
        raise AssertionError("prompt builder must not run after gateway stop")

    monkeypatch.setattr(ai_workflow, "build_synthetic_model_request", fail_if_called)

    result = build_synthetic_ai_workflow(case, provider=provider)

    assert result.gateway.decision is GatewayDecision.ESCALATE
    assert result.review_gate.allows_offline_mock_continuation is False
    assert result.review_gate is not None
    assert provider.requests == ()
    assert result.model_response is None
    assert result.structured_draft is None


def test_synthetic_ai_workflow_review_gate_stop_after_gateway_allow() -> None:
    case = _review_gate_stop_case()
    provider = FakeModelProvider(_model_response(VALID_STRUCTURED_CONTENT))

    result = build_synthetic_ai_workflow(case, provider=provider)

    assert result.gateway.decision is GatewayDecision.ALLOW_DRAFT
    assert result.risk_classification.risk_level is RiskLevel.CLASS_B
    assert result.review_gate.allows_offline_mock_continuation is False
    assert provider.requests == ()
    assert result.model_response is None
    assert result.structured_draft is None


def test_synthetic_ai_workflow_propagates_parser_errors_unchanged() -> None:
    provider = FakeModelProvider(_model_response('{"summary_points": []}'))

    with pytest.raises(StructuredDraftOutputParseError):
        build_synthetic_ai_workflow(_allowed_class_a_case(), provider=provider)

    assert provider.requests == (build_synthetic_model_request(_allowed_class_a_case()),)


def test_synthetic_ai_workflow_propagates_validation_errors_unchanged() -> None:
    case = _allowed_class_a_case()
    provider = FakeModelProvider(_model_response(SEMANTICALLY_INVALID_STRUCTURED_CONTENT))

    with pytest.raises(StructuredDraftOutputValidationError) as exc_info:
        build_synthetic_ai_workflow(case, provider=provider)

    error = exc_info.value
    assert error.rule == "blank_entry"
    assert error.field_name == "summary_points"
    assert error.item_index == 0
    assert provider.requests == (build_synthetic_model_request(case),)


def test_synthetic_ai_workflow_propagates_provider_errors_unchanged() -> None:
    class FailingProvider:
        def __init__(self) -> None:
            self.requests: list[ModelRequest] = []

        def generate(self, request: ModelRequest) -> ModelResponse:
            self.requests.append(request)
            raise RuntimeError("provider failed")

    case = _allowed_class_a_case()
    provider = FailingProvider()

    with pytest.raises(RuntimeError, match=r"^provider failed$"):
        build_synthetic_ai_workflow(case, provider=provider)

    assert provider.requests == [build_synthetic_model_request(case)]


def test_synthetic_ai_workflow_public_export() -> None:
    assert offline_mvp.SyntheticAIWorkflowOutput is SyntheticAIWorkflowOutput
    assert offline_mvp.build_synthetic_ai_workflow is build_synthetic_ai_workflow
    assert "SyntheticAIWorkflowOutput" in offline_mvp.__all__
    assert "build_synthetic_ai_workflow" in offline_mvp.__all__


def _allowed_class_a_case() -> IntakeCase:
    return IntakeCase(
        case_id="CASE_200",
        client_ref="CLIENT_200",
        scenario="synthetic controlled AI workflow fixture",
        period="2026-Q1",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_200",
                label="synthetic invoice descriptor",
                period="2026-Q1",
                source_note="synthetic source note",
            ),
        ),
        notes=("Internal synthetic preparation note.",),
    )


def _missing_context_case() -> IntakeCase:
    return IntakeCase(
        case_id="CASE_201",
        client_ref="CLIENT_201",
        scenario="synthetic missing context fixture",
        period="2026-Q1",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_201",
                label="synthetic payment overview descriptor",
                period="2026-Q1",
                source_note="synthetic source note",
            ),
        ),
        missing_items=("Synthetic missing source reference.",),
    )


def _review_gate_stop_case() -> IntakeCase:
    return IntakeCase(
        case_id="CASE_202",
        client_ref="CLIENT_202",
        scenario="synthetic document preparation fixture",
        period="2026-Q1",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_202",
                label="synthetic document descriptor",
                period="2026-Q1",
                source_note="synthetic source note",
            ),
        ),
        mock_risk_signals=(MockRiskSignal.DOCUMENT_PREPARATION.value,),
    )


def _model_response(content: str) -> ModelResponse:
    return ModelResponse(
        content=content,
        provider_name="fake",
        model_name="fake-model",
    )
