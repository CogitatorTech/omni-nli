"""Ollama provider for local LLM-based NLI evaluation.

This module provides NLI evaluation using an Ollama server running
locally or on a network, supporting various open-source models.
"""

import logging

import ollama
from async_lru import alru_cache

from ..settings import settings
from .base import NLIProvider, NLIResult

_logger = logging.getLogger(__name__)


class OllamaProvider(NLIProvider):
    """NLI provider using Ollama for local LLM inference.

    Connects to an Ollama server and uses available models for NLI tasks.
    Supports extended thinking/reasoning for compatible models.

    Attributes:
        name: Provider identifier ('ollama').
        supports_reasoning: Always True for this provider.
    """

    name = "ollama"
    supports_reasoning = True

    def __init__(self, host: str | None = None) -> None:
        """Initialize the Ollama provider.

        Args:
            host: Ollama server URL (defaults to configured host).
        """
        self.host = host or settings.ollama_host
        self._client = ollama.AsyncClient(host=self.host)

    async def evaluate(
        self,
        premise: str,
        hypothesis: str,
        context: str | None = None,
        model: str | None = None,
        use_reasoning: bool = False,
    ) -> NLIResult:
        """Evaluate NLI using an Ollama model.

        Args:
            premise: The base factual statement.
            hypothesis: The statement to test against the premise.
            context: Optional background context.
            model: Model to use (defaults to configured default).
            use_reasoning: Whether to use extended thinking.

        Returns:
            NLIResult with label, confidence, and optional reasoning.

        Raises:
            ollama.ResponseError: If the Ollama API returns an error.
        """
        model = model or settings.get_default_model(self.name)
        prompt = self._build_nli_prompt(
            premise,
            hypothesis,
            context=context,
            use_reasoning=use_reasoning,
        )

        _logger.debug(f"Calling Ollama model {model} (reasoning={use_reasoning})")

        try:
            response = await self._client.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1 if not use_reasoning else 0.3},
            )
        except ollama.ResponseError as e:
            _logger.error(f"Ollama error: {e}")
            raise

        response_text = response["message"]["content"]
        _logger.debug(f"Ollama response: {response_text[:200]}...")

        result = self._parse_nli_response(response_text, model)

        if "eval_count" in response:
            pass  # Token usage tracking removed by user request

        return result

    async def list_models(self) -> list[str]:
        """List models available on the Ollama server.

        Returns:
            List of model names, or empty list if unavailable.
        """
        try:
            models = await self._client.list()
            return [m["name"] for m in models.get("models", [])]
        except Exception as e:
            _logger.warning(f"Failed to list Ollama models: {e}")
            return []

    async def health_check(self) -> bool:
        """Check if the Ollama server is reachable.

        Returns:
            True if server responds, False otherwise.
        """
        try:
            await self._client.list()
            return True
        except Exception as e:
            _logger.warning(f"Ollama health check failed: {e}")
            return False


@alru_cache(maxsize=settings.provider_cache_size)
async def get_ollama_provider(host: str | None = None) -> OllamaProvider:
    """Get a cached Ollama provider instance.

    Args:
        host: Optional Ollama server URL.

    Returns:
        OllamaProvider instance.
    """
    return OllamaProvider(host=host)
