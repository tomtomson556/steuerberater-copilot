"""Versioned prompt definitions for synthetic offline MVP model requests."""

from __future__ import annotations

from dataclasses import dataclass
from string import Template


@dataclass(frozen=True, slots=True)
class VersionedPromptDefinition:
    """Immutable prompt text contract with explicit identity and version."""

    prompt_id: str
    version: str
    system_prompt: str
    user_prompt_template: str

    def render_user_prompt(self, *, case_data: str) -> str:
        """Render the user prompt from pre-serialized synthetic case data."""
        return Template(self.user_prompt_template).substitute(case_data=case_data)


SYNTHETIC_STRUCTURED_DRAFT_PROMPT_V1 = VersionedPromptDefinition(
    prompt_id="synthetic_structured_draft",
    version="1",
    system_prompt=(
        "You prepare internal draft material from synthetic offline MVP case data only.\n"
        "Use only the supplied data and do not invent missing facts.\n"
        "Do not provide tax advice, professional approval, or instructions for productive "
        "transmission.\n"
        "Keep uncertainties and missing information explicit.\n"
        "Return only one valid JSON object matching the required structured output contract.\n"
        "Do not use Markdown code fences or add text outside the JSON object.\n"
        "The result remains an internal draft and requires human review."
    ),
    user_prompt_template=(
        "Synthetic case data:\n"
        "$case_data\n"
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
    ),
)
