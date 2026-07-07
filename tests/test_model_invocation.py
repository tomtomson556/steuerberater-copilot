import pytest

from steuerberater_copilot.ai import (
    FakeModelProvider,
    ModelRequest,
    ModelResponse,
)
from steuerberater_copilot.offline_mvp.model_invocation import (
    ModelInvocationDeniedError,
    invoke_model_if_allowed,
)
from steuerberater_copilot.offline_mvp.models import (
    GatewayDecision,
    GatewayResult,
    ReviewGateDecision,
    ReviewGateStatus,
    RiskClassification,
    RiskLevel,
)


def test_invoke_model_if_allowed_calls_provider_after_positive_controls() -> None:
    response = _model_response()
    provider = FakeModelProvider(response)
    request = _model_request()
    gateway = _gateway(GatewayDecision.ALLOW_DRAFT)
    review_gate = _review_gate(
        status=ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION,
        allows_offline_mock_continuation=True,
        risk_level=RiskLevel.CLASS_A,
    )

    result = invoke_model_if_allowed(
        provider=provider,
        request=request,
        gateway=gateway,
        review_gate=review_gate,
    )

    assert result is response
    assert provider.requests == (request,)
    assert provider.requests[0] is request


@pytest.mark.parametrize(
    ("gateway_decision", "expected_message"),
    (
        (
            GatewayDecision.BLOCK,
            r"^model invocation denied: gateway decision is block$",
        ),
        (
            GatewayDecision.ESCALATE,
            r"^model invocation denied: gateway decision is escalate$",
        ),
    ),
)
def test_invoke_model_if_allowed_denies_gateway_rejections_before_provider_call(
    gateway_decision: GatewayDecision,
    expected_message: str,
) -> None:
    provider = FakeModelProvider(_model_response())
    request = _model_request()
    gateway = _gateway(gateway_decision)
    review_gate = _review_gate(
        status=ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION,
        allows_offline_mock_continuation=True,
        risk_level=RiskLevel.CLASS_A,
    )

    with pytest.raises(ModelInvocationDeniedError, match=expected_message):
        invoke_model_if_allowed(
            provider=provider,
            request=request,
            gateway=gateway,
            review_gate=review_gate,
        )

    assert provider.requests == ()


def test_invoke_model_if_allowed_denies_negative_review_gate_after_gateway_allow() -> None:
    provider = FakeModelProvider(_model_response())
    request = _model_request()
    gateway = _gateway(GatewayDecision.ALLOW_DRAFT)
    review_gate = _review_gate(
        status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
        allows_offline_mock_continuation=False,
        risk_level=RiskLevel.CLASS_B,
    )

    with pytest.raises(
        ModelInvocationDeniedError,
        match=(
            r"^model invocation denied: "
            r"review gate status is requires_human_review$"
        ),
    ):
        invoke_model_if_allowed(
            provider=provider,
            request=request,
            gateway=gateway,
            review_gate=review_gate,
        )

    assert provider.requests == ()


def test_invoke_model_if_allowed_checks_gateway_before_review_gate() -> None:
    provider = FakeModelProvider(_model_response())
    request = _model_request()
    gateway = _gateway(GatewayDecision.BLOCK)
    review_gate = _review_gate(
        status=ReviewGateStatus.REQUIRES_HUMAN_REVIEW,
        allows_offline_mock_continuation=False,
        risk_level=RiskLevel.CLASS_D,
    )

    with pytest.raises(
        ModelInvocationDeniedError,
        match=r"^model invocation denied: gateway decision is block$",
    ):
        invoke_model_if_allowed(
            provider=provider,
            request=request,
            gateway=gateway,
            review_gate=review_gate,
        )

    assert provider.requests == ()


def test_invoke_model_if_allowed_propagates_provider_errors() -> None:
    class FailingProvider:
        def __init__(self) -> None:
            self.requests: list[ModelRequest] = []

        def generate(self, request: ModelRequest) -> ModelResponse:
            self.requests.append(request)
            raise RuntimeError("provider failed")

    provider = FailingProvider()
    request = _model_request()
    gateway = _gateway(GatewayDecision.ALLOW_DRAFT)
    review_gate = _review_gate(
        status=ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION,
        allows_offline_mock_continuation=True,
        risk_level=RiskLevel.CLASS_A,
    )

    with pytest.raises(RuntimeError, match=r"^provider failed$"):
        invoke_model_if_allowed(
            provider=provider,
            request=request,
            gateway=gateway,
            review_gate=review_gate,
        )

    assert provider.requests == [request]


def _model_response() -> ModelResponse:
    return ModelResponse(
        content="Synthetic model response",
        provider_name="fake",
        model_name="fake-model",
    )


def _model_request() -> ModelRequest:
    return ModelRequest(
        system_prompt="Use only synthetic data.",
        user_prompt="Prepare a deterministic response.",
    )


def _gateway(decision: GatewayDecision) -> GatewayResult:
    return GatewayResult(
        decision=decision,
        checks=("synthetic_gateway_check",),
    )


def _review_gate(
    *,
    status: ReviewGateStatus,
    allows_offline_mock_continuation: bool,
    risk_level: RiskLevel,
) -> ReviewGateDecision:
    return ReviewGateDecision(
        status=status,
        allows_offline_mock_continuation=allows_offline_mock_continuation,
        risk_classification=RiskClassification(
            risk_level=risk_level,
            review_required=risk_level is not RiskLevel.CLASS_A,
            basis=("synthetic_internal_admin_fixture",),
        ),
        reason="Synthetic review-gate decision for model invocation tests.",
    )
