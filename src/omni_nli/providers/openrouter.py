import logging

from async_lru import alru_cache
from openai import AsyncOpenAI

from .base import NLIProvider, NLIResult
from ..settings import settings

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
