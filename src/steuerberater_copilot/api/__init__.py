"""HTTP demo boundary package. FastAPI types stay outside the application core."""

from .app import create_app

__all__ = ["create_app"]
