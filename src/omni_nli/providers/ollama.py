import logging

import ollama
from async_lru import alru_cache

from .base import NLIProvider, NLIResult
from ..settings import settings

_logger = logging.getLogger(__name__)


class OllamaProvider(NLIProvider):
    name = "ollama"
    supports_reasoning = True

    def __init__(self, host: str | None = None) -> None:
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
        try:
            models = await self._client.list()
            return [m["name"] for m in models.get("models", [])]
        except Exception as e:
            _logger.warning(f"Failed to list Ollama models: {e}")
            return []

    async def health_check(self) -> bool:
        try:
            await self._client.list()
            return True
        except Exception as e:
            _logger.warning(f"Ollama health check failed: {e}")
            return False


@alru_cache(maxsize=settings.provider_cache_size)
async def get_ollama_provider(host: str | None = None) -> OllamaProvider:
    return OllamaProvider(host=host)
