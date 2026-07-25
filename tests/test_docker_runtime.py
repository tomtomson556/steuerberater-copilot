"""Static, offline checks for the local Docker runtime baseline."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "Dockerfile"
DOCKERIGNORE = ROOT / ".dockerignore"
PYPROJECT = ROOT / "pyproject.toml"

PINNED_BASE_IMAGE = (
    "python:3.12.13-slim-bookworm@"
    "sha256:d50fb7611f86d04a3b0471b46d7557818d88983fc3136726336b2a4c657aa30b"
)

REQUIRED_DOCKERIGNORE_ENTRIES = (
    "fixtures/private/",
    "data/",
    "storage/",
    "exports/",
    "uploads/",
    "downloads/",
    "mandanten/",
    "belege/",
    "kanzlei/",
    "agenda/",
    "elster/",
    "secrets/",
    "vault/",
    "*.sqlite",
    "*.sqlite3",
    "*.db",
    "*.duckdb",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*.kdbx",
    "*.age",
    "*.gpg",
    ".env",
    ".env.*",
)


def test_dockerfile_and_dockerignore_exist() -> None:
    assert DOCKERFILE.is_file()
    assert DOCKERIGNORE.is_file()


def test_dockerfile_uses_pinned_python_base_image() -> None:
    contents = DOCKERFILE.read_text(encoding="utf-8")
    from_lines = [
        line.strip()
        for line in contents.splitlines()
        if line.strip().upper().startswith("FROM ")
    ]

    assert from_lines == [f"FROM {PINNED_BASE_IMAGE}"]


def test_dockerfile_runs_as_non_root_with_healthcheck_and_factory_cmd() -> None:
    contents = DOCKERFILE.read_text(encoding="utf-8")

    assert re.search(r"(?m)^USER\s+10001\s*$", contents)
    assert re.search(r"(?m)^EXPOSE\s+8000\s*$", contents)
    assert re.search(r"(?m)^HEALTHCHECK\b", contents)
    assert "/health" in contents
    assert "steuerberater_copilot.api.app:create_app" in contents
    assert "--factory" in contents


def test_dockerfile_has_no_secret_or_api_key_env() -> None:
    contents = DOCKERFILE.read_text(encoding="utf-8").lower()

    assert "api_key" not in contents
    assert "openai_api_key" not in contents
    assert "secret" not in contents
    assert "password" not in contents
    assert "token" not in contents


def test_dockerignore_keeps_readme_and_license() -> None:
    contents = DOCKERIGNORE.read_text(encoding="utf-8")
    lines = {
        line.strip()
        for line in contents.splitlines()
        if line.strip() and not line.strip().startswith("#")
    }

    assert "LICENSE" not in lines
    assert "!README.md" in lines


def test_dockerignore_excludes_sensitive_local_data_and_secret_paths() -> None:
    lines = {
        line.strip()
        for line in DOCKERIGNORE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }

    missing = [entry for entry in REQUIRED_DOCKERIGNORE_ENTRIES if entry not in lines]
    assert missing == []


def test_dockerfile_copies_only_offline_mvp_fixtures() -> None:
    contents = DOCKERFILE.read_text(encoding="utf-8")

    assert "COPY fixtures/offline_mvp ./fixtures/offline_mvp" in contents
    assert "COPY fixtures ./fixtures" not in contents
    assert "pip install --no-cache-dir -e ." in contents
    assert "--upgrade pip" not in contents


def test_pyproject_declares_uvicorn_runtime_dependency() -> None:
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]

    assert "uvicorn==0.51.0" in dependencies
