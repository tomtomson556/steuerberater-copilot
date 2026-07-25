"""CLI entry point for offline synthetic evaluation suites."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from .command_summary import (
    build_evaluation_command_summary,
    serialize_evaluation_command_summary,
)

CLI_NAME = "steuerberater-copilot-evaluate"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=CLI_NAME,
        description=(
            "Run all synthetic offline evaluation suites and emit deterministic JSON."
        ),
    )
    parser.parse_args(argv)

    summary = build_evaluation_command_summary()
    print(serialize_evaluation_command_summary(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
