"""Build internal model prompts from supplied synthetic offline MVP case data.

This formatter is not a privacy check, sanitization boundary, authorization
decision, or substitute for request gateway or human review.
"""

from __future__ import annotations

import json

from steuerberater_copilot.ai import ModelRequest
from steuerberater_copilot.rag import SourceDocument

from .models import IntakeCase
from .prompt_definition import (
    SYNTHETIC_GROUNDED_DRAFT_PROMPT_V1,
    SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1,
)


def build_synthetic_model_request(case: IntakeCase) -> ModelRequest:
    """Format one synthetic intake case as a provider-neutral model request."""

    payload = {
        "case_id": case.case_id,
        "scenario": case.scenario,
        "period": case.period,
        "documents": [
            {
                "document_id": document.document_id,
                "label": document.label,
                "period": document.period,
                "source_note": document.source_note,
            }
            for document in case.documents
        ],
        "notes": list(case.notes),
        "missing_items": list(case.missing_items),
    }
    case_data = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    )
    user_prompt = SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.render_user_prompt(
        case_data=case_data
    )

    return ModelRequest(
        prompt_id=SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.prompt_id,
        prompt_version=SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.version,
        system_prompt=SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.system_prompt,
        user_prompt=user_prompt,
    )


def build_synthetic_grounded_model_request(
    case: IntakeCase,
    *,
    retrieved_documents: tuple[SourceDocument, ...],
) -> ModelRequest:
    """Format one synthetic case and explicit retrieval context as a model request."""

    payload = {
        "case": {
            "case_id": case.case_id,
            "scenario": case.scenario,
            "period": case.period,
            "documents": [
                {
                    "document_id": document.document_id,
                    "label": document.label,
                    "period": document.period,
                    "source_note": document.source_note,
                }
                for document in case.documents
            ],
            "notes": list(case.notes),
            "missing_items": list(case.missing_items),
        },
        "retrieved_documents": [
            {
                "document_id": document.document_id,
                "title": document.title,
                "content": document.content,
            }
            for document in retrieved_documents
        ],
    }
    case_data = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    )
    user_prompt = SYNTHETIC_GROUNDED_DRAFT_PROMPT_V1.render_user_prompt(
        case_data=case_data
    )

    return ModelRequest(
        prompt_id=SYNTHETIC_GROUNDED_DRAFT_PROMPT_V1.prompt_id,
        prompt_version=SYNTHETIC_GROUNDED_DRAFT_PROMPT_V1.version,
        system_prompt=SYNTHETIC_GROUNDED_DRAFT_PROMPT_V1.system_prompt,
        user_prompt=user_prompt,
    )
