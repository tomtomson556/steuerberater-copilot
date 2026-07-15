from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from openai import APIError, APITimeoutError

from steuerberater_copilot.ai import (
    ModelRequest,
    OpenAIProviderError,
    OpenAIProviderTimeoutError,
    OpenAIResponsesProvider,
)

MODEL_NAME = "gpt-synthetic-test"
API_KEY = "SYNTHETIC_OPENAI_KEY_DO_NOT_USE"
RAW_JSON = (
    "{"
    '"summary_points":["Synthetic summary."],'
    '"uncertainties":["Synthetic uncertainty."],'
    '"review_questions":["Synthetic review question?"]'
    "}"
)


def test_public_provider_error_hierarchy_is_small_and_distinct() -> None:
    assert issubclass(OpenAIProviderTimeoutError, OpenAIProviderError)
    assert not issubclass(OpenAIProviderError, OpenAIProviderTimeoutError)


@pytest.mark.parametrize("model", ("", " \t\n", None, 123))
def test_provider_rejects_invalid_model(model: object) -> None:
    with pytest.raises(ValueError, match=r"^model must be a non-blank string\.$"):
        OpenAIResponsesProvider(
            client=Mock(),
            model=model,
            max_output_tokens=2_000,
        )


@pytest.mark.parametrize("max_output_tokens", (0, -1, True, False, 1.5, "2000"))
def test_provider_rejects_invalid_max_output_tokens(
    max_output_tokens: object,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"^max_output_tokens must be a positive integer\.$",
    ):
        OpenAIResponsesProvider(
            client=Mock(),
            model=MODEL_NAME,
            max_output_tokens=max_output_tokens,
        )


@pytest.mark.parametrize("api_key", ("", " \t\n", None, 123))
def test_factory_rejects_invalid_api_key_before_client_construction(
    api_key: object,
) -> None:
    with patch(
        "steuerberater_copilot.ai.openai_responses_provider.OpenAI"
    ) as openai_constructor:
        with pytest.raises(
            ValueError,
            match=r"^api_key must be a non-blank string\.$",
        ):
            OpenAIResponsesProvider.from_api_key(
                api_key=api_key,
                model=MODEL_NAME,
            )

    openai_constructor.assert_not_called()


@pytest.mark.parametrize(
    "timeout_seconds",
    (0, -1, True, False, float("nan"), float("inf"), float("-inf"), "60", None),
)
def test_factory_rejects_invalid_timeout_before_client_construction(
    timeout_seconds: object,
) -> None:
    with patch(
        "steuerberater_copilot.ai.openai_responses_provider.OpenAI"
    ) as openai_constructor:
        with pytest.raises(
            ValueError,
            match=r"^timeout_seconds must be a positive finite real number\.$",
        ):
            OpenAIResponsesProvider.from_api_key(
                api_key=API_KEY,
                model=MODEL_NAME,
                timeout_seconds=timeout_seconds,
            )

    openai_constructor.assert_not_called()


def test_factory_builds_one_sync_client_with_controlled_defaults() -> None:
    client, response = _client_with_response()

    with patch(
        "steuerberater_copilot.ai.openai_responses_provider.OpenAI",
        return_value=client,
    ) as openai_constructor:
        provider = OpenAIResponsesProvider.from_api_key(
            api_key=API_KEY,
            model=MODEL_NAME,
        )
        result = provider.generate(_request())

    openai_constructor.assert_called_once_with(
        api_key=API_KEY,
        timeout=60.0,
        max_retries=0,
    )
    client.responses.create.assert_called_once()
    assert result.content is response.output_text
    assert not hasattr(provider, "api_key")
    assert API_KEY not in repr(provider)
    assert API_KEY not in str(provider)


def test_factory_forwards_explicit_timeout_and_output_limit() -> None:
    client, _ = _client_with_response()

    with patch(
        "steuerberater_copilot.ai.openai_responses_provider.OpenAI",
        return_value=client,
    ) as openai_constructor:
        provider = OpenAIResponsesProvider.from_api_key(
            api_key=API_KEY,
            model=MODEL_NAME,
            timeout_seconds=12,
            max_output_tokens=321,
        )
        provider.generate(_request())

    openai_constructor.assert_called_once_with(
        api_key=API_KEY,
        timeout=12.0,
        max_retries=0,
    )
    assert client.responses.create.call_args.kwargs["max_output_tokens"] == 321


