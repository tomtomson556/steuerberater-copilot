from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
TEXT_FILENAMES = {
    "LICENSE",
}
IGNORED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
    "venv",
}
IGNORED_SUFFIXES = {
    ".pyc",
    ".pyo",
}
DISALLOWED_CHARACTERS = {
    0xFEFF: "remove BOM",
    0x00A0: "use normal ASCII space",
    0x00AD: "remove soft hyphen",
    0x200B: "remove zero width space",
    0x200C: "remove zero width non-joiner",
    0x200D: "remove zero width joiner",
    0x2060: "remove word joiner",
    0x2018: "use ASCII single quote",
    0x2019: "use ASCII single quote",
    0x201C: 'use ASCII double quote',
    0x201D: 'use ASCII double quote',
    0x201E: 'use ASCII double quote',
    0x2013: 'use "-"',
    0x2014: 'use "-"',
    0x2011: 'use "-"',
}


@dataclass(frozen=True)
class CharacterFinding:
    path: Path
    line_number: int
    column_number: int
    codepoint: int
    replacement_hint: str


def test_repository_text_files_do_not_contain_problematic_unicode_characters() -> None:
    findings = [
        finding
        for path in repository_text_files()
        for finding in find_disallowed_characters(path)
    ]

    assert findings == [], "\n".join(format_finding(finding) for finding in findings)


def test_repository_text_scan_includes_github_workflow_yaml() -> None:
    assert ROOT / ".github" / "workflows" / "ci.yml" in repository_text_files()


def repository_text_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not is_ignored_path(path)
        and (path.suffix.lower() in TEXT_SUFFIXES or path.name in TEXT_FILENAMES)
    )


def is_ignored_path(path: Path) -> bool:
    return (
        any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts)
        or path.suffix.lower() in IGNORED_SUFFIXES
        or any(part.endswith(".egg-info") for part in path.relative_to(ROOT).parts)
    )


def find_disallowed_characters(path: Path) -> list[CharacterFinding]:
    text = path.read_text(encoding="utf-8")
    findings: list[CharacterFinding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for column_number, character in enumerate(line, start=1):
            codepoint = ord(character)
            if codepoint in DISALLOWED_CHARACTERS:
                findings.append(
                    CharacterFinding(
                        path=path,
                        line_number=line_number,
                        column_number=column_number,
                        codepoint=codepoint,
                        replacement_hint=DISALLOWED_CHARACTERS[codepoint],
                    )
                )
    return findings


def format_finding(finding: CharacterFinding) -> str:
    relative_path = finding.path.relative_to(ROOT)
    codepoint = f"U+{finding.codepoint:04X}"
    name = unicodedata.name(chr(finding.codepoint), "UNKNOWN")
    return (
        f"{relative_path}:{finding.line_number}:{finding.column_number}: "
        f"{codepoint} {name}; {finding.replacement_hint}"
    )
