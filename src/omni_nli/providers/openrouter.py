import logging

from async_lru import alru_cache
from openai import AsyncOpenAI

from ..settings import settings
from .base import NLIProvider, NLIResult, TokenUsage

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
    name = "openrouter"
    supports_reasoning = True

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.openrouter_api_key
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
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
        client = self._get_client()

        if model is None:
            model = settings.default_model

        prompt = self._build_nli_prompt(
            premise, hypothesis, context=context, use_reasoning=use_reasoning
        )

        _logger.debug(f"Calling OpenRouter model {model} (reasoning={use_reasoning})")

        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1 if not use_reasoning else 0.3,
            max_tokens=settings.max_thinking_tokens if use_reasoning else 512,
        )

        response_text = response.choices[0].message.content or ""
        _logger.debug(f"OpenRouter response: {response_text[:200]}...")

        result = self._parse_nli_response(response_text, model)

        if response.usage:
            thinking_tokens = 0
            if result.thinking_trace:
                thinking_tokens = len(result.thinking_trace.split()) * 1.3

            result.usage = TokenUsage(
                total_tokens=response.usage.total_tokens,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                thinking_tokens=int(thinking_tokens),
            )

        return result

    async def list_models(self) -> list[str]:
        return REASONING_MODELS + STANDARD_MODELS

    async def health_check(self) -> bool:
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
    return OpenRouterProvider(api_key=api_key)
