"""CLI entry point for the deterministic offline MVP workflow."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .review_handoff import render_review_handoff
from .review_summary import build_review_summary
from .review_worklist import build_review_worklist
from .serialization import workflow_to_json
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
    parser.add_argument(
        "--review-handoff",
        type=Path,
        help="Write an optional local Markdown review handoff to this path.",
    )
    args = parser.parse_args(argv)

    cases = load_fixture_cases()
    cases_by_id = {case.case_id: case for case in cases}

    if args.list_cases:
        if args.review_handoff is not None:
            print("--review-handoff requires --case or --all.", file=sys.stderr)
            return 2
        _write_json(list(cases_by_id))
        return 0

    if args.review_worklist:
        if args.review_handoff is not None:
            print("--review-handoff requires --case or --all.", file=sys.stderr)
            return 2
        outputs = [build_mock_workflow(case) for case in cases]
        _write_json(build_review_worklist(outputs))
        return 0

    if args.review_summary:
        if args.review_handoff is not None:
            print("--review-handoff requires --case or --all.", file=sys.stderr)
            return 2
        outputs = [build_mock_workflow(case) for case in cases]
        _write_json(build_review_summary(outputs))
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


def _write_review_handoff(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
