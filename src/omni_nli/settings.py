"""Server settings and configuration management for Omni-NLI.

This module provides centralized configuration using Pydantic settings,
supporting both environment variables and .env files.
"""

from importlib.metadata import PackageNotFoundError, version

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_pkg_version() -> str:
    """Get the installed package version.

    Returns:
        The package version string, or '0.0.0' if not installed.
    """
    try:
        return version("omni-nli")
    except PackageNotFoundError:
        return "0.0.0"


def get_default_hf_cache_dir() -> str:
    """Return the default Hugging Face cache directory (OS-agnostic).

    We delegate to the official Hugging Face implementation, so it respects:
    - HF_HOME / TRANSFORMERS_CACHE / HF_HUB_CACHE env vars
    - platform defaults (like `~/.cache/huggingface` on Linux)
    """

    # Import lazily so importing settings doesn't hard-require transformers.
    try:
        from huggingface_hub.constants import HF_HUB_CACHE

        return str(HF_HUB_CACHE)
    except Exception:
        # Best-effort fallback: matches the typical default on Unix.
        import os

        return os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")


def _normalize_optional_str(v: str | None) -> str | None:
    """Treat empty/whitespace strings as None (common with .env vars like FOO=)."""

    if v is None:
        return None
    v2 = v.strip()
    return v2 or None


class ServerSettings(BaseSettings):
    """Application settings with environment variable and .env support.

    All settings can be configured via environment variables or a .env file.
    Environment variables take precedence over .env file values.

    Attributes:
        pkg_version: Current package version.
        host: Server bind address.
        port: Server bind port.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
        debug: Enable debug mode for detailed tracebacks.
        ollama_host: Ollama server URL.
        huggingface_token: HuggingFace API token for gated models.
        hf_cache_dir: HuggingFace model cache directory.
        openrouter_api_key: OpenRouter API key.
        default_backend: Default NLI backend provider.
        max_thinking_tokens: Maximum tokens for reasoning traces.
        return_thinking_trace: Whether to include reasoning in responses.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    pkg_version: str = get_pkg_version()
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    debug: bool = False

    ollama_host: str = "http://localhost:11434"
    huggingface_token: str | None = None

    # Optional but should default to Hugging Face's standard cache location when unset.
    hf_cache_dir: str | None = None

    openrouter_api_key: str | None = None

    default_backend: str = "huggingface"

    # Provider-specific defaults
    ollama_default_model: str = "qwen3:8b"
    huggingface_default_model: str = "microsoft/Phi-3.5-mini-instruct"
    openrouter_default_model: str = "openai/gpt-5-mini"

    max_thinking_tokens: int = 4096

    return_thinking_trace: bool = False

    provider_cache_size: int = 8

    @field_validator("huggingface_token", "openrouter_api_key", mode="before")
    @classmethod
    def normalize_empty_token(cls, v: str | None) -> str | None:
        """Treat empty/whitespace strings as None (common with .env vars like FOO=)."""
        if v is None:
            return None
        v2 = v.strip()
        return v2 or None

    def get_default_model(self, backend: str) -> str:
        """Get the default model for a given backend.

        Args:
            backend: The backend name ('ollama', 'huggingface', 'openrouter').

        Returns:
            The default model name for the specified backend.

        Raises:
            ValueError: If the backend is unknown.
        """
        if backend == "ollama":
            return self.ollama_default_model
        if backend == "huggingface":
            return self.huggingface_default_model
        if backend == "openrouter":
            return self.openrouter_default_model
        raise ValueError(f"Unknown backend: {backend}")

    @property
    def hf_cache_dir_effective(self) -> str:
        """Get the effective HuggingFace cache directory.

        Returns:
            The configured cache dir, or the platform default if not set.
        """
        # If user set HF_CACHE_DIR to an empty string, it is treated as unset.
        return _normalize_optional_str(self.hf_cache_dir) or get_default_hf_cache_dir()


settings = ServerSettings()
