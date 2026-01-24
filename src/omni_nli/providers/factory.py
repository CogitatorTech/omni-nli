import logging
from typing import Literal

from ..settings import settings
from .base import NLIProvider
from .huggingface import get_huggingface_provider
from .ollama import get_ollama_provider
from .openrouter import get_openrouter_provider

_logger = logging.getLogger(__name__)

BackendType = Literal["ollama", "huggingface", "openrouter"]


async def get_provider(backend: BackendType | None = None) -> NLIProvider:
    if backend is None:
        backend = settings.default_backend

    _logger.debug(f"Getting provider: backend={backend}")

    if backend == "ollama":
        provider = await get_ollama_provider()
        if not await provider.health_check():
            _logger.warning("Ollama not available, trying fallback providers")
            return await _get_fallback_provider()
        return provider

    elif backend == "huggingface":
        return await get_huggingface_provider()

    elif backend == "openrouter":
        if not settings.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured")
        return await get_openrouter_provider()

    else:
        raise ValueError(f"Unknown backend: {backend}")


async def _get_fallback_provider() -> NLIProvider:
    fallback_order = ["huggingface", "openrouter"]

    for backend in fallback_order:
        try:
            provider = await get_provider(backend)
            if await provider.health_check():
                return provider
        except ValueError:
            continue

    raise ValueError("No NLI providers available. Configure at least one backend.")


def list_available_providers() -> dict[str, dict]:
    return {
        "ollama": {
            "configured": True,
            "supports_reasoning": False,
        },
        "huggingface": {
            "configured": True,
            "supports_reasoning": False,
        },
        "openrouter": {
            "configured": settings.openrouter_api_key is not None,
            "supports_reasoning": True,
        },
    }
