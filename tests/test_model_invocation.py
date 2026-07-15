import pytest

from steuerberater_copilot.ai import (
    FakeModelProvider,
    ModelInvocationPolicy,
    ModelInvocationPolicyViolationError,
    ModelRequest,
    ModelResponse,
)
from steuerberater_copilot.offline_mvp.model_invocation import (
    SYNTHETIC_MODEL_INVOCATION_POLICY,
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
from steuerberater_copilot.offline_mvp.prompt_definition import (
    SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1,
)


def test_synthetic_model_invocation_policy_uses_versioned_prompt_source() -> None:
    assert SYNTHETIC_MODEL_INVOCATION_POLICY.allowed_prompt_versions == frozenset(
        {
            (
                SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.prompt_id,
                SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.version,
            )
        }
    )
    assert SYNTHETIC_MODEL_INVOCATION_POLICY.max_request_chars == 16_000
    assert SYNTHETIC_MODEL_INVOCATION_POLICY.max_response_chars == 16_000


def test_policy_violation_error_is_distinct_from_control_denial() -> None:
    assert not issubclass(
        ModelInvocationPolicyViolationError,
        ModelInvocationDeniedError,
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
        policy=_policy(),
    )

    assert result is response
    assert provider.requests == (request,)
    assert provider.requests[0] is request
    assert provider.requests[0].prompt_id == "synthetic_invocation_prompt"
    assert provider.requests[0].prompt_version == "1"


@pytest.mark.parametrize(
    ("prompt_id", "prompt_version"),
    (
        ("other_synthetic_invocation_prompt", "1"),
        ("synthetic_invocation_prompt", "2"),
    ),
)
def test_invoke_model_if_allowed_rejects_unknown_prompt_metadata_before_provider(
    prompt_id: str,
    prompt_version: str,
) -> None:
    provider = FakeModelProvider(_model_response())
    request = _model_request(
        prompt_id=prompt_id,
        prompt_version=prompt_version,
    )

    with pytest.raises(ModelInvocationPolicyViolationError):
        invoke_model_if_allowed(
            provider=provider,
            request=request,
            gateway=_gateway(GatewayDecision.ALLOW_DRAFT),
            review_gate=_review_gate(
                status=ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION,
                allows_offline_mock_continuation=True,
                risk_level=RiskLevel.CLASS_A,
            ),
            policy=_policy(),
        )

    assert provider.requests == ()


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
            policy=_policy(
                allowed_prompt_versions={
                    ("different_synthetic_invocation_prompt", "2")
                }
            ),
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
            policy=_policy(
                allowed_prompt_versions={
                    ("different_synthetic_invocation_prompt", "2")
                }
            ),
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
            policy=_policy(
                allowed_prompt_versions={
                    ("different_synthetic_invocation_prompt", "2")
                }
            ),
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
            policy=_policy(),
        )

    assert provider.requests == [request]


def test_invoke_model_if_allowed_rejects_oversized_request_before_provider() -> None:
    provider = FakeModelProvider(_model_response())
    request = _model_request()

    with pytest.raises(ModelInvocationPolicyViolationError):
        invoke_model_if_allowed(
            provider=provider,
            request=request,
            gateway=_gateway(GatewayDecision.ALLOW_DRAFT),
            review_gate=_review_gate(
                status=ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION,
                allows_offline_mock_continuation=True,
                risk_level=RiskLevel.CLASS_A,
            ),
            policy=_policy(max_request_chars=1),
        )

    assert provider.requests == ()


def test_invoke_model_if_allowed_rejects_oversized_response_after_one_call() -> None:
    provider = FakeModelProvider(_model_response())
    request = _model_request()

    with pytest.raises(ModelInvocationPolicyViolationError):
        invoke_model_if_allowed(
            provider=provider,
            request=request,
            gateway=_gateway(GatewayDecision.ALLOW_DRAFT),
            review_gate=_review_gate(
                status=ReviewGateStatus.ALLOWED_OFFLINE_MOCK_CONTINUATION,
                allows_offline_mock_continuation=True,
                risk_level=RiskLevel.CLASS_A,
            ),
            policy=_policy(max_response_chars=1),
        )

    assert provider.requests == (request,)


def _model_response() -> ModelResponse:
    return ModelResponse(
        content="Synthetic model response",
        provider_name="fake",
        model_name="fake-model",
    )


def _model_request(
    *,
    prompt_id: str = "synthetic_invocation_prompt",
    prompt_version: str = "1",
) -> ModelRequest:
    return ModelRequest(
        prompt_id=prompt_id,
        prompt_version=prompt_version,
        system_prompt="Use only synthetic data.",
        user_prompt="Prepare a deterministic response.",
    )


def _policy(
    *,
    allowed_prompt_versions: set[tuple[str, str]] | None = None,
    max_request_chars: int = 1_000,
    max_response_chars: int = 1_000,
) -> ModelInvocationPolicy:
    return ModelInvocationPolicy(
        allowed_prompt_versions=(
            allowed_prompt_versions
            or {("synthetic_invocation_prompt", "1")}
        ),
        max_request_chars=max_request_chars,
        max_response_chars=max_response_chars,
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
