import logging
from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, Field

_logger = logging.getLogger(__name__)


class TokenUsage(BaseModel):
    total_tokens: int = Field(0, description="Total tokens used in the request and response.")
    thinking_tokens: int = Field(0, description="Tokens used in the thinking/reasoning trace.")
    prompt_tokens: int = Field(0, description="Tokens used in the prompt.")
    completion_tokens: int = Field(0, description="Tokens used in the completion.")


class NLIResult(BaseModel):
    label: Literal["entailment", "contradiction", "neutral"] = Field(
        ..., description="The predicted NLI label."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score for the prediction (0-1)."
    )
    thinking_trace: str | None = Field(
        None, description="The reasoning trace from models that support extended thinking."
    )
    usage: TokenUsage = Field(default_factory=TokenUsage, description="Token usage statistics.")
    model: str = Field(..., description="The model that was used for evaluation.")
    backend: str = Field(..., description="The backend provider that was used.")


class NLIProvider(ABC):
    name: str = "base"
    supports_reasoning: bool = False

    @abstractmethod
    async def evaluate(
        self,
        premise: str,
        hypothesis: str,
        context: str | None = None,
        model: str | None = None,
        use_reasoning: bool = False,
    ) -> NLIResult: ...

    @abstractmethod
    async def list_models(self) -> list[str]: ...

    @abstractmethod
    async def health_check(self) -> bool: ...

    def _build_nli_prompt(
        self,
        premise: str,
        hypothesis: str,
        context: str | None = None,
        use_reasoning: bool = False,
    ) -> str:
        reasoning_instruction = ""
        if use_reasoning:
            reasoning_instruction = """
First, think through your reasoning step by step in <think> tags.
Analyze the logical relationship between the statements carefully.
Then provide your final answer."""

        context_section = ""
        if context:
            context_section = f"\n**Context**: {context}\n"

        return f"""You are an expert in natural language inference (NLI).
Your task is to determine the logical relationship between a premise and a hypothesis.

The possible relationships are:
- **entailment**: The hypothesis logically follows from the premise.
- **contradiction**: The hypothesis is logically incompatible with the premise.
- **neutral**: The hypothesis is neither entailed nor contradicted by the premise.
{reasoning_instruction}
{context_section}
**Premise**: {premise}

**Hypothesis**: {hypothesis}

Respond with ONLY a JSON object in this exact format:
{{"label": "<entailment|contradiction|neutral>", "confidence": <0.0-1.0>}}"""

    def _parse_nli_response(self, response_text: str, model: str) -> NLIResult:
        import json
        import re

        thinking_trace = None
        think_match = re.search(r"<think>(.*?)</think>", response_text, re.DOTALL)
        if think_match:
            thinking_trace = think_match.group(1).strip()

        json_match = re.search(r"\{[^{}]*\}", response_text)
        if not json_match:
            raise ValueError(f"Could not find JSON in response: {response_text[:200]}")

        try:
            result_data = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in response: {e}") from e

        label = result_data.get("label", "").lower().strip()
        if label not in ("entailment", "contradiction", "neutral"):
            raise ValueError(f"Invalid label: {label}")

        confidence = float(result_data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        return NLIResult(
            label=label,
            confidence=confidence,
            thinking_trace=thinking_trace,
            model=model,
            backend=self.name,
        )
