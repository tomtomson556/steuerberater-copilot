"""ASGI entry module for uvicorn: steuerberater_copilot.api.main:app."""

from .app import create_app

app = create_app()
