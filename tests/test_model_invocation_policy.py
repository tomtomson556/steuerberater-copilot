from dataclasses import FrozenInstanceError

import pytest

from steuerberater_copilot.ai import (
    ModelInvocationPolicy,
    ModelInvocationPolicyViolationError,
    ModelRequest,
    ModelResponse,
)


def test_model_invocation_policy_is_immutable_and_uses_slots() -> None:
    policy = _policy()

    with pytest.raises(FrozenInstanceError):
        policy.max_request_chars = 20

    assert not hasattr(policy, "__dict__")
    assert ModelInvocationPolicy.__slots__ == (
        "allowed_prompt_versions",
        "max_request_chars",
        "max_response_chars",
    )


def test_model_invocation_policy_defensively_freezes_mutable_allowlist() -> None:
    allowed_prompt_versions = {("synthetic_prompt", "1")}

    policy = ModelInvocationPolicy(
        allowed_prompt_versions=allowed_prompt_versions,
        max_request_chars=100,
        max_response_chars=100,
    )
    allowed_prompt_versions.add(("other_prompt", "2"))

    assert isinstance(policy.allowed_prompt_versions, frozenset)
    assert policy.allowed_prompt_versions == frozenset({("synthetic_prompt", "1")})


def test_model_invocation_policy_rejects_empty_allowlist() -> None:
    with pytest.raises(
        ValueError,
        match=r"^allowed_prompt_versions must not be empty\.$",
    ):
        ModelInvocationPolicy(
            allowed_prompt_versions=frozenset(),
            max_request_chars=100,
            max_response_chars=100,
        )


@pytest.mark.parametrize(
    "allowed_prompt_versions",
    (
        {("", "1")},
        {(" \t\n", "1")},
        {("synthetic_prompt", "")},
        {("synthetic_prompt", " \t\n")},
        {(1, "1")},
        {("synthetic_prompt", 1)},
    ),
)
def test_model_invocation_policy_rejects_invalid_prompt_metadata(
    allowed_prompt_versions: set[tuple[object, object]],
) -> None:
    with pytest.raises(ValueError, match=r"must be non-blank strings\.$"):
        ModelInvocationPolicy(
            allowed_prompt_versions=allowed_prompt_versions,
            max_request_chars=100,
            max_response_chars=100,
        )


@pytest.mark.parametrize(
    "allowed_prompt_versions",
    (
        {("synthetic_prompt",)},
        {("synthetic_prompt", "1", "extra")},
        {"synthetic_prompt"},
    ),
)
def test_model_invocation_policy_rejects_non_pair_allowlist_entries(
    allowed_prompt_versions: set[object],
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"^Each allowed_prompt_versions entry must be a "
            r"\(prompt_id, prompt_version\) tuple\.$"
        ),
    ):
        ModelInvocationPolicy(
            allowed_prompt_versions=allowed_prompt_versions,
            max_request_chars=100,
            max_response_chars=100,
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("max_request_chars", 0),
        ("max_request_chars", -1),
        ("max_request_chars", True),
        ("max_request_chars", 1.5),
        ("max_response_chars", 0),
        ("max_response_chars", -1),
        ("max_response_chars", False),
        ("max_response_chars", "100"),
    ),
)
def test_model_invocation_policy_rejects_invalid_character_limits(
    field_name: str,
    value: object,
) -> None:
    arguments = {
        "allowed_prompt_versions": frozenset({("synthetic_prompt", "1")}),
        "max_request_chars": 100,
        "max_response_chars": 100,
    }
    arguments[field_name] = value

    with pytest.raises(
        ValueError,
        match=rf"^{field_name} must be a positive integer\.$",
    ):
        ModelInvocationPolicy(**arguments)


@pytest.mark.parametrize(
    ("prompt_id", "prompt_version"),
    (
        ("synthetic_prompt", "1"),
        ("other_prompt", "2"),
    ),
)
def test_request_policy_accepts_exact_allowed_prompt_pairs(
    prompt_id: str,
    prompt_version: str,
) -> None:
    policy = _policy(
        allowed_prompt_versions={
            ("synthetic_prompt", "1"),
            ("other_prompt", "2"),
        }
    )

    policy.validate_request(
        _request(prompt_id=prompt_id, prompt_version=prompt_version)
    )


