#!/usr/bin/env python3
"""Local markdown claim checker for Steuerberater-Copilot policies."""

from __future__ import annotations

import argparse
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]

RISKY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("rechtssicher", re.compile(r"\brechtssicher\w*\b", re.IGNORECASE)),
    ("DSGVO-konform", re.compile(r"\bDSGVO[- ]?konform\w*\b", re.IGNORECASE)),
    ("GoBD-konform", re.compile(r"\bGoBD[- ]?konform\w*\b", re.IGNORECASE)),
    ("AI-Act-konform", re.compile(r"\bAI[- ]?Act[- ]?konform\w*\b", re.IGNORECASE)),
    ("steuerlich geprueft", re.compile(r"\bsteuerlich\s+gepr(?:ue|ü)ft\w*\b", re.IGNORECASE)),
    ("final risk classification", re.compile(r"\bfinal\s+risk\s+classification\b", re.IGNORECASE)),
    ("autonomous tax advisor", re.compile(r"\bautonomous\s+tax\s+advisor\b", re.IGNORECASE)),
    ("KI-Steuerberater", re.compile(r"\bKI[- ]?Steuerberater\b", re.IGNORECASE)),
    ("production-ready", re.compile(r"\bproduction[- ]ready\b", re.IGNORECASE)),
    ("fully compliant", re.compile(r"\bfully\s+compliant\b", re.IGNORECASE)),
    (
        "verbindliche Steuerberatung",
        re.compile(r"\bverbindliche\s+Steuerberatung\b", re.IGNORECASE),
    ),
)

NEGATIVE_CONTEXT_RE = re.compile(
    r"("
    r"\bkein(?:e|en|er|es)?\b|"
    r"\bnicht\b|"
    r"\bniemals\b|"
    r"\bohne\b|"
    r"\bno\b|"
    r"\bnot\b|"
    r"\bnever\b|"
    r"keine\s+(?:Zusage|Garantie|Aussage|Rechtsberatung|Konformit(?:ae|ä)t)|"
    r"keinen\s+(?:Nachweis|Ersatz)|"
    r"darf\s+nicht|"
    r"duerfen\s+nicht|"
    r"dürfen\s+nicht|"
    r"nicht\s+erlaubt|"
    r"ausgeschlossen|"
    r"verboten|"
    r"unzul(?:ae|ä)ssig|"
    r"blockieren|"
    r"blockiert|"
    r"eskalieren|"
    r"Stop"
    r")",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Finding:
    path: Path
    line_number: int
    label: str
    line: str


def markdown_files(root: Path) -> list[Path]:
    ignored_parts = {".git", ".venv", "venv", "__pycache__"}
    files: list[Path] = []
    for path in root.rglob("*.md"):
        if any(part in ignored_parts for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def has_negative_context(lines: Sequence[str], index: int) -> bool:
    window_start = max(0, index - 3)
    window = " ".join(line.strip() for line in lines[window_start : index + 1])
    return bool(NEGATIVE_CONTEXT_RE.search(window))


def check_file(path: Path) -> list[Finding]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    findings: list[Finding] = []
    for index, line in enumerate(lines):
        for label, pattern in RISKY_PATTERNS:
            if pattern.search(line) and not has_negative_context(lines, index):
                findings.append(
                    Finding(path=path, line_number=index + 1, label=label, line=line.strip())
                )
    return findings


def check_paths(paths: Iterable[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        findings.extend(check_file(path))
    return findings


def format_finding(finding: Finding, root: Path) -> str:
    try:
        display_path = finding.path.relative_to(root)
    except ValueError:
        display_path = finding.path
    return f"{display_path}:{finding.line_number}: {finding.label}: {finding.line}"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan local markdown files for prohibited compliance or autonomy claims."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Markdown files or directories to scan. Defaults to the repository root.",
    )
    args = parser.parse_args(argv)

    roots = args.paths or [DEFAULT_ROOT]
    scan_files: list[Path] = []
    for root in roots:
        if root.is_dir():
            scan_files.extend(markdown_files(root))
        elif root.suffix.lower() == ".md":
            scan_files.append(root)

    findings = check_paths(sorted(set(scan_files)))
    if findings:
        print("Policy claim check failed. Review these risky claims:")
        for finding in findings:
            print(format_finding(finding, DEFAULT_ROOT))
        return 1

    print(f"Policy claim check passed. Scanned {len(scan_files)} markdown file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
