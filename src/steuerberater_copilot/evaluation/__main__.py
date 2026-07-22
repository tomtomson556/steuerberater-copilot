"""CLI entry point for offline synthetic evaluation suites."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from .portfolio_report import (
    build_portfolio_evaluation_baseline_report,
    portfolio_evaluation_baseline_to_dict,
)

CLI_NAME = "steuerberater-copilot-evaluate"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run deterministic offline synthetic evaluation suites. "
            "Uses FakeModelProvider only; no network."
        )
    )
    parser.add_argument(
        "--portfolio-baseline",
        action="store_true",
        help="Run the aggregated portfolio evaluation baseline and print JSON.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the evaluation CLI name and exit.",
    )
    args = parser.parse_args(argv)

    if args.version:
        print(f"{CLI_NAME} offline-synthetic")
        return 0

    if not args.portfolio_baseline:
        parser.print_help(sys.stderr)
        return 2

    report = build_portfolio_evaluation_baseline_report()
    payload = portfolio_evaluation_baseline_to_dict(report)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report.binary_suite_passed_case_count == report.binary_suite_case_count else 1


if __name__ == "__main__":
    raise SystemExit(main())
