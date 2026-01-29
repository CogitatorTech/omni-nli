"""OpenRouter API provider for cloud-based NLI evaluation.

This module provides NLI evaluation using OpenRouter's unified API,
which provides access to various LLM providers including OpenAI,
Anthropic, and Google models.
"""

import logging

from async_lru import alru_cache
from openai import AsyncOpenAI

from ..settings import settings
from .base import NLIProvider, NLIResult

_logger = logging.getLogger(__name__)

REASONING_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3.7-sonnet",
    "deepseek/deepseek-r1",
    "openai/o3-mini",
    "google/gemini-2.0-flash-thinking-exp:free",
]

STANDARD_MODELS = [
    "anthropic/claude-3.5-haiku",
    "openai/gpt-4o-mini",
    "google/gemini-2.0-flash-001",
]


class OpenRouterProvider(NLIProvider):
    """NLI provider using OpenRouter's unified LLM API.

    Provides access to multiple LLM providers through a single API,
    supporting models from OpenAI, Anthropic, Google, and others.

    Attributes:
        name: Provider identifier ('openrouter').
        supports_reasoning: Always True for this provider.
    """

    name = "openrouter"
    supports_reasoning = True

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the OpenRouter provider.

        Args:
            api_key: OpenRouter API key (defaults to configured key).
        """
        self.api_key = api_key or settings.openrouter_api_key
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        """Get or create the OpenAI-compatible client.

        Returns:
            AsyncOpenAI client configured for OpenRouter.

        Raises:
            ValueError: If API key is not configured.
        """
        if self._client is None:
            if not self.api_key:
                raise ValueError("OpenRouter API key not configured")
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1",
            )
        return self._client

    async def evaluate(
        self,
        premise: str,
        hypothesis: str,
        context: str | None = None,
        model: str | None = None,
        use_reasoning: bool = False,
    ) -> NLIResult:
        """Evaluate NLI using an OpenRouter model.

        Args:
            premise: The base factual statement.
            hypothesis: The statement to test against the premise.
            context: Optional background context.
            model: Model to use (defaults to configured default).
            use_reasoning: Whether to use extended thinking.

        Returns:
            NLIResult with label, confidence, and optional reasoning.
        """
        client = self._get_client()

        if model is None:
            model = settings.get_default_model(self.name)

        prompt = self._build_nli_prompt(
            premise, hypothesis, context=context, use_reasoning=use_reasoning
        )

        _logger.debug(f"Calling OpenRouter model {model} (reasoning={use_reasoning})")

        messages = [{"role": "user", "content": prompt}]  # type: ignore[var-annotated]

        response = await client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            temperature=0.1 if not use_reasoning else 0.3,
            max_tokens=settings.max_thinking_tokens if use_reasoning else 512,
        )

        response_text = response.choices[0].message.content or ""
        _logger.debug(f"OpenRouter response: {response_text[:200]}...")

        result = self._parse_nli_response(response_text, model)

        if response.usage:
            pass  # Token usage tracking removed by user request

        return result

    async def list_models(self) -> list[str]:
        """List available OpenRouter models.

        Returns:
            Combined list of reasoning and standard models.
        """
        return REASONING_MODELS + STANDARD_MODELS

    async def health_check(self) -> bool:
        """Check if OpenRouter API is accessible.

        Returns:
            True if API key is set and API responds, False otherwise.
        """
        if not self.api_key:
            return False

        try:
            client = self._get_client()
            await client.models.list()
            return True
        except Exception as e:
            _logger.warning(f"OpenRouter health check failed: {e}")
            return False


@alru_cache(maxsize=settings.provider_cache_size)
async def get_openrouter_provider(api_key: str | None = None) -> OpenRouterProvider:
    """Get a cached OpenRouter provider instance.

    Args:
        api_key: Optional OpenRouter API key.

    Returns:
        OpenRouterProvider instance.
    """
    return OpenRouterProvider(api_key=api_key)
