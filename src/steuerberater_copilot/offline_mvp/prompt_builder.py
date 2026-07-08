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
    "Return only one valid JSON object matching the required structured output contract.\n"
    "Do not use Markdown code fences or add text outside the JSON object.\n"
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
        ensure_ascii=False,
        indent=2,
    )
    user_prompt = (
        "Synthetic case data:\n"
        f"{case_data}\n"
        "\n"
        "Output contract:\n"
        "Return exactly one valid JSON object with these keys in this order:\n"
        "{\n"
        '  "summary_points": [],\n'
        '  "uncertainties": [],\n'
        '  "review_questions": []\n'
        "}\n"
        "\n"
        "Requirements:\n"
        "- Use exactly these three keys and no additional keys.\n"
        "- Each value must be a JSON array containing only strings.\n"
        "- Populate the arrays only with information supported by the supplied synthetic data.\n"
        "- Use an empty array when the supplied data supports no entry for a field.\n"
        "- summary_points must summarize only facts present in the supplied synthetic data.\n"
        "- uncertainties must state missing, unclear, or unsupported information explicitly.\n"
        "- review_questions must contain questions only for internal human review.\n"
        "- Do not infer, invent, or add missing facts.\n"
        "- Do not include Markdown code fences or any text outside the JSON object."
    )

    return ModelRequest(
        system_prompt=_SYNTHETIC_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )
