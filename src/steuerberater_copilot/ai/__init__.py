"""Provider-independent model boundary exports."""

from .fake_model_provider import FakeModelProvider
from .invocation_policy import (
    ModelInvocationPolicy,
    ModelInvocationPolicyViolationError,
)
from .model_provider import ModelProvider, ModelRequest, ModelResponse

_OPENAI_PROVIDER_EXPORTS = frozenset(
    {
        "OpenAIProviderError",
        "OpenAIProviderTimeoutError",
        "OpenAIResponsesProvider",
    }
)

__all__ = [
    "FakeModelProvider",
    "ModelInvocationPolicy",
    "ModelInvocationPolicyViolationError",
    "ModelProvider",
    "ModelRequest",
    "ModelResponse",
    "OpenAIProviderError",
    "OpenAIProviderTimeoutError",
    "OpenAIResponsesProvider",
]


def __getattr__(name: str) -> object:
    if name not in _OPENAI_PROVIDER_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from .openai_responses_provider import (
        OpenAIProviderError,
        OpenAIProviderTimeoutError,
        OpenAIResponsesProvider,
    )

    exports = {
        "OpenAIProviderError": OpenAIProviderError,
        "OpenAIProviderTimeoutError": OpenAIProviderTimeoutError,
        "OpenAIResponsesProvider": OpenAIResponsesProvider,
    }
    globals().update(exports)
    return exports[name]
