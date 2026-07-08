import steuerberater_copilot.offline_mvp as offline_mvp
from steuerberater_copilot.ai import ModelRequest
from steuerberater_copilot.offline_mvp import build_synthetic_model_request
from steuerberater_copilot.offline_mvp.models import IntakeCase, SyntheticDocument

EXPECTED_SYSTEM_PROMPT = (
    "You prepare internal draft material from synthetic offline MVP case data only.\n"
    "Use only the supplied data and do not invent missing facts.\n"
    "Do not provide tax advice, professional approval, or instructions for productive "
    "transmission.\n"
    "Keep uncertainties and missing information explicit.\n"
    "The result remains an internal draft and requires human review."
)


def test_synthetic_prompt_builder_returns_model_request() -> None:
    result = build_synthetic_model_request(_minimal_case())

    assert isinstance(result, ModelRequest)


def test_synthetic_prompt_builder_system_prompt_contract() -> None:
    result = build_synthetic_model_request(_minimal_case())

    assert result.system_prompt == EXPECTED_SYSTEM_PROMPT
    assert not result.system_prompt.endswith("\n")


def test_synthetic_prompt_builder_user_prompt_contract() -> None:
    case = IntakeCase(
        case_id="CASE_100",
        client_ref="CLIENT_100",
        scenario="synthetic document preparation",
        period="2026-Q1",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_100",
                label="synthetic invoice list",
                period="2026-Q1",
                source_note="first synthetic descriptor",
            ),
            SyntheticDocument(
                document_id="DOCUMENT_101",
                label="synthetic payment overview",
                period="2026-Q1",
                source_note="second synthetic descriptor",
            ),
        ),
        notes=(
            "First internal draft note.",
            "Second internal draft note.",
        ),
        missing_items=(
            "Clarify source reference.",
            "Clarify period boundary.",
        ),
        mock_risk_signals=("SHOULD_NOT_APPEAR_RISK_SIGNAL",),
    )

    result = build_synthetic_model_request(case)

    expected_user_prompt = (
        "Synthetic case data:\n"
        "{\n"
        '  "case_id": "CASE_100",\n'
        '  "scenario": "synthetic document preparation",\n'
        '  "period": "2026-Q1",\n'
        '  "documents": [\n'
        "    {\n"
        '      "document_id": "DOCUMENT_100",\n'
        '      "label": "synthetic invoice list",\n'
        '      "period": "2026-Q1",\n'
        '      "source_note": "first synthetic descriptor"\n'
        "    },\n"
        "    {\n"
        '      "document_id": "DOCUMENT_101",\n'
        '      "label": "synthetic payment overview",\n'
        '      "period": "2026-Q1",\n'
        '      "source_note": "second synthetic descriptor"\n'
        "    }\n"
        "  ],\n"
        '  "notes": [\n'
        '    "First internal draft note.",\n'
        '    "Second internal draft note."\n'
        "  ],\n"
        '  "missing_items": [\n'
        '    "Clarify source reference.",\n'
        '    "Clarify period boundary."\n'
        "  ]\n"
        "}\n"
        "\n"
        "Task:\n"
        "Prepare a concise internal draft with:\n"
        "- a summary of the supplied facts\n"
        "- explicit uncertainties and missing information\n"
        "- questions for human review\n"
        "\n"
        "Use only the supplied synthetic data. Do not infer or add missing facts."
    )
    assert result.user_prompt == expected_user_prompt
    assert not result.user_prompt.endswith("\n")


def test_synthetic_prompt_builder_keeps_empty_collections_as_json_arrays() -> None:
    result = build_synthetic_model_request(
        IntakeCase(
            case_id="CASE_101",
            client_ref="CLIENT_101",
            scenario="synthetic empty collection case",
            period="2026-Q2",
            documents=(),
            notes=(),
            missing_items=(),
        )
    )

    assert '  "documents": [],' in result.user_prompt
    assert '  "notes": [],' in result.user_prompt
    assert '  "missing_items": []' in result.user_prompt
    assert "none" not in result.user_prompt.lower()
    assert "n/a" not in result.user_prompt.lower()
    assert "not provided" not in result.user_prompt.lower()


def test_synthetic_prompt_builder_excludes_non_prompt_control_fields() -> None:
    case = IntakeCase(
        case_id="CASE_102",
        client_ref="CLIENT_SHOULD_NOT_APPEAR",
        scenario="synthetic data minimization case",
        period="2026-Q3",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_102",
                label="synthetic descriptor",
                period="2026-Q3",
                source_note="synthetic source note",
            ),
        ),
        mock_risk_signals=("SHOULD_NOT_APPEAR_RISK_SIGNAL",),
    )

    result = build_synthetic_model_request(case)

    assert case.client_ref not in result.system_prompt
    assert case.client_ref not in result.user_prompt
    assert "SHOULD_NOT_APPEAR_RISK_SIGNAL" not in result.system_prompt
    assert "SHOULD_NOT_APPEAR_RISK_SIGNAL" not in result.user_prompt


def test_synthetic_prompt_builder_uses_standard_json_escaping() -> None:
    result = build_synthetic_model_request(
        IntakeCase(
            case_id="CASE_103",
            client_ref="CLIENT_103",
            scenario='synthetic "quoted" value with backslash \\ and newline\nmarker',
            period="2026-Q4",
            documents=(),
        )
    )

    assert (
        '  "scenario": "synthetic \\"quoted\\" value with backslash \\\\ '
        'and newline\\nmarker",'
    ) in result.user_prompt
    assert 'newline\nmarker' not in result.user_prompt


def test_synthetic_prompt_builder_preserves_unicode_while_escaping_json_controls() -> None:
    result = build_synthetic_model_request(
        IntakeCase(
            case_id="CASE_104",
            client_ref="CLIENT_104",
            scenario=(
                'synthetische Erklärung: ä ö ü ß € with "quote", '
                "backslash \\ and newline\nmarker"
            ),
            period="2027-Q1",
            documents=(),
        )
    )

    assert "ä ö ü ß €" in result.user_prompt
    for escaped_value in ("\\u00e4", "\\u00f6", "\\u00fc", "\\u00df", "\\u20ac"):
        assert escaped_value not in result.user_prompt
    assert (
        '  "scenario": "synthetische Erklärung: ä ö ü ß € with \\"quote\\", '
        'backslash \\\\ and newline\\nmarker",'
    ) in result.user_prompt
    assert 'newline\nmarker' not in result.user_prompt


def test_synthetic_prompt_builder_is_deterministic_for_same_instance() -> None:
    case = _minimal_case()

    first = build_synthetic_model_request(case)
    second = build_synthetic_model_request(case)

    assert first == second


def test_synthetic_prompt_builder_public_export() -> None:
    assert offline_mvp.build_synthetic_model_request is build_synthetic_model_request
    assert "build_synthetic_model_request" in offline_mvp.__all__


def _minimal_case() -> IntakeCase:
    return IntakeCase(
        case_id="CASE_099",
        client_ref="CLIENT_099",
        scenario="synthetic minimal case",
        period="2026-Q1",
        documents=(
            SyntheticDocument(
                document_id="DOCUMENT_099",
                label="synthetic document descriptor",
                period="2026-Q1",
                source_note="synthetic source note",
            ),
        ),
    )