def test_generate_maps_exact_request_to_one_responses_api_call() -> None:
    client, _ = _client_with_response()
    provider = OpenAIResponsesProvider(
        client=client,
        model=MODEL_NAME,
        max_output_tokens=456,
    )
    request = _request()

    provider.generate(request)

    client.responses.create.assert_called_once_with(
        model=MODEL_NAME,
        instructions=request.system_prompt,
        input=request.user_prompt,
        max_output_tokens=456,
        store=False,
        text={"format": {"type": "json_object"}},
    )


def test_generate_preserves_raw_output_text_and_sdk_model_name() -> None:
    raw_output = f"\n{RAW_JSON}\n"
    client, _ = _client_with_response(
        output_text=raw_output,
        model="gpt-sdk-response-model",
    )
    provider = OpenAIResponsesProvider(
        client=client,
        model=MODEL_NAME,
        max_output_tokens=2_000,
    )

    result = provider.generate(_request())

    assert result.content is raw_output
    assert result.provider_name == "openai"
    assert result.model_name == "gpt-sdk-response-model"


@pytest.mark.parametrize("response_model", (None, "", " \t\n", 123))
def test_generate_falls_back_to_configured_model_for_unusable_response_model(
    response_model: object,
) -> None:
    client, _ = _client_with_response(model=response_model)
    provider = OpenAIResponsesProvider(
        client=client,
        model=MODEL_NAME,
        max_output_tokens=2_000,
    )

    result = provider.generate(_request())

    assert result.model_name == MODEL_NAME


def test_generate_falls_back_when_response_model_is_missing() -> None:
    client, response = _client_with_response()
    del response.model
    provider = OpenAIResponsesProvider(
        client=client,
        model=MODEL_NAME,
        max_output_tokens=2_000,
    )

    result = provider.generate(_request())

    assert result.model_name == MODEL_NAME


@pytest.mark.parametrize("status", ("failed", "cancelled", "queued", None, "other"))
def test_generate_rejects_non_completed_response_status(status: object) -> None:
    client, _ = _client_with_response(
        status=status,
        output_text="SENSITIVE_SYNTHETIC_RESPONSE_CONTENT",
    )
    provider = OpenAIResponsesProvider(
        client=client,
        model=MODEL_NAME,
        max_output_tokens=2_000,
    )

    with pytest.raises(OpenAIProviderError) as exc_info:
        provider.generate(_request())

    message = str(exc_info.value)
    expected_status = status if status in {"failed", "cancelled", "queued"} else "unknown"
    assert message == f"OpenAI response was not completed: status={expected_status}"
    assert "SENSITIVE_SYNTHETIC_RESPONSE_CONTENT" not in message


@pytest.mark.parametrize("reason", ("max_output_tokens", "content_filter"))
def test_generate_reports_only_known_safe_incomplete_reason(reason: str) -> None:
    client, _ = _client_with_response(status="incomplete", incomplete_reason=reason)
    provider = OpenAIResponsesProvider(
        client=client,
        model=MODEL_NAME,
        max_output_tokens=2_000,
    )

    with pytest.raises(
        OpenAIProviderError,
        match=(
            rf"^OpenAI response was not completed: status=incomplete, "
            rf"reason={reason}$"
        ),
    ):
        provider.generate(_request())


def test_generate_does_not_report_unknown_incomplete_reason() -> None:
    client, response = _client_with_response(status="incomplete")
    response.incomplete_details = SimpleNamespace(
        reason="SENSITIVE_SYNTHETIC_RESPONSE_REASON"
    )
    provider = OpenAIResponsesProvider(
        client=client,
        model=MODEL_NAME,
        max_output_tokens=2_000,
    )

    with pytest.raises(OpenAIProviderError) as exc_info:
        provider.generate(_request())

    assert str(exc_info.value) == (
        "OpenAI response was not completed: status=incomplete"
    )
    assert "SENSITIVE_SYNTHETIC_RESPONSE_REASON" not in str(exc_info.value)


