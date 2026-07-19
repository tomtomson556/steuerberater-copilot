import pytest

import steuerberater_copilot.offline_mvp as offline_mvp
from steuerberater_copilot.offline_mvp import (
    StructuredDraftOutputValidationError,
    validate_structured_draft_output,
)
from steuerberater_copilot.offline_mvp.structured_output import StructuredDraftOutput


def test_validate_structured_draft_output_accepts_clean_draft() -> None:
    validate_structured_draft_output(
        StructuredDraftOutput(
            summary_points=(
                " leading space",
                "trailing space ",
                "text\nwith newline",
            ),
            uncertainties=("Synthetic uncertainty.",),
            review_questions=("Synthetic review question?",),
        )
    )


def test_validate_structured_draft_output_accepts_empty_tuples() -> None:
    validate_structured_draft_output(
        StructuredDraftOutput(
            summary_points=(),
            uncertainties=(),
            review_questions=(),
        )
    )


@pytest.mark.parametrize("blank_entry", ("", " ", "\t\n"))
def test_validate_structured_draft_output_rejects_blank_entries(
    blank_entry: str,
) -> None:
    output = _structured_output(summary_points=(blank_entry,))

    with pytest.raises(StructuredDraftOutputValidationError) as exc_info:
        validate_structured_draft_output(output)

    error = exc_info.value
    assert error.rule == "blank_entry"
    assert error.field_name == "summary_points"
    assert error.item_index == 0
    assert "blank_entry" in str(error)
    assert "summary_points" in str(error)
    assert "index=0" in str(error)


def test_validate_structured_draft_output_rejects_exact_duplicate_in_same_field() -> None:
    output = _structured_output(
        uncertainties=(
            "Same synthetic uncertainty.",
            "Same synthetic uncertainty.",
        )
    )

    with pytest.raises(
        StructuredDraftOutputValidationError,
        match="duplicate_entry",
    ) as exc_info:
        validate_structured_draft_output(output)

    error = exc_info.value
    assert error.rule == "duplicate_entry"
    assert error.field_name == "uncertainties"
    assert error.item_index == 1


def test_validate_structured_draft_output_allows_same_string_in_different_fields() -> None:
    validate_structured_draft_output(
        StructuredDraftOutput(
            summary_points=("Same string.",),
            uncertainties=("Same string.",),
            review_questions=("Same string.",),
        )
    )


def test_validate_structured_draft_output_uses_unchanged_string_equality() -> None:
    validate_structured_draft_output(
        _structured_output(
            summary_points=(
                "Synthetic Fact.",
                "synthetic fact.",
                "Synthetic Fact. ",
                " Synthetic Fact.",
            )
        )
    )


@pytest.mark.parametrize(
    "entry",
    (
        "Der Entwurf ist fachlich gepr\u00fcft.",
        "Der Entwurf wurde steuerlich gepr\u00fcft.",
        "The draft has been professionally reviewed.",
        "The result is tax reviewed.",
    ),
)
def test_validate_structured_draft_output_rejects_professional_review_claims(
    entry: str,
) -> None:
    output = _structured_output(review_questions=(entry,))

    with pytest.raises(
        StructuredDraftOutputValidationError,
        match="professional_review_claim",
    ) as exc_info:
        validate_structured_draft_output(output)

    error = exc_info.value
    assert error.rule == "professional_review_claim"
    assert error.field_name == "review_questions"
    assert error.item_index == 0


@pytest.mark.parametrize(
    "entry",
    (
        "Interner Hinweis: Der Entwurf ist fachlich gepr\u00fcft und bleibt ein Entwurf.",
        "Das Ergebnis gilt als steuerlich gepr\u00fcft, ben\u00f6tigt aber Human Review.",
        "Die fachliche Pr\u00fcfung ist abgeschlossen; Human Review bleibt erforderlich.",
        "For internal use, the draft was professionally reviewed and documented.",
        "The result has been fully tax reviewed, but remains a draft.",
        "The professional review has been completed; human review still applies.",
        (
            "Der Entwurf ist nicht fachlich gepr\u00fcft; "
            "dieser Entwurf wurde fachlich gepr\u00fcft."
        ),
        "Der Entwurf wurde erfolgreich fachlich gepr\u00fcft.",
        "Die fachliche Pr\u00fcfung wurde erfolgreich abgeschlossen.",
        "The draft was successfully professionally reviewed.",
        "The professional review has been successfully completed.",
        "Der Entwurf ist nicht final freigegeben, aber fachlich gepr\u00fcft.",
        "The draft is not approved for filing, but professionally reviewed.",
    ),
)
def test_validate_structured_draft_output_rejects_embedded_or_variant_professional_claims(
    entry: str,
) -> None:
    output = _structured_output(review_questions=(entry,))

    with pytest.raises(
        StructuredDraftOutputValidationError,
        match="professional_review_claim",
    ) as exc_info:
        validate_structured_draft_output(output)

    error = exc_info.value
    assert error.rule == "professional_review_claim"
    assert error.field_name == "review_questions"
    assert error.item_index == 0


