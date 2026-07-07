from __future__ import annotations

import subprocess
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIDIRECTIONAL_CONTROL_CHARACTERS = {
    0x061C: "remove Arabic letter mark",
    0x200E: "remove left-to-right mark",
    0x200F: "remove right-to-left mark",
    0x202A: "remove left-to-right embedding",
    0x202B: "remove right-to-left embedding",
    0x202C: "remove pop directional formatting",
    0x202D: "remove left-to-right override",
    0x202E: "remove right-to-left override",
    0x2066: "remove left-to-right isolate",
    0x2067: "remove right-to-left isolate",
    0x2068: "remove first strong isolate",
    0x2069: "remove pop directional isolate",
}
INVISIBLE_CONTROL_CHARACTERS = {
    0xFEFF: "remove BOM",
    0x200B: "remove zero width space",
    0x200C: "remove zero width non-joiner",
    0x200D: "remove zero width joiner",
    0x2060: "remove word joiner",
}
TEXT_SUFFIXES = {
    ".json",
    ".md",
    ".mdc",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
TEXT_FILENAMES = {
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
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
    **BIDIRECTIONAL_CONTROL_CHARACTERS,
    **INVISIBLE_CONTROL_CHARACTERS,
    0x00A0: "use normal ASCII space",
    0x00AD: "remove soft hyphen",
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
    line_text: str


def test_repository_text_files_do_not_contain_problematic_unicode_characters() -> None:
    findings = [
        finding
        for path in repository_text_files()
        for finding in find_disallowed_characters(path)
    ]

    assert findings == [], "\n".join(format_finding(finding) for finding in findings)


def test_repository_text_scan_includes_github_workflow_yaml() -> None:
    assert ROOT / ".github" / "workflows" / "ci.yml" in repository_text_files()


def test_repository_text_scan_includes_tracked_config_dotfiles() -> None:
    text_files = repository_text_files()

    assert ROOT / ".editorconfig" in text_files
    assert ROOT / ".gitattributes" in text_files
    assert ROOT / ".gitignore" in text_files


def test_hidden_unicode_guard_covers_bidi_and_invisible_controls() -> None:
    required_disallowed_codepoints = (
        set(BIDIRECTIONAL_CONTROL_CHARACTERS)
        | set(INVISIBLE_CONTROL_CHARACTERS)
        | {0x00AD}
    )

    assert required_disallowed_codepoints <= set(DISALLOWED_CHARACTERS)


def repository_text_files() -> list[Path]:
    files: list[Path] = []
    for relative_path in tracked_repository_files():
        path = ROOT / relative_path
        if (
            path.is_file()
            and not is_ignored_path(path)
            and (path.suffix.lower() in TEXT_SUFFIXES or path.name in TEXT_FILENAMES)
        ):
            files.append(path)
    return sorted(files)


def tracked_repository_files() -> list[Path]:
    output = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT, text=True)
    return [Path(name) for name in output.split("\0") if name]


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
                        line_text=line,
                    )
                )
    return findings


def format_finding(finding: CharacterFinding) -> str:
    relative_path = finding.path.relative_to(ROOT)
    codepoint = f"U+{finding.codepoint:04X}"
    name = unicodedata.name(chr(finding.codepoint), "UNKNOWN")
    return (
        f"{relative_path}:{finding.line_number}:{finding.column_number}: "
        f"{codepoint} {name}; {finding.replacement_hint}; line={finding.line_text!r}"
    )