@pytest.mark.parametrize("output_text", ("", " \t\n", None, 123))
def test_generate_rejects_unusable_output_text_without_disclosing_it(
    output_text: object,
) -> None:
    client, _ = _client_with_response(output_text=output_text)
    provider = OpenAIResponsesProvider(
        client=client,
        model=MODEL_NAME,
        max_output_tokens=2_000,
    )

    with pytest.raises(
        OpenAIProviderError,
        match=r"^OpenAI response did not contain usable output text\.$",
    ):
        provider.generate(_request())


def test_generate_rejects_missing_output_text() -> None:
    client, response = _client_with_response()
    del response.output_text
    provider = OpenAIResponsesProvider(
        client=client,
        model=MODEL_NAME,
        max_output_tokens=2_000,
    )

    with pytest.raises(
        OpenAIProviderError,
        match=r"^OpenAI response did not contain usable output text\.$",
    ):
        provider.generate(_request())


def test_generate_translates_timeout_with_safe_message_and_exception_chain() -> None:
    client = Mock()
    timeout_error = APITimeoutError(Mock())
    client.responses.create.side_effect = timeout_error
    request = _request()

    with patch(
        "steuerberater_copilot.ai.openai_responses_provider.OpenAI",
        return_value=client,
    ):
        provider = OpenAIResponsesProvider.from_api_key(
            api_key=API_KEY,
            model=MODEL_NAME,
        )
        with pytest.raises(OpenAIProviderTimeoutError) as exc_info:
            provider.generate(request)

    assert str(exc_info.value) == "OpenAI request timed out."
    assert exc_info.value.__cause__ is timeout_error
    assert request.system_prompt not in str(exc_info.value)
    assert request.user_prompt not in str(exc_info.value)
    assert API_KEY not in str(exc_info.value)


def test_generate_translates_api_error_with_safe_message_and_exception_chain() -> None:
    client = Mock()
    api_error = APIError("SENSITIVE_SDK_ERROR", Mock(), body=None)
    client.responses.create.side_effect = api_error
    request = _request()

    with patch(
        "steuerberater_copilot.ai.openai_responses_provider.OpenAI",
        return_value=client,
    ):
        provider = OpenAIResponsesProvider.from_api_key(
            api_key=API_KEY,
            model=MODEL_NAME,
        )
        with pytest.raises(OpenAIProviderError) as exc_info:
            provider.generate(request)

    assert type(exc_info.value) is OpenAIProviderError
    assert str(exc_info.value) == "OpenAI API request failed."
    assert exc_info.value.__cause__ is api_error
    assert "SENSITIVE_SDK_ERROR" not in str(exc_info.value)
    assert request.system_prompt not in str(exc_info.value)
    assert request.user_prompt not in str(exc_info.value)
    assert API_KEY not in str(exc_info.value)


def test_generate_does_not_reclassify_unexpected_programming_error() -> None:
    client = Mock()
    unexpected_error = TypeError("synthetic unexpected programming error")
    client.responses.create.side_effect = unexpected_error
    provider = OpenAIResponsesProvider(
        client=client,
        model=MODEL_NAME,
        max_output_tokens=2_000,
    )

    with pytest.raises(TypeError) as exc_info:
        provider.generate(_request())

    assert exc_info.value is unexpected_error


def _request() -> ModelRequest:
    return ModelRequest(
        prompt_id="synthetic_openai_provider_test",
        prompt_version="1",
        system_prompt="SENSITIVE_SYNTHETIC_SYSTEM_PROMPT",
        user_prompt="SENSITIVE_SYNTHETIC_USER_PROMPT",
    )


def _client_with_response(
    *,
    status: object = "completed",
    output_text: object = RAW_JSON,
    model: object = MODEL_NAME,
    incomplete_reason: str | None = None,
) -> tuple[Mock, SimpleNamespace]:
    incomplete_details = (
        SimpleNamespace(reason=incomplete_reason)
        if incomplete_reason is not None
        else None
    )
    response = SimpleNamespace(
        status=status,
        output_text=output_text,
        model=model,
        incomplete_details=incomplete_details,
    )
    client = Mock()
    client.responses.create.return_value = response
    return client, response
