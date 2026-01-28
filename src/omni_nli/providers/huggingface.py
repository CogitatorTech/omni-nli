import asyncio
import functools
import logging
from typing import Any

from async_lru import alru_cache
from transformers import pipeline

from .base import NLIProvider, NLIResult
from ..settings import settings

_logger = logging.getLogger(__name__)

DEFAULT_HF_MODELS = [
    "Qwen/Qwen2.5-1.5B-Instruct",
    "meta-llama/Llama-3.2-3B-Instruct",
]


class HuggingFaceProvider(NLIProvider):
    name = "huggingface"
    supports_reasoning = True

    def __init__(self, token: str | None = None, cache_dir: str | None = None) -> None:
        self.token = token or settings.huggingface_token
        self.cache_dir = cache_dir or settings.hf_cache_dir_effective
        self._pipelines: dict[str, Any] = {}

    async def _get_pipeline(self, model_id: str) -> Any:  # noqa: ANN401
        if model_id in self._pipelines:
            return self._pipelines[model_id]

        _logger.info(f"Loading local model: {model_id} (this may take a while)...")

        try:
            # Run model loading in a separate thread to avoid blocking the event loop
            pipe = await asyncio.to_thread(
                functools.partial(
                    pipeline,
                    "text-generation",
                    model=model_id,
                    token=self.token,
                    model_kwargs={"cache_dir": self.cache_dir},
                    device_map="auto",
                )
            )
            self._pipelines[model_id] = pipe
            return pipe
        except Exception as e:
            _logger.error(f"Failed to load model {model_id}: {e}")
            raise ValueError(f"Could not load model {model_id}. Check internet/disk.") from e

    async def evaluate(
        self,
        premise: str,
        hypothesis: str,
        context: str | None = None,
        model: str | None = None,
        use_reasoning: bool = False,
    ) -> NLIResult:
        if model is None:
            model = settings.get_default_model(self.name)

        pipe = await self._get_pipeline(model)

        prompt = self._build_nli_prompt(
            premise,
            hypothesis,
            context=context,
            use_reasoning=use_reasoning,
        )

        if pipe.tokenizer.chat_template:
            messages = [{"role": "user", "content": prompt}]
            prompt_formatted = pipe.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        else:
            prompt_formatted = prompt

        _logger.debug(f"Running inference on {model} (reasoning={use_reasoning})...")

        # Run inference in a separate thread
        outputs = await asyncio.to_thread(
            functools.partial(
                pipe,
                prompt_formatted,
                max_new_tokens=settings.max_thinking_tokens if use_reasoning else 256,
                temperature=0.3 if use_reasoning else 0.1,
                return_full_text=False,
                do_sample=use_reasoning,
            )
        )

        response_text = outputs[0]["generated_text"]
        _logger.debug(f"Local model response: {response_text[:200]}...")

        result = self._parse_nli_response(response_text, model)

        # Token usage tracking removed by user request

        return result

    async def list_models(self) -> list[str]:
        # Provide a small curated list plus the configured default.
        models = DEFAULT_HF_MODELS.copy()
        default_model = settings.get_default_model(self.name)
        if default_model not in models:
            models.insert(0, default_model)
        return models

    async def health_check(self) -> bool:
        try:
            from transformers import is_torch_available

            return is_torch_available()
        except ImportError:
            return False


@alru_cache(maxsize=settings.provider_cache_size)
async def get_huggingface_provider(token: str | None = None) -> HuggingFaceProvider:
    return HuggingFaceProvider(token=token)