@pytest.mark.parametrize(
    "entry",
    (
        "Der Entwurf ist nicht fachlich gepr\u00fcft.",
        "Der Entwurf wurde nicht steuerlich gepr\u00fcft.",
        "The draft has not been professionally reviewed.",
        "The result is not tax reviewed.",
        "Der Entwurf wurde nicht fachlich gepr\u00fcft und bleibt im Human Review.",
        "Das Ergebnis gilt nicht als steuerlich gepr\u00fcft.",
        "Die fachliche Pr\u00fcfung ist nicht abgeschlossen.",
        "The draft was not professionally reviewed and remains a draft.",
        "The result has not been tax reviewed.",
        "The professional review has not been completed.",
        "Der Entwurf wurde nicht erfolgreich fachlich gepr\u00fcft.",
        "Die fachliche Pr\u00fcfung wurde nicht erfolgreich abgeschlossen.",
        "The draft was not successfully professionally reviewed.",
        "The professional review has not been successfully completed.",
        "Der Entwurf ist nicht final freigegeben und nicht fachlich gepr\u00fcft.",
        "Der Entwurf ist nicht final freigegeben, aber nicht fachlich gepr\u00fcft.",
        "Der Entwurf wurde in keiner Weise fachlich gepr\u00fcft.",
        "Die fachliche Pr\u00fcfung wurde keinesfalls abgeschlossen.",
        "The draft was in no way professionally reviewed.",
        "The draft is not approved for filing, but not professionally reviewed.",
    ),
)
def test_validate_structured_draft_output_allows_negative_professional_review_statements(
    entry: str,
) -> None:
    validate_structured_draft_output(_structured_output(review_questions=(entry,)))


@pytest.mark.parametrize(
    "entry",
    (
        "Der Entwurf ist final freigegeben.",
        "Der Entwurf wurde endg\u00fcltig genehmigt.",
        "Der Entwurf ist zur Einreichung freigegeben.",
        "The draft is finally approved.",
        "The draft is approved for filing.",
        "The result is cleared for submission.",
    ),
)
def test_validate_structured_draft_output_rejects_finality_or_release_claims(
    entry: str,
) -> None:
    output = _structured_output(uncertainties=(entry,))

    with pytest.raises(
        StructuredDraftOutputValidationError,
        match="finality_or_release_claim",
    ) as exc_info:
        validate_structured_draft_output(output)

    error = exc_info.value
    assert error.rule == "finality_or_release_claim"
    assert error.field_name == "uncertainties"
    assert error.item_index == 0


@pytest.mark.parametrize(
    "entry",
    (
        "Interner Hinweis: Der Entwurf ist final freigegeben und bleibt dokumentiert.",
        "Das Ergebnis wurde endg\u00fcltig genehmigt, obwohl Human Review n\u00f6tig ist.",
        "Der Entwurf ist f\u00fcr die Einreichung freigegeben und kann \u00fcbernommen werden.",
        "Dieser Entwurf hat die finale Freigabe erhalten, bleibt aber intern.",
        "The draft has been finally approved and recorded.",
        "The result is approved for submission, but still marked as a draft.",
        "For the next step, this result was cleared for submission and recorded.",
        "This draft has received final approval, but still requires review.",
        (
            "The draft is not approved for filing, but "
            "the result is approved for submission."
        ),
        "Der Entwurf ist nicht fachlich gepr\u00fcft, aber final freigegeben.",
        "The draft is not professionally reviewed, but finally approved.",
        "The result is not tax reviewed, but approved for submission.",
    ),
)
def test_validate_structured_draft_output_rejects_embedded_or_variant_release_claims(
    entry: str,
) -> None:
    output = _structured_output(uncertainties=(entry,))

    with pytest.raises(
        StructuredDraftOutputValidationError,
        match="finality_or_release_claim",
    ) as exc_info:
        validate_structured_draft_output(output)

    error = exc_info.value
    assert error.rule == "finality_or_release_claim"
    assert error.field_name == "uncertainties"
    assert error.item_index == 0


