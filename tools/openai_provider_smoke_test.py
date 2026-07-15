"""Explicit opt-in live smoke test for the controlled OpenAI provider adapter."""

from __future__ import annotations

import os
import sys

from steuerberater_copilot.ai import OpenAIResponsesProvider
from steuerberater_copilot.offline_mvp import (
    build_synthetic_ai_workflow,
    build_synthetic_model_request,
    load_fixture_cases,
)

_LIVE_OPT_IN_VARIABLE = "RUN_OPENAI_LIVE_SMOKE"
_API_KEY_VARIABLE = "OPENAI_API_KEY"
_MODEL_VARIABLE = "OPENAI_MODEL"
_TIMEOUT_VARIABLE = "OPENAI_TIMEOUT_SECONDS"
_MAX_OUTPUT_TOKENS_VARIABLE = "OPENAI_MAX_OUTPUT_TOKENS"
_SMOKE_CASE_ID = "CASE_002"


def main() -> int:
    """Run one controlled live request only after explicit environment opt-in."""
    if os.environ.get(_LIVE_OPT_IN_VARIABLE) != "1":
        print("status=disabled", file=sys.stderr)
        return 2

    if any(
        not os.environ.get(variable) or os.environ[variable].isspace()
        for variable in (_API_KEY_VARIABLE, _MODEL_VARIABLE)
    ):
        print("status=missing_configuration", file=sys.stderr)
        return 2

    try:
        timeout_seconds = _read_float(_TIMEOUT_VARIABLE, default=60.0)
        max_output_tokens = _read_integer(
            _MAX_OUTPUT_TOKENS_VARIABLE,
            default=2_000,
        )
        provider = OpenAIResponsesProvider.from_api_key(
            api_key=os.environ[_API_KEY_VARIABLE],
            model=os.environ[_MODEL_VARIABLE],
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens,
        )
    except ValueError:
        print("status=invalid_configuration", file=sys.stderr)
        return 2

    cases_by_id = {case.case_id: case for case in load_fixture_cases()}
    case = cases_by_id[_SMOKE_CASE_ID]
    request = build_synthetic_model_request(case)

    try:
        result = build_synthetic_ai_workflow(case, provider=provider)
    except Exception:
        print("status=failed", file=sys.stderr)
        return 1

    if result.model_response is None or result.structured_draft is None:
        print("status=failed", file=sys.stderr)
        return 1

    print("status=completed")
    print(f"provider_name={result.model_response.provider_name}")
    print(f"model_name={result.model_response.model_name}")
    print(f"prompt_id={request.prompt_id}")
    print(f"prompt_version={request.prompt_version}")
    print(f"summary_points={len(result.structured_draft.summary_points)}")
    print(f"uncertainties={len(result.structured_draft.uncertainties)}")
    print(f"review_questions={len(result.structured_draft.review_questions)}")
    return 0


def _read_float(variable: str, *, default: float) -> float:
    raw_value = os.environ.get(variable)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError:
        raise ValueError(f"{variable} must contain a number.") from None


def _read_integer(variable: str, *, default: int) -> int:
    raw_value = os.environ.get(variable)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        raise ValueError(f"{variable} must contain an integer.") from None


if __name__ == "__main__":
    raise SystemExit(main())
