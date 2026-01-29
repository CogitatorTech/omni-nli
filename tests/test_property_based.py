"""Property-based tests for Omni-NLI using Hypothesis.

These tests verify invariants and properties of the system without mocks.
They focus on pure functions and deterministic components.
"""

import string

import pytest
from hypothesis import given, settings as hyp_settings, strategies as st
from mcp import types
from pydantic import BaseModel
from pydantic import ValidationError

from omni_nli.event_store import InMemoryEventStore
from omni_nli.providers.base import NLIProvider, NLIResult
from omni_nli.tools import EvaluateNLIArgs, ListProvidersArgs, ToolRegistry

# =============================================================================
# Custom Strategies
# =============================================================================

# Non-whitespace strings for valid premise/hypothesis
valid_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
    min_size=1,
    max_size=100,
).filter(lambda s: s.strip())

# Longer valid text for testing near-limit cases
valid_text_long = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
    min_size=1,
    max_size=4096,
).filter(lambda s: s.strip())

# Whitespace-only strings for rejection tests
whitespace_only = st.text(
    alphabet=" \t\n\r",
    min_size=1,
    max_size=20,
)

# Valid NLI labels
nli_labels = st.sampled_from(["entailment", "contradiction", "neutral"])

# Valid confidence values
valid_confidence = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)

# Out-of-bounds confidence values
oob_confidence = st.one_of(
    st.floats(min_value=1.01, max_value=100.0, allow_nan=False),
    st.floats(min_value=-100.0, max_value=-0.01, allow_nan=False),
)

# Valid backend choices
valid_backends = st.sampled_from(["ollama", "huggingface", "openrouter", None])

# Stream IDs for event store tests
stream_ids = st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20)


# =============================================================================
# EvaluateNLIArgs Validation Tests
# =============================================================================


class TestEvaluateNLIArgsProperties:
    """Property-based tests for EvaluateNLIArgs validation."""

    @given(premise=valid_text, hypothesis=valid_text, backend=valid_backends)
    @hyp_settings(max_examples=100)
    def test_valid_inputs_always_parse(self, premise: str, hypothesis: str, backend):
        """Valid non-whitespace premise/hypothesis should always parse successfully."""
        args = EvaluateNLIArgs(
            premise=premise,
            hypothesis=hypothesis,
            backend=backend,
        )
        assert args.premise == premise
        assert args.hypothesis == hypothesis
        assert args.backend == backend

    @given(premise=valid_text, hypothesis=valid_text, context=valid_text)
    @hyp_settings(max_examples=50)
    def test_optional_context_accepted(self, premise: str, hypothesis: str, context: str):
        """Optional context with valid text should be accepted."""
        args = EvaluateNLIArgs(
            premise=premise,
            hypothesis=hypothesis,
            context=context,
        )
        assert args.context == context

    @given(premise=whitespace_only, hypothesis=valid_text)
    @hyp_settings(max_examples=50)
    def test_whitespace_only_premise_rejected(self, premise: str, hypothesis: str):
        """Whitespace-only premise should always be rejected."""
        with pytest.raises(ValidationError):
            EvaluateNLIArgs(premise=premise, hypothesis=hypothesis)

    @given(premise=valid_text, hypothesis=whitespace_only)
    @hyp_settings(max_examples=50)
    def test_whitespace_only_hypothesis_rejected(self, premise: str, hypothesis: str):
        """Whitespace-only hypothesis should always be rejected."""
        with pytest.raises(ValidationError):
            EvaluateNLIArgs(premise=premise, hypothesis=hypothesis)

    @given(premise=valid_text, hypothesis=valid_text, use_reasoning=st.booleans())
    @hyp_settings(max_examples=50)
    def test_use_reasoning_flag_preserved(
        self, premise: str, hypothesis: str, use_reasoning: bool
    ):
        """use_reasoning flag should be preserved correctly."""
        args = EvaluateNLIArgs(
            premise=premise,
            hypothesis=hypothesis,
            use_reasoning=use_reasoning,
        )
        assert args.use_reasoning == use_reasoning

    @given(premise=valid_text, hypothesis=valid_text)
    @hyp_settings(max_examples=50)
    def test_serialization_roundtrip(self, premise: str, hypothesis: str):
        """Serialized args can be deserialized back."""
        original = EvaluateNLIArgs(premise=premise, hypothesis=hypothesis)
        dumped = original.model_dump()
        restored = EvaluateNLIArgs(**dumped)
        assert restored == original


