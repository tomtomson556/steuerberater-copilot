from steuerberater_copilot.ai import (
    FakeModelProvider,
    ModelProvider,
    ModelRequest,
    ModelResponse,
)


def test_fake_model_provider_initial_state_and_protocol() -> None:
    response = ModelResponse(
        content="Synthetic model response",
        provider_name="fake",
        model_name="fake-model",
    )

    provider = FakeModelProvider(response)

    assert isinstance(provider, ModelProvider)
    assert provider.requests == ()


def test_fake_model_provider_returns_configured_response_and_records_exact_request() -> None:
    response = ModelResponse(
        content="Synthetic model response",
        provider_name="fake",
        model_name="fake-model",
    )
    provider = FakeModelProvider(response)
    request = ModelRequest(
        system_prompt="Use only synthetic data.",
        user_prompt="Prepare a deterministic response.",
    )

    result = provider.generate(request)

    assert result is response
    assert provider.requests == (request,)
    assert provider.requests[0] is request


def test_fake_model_provider_repeated_calls_remain_deterministic() -> None:
    response = ModelResponse(
        content="Synthetic model response",
        provider_name="fake",
        model_name="fake-model",
    )
    provider = FakeModelProvider(response)
    first_request = ModelRequest(
        system_prompt="Use only synthetic data.",
        user_prompt="Prepare the first deterministic response.",
    )
    second_request = ModelRequest(
        system_prompt="Use only synthetic data.",
        user_prompt="Prepare the second deterministic response.",
    )

    first_result = provider.generate(first_request)
    second_result = provider.generate(second_request)

    assert first_result is response
    assert second_result is response
    assert provider.requests == (first_request, second_request)


def test_fake_model_provider_requests_property_returns_snapshot() -> None:
    response = ModelResponse(
        content="Synthetic model response",
        provider_name="fake",
        model_name="fake-model",
    )
    provider = FakeModelProvider(response)
    first_request = ModelRequest(
        system_prompt="Use only synthetic data.",
        user_prompt="Prepare the first deterministic response.",
    )
    second_request = ModelRequest(
        system_prompt="Use only synthetic data.",
        user_prompt="Prepare the second deterministic response.",
    )

    provider.generate(first_request)
    snapshot = provider.requests
    provider.generate(second_request)

    assert snapshot == (first_request,)
    assert provider.requests == (first_request, second_request)
