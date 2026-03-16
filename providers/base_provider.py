"""
providers/base_provider.py — provider abstraction and factory.

Each provider returns a Strands-compatible model object.
The factory function `get_strands_model` is the single entry point used
by the workflow — it reads the active provider from config and returns the
appropriate model without the caller needing to know which provider is active.

Adding a new provider:
  1. Add a new entry to the Provider enum in agent/config.py
  2. Add a branch in get_strands_model() below
  3. Add any required env vars to .env.example
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from agent.config import AgentConfig, Provider


# ---------------------------------------------------------------------------
# Abstract base — all provider builders must implement this interface
# ---------------------------------------------------------------------------

class BaseProviderBuilder(ABC):
    """
    Minimal interface for constructing a Strands-compatible model object.

    Implementing classes are not used directly — `get_strands_model` is the
    public API. This base class exists for type-safety and documentation.
    """

    def __init__(self, config: AgentConfig) -> None:
        self.config = config

    @abstractmethod
    def build(self) -> Any:
        """Return a configured Strands model instance."""
        ...


# ---------------------------------------------------------------------------
# Anthropic provider
# ---------------------------------------------------------------------------

class AnthropicProvider(BaseProviderBuilder):
    """
    Uses strands.models.BedrockModel or the native Anthropic model depending
    on what strands-agents exposes.

    For Phase 1 this wraps strands_agents with the Anthropic API key.
    """

    def build(self) -> Any:
        # Strands ships its own Anthropic integration.
        # Import here so the module is importable without strands installed.
        from strands.models.anthropic import AnthropicModel

        return AnthropicModel(
            client_args={"api_key": self.config.anthropic_api_key},
            model_id=self.config.anthropic_model,
        )


# ---------------------------------------------------------------------------
# OpenAI provider
# ---------------------------------------------------------------------------

class OpenAIProvider(BaseProviderBuilder):
    """Wraps the Strands OpenAI model with credentials from env vars."""

    def build(self) -> Any:
        from strands.models.openai import OpenAIModel

        return OpenAIModel(
            client_args={"api_key": self.config.openai_api_key},
            model_id=self.config.openai_model,
        )


# ---------------------------------------------------------------------------
# Ollama provider  (container-first — uses OLLAMA_BASE_URL)
# ---------------------------------------------------------------------------

class OllamaProvider(BaseProviderBuilder):
    """
    Points Strands at a running Ollama instance.

    The base URL defaults to http://ollama:11434 (Docker Compose service name).
    For native local execution, set OLLAMA_BASE_URL=http://localhost:11434.

    No API key is required for Ollama.
    """

    def build(self) -> Any:
        from strands.models.ollama import OllamaModel

        return OllamaModel(
            host=self.config.ollama_base_url,
            model_id=self.config.ollama_model,
        )


# ---------------------------------------------------------------------------
# Factory — the only function the workflow needs to call
# ---------------------------------------------------------------------------

_PROVIDER_MAP: dict[Provider, type[BaseProviderBuilder]] = {
    Provider.anthropic: AnthropicProvider,
    Provider.openai: OpenAIProvider,
    Provider.ollama: OllamaProvider,
}


def get_strands_model(config: AgentConfig) -> Any:
    """
    Return a configured Strands model object for the active provider.

    This is the single entry point used by workflow.py.
    Raises ValueError for unknown providers (should never happen after
    pydantic validation, but kept as a safety net).
    """
    builder_cls = _PROVIDER_MAP.get(config.default_provider)
    if builder_cls is None:
        raise ValueError(
            f"No provider builder registered for '{config.default_provider}'. "
            f"Known providers: {list(_PROVIDER_MAP)}"
        )
    return builder_cls(config).build()
