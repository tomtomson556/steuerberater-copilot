"""Deterministic in-memory model provider for tests."""

from .model_provider import ModelRequest, ModelResponse


class FakeModelProvider:
    """Deterministic provider without model or network invocation."""

    def __init__(self, response: ModelResponse) -> None:
        self._response = response
        self._requests: list[ModelRequest] = []

    @property
    def requests(self) -> tuple[ModelRequest, ...]:
        """Return an immutable snapshot of recorded requests."""
        return tuple(self._requests)

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Record the request and return the configured response."""
        self._requests.append(request)
        return self._response
