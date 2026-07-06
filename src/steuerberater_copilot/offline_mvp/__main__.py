"""CLI entry point for the deterministic offline MVP workflow."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from .models import WorkflowOutput
from .review_handoff import render_review_handoff
from .review_summary import build_review_summary
from .review_worklist import build_review_worklist, filter_review_worklist
from .serialization import workflow_to_json
from .workflow import build_mock_workflow, load_fixture_cases

CLI_NAME = "steuerberater-copilot-offline-mvp"
PACKAGE_NAME = "steuerberater-copilot"
REVIEW_FILTER_ERROR = "review filters require --review-worklist or --review-summary."
REVIEW_HANDOFF_ERROR = "--review-handoff requires --case or --all."


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
    selection.add_argument(
        "--review-worklist",
        action="store_true",
        help="Emit a local JSON review worklist for all synthetic fixture cases.",
    )
    selection.add_argument(
        "--review-summary",
        action="store_true",
        help="Emit a local JSON review summary for all synthetic fixture cases.",
    )
    selection.add_argument(
        "--version",
        action="store_true",
        help="Print the local CLI version and exit.",
    )
    parser.add_argument(
        "--review-handoff",
        type=Path,
        help="Write an optional local Markdown review handoff to this path.",
    )
    parser.add_argument(
        "--review-limit",
        type=_positive_int,
        help="Limit local review worklist or review summary output to the first N entries.",
    )
    parser.add_argument(
        "--review-min-risk",
        choices=("A", "B", "C", "D"),
        help="Filter local review worklist or review summary output by minimum RiskLevel.",
    )
    parser.add_argument(
        "--review-gateway",
        choices=("allow_draft", "escalate", "block"),
        help="Filter local review worklist or review summary output by gateway decision.",
    )
    parser.add_argument(
        "--review-open-questions-only",
        action="store_true",
        help="Filter local review worklist or review summary output to cases with open questions.",
    )
    args = parser.parse_args(argv)

    if _has_review_filters(args) and not (args.review_worklist or args.review_summary):
        print(REVIEW_FILTER_ERROR, file=sys.stderr)
        return 2

    if _review_handoff_without_workflow_result(args):
        print(REVIEW_HANDOFF_ERROR, file=sys.stderr)
        return 2

    if args.version:
        print(f"{CLI_NAME} {_package_version()}")
        return 0

    cases = load_fixture_cases()
    cases_by_id = {case.case_id: case for case in cases}

    if args.list_cases:
        _write_json(list(cases_by_id))
        return 0

    if args.review_worklist:
        outputs = [build_mock_workflow(case) for case in cases]
        worklist = build_review_worklist(outputs)
        _write_json(
            filter_review_worklist(
                worklist,
                **_review_filter_kwargs(args),
            )
        )
        return 0

    if args.review_summary:
        outputs = [build_mock_workflow(case) for case in cases]
        summary = build_review_summary(_filter_outputs_for_summary(outputs, args))
        if _has_review_filters(args):
            summary["summary_scope"] = "filtered"
            summary["applied_filters"] = _applied_review_filters(args)
        _write_json(summary)
        return 0

    if args.case_id:
        case = cases_by_id.get(args.case_id)
        if case is None:
            print(f"Unknown synthetic case ID: {args.case_id}", file=sys.stderr)
            return 2
        output = build_mock_workflow(case)
        if args.review_handoff is not None:
            _write_review_handoff(args.review_handoff, render_review_handoff(output))
        _write_json(workflow_to_json(output))
        return 0

    outputs = [build_mock_workflow(case) for case in cases]
    if args.review_handoff is not None:
        _write_review_handoff(
            args.review_handoff,
            "\n".join(render_review_handoff(output) for output in outputs),
        )
    _write_json([workflow_to_json(output) for output in outputs])
    return 0


def _write_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _has_review_filters(args: argparse.Namespace) -> bool:
    return (
        args.review_limit is not None
        or args.review_min_risk is not None
        or args.review_gateway is not None
        or args.review_open_questions_only
    )


def _review_handoff_without_workflow_result(args: argparse.Namespace) -> bool:
    return args.review_handoff is not None and not (args.case_id or args.all)


def _review_filter_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "limit": args.review_limit,
        "min_risk": args.review_min_risk,
        "gateway_decision": args.review_gateway,
        "open_questions_only": args.review_open_questions_only,
    }


def _applied_review_filters(args: argparse.Namespace) -> dict[str, Any]:
    applied: dict[str, Any] = {}
    if args.review_limit is not None:
        applied["review_limit"] = args.review_limit
    if args.review_min_risk is not None:
        applied["review_min_risk"] = args.review_min_risk
    if args.review_gateway is not None:
        applied["review_gateway"] = args.review_gateway
    if args.review_open_questions_only:
        applied["review_open_questions_only"] = True
    return applied


def _filter_outputs_for_summary(
    outputs: list[WorkflowOutput], args: argparse.Namespace
) -> list[WorkflowOutput]:
    if not _has_review_filters(args):
        return outputs

    outputs_by_case_id = {output.intake.case_id: output for output in outputs}
    filtered_worklist = filter_review_worklist(
        build_review_worklist(outputs),
        **_review_filter_kwargs(args),
    )
    return [outputs_by_case_id[item["case_id"]] for item in filtered_worklist]


def _package_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "unknown"
    except Exception:
        return "unknown"


def _write_review_handoff(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
