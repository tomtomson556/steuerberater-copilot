"""Minimal FastAPI application factory at the HTTP system boundary."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from fastapi import FastAPI

PACKAGE_NAME = "steuerberater-copilot"


def create_app() -> FastAPI:
    """Create an independent FastAPI app with health and version routes only."""
    app = FastAPI(title="steuerberater-copilot")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/version")
    def package_version_endpoint() -> dict[str, str]:
        return {"version": _package_version()}

    return app


def _package_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "unknown"
