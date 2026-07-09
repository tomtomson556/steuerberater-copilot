"""Build internal model prompts from supplied synthetic offline MVP case data.

This formatter is not a privacy check, sanitization boundary, authorization
decision, or substitute for request gateway or human review.
"""

from __future__ import annotations

import json

from steuerberater_copilot.ai import ModelRequest

from .models import IntakeCase
from .prompt_definition import SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1


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
        system_prompt=SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1.system_prompt,
        user_prompt=user_prompt,
    )
