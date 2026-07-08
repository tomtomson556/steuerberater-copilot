"""Build internal model prompts from supplied synthetic offline MVP case data.

This formatter is not a privacy check, sanitization boundary, authorization
decision, or substitute for request gateway or human review.
"""

from __future__ import annotations

import json

from steuerberater_copilot.ai import ModelRequest

from .models import IntakeCase

_SYNTHETIC_SYSTEM_PROMPT = (
    "You prepare internal draft material from synthetic offline MVP case data only.\n"
    "Use only the supplied data and do not invent missing facts.\n"
    "Do not provide tax advice, professional approval, or instructions for productive "
    "transmission.\n"
    "Keep uncertainties and missing information explicit.\n"
    "The result remains an internal draft and requires human review."
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
        ensure_ascii=True,
        indent=2,
    )
    user_prompt = (
        "Synthetic case data:\n"
        f"{case_data}\n"
        "\n"
        "Task:\n"
        "Prepare a concise internal draft with:\n"
        "- a summary of the supplied facts\n"
        "- explicit uncertainties and missing information\n"
        "- questions for human review\n"
        "\n"
        "Use only the supplied synthetic data. Do not infer or add missing facts."
    )

    return ModelRequest(
        system_prompt=_SYNTHETIC_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )
