"""Static, offline checks for the local Docker runtime baseline."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "Dockerfile"
DOCKERIGNORE = ROOT / ".dockerignore"
PYPROJECT = ROOT / "pyproject.toml"
RUNTIME_LOCK = ROOT / "requirements-runtime.lock"
WORKFLOW = ROOT / "src" / "steuerberater_copilot" / "offline_mvp" / "workflow.py"

PINNED_BASE_IMAGE = (
    "python:3.12.13-slim-bookworm@"
    "sha256:d50fb7611f86d04a3b0471b46d7557818d88983fc3136726336b2a4c657aa30b"
)

REQUIRED_ALLOWLIST_ENTRIES = (
    "**",
    "!Dockerfile",
    "!.dockerignore",
    "!pyproject.toml",
    "!requirements-runtime.lock",
    "!README.md",
    "!LICENSE",
    "!src/",
    "!src/**",
    "!fixtures/",
    "!fixtures/offline_mvp/",
    "!fixtures/offline_mvp/cases.json",
)


def test_dockerfile_and_dockerignore_exist() -> None:
    assert DOCKERFILE.is_file()
    assert DOCKERIGNORE.is_file()
    assert RUNTIME_LOCK.is_file()


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


def test_dockerignore_uses_allowlist() -> None:
    lines = [
        line.strip()
        for line in DOCKERIGNORE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    assert lines[0] == "**"
    missing = [entry for entry in REQUIRED_ALLOWLIST_ENTRIES if entry not in lines]
    assert missing == []


def test_workflow_has_no_docker_specific_fixture_fallback() -> None:
    contents = WORKFLOW.read_text(encoding="utf-8")

    assert "_DOCKER_FIXTURE_PATH" not in contents
    assert "_resolve_default_fixture_path" not in contents
    assert "/app/fixtures" not in contents
    assert 'Path("/app' not in contents
    assert "def load_fixture_cases(path: Path = DEFAULT_FIXTURE_PATH)" in contents


def test_dockerfile_copies_only_cases_json_and_installs_at_default_path() -> None:
    contents = DOCKERFILE.read_text(encoding="utf-8")

    assert (
        "COPY fixtures/offline_mvp/cases.json ./fixtures/offline_mvp/cases.json"
        in contents
    )
    assert "COPY fixtures/offline_mvp ./fixtures/offline_mvp" not in contents
    assert "COPY fixtures ./fixtures" not in contents
    assert "DEFAULT_FIXTURE_PATH" in contents
    assert "install -m 0444 /app/fixtures/offline_mvp/cases.json" in contents
    assert "rm -rf /app/fixtures" in contents


def test_dockerfile_uses_hashed_lock_and_no_deps_local_install() -> None:
    contents = DOCKERFILE.read_text(encoding="utf-8")

    assert "--require-hashes" in contents
    assert "requirements-runtime.lock" in contents
    assert "--no-deps --no-build-isolation" in contents
    assert "pip install --no-cache-dir -e ." not in contents
    assert "chown -R appuser:appuser /app" not in contents
    assert "--upgrade pip" not in contents


def test_runtime_lock_contains_exact_pins_and_hashes() -> None:
    contents = RUNTIME_LOCK.read_text(encoding="utf-8")
    requirement_lines = [
        line.strip()
        for line in contents.splitlines()
        if line.strip()
        and not line.strip().startswith("#")
        and not line.strip().startswith("--")
    ]
    package_lines = [line.rstrip(" \\") for line in requirement_lines if "==" in line]

    assert package_lines
    assert all(re.fullmatch(r"[A-Za-z0-9_.-]+==[A-Za-z0-9_.+-]+", line) for line in package_lines)
    assert contents.count("--hash=sha256:") >= len(package_lines)
    assert "fastapi==0.139.2" in contents
    assert "openai==2.45.0" in contents
    assert "pydantic==2.13.4" in contents
    assert "uvicorn==0.51.0" in contents


def test_pyproject_declares_uvicorn_runtime_dependency() -> None:
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]

    assert "uvicorn==0.51.0" in dependencies
