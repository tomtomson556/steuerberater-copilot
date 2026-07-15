"""Controlled synchronous OpenAI Responses API adapter."""

from __future__ import annotations

import math
from numbers import Real

from openai import APIError, APITimeoutError, OpenAI

from .model_provider import ModelRequest, ModelResponse

_SAFE_RESPONSE_STATUSES = frozenset(
    {"completed", "failed", "in_progress", "cancelled", "queued", "incomplete"}
)
_SAFE_INCOMPLETE_REASONS = frozenset({"max_output_tokens", "content_filter"})


class OpenAIProviderError(RuntimeError):
    """Safe application-level failure of the OpenAI provider adapter."""


class OpenAIProviderTimeoutError(OpenAIProviderError):
    """Raised when the configured OpenAI request timeout is exceeded."""


class OpenAIResponsesProvider:
    """Synchronous provider adapter for one explicitly configured OpenAI model."""

    __slots__ = ("_client", "_model", "_max_output_tokens")

    def __init__(
        self,
        *,
        client: OpenAI,
        model: str,
        max_output_tokens: int,
    ) -> None:
        self._client = client
        self._model = _validate_non_blank_string(model, field_name="model")
        self._max_output_tokens = _validate_positive_integer(
            max_output_tokens,
            field_name="max_output_tokens",
        )

    @classmethod
    def from_api_key(
        cls,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float = 60.0,
        max_output_tokens: int = 2_000,
    ) -> OpenAIResponsesProvider:
        """Create a provider with an explicit timeout and disabled SDK retries."""
        validated_api_key = _validate_non_blank_string(
            api_key,
            field_name="api_key",
        )
        validated_timeout = _validate_positive_finite_real(
            timeout_seconds,
            field_name="timeout_seconds",
        )
        validated_model = _validate_non_blank_string(model, field_name="model")
        validated_max_output_tokens = _validate_positive_integer(
            max_output_tokens,
            field_name="max_output_tokens",
        )
        client = OpenAI(
            api_key=validated_api_key,
            timeout=validated_timeout,
            max_retries=0,
        )
        return cls(
            client=client,
            model=validated_model,
            max_output_tokens=validated_max_output_tokens,
        )

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Make one Responses API call and return its unchanged raw JSON text."""
        try:
            response = self._client.responses.create(
                model=self._model,
                instructions=request.system_prompt,
                input=request.user_prompt,
                max_output_tokens=self._max_output_tokens,
                store=False,
                text={"format": {"type": "json_object"}},
            )
        except APITimeoutError as exc:
            raise OpenAIProviderTimeoutError("OpenAI request timed out.") from exc
        except APIError as exc:
            raise OpenAIProviderError("OpenAI API request failed.") from exc

        _ensure_response_completed(response)
        output_text = getattr(response, "output_text", None)
        if not isinstance(output_text, str) or not output_text or output_text.isspace():
            raise OpenAIProviderError("OpenAI response did not contain usable output text.")

        response_model = getattr(response, "model", None)
        model_name = (
            response_model
            if isinstance(response_model, str)
            and response_model
            and not response_model.isspace()
            else self._model
        )
        return ModelResponse(
            content=output_text,
            provider_name="openai",
            model_name=model_name,
        )


def _ensure_response_completed(response: object) -> None:
    status = getattr(response, "status", None)
    if status == "completed":
        return

    safe_status = (
        status
        if isinstance(status, str) and status in _SAFE_RESPONSE_STATUSES
        else "unknown"
    )
    message = f"OpenAI response was not completed: status={safe_status}"
    if safe_status == "incomplete":
        incomplete_details = getattr(response, "incomplete_details", None)
        reason = getattr(incomplete_details, "reason", None)
        if reason in _SAFE_INCOMPLETE_REASONS:
            message = f"{message}, reason={reason}"
    raise OpenAIProviderError(message)


def _validate_non_blank_string(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not value or value.isspace():
        raise ValueError(f"{field_name} must be a non-blank string.")
    return value


def _validate_positive_integer(value: object, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer.")
    return value


def _validate_positive_finite_real(value: object, *, field_name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, Real)
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError(f"{field_name} must be a positive finite real number.")
    return float(value)
