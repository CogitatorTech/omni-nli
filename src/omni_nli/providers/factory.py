"""Factory functions for creating and managing NLI providers.

This module provides the main entry points for obtaining provider instances
and listing available provider configurations.
"""

import logging
from typing import Literal, cast

from ..settings import settings
from .base import NLIProvider
from .huggingface import get_huggingface_provider
from .ollama import get_ollama_provider
from .openrouter import get_openrouter_provider

_logger = logging.getLogger(__name__)

BackendType = Literal["ollama", "huggingface", "openrouter"]


async def get_provider(backend: BackendType | None = None) -> NLIProvider:
    """Get an NLI provider instance for the specified backend.

    Args:
        backend: The backend to use ('ollama', 'huggingface', 'openrouter').
                 If None, uses the configured default backend.

    Returns:
        An NLIProvider instance ready for evaluation.

    Raises:
        ValueError: If the backend is unknown or unavailable.
    """
    if backend is None:
        backend = cast(BackendType, settings.default_backend)

    _logger.debug(f"Getting provider: backend={backend}")

    if backend == "ollama":
        provider = await get_ollama_provider()
        if not await provider.health_check():
            _logger.warning("Ollama not available, trying fallback providers")
            return await _get_fallback_provider()
        return provider

    elif backend == "huggingface":
        from .huggingface import _HF_AVAILABLE

        if not _HF_AVAILABLE:
            raise ValueError(
                "HuggingFace backend requires optional dependencies. "
                "Install with: pip install omni-nli[huggingface]"
            )
        return await get_huggingface_provider()

    elif backend == "openrouter":
        if not settings.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured")
        return await get_openrouter_provider()

    else:
        raise ValueError(f"Unknown backend: {backend}")


async def _get_fallback_provider() -> NLIProvider:
    """Try to get an alternative provider when the primary is unavailable.

    Returns:
        The first healthy fallback provider found.

    Raises:
        ValueError: If no fallback providers are available.
    """
    fallback_order: list[BackendType] = ["huggingface", "openrouter"]

    for fallback_backend in fallback_order:
        try:
            provider = await get_provider(fallback_backend)
            if await provider.health_check():
                return provider
        except ValueError:
            continue

    raise ValueError("No NLI providers available. Configure at least one backend.")


def list_available_providers() -> dict[str, dict]:
    """List all available providers with their configuration status.

    Returns:
        Dictionary mapping provider names to their config info.
    """
    huggingface_token_set = settings.huggingface_token is not None

    return {
        "ollama": {
            "host": settings.ollama_host,
            "default_model": settings.get_default_model("ollama"),
        },
        "huggingface": {
            "token_configured": huggingface_token_set,
            "cache_dir": settings.hf_cache_dir_effective,
            "default_model": settings.get_default_model("huggingface"),
        },
        "openrouter": {
            "token_configured": settings.openrouter_api_key is not None,
            "default_model": settings.get_default_model("openrouter"),
        },
    }