@pytest.mark.parametrize(
    "entry",
    (
        "Der Entwurf ist nicht final freigegeben.",
        "Der Entwurf ist nicht zur Einreichung freigegeben.",
        "The draft is not approved for filing.",
        "The result is not cleared for submission.",
        "Der Entwurf ist nicht freigegeben und bleibt im Human Review.",
        "Das Ergebnis wurde noch nicht endg\u00fcltig genehmigt.",
        "Der Entwurf ist nicht f\u00fcr die Einreichung freigegeben.",
        "Dieser Entwurf hat keine finale Freigabe erhalten.",
        "The draft has not been finally approved.",
        "The result is not approved for submission.",
        "This draft has not received final approval.",
        "Der Entwurf ist nicht fachlich gepr\u00fcft und nicht final freigegeben.",
        "Der Entwurf ist nicht fachlich gepr\u00fcft, aber nicht final freigegeben.",
        "The draft is not professionally reviewed, but not finally approved.",
        "The result is not tax reviewed, but not approved for submission.",
    ),
)
def test_validate_structured_draft_output_allows_negative_finality_or_release_statements(
    entry: str,
) -> None:
    validate_structured_draft_output(_structured_output(uncertainties=(entry,)))


def test_validate_structured_draft_output_is_case_insensitive_for_claims() -> None:
    output = _structured_output(summary_points=("THE DRAFT IS APPROVED FOR FILING.",))

    with pytest.raises(
        StructuredDraftOutputValidationError,
        match="finality_or_release_claim",
    ):
        validate_structured_draft_output(output)


@pytest.mark.parametrize(
    "field_name",
    ("summary_points", "uncertainties", "review_questions"),
)
def test_validate_structured_draft_output_checks_hardened_claims_in_every_field(
    field_name: str,
) -> None:
    output = _structured_output(
        **{
            field_name: (
                "For internal use, the draft was professionally reviewed and recorded.",
            )
        }
    )

    with pytest.raises(StructuredDraftOutputValidationError) as exc_info:
        validate_structured_draft_output(output)

    error = exc_info.value
    assert error.rule == "professional_review_claim"
    assert error.field_name == field_name
    assert error.item_index == 0


def test_validate_structured_draft_output_stops_at_first_error_by_field_order() -> None:
    output = StructuredDraftOutput(
        summary_points=("The draft is approved for filing.",),
        uncertainties=("",),
        review_questions=("Same question?", "Same question?"),
    )

    with pytest.raises(StructuredDraftOutputValidationError) as exc_info:
        validate_structured_draft_output(output)

    error = exc_info.value
    assert error.rule == "finality_or_release_claim"
    assert error.field_name == "summary_points"
    assert error.item_index == 0
    assert "uncertainties" not in str(error)


def test_validate_structured_draft_output_stops_at_first_error_by_entry_order() -> None:
    output = _structured_output(
        review_questions=(
            "The draft has been professionally reviewed.",
            "",
        )
    )

    with pytest.raises(StructuredDraftOutputValidationError) as exc_info:
        validate_structured_draft_output(output)

    error = exc_info.value
    assert error.rule == "professional_review_claim"
    assert error.item_index == 0
    assert "blank_entry" not in str(error)


def test_validate_structured_draft_output_public_export() -> None:
    assert (
        offline_mvp.StructuredDraftOutputValidationError
        is StructuredDraftOutputValidationError
    )
    assert offline_mvp.validate_structured_draft_output is validate_structured_draft_output
    assert "StructuredDraftOutputValidationError" in offline_mvp.__all__
    assert "validate_structured_draft_output" in offline_mvp.__all__


def _structured_output(
    *,
    summary_points: tuple[str, ...] = ("Synthetic summary.",),
    uncertainties: tuple[str, ...] = ("Synthetic uncertainty.",),
    review_questions: tuple[str, ...] = ("Synthetic review question?",),
) -> StructuredDraftOutput:
    return StructuredDraftOutput(
        summary_points=summary_points,
        uncertainties=uncertainties,
        review_questions=review_questions,
    )
