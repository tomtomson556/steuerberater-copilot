"""Markdown review handoff rendering for offline MVP workflow results."""

from __future__ import annotations

from collections.abc import Iterable

from ._response_markers import (
    REVIEW_HANDOFF_ARTIFACT_NOTICE,
    REVIEW_HANDOFF_CLOSING_NOTE,
    REVIEW_HANDOFF_NO_EXTERNAL_ACTION_NOTICE,
)
from .models import WorkflowOutput


def render_review_handoff(output: WorkflowOutput) -> str:
    """Render a local Markdown review handoff from an existing workflow result."""

    draft_available = output.draft_available
    lines: list[str] = [
        "# Review Handoff",
        "",
        REVIEW_HANDOFF_ARTIFACT_NOTICE,
        "",
        REVIEW_HANDOFF_NO_EXTERNAL_ACTION_NOTICE,
        "",
        "## Case",
        "",
        f"- Case ID: `{output.intake.case_id}`",
        f"- Scenario: {output.intake.scenario}",
        f"- Period: {output.intake.period}",
        "",
        "## Review Gate",
        "",
        f"- Status: `{output.review_gate.status.value}`",
        f"- Allows offline mock continuation: "
        f"`{output.review_gate.allows_offline_mock_continuation}`",
        f"- Reason: {output.review_gate.reason}",
        "",
        "## Draft State",
        "",
        f"- Draft available: `{draft_available}`",
        f"- Review status: `{output.draft_package.review_status.value}`",
        "",
        "## Risk Basis",
        "",
        f"- Risk level: `{output.risk_classification.risk_level.value}`",
        f"- Review required: `{output.risk_classification.review_required}`",
    ]

    lines.extend(_bullet_list(output.risk_classification.basis))
    lines.extend(_section("Summary Points", _summary_points(output, draft_available)))
    lines.extend(_section("Open Review Questions", output.draft_package.question_drafts))
    lines.extend(_section("Handoff Notes", output.draft_package.handoff_notes))
    lines.extend(_section("Disclaimers", output.draft_package.disclaimers))
    lines.extend(
        [
            "",
            "## Closing Note",
            "",
            REVIEW_HANDOFF_CLOSING_NOTE,
        ]
    )
    return "\n".join(lines) + "\n"


def _summary_points(output: WorkflowOutput, draft_available: bool) -> tuple[str, ...]:
    if draft_available:
        return output.draft_package.summary_points
    return ()


def _section(title: str, items: Iterable[str]) -> list[str]:
    return ["", f"## {title}", "", *_bullet_list(tuple(items))]


def _bullet_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None."]
    return [f"- {item}" for item in items]