# =============================================================================
# NLIResult Model Tests
# =============================================================================


class TestNLIResultProperties:
    """Property-based tests for NLIResult model."""

    @given(
        label=nli_labels,
        confidence=valid_confidence,
        model=valid_text,
        backend=valid_text,
    )
    @hyp_settings(max_examples=100)
    def test_valid_results_always_construct(
        self, label: str, confidence: float, model: str, backend: str
    ):
        """Valid inputs should always produce a valid NLIResult."""
        result = NLIResult(
            label=label,
            confidence=confidence,
            model=model,
            backend=backend,
        )
        assert result.label == label
        assert result.confidence == confidence

    @given(
        label=nli_labels,
        confidence=valid_confidence,
        model=valid_text,
        backend=valid_text,
        trace=st.one_of(st.none(), valid_text),
    )
    @hyp_settings(max_examples=50)
    def test_optional_thinking_trace(
        self, label: str, confidence: float, model: str, backend: str, trace
    ):
        """Optional thinking_trace should be accepted."""
        result = NLIResult(
            label=label,
            confidence=confidence,
            model=model,
            backend=backend,
            thinking_trace=trace,
        )
        assert result.thinking_trace == trace

    @given(
        label=nli_labels,
        confidence=valid_confidence,
        model=valid_text,
        backend=valid_text,
    )
    @hyp_settings(max_examples=50)
    def test_serialization_roundtrip(
        self, label: str, confidence: float, model: str, backend: str
    ):
        """Serialized result can be deserialized back."""
        original = NLIResult(
            label=label,
            confidence=confidence,
            model=model,
            backend=backend,
        )
        dumped = original.model_dump()
        restored = NLIResult(**dumped)
        assert restored == original

    @given(label=st.text(min_size=1, max_size=20).filter(
        lambda s: s.lower() not in ("entailment", "contradiction", "neutral")
    ))
    @hyp_settings(max_examples=50)
    def test_invalid_labels_rejected(self, label: str):
        """Invalid labels should be rejected."""
        with pytest.raises(ValidationError):
            NLIResult(label=label, confidence=0.5, model="test", backend="test")

    @given(confidence=oob_confidence)
    @hyp_settings(max_examples=50)
    def test_out_of_bounds_confidence_rejected(self, confidence: float):
        """Out-of-bounds confidence values should be rejected."""
        with pytest.raises(ValidationError):
            NLIResult(
                label="neutral",
                confidence=confidence,
                model="test",
                backend="test",
            )


# =============================================================================
# InMemoryEventStore Tests
# =============================================================================


class TestInMemoryEventStoreProperties:
    """Property-based tests for InMemoryEventStore."""

    @given(
        stream_id=stream_ids,
        num_events=st.integers(min_value=1, max_value=50),
    )
    @hyp_settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_stored_events_have_unique_ids(self, stream_id: str, num_events: int):
        """All stored events should have unique IDs."""
        store = InMemoryEventStore(max_events_per_stream=100)
        event_ids = []

        for i in range(num_events):
            message = {"jsonrpc": "2.0", "method": "test", "id": i}
            event_id = await store.store_event(stream_id, message)
            event_ids.append(event_id)

        # All IDs should be unique
        assert len(event_ids) == len(set(event_ids))

    @given(
        stream_id=stream_ids,
        max_events=st.integers(min_value=5, max_value=20),
        num_events=st.integers(min_value=1, max_value=50),
    )
    @hyp_settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_respects_max_events_per_stream(
        self, stream_id: str, max_events: int, num_events: int
    ):
        """Event store should never exceed max_events_per_stream."""
        store = InMemoryEventStore(max_events_per_stream=max_events)

        for i in range(num_events):
            message = {"jsonrpc": "2.0", "method": "test", "id": i}
            await store.store_event(stream_id, message)

        assert len(store.streams[stream_id]) <= max_events

    @given(
        num_streams=st.integers(min_value=1, max_value=20),
        max_streams=st.integers(min_value=5, max_value=15),
    )
    @hyp_settings(max_examples=30)
    @pytest.mark.asyncio
    async def test_respects_max_streams(self, num_streams: int, max_streams: int):
        """Event store should never exceed max_streams."""
        store = InMemoryEventStore(max_streams=max_streams, max_events_per_stream=10)

        for i in range(num_streams):
            stream_id = f"stream_{i}"
            message = {"jsonrpc": "2.0", "method": "test", "id": i}
            await store.store_event(stream_id, message)

        assert len(store.streams) <= max_streams

    @given(stream_id=stream_ids)
    @hyp_settings(max_examples=30)
    @pytest.mark.asyncio
    async def test_event_index_consistent_with_streams(self, stream_id: str):
        """Event index should be consistent with stream storage."""
        store = InMemoryEventStore(max_events_per_stream=10)

        stored_ids = []
        for i in range(5):
            message = {"jsonrpc": "2.0", "method": "test", "id": i}
            event_id = await store.store_event(stream_id, message)
            stored_ids.append(event_id)

        # All stored IDs should be in the index
        for event_id in stored_ids:
            assert event_id in store.event_index


