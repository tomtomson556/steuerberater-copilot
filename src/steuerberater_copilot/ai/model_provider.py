"""Provider-independent model boundary without model invocation.

This module defines only the neutral request, response, and provider contract.
Concrete providers are implemented separately.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class ModelRequest:
    """Text prompts prepared for a concrete provider implementation."""

    system_prompt: str
    user_prompt: str


@dataclass(frozen=True, slots=True)
class ModelResponse:
    """Raw text response metadata returned by a concrete provider."""

    content: str
    provider_name: str
    model_name: str


@runtime_checkable
class ModelProvider(Protocol):
    """Synchronous provider-independent model generation contract."""

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a model response for the given request."""
        ...
