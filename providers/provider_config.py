"""
providers/provider_config.py — per-provider configuration documentation.

This module is intentionally lightweight. Its purpose is to document which
environment variables each provider requires and to provide a helper that
surfaces missing variables before a run fails deep inside the provider builder.

No secrets are stored here. All values come from AgentConfig (env vars).
"""

from __future__ import annotations

from dataclasses import dataclass

from agent.config import AgentConfig, Provider


@dataclass(frozen=True)
class ProviderRequirements:
    """Metadata about what a provider needs to run."""

    name: str
    required_env_vars: tuple[str, ...]
    optional_env_vars: tuple[str, ...]
    notes: str


PROVIDER_REQUIREMENTS: dict[Provider, ProviderRequirements] = {
    Provider.anthropic: ProviderRequirements(
        name="Anthropic",
        required_env_vars=("ANTHROPIC_API_KEY",),
        optional_env_vars=("ANTHROPIC_MODEL",),
        notes="Uses the Anthropic Messages API directly via strands-agents.",
    ),
    Provider.openai: ProviderRequirements(
        name="OpenAI",
        required_env_vars=("OPENAI_API_KEY",),
        optional_env_vars=("OPENAI_MODEL",),
        notes="Uses the OpenAI Chat Completions API via strands-agents.",
    ),
    Provider.ollama: ProviderRequirements(
        name="Ollama",
        required_env_vars=("OLLAMA_BASE_URL", "OLLAMA_MODEL"),
        optional_env_vars=(),
        notes=(
            "No API key required. "
            "Ollama must be running and accessible at OLLAMA_BASE_URL. "
            "Recommended: use Docker Compose (see compose.yaml). "
            "Pull the model first: docker compose exec ollama ollama pull <model>"
        ),
    ),
}


def check_provider_requirements(config: AgentConfig) -> list[str]:
    """
    Return a list of unmet requirements for the active provider.
    An empty list means all requirements are satisfied.
    """
    reqs = PROVIDER_REQUIREMENTS.get(config.default_provider)
    if reqs is None:
        return [f"Unknown provider: {config.default_provider}"]

    issues: list[str] = []

    for var in reqs.required_env_vars:
        value = getattr(config, var.lower(), None)
        if not value:
            issues.append(f"Missing required env var: {var}")

    return issues
