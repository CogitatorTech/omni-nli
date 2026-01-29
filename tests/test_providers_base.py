"""Tests for the NLI provider base class and response parsing."""

import pytest

from omni_nli.providers.base import NLIProvider, NLIResult


class ConcreteProvider(NLIProvider):
    """Concrete implementation for testing abstract base class."""

    name = "test"
    supports_reasoning = True

    async def evaluate(self, premise, hypothesis, context=None, model=None, use_reasoning=False):
        pass

    async def list_models(self):
        return ["test-model"]

    async def health_check(self):
        return True


class TestNLIResult:
    """Tests for the NLIResult model."""

    def test_valid_entailment_result(self):
        result = NLIResult(
            label="entailment",
            confidence=0.95,
            thinking_trace=None,
            model="test-model",
            backend="test",
        )
        assert result.label == "entailment"
        assert result.confidence == 0.95

    def test_valid_contradiction_result(self):
        result = NLIResult(
            label="contradiction",
            confidence=0.8,
            thinking_trace="Some reasoning",
            model="test-model",
            backend="test",
        )
        assert result.label == "contradiction"
        assert result.thinking_trace == "Some reasoning"

    def test_valid_neutral_result(self):
        result = NLIResult(
            label="neutral",
            confidence=0.5,
            thinking_trace=None,
            model="test-model",
            backend="test",
        )
        assert result.label == "neutral"

    def test_confidence_bounds(self):
        # Lower bound
        result_low = NLIResult(
            label="neutral", confidence=0.0, model="test", backend="test"
        )
        assert result_low.confidence == 0.0

        # Upper bound
        result_high = NLIResult(
            label="neutral", confidence=1.0, model="test", backend="test"
        )
        assert result_high.confidence == 1.0

    def test_invalid_label_raises_error(self):
        with pytest.raises(ValueError):
            NLIResult(
                label="invalid",
                confidence=0.5,
                model="test",
                backend="test",
            )

    def test_confidence_out_of_bounds_raises_error(self):
        with pytest.raises(ValueError):
            NLIResult(
                label="neutral",
                confidence=1.5,
                model="test",
                backend="test",
            )

        with pytest.raises(ValueError):
            NLIResult(
                label="neutral",
                confidence=-0.1,
                model="test",
                backend="test",
            )


class TestNLIProviderPromptBuilding:
    """Tests for NLIProvider prompt building."""

    @pytest.fixture
    def provider(self) -> ConcreteProvider:
        return ConcreteProvider()

    def test_build_basic_prompt(self, provider: ConcreteProvider):
        prompt = provider._build_nli_prompt(
            premise="The sky is blue.",
            hypothesis="The sky has a color.",
        )

        assert "The sky is blue." in prompt
        assert "The sky has a color." in prompt
        assert "entailment" in prompt
        assert "contradiction" in prompt
        assert "neutral" in prompt

    def test_build_prompt_with_context(self, provider: ConcreteProvider):
        prompt = provider._build_nli_prompt(
            premise="The sky is blue.",
            hypothesis="The sky has a color.",
            context="We are discussing weather conditions.",
        )

        assert "We are discussing weather conditions." in prompt
        assert "Context" in prompt

    def test_build_prompt_with_reasoning(self, provider: ConcreteProvider):
        prompt = provider._build_nli_prompt(
            premise="The sky is blue.",
            hypothesis="The sky has a color.",
            use_reasoning=True,
        )

        assert "<think>" in prompt
        assert "step by step" in prompt


class TestNLIProviderResponseParsing:
    """Tests for NLIProvider response parsing."""

    @pytest.fixture
    def provider(self) -> ConcreteProvider:
        return ConcreteProvider()

    def test_parse_simple_json_response(self, provider: ConcreteProvider):
        response = '{"label": "entailment", "confidence": 0.95}'
        result = provider._parse_nli_response(response, "test-model")

        assert result.label == "entailment"
        assert result.confidence == 0.95
        assert result.model == "test-model"
        assert result.backend == "test"

    def test_parse_json_in_code_block(self, provider: ConcreteProvider):
        response = '''Here is my analysis:
```json
{"label": "contradiction", "confidence": 0.8}
```
'''
        result = provider._parse_nli_response(response, "test-model")

        assert result.label == "contradiction"
        assert result.confidence == 0.8

    def test_parse_json_with_extra_text(self, provider: ConcreteProvider):
        response = 'Based on my analysis, the answer is: {"label": "neutral", "confidence": 0.6}'
        result = provider._parse_nli_response(response, "test-model")

        assert result.label == "neutral"
        assert result.confidence == 0.6

    def test_parse_response_clamps_confidence(self, provider: ConcreteProvider):
        # Confidence above 1.0 should be clamped
        response = '{"label": "entailment", "confidence": 1.5}'
        result = provider._parse_nli_response(response, "test-model")
        assert result.confidence == 1.0

        # Confidence below 0.0 should be clamped
        response = '{"label": "entailment", "confidence": -0.5}'
        result = provider._parse_nli_response(response, "test-model")
        assert result.confidence == 0.0

    def test_parse_response_normalizes_label_case(self, provider: ConcreteProvider):
        response = '{"label": "ENTAILMENT", "confidence": 0.9}'
        result = provider._parse_nli_response(response, "test-model")
        assert result.label == "entailment"

    def test_parse_response_invalid_label_raises_error(self, provider: ConcreteProvider):
        response = '{"label": "maybe", "confidence": 0.9}'
        with pytest.raises(ValueError, match="Invalid label"):
            provider._parse_nli_response(response, "test-model")

    def test_parse_response_invalid_json_raises_error(self, provider: ConcreteProvider):
        response = "This is not valid JSON at all"
        with pytest.raises(ValueError, match="Failed to parse"):
            provider._parse_nli_response(response, "test-model")

    def test_parse_response_default_confidence(self, provider: ConcreteProvider):
        response = '{"label": "neutral"}'
        result = provider._parse_nli_response(response, "test-model")
        assert result.confidence == 0.5  # Default value
