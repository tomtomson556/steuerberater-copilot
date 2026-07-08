from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.offline_mvp as offline_mvp
from steuerberater_copilot.offline_mvp import StructuredDraftOutput


def test_structured_draft_output_keeps_ordered_field_values() -> None:
    output = _structured_output()

    assert output.summary_points == (
        "Synthetic invoice overview is available.",
        "Synthetic period is 2026-Q1.",
    )
    assert output.uncertainties == (
        "Source reference remains unclear.",
        "Period boundary requires review.",
    )
    assert output.review_questions == (
        "Which synthetic source should be referenced?",
        "Is the synthetic period boundary complete?",
    )


def test_structured_draft_output_uses_value_equality() -> None:
    assert _structured_output() == _structured_output()


def test_structured_draft_output_is_immutable() -> None:
    output = _structured_output()

    with pytest.raises(FrozenInstanceError):
        output.summary_points = ("Changed.",)


def test_structured_draft_output_accepts_empty_tuples_without_validation() -> None:
    output = StructuredDraftOutput(
        summary_points=(),
        uncertainties=(),
        review_questions=(),
    )

    assert output.summary_points == ()
    assert output.uncertainties == ()
    assert output.review_questions == ()


def test_structured_draft_output_does_not_convert_input_values() -> None:
    summary_points = ["Synthetic list remains a list."]
    uncertainties = "Synthetic string remains a string."
    review_questions = ("Synthetic question remains a tuple.",)

    output = StructuredDraftOutput(
        summary_points=summary_points,
        uncertainties=uncertainties,
        review_questions=review_questions,
    )

    assert output.summary_points is summary_points
    assert output.uncertainties is uncertainties
    assert output.review_questions is review_questions


def test_structured_draft_output_public_export() -> None:
    assert offline_mvp.StructuredDraftOutput is StructuredDraftOutput
    assert "StructuredDraftOutput" in offline_mvp.__all__


def _structured_output() -> StructuredDraftOutput:
    return StructuredDraftOutput(
        summary_points=(
            "Synthetic invoice overview is available.",
            "Synthetic period is 2026-Q1.",
        ),
        uncertainties=(
            "Source reference remains unclear.",
            "Period boundary requires review.",
        ),
        review_questions=(
            "Which synthetic source should be referenced?",
            "Is the synthetic period boundary complete?",
        ),
    )
