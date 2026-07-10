from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.ai as ai
from steuerberater_copilot.ai import FakeModelProvider, ModelProvider, ModelRequest, ModelResponse


def test_model_request_is_immutable_contract() -> None:
    request = ModelRequest(
        prompt_id="synthetic_test_prompt",
        prompt_version="1",
        system_prompt="Prepare a synthetic draft.",
        user_prompt="Summarize the provided synthetic case.",
    )

    assert request.prompt_id == "synthetic_test_prompt"
    assert request.prompt_version == "1"
    assert request.system_prompt == "Prepare a synthetic draft."
    assert request.user_prompt == "Summarize the provided synthetic case."
    assert request == ModelRequest(
        prompt_id="synthetic_test_prompt",
        prompt_version="1",
        system_prompt="Prepare a synthetic draft.",
        user_prompt="Summarize the provided synthetic case.",
    )
    with pytest.raises(FrozenInstanceError):
        request.system_prompt = "Changed."


def test_model_request_equality_includes_prompt_version() -> None:
    first = ModelRequest(
        prompt_id="synthetic_test_prompt",
        prompt_version="1",
        system_prompt="Prepare a synthetic draft.",
        user_prompt="Summarize the provided synthetic case.",
    )
    second = ModelRequest(
        prompt_id="synthetic_test_prompt",
        prompt_version="2",
        system_prompt="Prepare a synthetic draft.",
        user_prompt="Summarize the provided synthetic case.",
    )

    assert first != second


def test_model_request_equality_includes_prompt_id() -> None:
    first = ModelRequest(
        prompt_id="synthetic_test_prompt",
        prompt_version="1",
        system_prompt="Prepare a synthetic draft.",
        user_prompt="Summarize the provided synthetic case.",
    )
    second = ModelRequest(
        prompt_id="other_synthetic_test_prompt",
        prompt_version="1",
        system_prompt="Prepare a synthetic draft.",
        user_prompt="Summarize the provided synthetic case.",
    )

    assert first != second


def test_model_response_is_immutable_contract() -> None:
    response = ModelResponse(
        content="Synthetic response",
        provider_name="test-provider",
        model_name="test-model",
    )

    assert response.content == "Synthetic response"
    assert response.provider_name == "test-provider"
    assert response.model_name == "test-model"
    assert response == ModelResponse(
        content="Synthetic response",
        provider_name="test-provider",
        model_name="test-model",
    )
    with pytest.raises(FrozenInstanceError):
        response.content = "Changed."


def test_conforming_provider_generates_expected_response() -> None:
    class StubProvider:
        def __init__(self) -> None:
            self.requests: list[ModelRequest] = []

        def generate(self, request: ModelRequest) -> ModelResponse:
            self.requests.append(request)
            return ModelResponse(
                content="Synthetic response",
                provider_name="stub",
                model_name="stub-model",
            )

    provider = StubProvider()
    request = ModelRequest(
        prompt_id="synthetic_test_prompt",
        prompt_version="1",
        system_prompt="Prepare a synthetic draft.",
        user_prompt="Summarize the provided synthetic case.",
    )

    response = provider.generate(request)

    assert isinstance(provider, ModelProvider)
    assert provider.requests == [request]
    assert response == ModelResponse(
        content="Synthetic response",
        provider_name="stub",
        model_name="stub-model",
    )


def test_object_without_generate_is_not_a_model_provider() -> None:
    class ObjectWithoutGenerate:
        pass

    assert not isinstance(ObjectWithoutGenerate(), ModelProvider)


def test_public_ai_package_exports_model_boundary() -> None:
    assert ai.FakeModelProvider is FakeModelProvider
    assert ai.ModelProvider is ModelProvider
    assert ai.ModelRequest is ModelRequest
    assert ai.ModelResponse is ModelResponse
    assert ai.__all__ == [
        "FakeModelProvider",
        "ModelProvider",
        "ModelRequest",
        "ModelResponse",
    ]
