"""Controlled model invocation after existing offline MVP gates."""

from __future__ import annotations

from steuerberater_copilot.ai import (
    ModelInvocationPolicy,
    ModelProvider,
    ModelRequest,
    ModelResponse,
)

from .models import GatewayDecision, GatewayResult, ReviewGateDecision
from .prompt_definition import SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1

SYNTHETIC_MODEL_INVOCATION_POLICY = ModelInvocationPolicy(
    allowed_prompt_versions=frozenset(
        {
            (
                SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.prompt_id,
                SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.version,
            )
        }
    ),
    max_request_chars=16_000,
    max_response_chars=16_000,
)


class ModelInvocationDeniedError(RuntimeError):
    """Raised when control decisions do not permit model invocation."""


def invoke_model_if_allowed(
    *,
    provider: ModelProvider,
    request: ModelRequest,
    gateway: GatewayResult,
    review_gate: ReviewGateDecision,
    policy: ModelInvocationPolicy,
) -> ModelResponse:
    """Invoke the provider after controls and enforce request/response policy."""
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

    policy.validate_request(request)
    response = provider.generate(request)
    policy.validate_response(response)
    return response