@pytest.mark.parametrize(
    ("prompt_id", "prompt_version"),
    (
        ("unknown_prompt", "1"),
        ("synthetic_prompt", "unknown_version"),
        ("synthetic_prompt", "2"),
    ),
)
def test_request_policy_rejects_unknown_and_crossed_prompt_pairs(
    prompt_id: str,
    prompt_version: str,
) -> None:
    policy = _policy(
        allowed_prompt_versions={
            ("synthetic_prompt", "1"),
            ("other_prompt", "2"),
        }
    )

    with pytest.raises(
        ModelInvocationPolicyViolationError,
        match=r"^model invocation policy violation: prompt combination is not allowed",
    ):
        policy.validate_request(
            _request(prompt_id=prompt_id, prompt_version=prompt_version)
        )


@pytest.mark.parametrize(
    ("field_name", "prompt"),
    (
        ("system_prompt", ""),
        ("system_prompt", " \t\n"),
        ("user_prompt", ""),
        ("user_prompt", " \t\n"),
    ),
)
def test_request_policy_rejects_blank_prompts(
    field_name: str,
    prompt: str,
) -> None:
    arguments = {
        "prompt_id": "synthetic_prompt",
        "prompt_version": "1",
        "system_prompt": "system",
        "user_prompt": "user",
    }
    arguments[field_name] = prompt

    with pytest.raises(
        ModelInvocationPolicyViolationError,
        match=(
            rf"^model invocation policy violation: "
            rf"{field_name.removesuffix('_prompt')} prompt must not be blank\.$"
        ),
    ):
        _policy().validate_request(ModelRequest(**arguments))


def test_request_policy_accepts_request_exactly_at_character_limit() -> None:
    _policy(max_request_chars=10).validate_request(
        _request(system_prompt="1234", user_prompt="123456")
    )


def test_request_policy_rejects_request_one_character_over_limit() -> None:
    with pytest.raises(
        ModelInvocationPolicyViolationError,
        match=r"observed_chars=11, max_chars=10",
    ):
        _policy(max_request_chars=10).validate_request(
            _request(system_prompt="1234", user_prompt="1234567")
        )


def test_response_policy_accepts_response_exactly_at_character_limit() -> None:
    _policy(max_response_chars=10).validate_response(_response("1234567890"))


def test_response_policy_rejects_response_one_character_over_limit() -> None:
    with pytest.raises(
        ModelInvocationPolicyViolationError,
        match=r"observed_chars=11, max_chars=10",
    ):
        _policy(max_response_chars=10).validate_response(_response("12345678901"))


def test_response_policy_leaves_empty_response_to_later_boundaries() -> None:
    _policy().validate_response(_response(""))


def test_request_policy_error_does_not_disclose_prompt_content() -> None:
    request = _request(
        system_prompt="SENSITIVE_SYNTHETIC_SYSTEM_CONTENT",
        user_prompt="SENSITIVE_SYNTHETIC_USER_CONTENT",
    )

    with pytest.raises(ModelInvocationPolicyViolationError) as exc_info:
        _policy(max_request_chars=1).validate_request(request)

    message = str(exc_info.value)
    assert "SENSITIVE_SYNTHETIC_SYSTEM_CONTENT" not in message
    assert "SENSITIVE_SYNTHETIC_USER_CONTENT" not in message
    assert "observed_chars=" in message
    assert "max_chars=1" in message


def test_response_policy_error_does_not_disclose_response_content() -> None:
    response = _response("SENSITIVE_SYNTHETIC_RESPONSE_CONTENT")

    with pytest.raises(ModelInvocationPolicyViolationError) as exc_info:
        _policy(max_response_chars=1).validate_response(response)

    message = str(exc_info.value)
    assert "SENSITIVE_SYNTHETIC_RESPONSE_CONTENT" not in message
    assert "observed_chars=" in message
    assert "max_chars=1" in message


def _policy(
    *,
    allowed_prompt_versions: set[tuple[str, str]] | None = None,
    max_request_chars: int = 100,
    max_response_chars: int = 100,
) -> ModelInvocationPolicy:
    return ModelInvocationPolicy(
        allowed_prompt_versions=(
            allowed_prompt_versions or {("synthetic_prompt", "1")}
        ),
        max_request_chars=max_request_chars,
        max_response_chars=max_response_chars,
    )


def _request(
    *,
    prompt_id: str = "synthetic_prompt",
    prompt_version: str = "1",
    system_prompt: str = "system",
    user_prompt: str = "user",
) -> ModelRequest:
    return ModelRequest(
        prompt_id=prompt_id,
        prompt_version=prompt_version,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )


def _response(content: str) -> ModelResponse:
    return ModelResponse(
        content=content,
        provider_name="synthetic-policy-test",
        model_name="synthetic-policy-model",
    )
