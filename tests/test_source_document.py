from dataclasses import FrozenInstanceError

import pytest

import steuerberater_copilot.rag as rag
from steuerberater_copilot.rag import SourceDocument


def test_source_document_keeps_valid_field_values_unchanged() -> None:
    document = SourceDocument(
        document_id=" synthetic-source:alpha/01 ",
        title=" Synthetic source title ",
        content="\nSynthetic source content remains unchanged.\n",
    )

    assert document.document_id == " synthetic-source:alpha/01 "
    assert document.title == " Synthetic source title "
    assert document.content == "\nSynthetic source content remains unchanged.\n"


def test_source_document_uses_value_equality() -> None:
    assert _source_document() == _source_document()


def test_source_document_is_immutable_and_uses_slots() -> None:
    document = _source_document()

    for field_name in ("document_id", "title", "content"):
        with pytest.raises(FrozenInstanceError):
            setattr(document, field_name, "Changed synthetic value.")

    assert not hasattr(document, "__dict__")
    assert SourceDocument.__slots__ == ("document_id", "title", "content")


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("document_id", 1),
        ("title", None),
        ("content", ["Synthetic non-string content."]),
    ),
)
def test_source_document_rejects_non_string_fields(
    field_name: str,
    invalid_value: object,
) -> None:
    arguments: dict[str, object] = _source_document_arguments()
    arguments[field_name] = invalid_value

    with pytest.raises(TypeError, match=rf"^{field_name} must be a string\.$"):
        SourceDocument(**arguments)


@pytest.mark.parametrize("field_name", ("document_id", "title", "content"))
def test_source_document_rejects_empty_fields(field_name: str) -> None:
    arguments = _source_document_arguments()
    arguments[field_name] = ""

    with pytest.raises(ValueError, match=rf"^{field_name} must not be blank\.$"):
        SourceDocument(**arguments)


@pytest.mark.parametrize("field_name", ("document_id", "title", "content"))
def test_source_document_rejects_whitespace_only_fields(field_name: str) -> None:
    arguments = _source_document_arguments()
    arguments[field_name] = " \t\n"

    with pytest.raises(ValueError, match=rf"^{field_name} must not be blank\.$"):
        SourceDocument(**arguments)


def test_rag_package_exports_source_document() -> None:
    assert rag.SourceDocument is SourceDocument
    assert rag.__all__ == ["SourceDocument", "LocalDocumentRetriever"]


def _source_document() -> SourceDocument:
    return SourceDocument(**_source_document_arguments())


def _source_document_arguments() -> dict[str, str]:
    return {
        "document_id": "SYNTHETIC_SOURCE_001",
        "title": "Synthetic source title",
        "content": "Synthetic source content for contract testing only.",
    }
