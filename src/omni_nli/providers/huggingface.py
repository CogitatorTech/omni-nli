import logging
from typing import Any

from async_lru import alru_cache
from transformers import pipeline

from ..settings import settings
from .base import NLIProvider, NLIResult, TokenUsage

_logger = logging.getLogger(__name__)

DEFAULT_HF_MODELS = [
    "Qwen/Qwen2.5-1.5B-Instruct",
    "meta-llama/Llama-3.2-3B-Instruct",
]


class HuggingFaceProvider(NLIProvider):
    name = "huggingface"
    supports_reasoning = False

    def __init__(self, token: str | None = None, cache_dir: str | None = None) -> None:
        self.token = token or settings.huggingface_token
        self.cache_dir = cache_dir or settings.hf_cache_dir
        self._pipelines: dict[str, Any] = {}

    def _get_pipeline(self, model_id: str) -> Any:  # noqa: ANN401
        if model_id in self._pipelines:
            return self._pipelines[model_id]

        _logger.info(f"Loading local model: {model_id} (this may take a while)...")

        try:
            pipe = pipeline(
                "text-generation",
                model=model_id,
                token=self.token,
                model_kwargs={"cache_dir": self.cache_dir},
                device_map="auto",
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
            if "/" in settings.default_model:
                model = settings.default_model
            else:
                model = DEFAULT_HF_MODELS[0]

        pipe = self._get_pipeline(model)

        prompt = self._build_nli_prompt(premise, hypothesis, context=context, use_reasoning=False)

        if pipe.tokenizer.chat_template:
            messages = [{"role": "user", "content": prompt}]
            prompt_formatted = pipe.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        else:
            prompt_formatted = prompt

        _logger.debug(f"Running inference on {model}...")

        outputs = pipe(
            prompt_formatted,
            max_new_tokens=256,
            temperature=0.1,
            return_full_text=False,
            do_sample=False,
        )

        response_text = outputs[0]["generated_text"]
        _logger.debug(f"Local model response: {response_text[:200]}...")

        result = self._parse_nli_response(response_text, model)

        prompt_tokens = len(pipe.tokenizer.encode(prompt_formatted))
        completion_tokens = len(pipe.tokenizer.encode(response_text))
        result.usage = TokenUsage(
            total_tokens=prompt_tokens + completion_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        return result

    async def list_models(self) -> list[str]:
        return DEFAULT_HF_MODELS.copy()

    async def health_check(self) -> bool:
        try:
            from transformers import is_torch_available

            return is_torch_available()
        except ImportError:
            return False


@alru_cache(maxsize=settings.provider_cache_size)
async def get_huggingface_provider(token: str | None = None) -> HuggingFaceProvider:
    return HuggingFaceProvider(token=token)
