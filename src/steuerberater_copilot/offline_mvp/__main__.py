"""CLI entry point for the deterministic offline MVP workflow."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any

from .models import GatewayDecision, RiskLevel, WorkflowOutput
from .workflow import build_mock_workflow, load_fixture_cases


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the offline MVP workflow against synthetic fixtures."
    )
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--case", dest="case_id", help="Run one synthetic fixture case.")
    selection.add_argument("--all", action="store_true", help="Run all synthetic fixture cases.")
    selection.add_argument(
        "--list-cases",
        action="store_true",
        help="List available fixture case IDs.",
    )
    args = parser.parse_args(argv)

    cases = load_fixture_cases()
    cases_by_id = {case.case_id: case for case in cases}

    if args.list_cases:
        _write_json(list(cases_by_id))
        return 0

    if args.case_id:
        case = cases_by_id.get(args.case_id)
        if case is None:
            print(f"Unknown synthetic case ID: {args.case_id}", file=sys.stderr)
            return 2
        _write_json(_workflow_to_json(build_mock_workflow(case)))
        return 0

    _write_json([_workflow_to_json(build_mock_workflow(case)) for case in cases])
    return 0


def _workflow_to_json(output: WorkflowOutput) -> dict[str, Any]:
    draft_available = (
        output.gateway.decision is GatewayDecision.ALLOW_DRAFT
        and output.risk_classification.risk_level is RiskLevel.CLASS_A
        and output.review_gate.allows_offline_mock_continuation
    )
    summary = list(output.draft_package.summary_points) if draft_available else []
    questions = list(output.draft_package.question_drafts)

    return {
        "case_id": output.intake.case_id,
        "gateway": {
            "decision": output.gateway.decision.value,
            "checks": list(output.gateway.checks),
            "reasons": list(output.gateway.escalation_reasons),
            "block_reasons": list(output.gateway.block_reasons),
        },
        "risk": {
            "level": output.risk_classification.risk_level.value,
            "review_required": output.risk_classification.review_required,
            "basis": list(output.risk_classification.basis),
        },
        "review_gate": {
            "status": output.review_gate.status.value,
            "decision": output.review_gate.status.value,
            "allows_offline_mock_continuation": (
                output.review_gate.allows_offline_mock_continuation
            ),
            "reason": output.review_gate.reason,
        },
        "draft": {
            "available": draft_available,
            "draft_only": True,
            "review_status": output.draft_package.review_status.value,
            "summary": summary,
            "summary_points": summary,
            "questions": questions,
            "handoff_notes": list(output.draft_package.handoff_notes),
            "disclaimers": list(output.draft_package.disclaimers),
        },
    }


def _write_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
