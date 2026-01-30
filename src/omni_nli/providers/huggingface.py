"""HuggingFace Transformers provider for local NLI evaluation.

This module provides NLI evaluation using locally-loaded HuggingFace
transformer models.

Note: Requires optional dependencies. Install with: pip install omni-nli[huggingface]
"""

import asyncio
import functools
import logging
from typing import Any

from async_lru import alru_cache

from ..settings import settings
from .base import NLIProvider, NLIResult

_logger = logging.getLogger(__name__)

# Check if HuggingFace dependencies are available
_HF_AVAILABLE = False
try:
    from transformers import pipeline  # noqa: F401

    _HF_AVAILABLE = True
except ImportError:
    _logger.debug(
        "HuggingFace transformers not installed. Install with: pip install omni-nli[huggingface]"
    )

DEFAULT_HF_MODELS = [
    "Qwen/Qwen2.5-1.5B-Instruct",
    "meta-llama/Llama-3.2-3B-Instruct",
]


class HuggingFaceProvider(NLIProvider):
    """NLI provider using HuggingFace Transformers for local inference.

    Loads models locally and runs text generation pipelines for NLI tasks.
    Supports extended thinking/reasoning with configurable token limits.

    Attributes:
        name: Provider identifier ('huggingface').
        supports_reasoning: Always True for this provider.
    """

    name = "huggingface"
    supports_reasoning = True

    def __init__(self, token: str | None = None, cache_dir: str | None = None) -> None:
        """Initialize the HuggingFace provider.

        Args:
            token: HuggingFace API token for gated models.
            cache_dir: Directory for caching downloaded models.
        """
        self.token = token or settings.huggingface_token
        self.cache_dir = cache_dir or settings.hf_cache_dir_effective
        self._pipelines: dict[str, Any] = {}

    async def _get_pipeline(self, model_id: str) -> Any:  # noqa: ANN401
        """Get or create a text generation pipeline for a model.

        Args:
            model_id: The HuggingFace model identifier.

        Returns:
            A transformers pipeline ready for inference.

        Raises:
            ValueError: If the model cannot be loaded.
        """
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
        """Evaluate NLI using a local HuggingFace model.

        Args:
            premise: The base factual statement.
            hypothesis: The statement to test against the premise.
            context: Optional background context.
            model: Model to use (defaults to configured default).
            use_reasoning: Whether to use extended thinking.

        Returns:
            NLIResult with label, confidence, and optional reasoning.
        """
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
        truncated = len(response_text) > 200
        _logger.debug(f"Local model response: {response_text[:200]}{'...' if truncated else ''}")

        result = self._parse_nli_response(response_text, model)

        # Token usage tracking removed by user request

        return result

    async def list_models(self) -> list[str]:
        """List available HuggingFace models.

        Returns:
            List of curated model identifiers plus the configured default.
        """
        # Provide a small curated list plus the configured default.
        models = DEFAULT_HF_MODELS.copy()
        default_model = settings.get_default_model(self.name)
        if default_model not in models:
            models.insert(0, default_model)
        return models

    async def health_check(self) -> bool:
        """Check if PyTorch is available for local inference.

        Returns:
            True if PyTorch is available, False otherwise.
        """
        try:
            from transformers import is_torch_available

            return is_torch_available()
        except ImportError:
            return False


@alru_cache(maxsize=settings.provider_cache_size)
async def get_huggingface_provider(token: str | None = None) -> HuggingFaceProvider:
    """Get a cached HuggingFace provider instance.

    Args:
        token: Optional HuggingFace API token.

    Returns:
        HuggingFaceProvider instance.
    """
    return HuggingFaceProvider(token=token)
