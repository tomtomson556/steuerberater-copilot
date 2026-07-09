from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.offline_mvp as offline_mvp
from steuerberater_copilot.offline_mvp.prompt_definition import (
    SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1,
    VersionedPromptDefinition,
)


def test_synthetic_structured_draft_prompt_identity() -> None:
    assert SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.prompt_id == (
        "synthetic_structured_draft"
    )
    assert SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.version == "1"


def test_versioned_prompt_definition_is_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.version = "2"


def test_versioned_prompt_definition_renders_user_prompt_deterministically() -> None:
    case_data = '{"case_id": "CASE_TEST"}'

    first = SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.render_user_prompt(
        case_data=case_data
    )
    second = SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.render_user_prompt(
        case_data=case_data
    )

    assert first == second


def test_versioned_prompt_definition_replaces_case_data_placeholder_once() -> None:
    case_data = '{"case_id": "CASE_TEST"}'

    result = SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.render_user_prompt(
        case_data=case_data
    )

    assert case_data in result
    assert "$case_data" not in result
    assert result.count(case_data) == 1


def test_versioned_prompt_definition_prompts_have_no_trailing_newline() -> None:
    user_prompt = SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.render_user_prompt(
        case_data='{"case_id": "CASE_TEST"}'
    )

    assert not SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.system_prompt.endswith("\n")
    assert not user_prompt.endswith("\n")


def test_versioned_prompt_definition_public_exports() -> None:
    assert offline_mvp.VersionedPromptDefinition is VersionedPromptDefinition
    assert (
        offline_mvp.SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1
        is SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1
    )
    assert "VersionedPromptDefinition" in offline_mvp.__all__
    assert "SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1" in offline_mvp.__all__
