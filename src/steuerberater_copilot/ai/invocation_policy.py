"""Provider-independent policy for controlled model request and response sizes."""

from __future__ import annotations

from dataclasses import dataclass

from .model_provider import ModelRequest, ModelResponse


class ModelInvocationPolicyViolationError(RuntimeError):
    """Raised when a model request or response violates invocation policy."""


@dataclass(frozen=True, slots=True)
class ModelInvocationPolicy:
    """Immutable allowlist and character limits for one invocation boundary."""

    allowed_prompt_versions: frozenset[tuple[str, str]]
    max_request_chars: int
    max_response_chars: int

    def __post_init__(self) -> None:
        try:
            allowed_prompt_versions = frozenset(self.allowed_prompt_versions)
        except TypeError as exc:
            raise ValueError(
                "allowed_prompt_versions must contain hashable prompt pairs."
            ) from exc

        if not allowed_prompt_versions:
            raise ValueError("allowed_prompt_versions must not be empty.")

        for prompt_pair in allowed_prompt_versions:
            if not isinstance(prompt_pair, tuple) or len(prompt_pair) != 2:
                raise ValueError(
                    "Each allowed_prompt_versions entry must be a "
                    "(prompt_id, prompt_version) tuple."
                )
            prompt_id, prompt_version = prompt_pair
            self._validate_prompt_metadata(prompt_id, field_name="prompt_id")
            self._validate_prompt_metadata(
                prompt_version,
                field_name="prompt_version",
            )

        self._validate_positive_limit(
            self.max_request_chars,
            field_name="max_request_chars",
        )
        self._validate_positive_limit(
            self.max_response_chars,
            field_name="max_response_chars",
        )
        object.__setattr__(
            self,
            "allowed_prompt_versions",
            allowed_prompt_versions,
        )

    def validate_request(self, request: ModelRequest) -> None:
        """Reject unknown prompt metadata, blank prompts, or oversized requests."""
        prompt_pair = (request.prompt_id, request.prompt_version)
        if prompt_pair not in self.allowed_prompt_versions:
            raise ModelInvocationPolicyViolationError(
                "model invocation policy violation: prompt combination is not allowed "
                f"(prompt_id={request.prompt_id!r}, "
                f"prompt_version={request.prompt_version!r})."
            )

        if not request.system_prompt or request.system_prompt.isspace():
            raise ModelInvocationPolicyViolationError(
                "model invocation policy violation: system prompt must not be blank."
            )

        if not request.user_prompt or request.user_prompt.isspace():
            raise ModelInvocationPolicyViolationError(
                "model invocation policy violation: user prompt must not be blank."
            )

        observed_chars = len(request.system_prompt) + len(request.user_prompt)
        if observed_chars > self.max_request_chars:
            raise ModelInvocationPolicyViolationError(
                "model invocation policy violation: request character count exceeds "
                f"allowed limit (observed_chars={observed_chars}, "
                f"max_chars={self.max_request_chars})."
            )

    def validate_response(self, response: ModelResponse) -> None:
        """Reject a raw provider response that exceeds the character limit."""
        observed_chars = len(response.content)
        if observed_chars > self.max_response_chars:
            raise ModelInvocationPolicyViolationError(
                "model invocation policy violation: response character count exceeds "
                f"allowed limit (observed_chars={observed_chars}, "
                f"max_chars={self.max_response_chars})."
            )

    @staticmethod
    def _validate_prompt_metadata(value: object, *, field_name: str) -> None:
        if not isinstance(value, str) or not value or value.isspace():
            raise ValueError(f"{field_name} entries must be non-blank strings.")

    @staticmethod
    def _validate_positive_limit(value: object, *, field_name: str) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")