# =============================================================================
# NLIProvider Prompt Building Tests
# =============================================================================


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


class TestNLIProviderPromptProperties:
    """Property-based tests for NLIProvider prompt building."""

    @given(premise=valid_text, hypothesis=valid_text)
    @hyp_settings(max_examples=100)
    def test_prompt_contains_inputs(self, premise: str, hypothesis: str):
        """Prompt should always contain the premise and hypothesis."""
        provider = ConcreteProvider()
        prompt = provider._build_nli_prompt(premise=premise, hypothesis=hypothesis)
        assert premise in prompt
        assert hypothesis in prompt

    @given(premise=valid_text, hypothesis=valid_text, context=valid_text)
    @hyp_settings(max_examples=50)
    def test_prompt_contains_context_when_provided(
        self, premise: str, hypothesis: str, context: str
    ):
        """Prompt should contain context when provided."""
        provider = ConcreteProvider()
        prompt = provider._build_nli_prompt(
            premise=premise,
            hypothesis=hypothesis,
            context=context,
        )
        assert context in prompt
        assert "Context" in prompt

    @given(premise=valid_text, hypothesis=valid_text)
    @hyp_settings(max_examples=50)
    def test_prompt_always_contains_labels(self, premise: str, hypothesis: str):
        """Prompt should always mention all three NLI labels."""
        provider = ConcreteProvider()
        prompt = provider._build_nli_prompt(premise=premise, hypothesis=hypothesis)
        assert "entailment" in prompt
        assert "contradiction" in prompt
        assert "neutral" in prompt

    @given(premise=valid_text, hypothesis=valid_text, use_reasoning=st.booleans())
    @hyp_settings(max_examples=50)
    def test_prompt_contains_json_format_instruction(
        self, premise: str, hypothesis: str, use_reasoning: bool
    ):
        """Prompt should always contain JSON format instruction."""
        provider = ConcreteProvider()
        prompt = provider._build_nli_prompt(
            premise=premise,
            hypothesis=hypothesis,
            use_reasoning=use_reasoning,
        )
        assert "JSON" in prompt or "json" in prompt
        assert "label" in prompt
        assert "confidence" in prompt

    @given(premise=valid_text, hypothesis=valid_text)
    @hyp_settings(max_examples=30)
    def test_reasoning_instruction_when_enabled(self, premise: str, hypothesis: str):
        """Prompt should contain thinking instruction when use_reasoning is True."""
        provider = ConcreteProvider()
        prompt = provider._build_nli_prompt(
            premise=premise,
            hypothesis=hypothesis,
            use_reasoning=True,
        )
        assert "<think>" in prompt


# =============================================================================
# NLIProvider Response Parsing Tests
# =============================================================================


