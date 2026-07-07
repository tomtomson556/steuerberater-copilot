"""Controlled model invocation after existing offline MVP gates."""

from __future__ import annotations

from steuerberater_copilot.ai import ModelProvider, ModelRequest, ModelResponse

from .models import GatewayDecision, GatewayResult, ReviewGateDecision


class ModelInvocationDeniedError(RuntimeError):
    """Raised when control decisions do not permit model invocation."""


def invoke_model_if_allowed(
    *,
    provider: ModelProvider,
    request: ModelRequest,
    gateway: GatewayResult,
    review_gate: ReviewGateDecision,
) -> ModelResponse:
    """Invoke the provider only after gateway and review-gate approval."""
    if gateway.decision is not GatewayDecision.ALLOW_DRAFT:
        raise ModelInvocationDeniedError(
            "model invocation denied: "
            f"gateway decision is {gateway.decision.value}"
        )

    if not review_gate.allows_offline_mock_continuation:
        raise ModelInvocationDeniedError(
            "model invocation denied: "
            f"review gate status is {review_gate.status.value}"
        )

    return provider.generate(request)
