"""Minimal FastAPI application factory at the HTTP system boundary."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from fastapi import FastAPI, HTTPException

from .ai_draft import UnknownSyntheticDemoCaseError, run_synthetic_ai_draft
from .contracts import AIDraftRequest, AIDraftResponse

PACKAGE_NAME = "steuerberater-copilot"


def create_app() -> FastAPI:
    """Create an independent FastAPI app with health, version, and AI draft routes."""
    app = FastAPI(title="steuerberater-copilot")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/version")
    def package_version_endpoint() -> dict[str, str]:
        return {"version": _package_version()}

    @app.post("/ai/draft", response_model=AIDraftResponse)
    def ai_draft(request: AIDraftRequest) -> AIDraftResponse:
        try:
            return run_synthetic_ai_draft(request)
        except UnknownSyntheticDemoCaseError as exc:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown synthetic demo case_id: {exc.args[0]}",
            ) from exc

    return app


def _package_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "unknown"
