"""Base classes for NLI provider implementations.

This module defines the abstract base class and result model that all
NLI providers must implement, along with shared utility methods.
"""

import logging
from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, Field

from ..settings import settings

_logger = logging.getLogger(__name__)


class NLIResult(BaseModel):
    """Result of an NLI evaluation.

    Attributes:
        label: The predicted relationship (entailment/contradiction/neutral).
        confidence: Confidence score between 0 and 1.
        thinking_trace: Optional reasoning trace from extended thinking.
        model: The model that produced this result.
        backend: The backend provider that was used.
    """

    label: Literal["entailment", "contradiction", "neutral"] = Field(
        ..., description="The predicted NLI label."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score for the prediction (0-1)."
    )
    thinking_trace: str | None = Field(
        None, description="The reasoning trace from models that support extended thinking."
    )
    model: str = Field(..., description="The model that was used for evaluation.")
    backend: str = Field(..., description="The backend provider that was used.")


class NLIProvider(ABC):
    """Abstract base class for NLI providers.

    Subclasses must implement evaluate(), list_models(), and health_check().
    Common functionality like prompt building and response parsing is provided.

    Attributes:
        name: Provider identifier string.
        supports_reasoning: Whether the provider supports extended thinking.
    """

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
    ) -> NLIResult:
        """Evaluate the NLI relationship between premise and hypothesis.

        Args:
            premise: The base factual statement.
            hypothesis: The statement to test against the premise.
            context: Optional background context.
            model: Specific model to use (None for default).
            use_reasoning: Whether to use extended thinking.

        Returns:
            NLIResult with label, confidence, and optional reasoning.
        """
        ...

    @abstractmethod
    async def list_models(self) -> list[str]:
        """List available models for this provider.

        Returns:
            List of model identifiers.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available and functioning.

        Returns:
            True if provider is healthy, False otherwise.
        """
        ...

    def _build_nli_prompt(
        self,
        premise: str,
        hypothesis: str,
        context: str | None = None,
        use_reasoning: bool = False,
    ) -> str:
        """Build the NLI evaluation prompt.

        Args:
            premise: The base factual statement.
            hypothesis: The statement to test.
            context: Optional background context.
            use_reasoning: Whether to include reasoning instructions.

        Returns:
            Formatted prompt string for the LLM.
        """
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
        """Parse the LLM response into an NLIResult.

        Handles extraction of thinking traces from <think> tags or pre-JSON text.

        Args:
            response_text: Raw response from the LLM.
            model: The model that produced the response.

        Returns:
            Parsed NLIResult with label, confidence, and optional trace.

        Raises:
            ValueError: If response cannot be parsed as valid NLI result.
        """
        import re

        thinking_trace = None

        # First, try to extract thinking from <think> tags
        think_match = re.search(r"<think>(.*?)</think>", response_text, re.DOTALL)
        if think_match:
            thinking_trace = think_match.group(1).strip()

        # Try to find a JSON block
        json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)

        # If no <think> tags found, capture pre-JSON text as reasoning
        if thinking_trace is None and json_match:
            pre_json_text = response_text[: json_match.start()].strip()
            if pre_json_text:
                thinking_trace = pre_json_text

        # If still no thinking trace, try to capture text before raw JSON
        if thinking_trace is None:
            # Look for text before a JSON object starts
            json_start = re.search(r"[\{\[]", response_text)
            if json_start and json_start.start() > 10:  # At least some text before JSON
                pre_json_text = response_text[: json_start.start()].strip()
                if pre_json_text:
                    thinking_trace = pre_json_text

        if not settings.return_thinking_trace:
            thinking_trace = None

        text_to_parse = json_match.group(1) if json_match else response_text

        # Use json_repair to parse and fix the JSON
        try:
            from json_repair import repair_json

            # First attempt: let json_repair find objects (return_objects=True)
            # We pass the text because json_repair is good at finding JSON in text
            result_data = repair_json(text_to_parse, return_objects=True)

            # If it returns a list, try to find the relevant object
            if isinstance(result_data, list):
                for item in result_data:
                    if isinstance(item, dict) and "label" in item:
                        result_data = item
                        break
                else:
                    # Fallback if no valid object found in list
                    if result_data and isinstance(result_data[0], dict):
                        result_data = result_data[0]
                    else:
                        pass

            if not isinstance(result_data, dict):
                raise ValueError("Parsed result is not a dictionary")

        except Exception as e:
            raise ValueError(
                f"Failed to parse JSON response: {e}. content: {response_text[:200]}..."
            ) from e

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
