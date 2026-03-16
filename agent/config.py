"""
agent/config.py — environment-driven configuration with validation.

All runtime settings come from environment variables.
No secrets are ever hardcoded here.
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Provider(str, Enum):
    anthropic = "anthropic"
    openai = "openai"
    ollama = "ollama"


class AgentRuntime(str, Enum):
    local = "local"
    docker = "docker"
    kubernetes = "kubernetes"


class AgentConfig(BaseSettings):
    """
    Single source of truth for all runtime configuration.

    Values are read from environment variables (or a .env file if present).
    Required fields that are missing will raise a clear ValidationError at
    startup — never silently at use time.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Provider selection
    # ------------------------------------------------------------------
    default_provider: Provider = Field(
        default=Provider.anthropic,
        description="Active provider: anthropic | openai | ollama",
    )

    # ------------------------------------------------------------------
    # Anthropic
    # ------------------------------------------------------------------
    anthropic_api_key: Optional[str] = Field(default=None, repr=False)
    anthropic_model: str = Field(default="claude-sonnet-4-6")

    # ------------------------------------------------------------------
    # OpenAI
    # ------------------------------------------------------------------
    openai_api_key: Optional[str] = Field(default=None, repr=False)
    openai_model: str = Field(default="gpt-4o")

    # ------------------------------------------------------------------
    # Ollama  (container-friendly defaults)
    # ------------------------------------------------------------------
    ollama_base_url: str = Field(default="http://ollama:11434")
    ollama_model: str = Field(default="llama3")

    # ------------------------------------------------------------------
    # Runtime behaviour
    # ------------------------------------------------------------------
    agent_runtime: AgentRuntime = Field(default=AgentRuntime.local)
    log_level: str = Field(default="INFO")
    max_iterations: int = Field(default=10, ge=1, le=100)
    results_dir: str = Field(default="eval/results")
    sample_repo_path: str = Field(default="./sample_repos")

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"LOG_LEVEL must be one of {valid}, got '{v}'")
        return upper

    @model_validator(mode="after")
    def validate_provider_credentials(self) -> "AgentConfig":
        """Fail fast with a clear message if the selected provider has no credentials."""
        provider = self.default_provider

        if provider == Provider.anthropic and not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when DEFAULT_PROVIDER=anthropic. "
                "Set it in your .env file or environment."
            )

        if provider == Provider.openai and not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when DEFAULT_PROVIDER=openai. "
                "Set it in your .env file or environment."
            )

        # Ollama requires no API key, but we warn if the URL looks wrong
        if provider == Provider.ollama and not self.ollama_base_url:
            raise ValueError(
                "OLLAMA_BASE_URL must be set when DEFAULT_PROVIDER=ollama. "
                "Typical value: http://ollama:11434 (Docker) or http://localhost:11434 (native)."
            )

        return self

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def active_model(self) -> str:
        """Return the model ID for the currently selected provider."""
        return {
            Provider.anthropic: self.anthropic_model,
            Provider.openai: self.openai_model,
            Provider.ollama: self.ollama_model,
        }[self.default_provider]

    def doctor_report(self) -> dict[str, str]:
        """Return a human-readable health summary (no secret values)."""
        return {
            "default_provider": self.default_provider.value,
            "active_model": self.active_model(),
            "anthropic_api_key": "set" if self.anthropic_api_key else "NOT SET",
            "openai_api_key": "set" if self.openai_api_key else "NOT SET",
            "ollama_base_url": self.ollama_base_url,
            "ollama_model": self.ollama_model,
            "agent_runtime": self.agent_runtime.value,
            "log_level": self.log_level,
            "max_iterations": str(self.max_iterations),
            "results_dir": self.results_dir,
        }


def load_config() -> AgentConfig:
    """Load and validate config from the environment. Call once at startup."""
    return AgentConfig()