class TestNLIProviderParsingProperties:
    """Property-based tests for NLIProvider response parsing."""

    @given(label=nli_labels, confidence=valid_confidence)
    @hyp_settings(max_examples=100)
    def test_valid_json_always_parsed(self, label: str, confidence: float):
        """Valid JSON responses should always be parsed successfully."""
        provider = ConcreteProvider()
        response = f'{{"label": "{label}", "confidence": {confidence}}}'
        result = provider._parse_nli_response(response, "test-model")
        assert result.label == label
        # Confidence might be clamped but should be in bounds
        assert 0.0 <= result.confidence <= 1.0

    @given(label=nli_labels, confidence=valid_confidence)
    @hyp_settings(max_examples=50)
    def test_json_in_code_block_parsed(self, label: str, confidence: float):
        """JSON in code blocks should be parsed correctly."""
        provider = ConcreteProvider()
        response = f'''Here is my analysis:
```json
{{"label": "{label}", "confidence": {confidence}}}
```
'''
        result = provider._parse_nli_response(response, "test-model")
        assert result.label == label

    @given(label=nli_labels)
    @hyp_settings(max_examples=50)
    def test_uppercase_labels_normalized(self, label: str):
        """Uppercase labels should be normalized to lowercase."""
        provider = ConcreteProvider()
        response = f'{{"label": "{label.upper()}", "confidence": 0.8}}'
        result = provider._parse_nli_response(response, "test-model")
        assert result.label == label.lower()

    @given(
        label=nli_labels,
        high_confidence=st.floats(min_value=1.01, max_value=10.0, allow_nan=False),
    )
    @hyp_settings(max_examples=30)
    def test_high_confidence_clamped(self, label: str, high_confidence: float):
        """Confidence > 1.0 should be clamped to 1.0."""
        provider = ConcreteProvider()
        response = f'{{"label": "{label}", "confidence": {high_confidence}}}'
        result = provider._parse_nli_response(response, "test-model")
        assert result.confidence == 1.0

    @given(
        label=nli_labels,
        low_confidence=st.floats(min_value=-10.0, max_value=-0.01, allow_nan=False),
    )
    @hyp_settings(max_examples=30)
    def test_low_confidence_clamped(self, label: str, low_confidence: float):
        """Confidence < 0.0 should be clamped to 0.0."""
        provider = ConcreteProvider()
        response = f'{{"label": "{label}", "confidence": {low_confidence}}}'
        result = provider._parse_nli_response(response, "test-model")
        assert result.confidence == 0.0

    @given(label=nli_labels)
    @hyp_settings(max_examples=30)
    def test_missing_confidence_defaults(self, label: str):
        """Missing confidence should default to 0.5."""
        provider = ConcreteProvider()
        response = f'{{"label": "{label}"}}'
        result = provider._parse_nli_response(response, "test-model")
        assert result.confidence == 0.5


# =============================================================================
# ToolRegistry Tests
# =============================================================================


class TestToolRegistryProperties:
    """Property-based tests for ToolRegistry."""

    @given(tool_names=st.lists(
        st.text(alphabet=string.ascii_lowercase, min_size=3, max_size=20),
        min_size=1,
        max_size=10,
        unique=True,
    ))
    @hyp_settings(max_examples=50)
    def test_registered_tools_appear_in_list(self, tool_names: list[str]):
        """All registered tools should appear in the tool list."""
        registry = ToolRegistry()

        for name in tool_names:
            class DummyArgs(BaseModel):
                pass

            tool_def = types.Tool(
                name=name,
                title=f"Tool {name}",
                description="A test tool",
                inputSchema={"type": "object"},
            )

            async def dummy_handler(args):
                return [types.TextContent(type="text", text="ok")]

            registry.register_tool(tool_def, DummyArgs, dummy_handler)

        listed = registry.list()
        listed_names = {t.name for t in listed}

        for name in tool_names:
            assert name in listed_names

    @given(tool_name=st.text(alphabet=string.ascii_lowercase, min_size=3, max_size=20))
    @hyp_settings(max_examples=30)
    def test_duplicate_registration_raises_error(self, tool_name: str):
        """Registering the same tool twice should raise ValueError."""
        registry = ToolRegistry()

        class DummyArgs(BaseModel):
            pass

        tool_def = types.Tool(
            name=tool_name,
            title="Tool",
            description="A test tool",
            inputSchema={"type": "object"},
        )

        async def dummy_handler(args):
            return [types.TextContent(type="text", text="ok")]

        registry.register_tool(tool_def, DummyArgs, dummy_handler)

        with pytest.raises(ValueError, match="already registered"):
            registry.register_tool(tool_def, DummyArgs, dummy_handler)


# =============================================================================
# ListProvidersArgs Tests
# =============================================================================


class TestListProvidersArgsProperties:
    """Property-based tests for ListProvidersArgs."""

    def test_empty_args_always_valid(self):
        """Empty args should always be valid."""
        args = ListProvidersArgs()
        assert args is not None

    @given(extra_field=valid_text)
    @hyp_settings(max_examples=20)
    def test_extra_fields_rejected(self, extra_field: str):
        """Extra fields should be rejected (extra=forbid)."""
        with pytest.raises(ValidationError):
            ListProvidersArgs(**{"unexpected": extra_field})
