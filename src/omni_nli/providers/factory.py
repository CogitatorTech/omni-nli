import logging
from typing import Literal

from .base import NLIProvider
from .huggingface import get_huggingface_provider
from .ollama import get_ollama_provider
from .openrouter import get_openrouter_provider
from ..settings import settings

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
    huggingface_token_set = settings.huggingface_token is not None
    public_models_enabled = True

    return {
        "ollama": {
            "configured": True,
            "supports_reasoning": False,
            "host": settings.ollama_host,
            "default_model": settings.default_model,
        },
        "huggingface": {
            "configured": public_models_enabled or huggingface_token_set,
            "supports_reasoning": False,
            "token_configured": huggingface_token_set,
            "public_models_enabled": public_models_enabled,
            "cache_dir": settings.hf_cache_dir,
            "default_model": settings.default_model,
        },
        "openrouter": {
            "configured": settings.openrouter_api_key is not None,
            "supports_reasoning": True,
            "token_configured": settings.openrouter_api_key is not None,
            "default_model": settings.default_model,
        },
    }
