import asyncio
from unittest.mock import MagicMock, patch

import pytest
from starlette.requests import Request

from omni_nli.providers.base import NLIProvider
from omni_nli.providers.huggingface import HuggingFaceProvider
from omni_nli.rest import _parse_json_body


# --- 1. JSON Parsing Verification ---

class TestProvider(NLIProvider):
    async def evaluate(self, *args, **kwargs):
        pass

    async def list_models(self):
        return []

    async def health_check(self):
        return True


def test_robust_json_parsing():
    provider = TestProvider()

    # Case 1: Clean JSON
    text = '{"label": "entailment", "confidence": 0.9}'
    result = provider._parse_nli_response(text, "test")
    assert result.label == "entailment"

    # Case 2: Thinking trace before JSON
    text = '<think>some reasoning</think>\n{"label": "contradiction", "confidence": 0.1}'
    with patch("omni_nli.providers.base.settings.return_thinking_trace", True):
        result = provider._parse_nli_response(text, "test")
        assert result.label == "contradiction"
        assert result.thinking_trace == "some reasoning"

    # Case 3: Extra text around JSON
    text = 'Sure, here is the JSON:\n{"label": "neutral", "confidence": 0.5}\nHope this helps!'
    result = provider._parse_nli_response(text, "test")
    assert result.label == "neutral"

    # Case 4: Broken JSON (should now pass with json_repair)
    text = '{"label": "neutral"'
    result = provider._parse_nli_response(text, "test")
    assert result.label == "neutral"

    # Case 5: Garbage (should fail)
    text = "I am just plain text with no json"
    with pytest.raises(ValueError):
        provider._parse_nli_response(text, "test")


# --- 2. HuggingFace Async Verification ---

@pytest.mark.asyncio
async def test_huggingface_async_execution():
    # Mock the pipeline
    mock_pipeline = MagicMock()
    mock_pipeline.tokenizer.chat_template = None
    mock_pipeline.return_value = [{"generated_text": '{"label": "entailment"}'}]

    with patch("omni_nli.providers.huggingface.pipeline", return_value=mock_pipeline) as mock_init:
        provider = HuggingFaceProvider(token="test")

        # We need to mock _get_pipeline to inject our mock, but since we refactored it
        # we can just let it run. However, we want to verify it runs in a thread.
        # Ideally, we check that the main thread is not blocked, but that's hard.
        # Instead, we check if asyncio.to_thread was called.

        with patch("asyncio.to_thread", side_effect=asyncio.to_thread) as mock_to_thread:
            # We must mock the internal _pipelines cache or else _get_pipeline won't call load
            # provider._pipelines = {"test-model": mock_pipeline}
            # Actually, let's just test get_pipeline call first

            # Reset pipelines
            provider._pipelines = {}

            # Just make it return a dummy
            await provider._get_pipeline("test-model")

            # Check if to_thread was called
            assert mock_to_thread.called


# --- 3. Rest API DoS Verification ---

@pytest.mark.asyncio
async def test_rest_dos_protection():
    # legitimate request
    scope = {
        "type": "http",
        "headers": [(b"content-type", b"application/json"), (b"content-length", b"10")],
    }

    async def receive_small():
        return {"type": "http.request", "body": b'{"a": 1}', "more_body": False}

    req = Request(scope, receive=receive_small)
    data = await _parse_json_body(req)
    assert data == {"a": 1}

    # Large request header (10MB + 1)
    large_scope = {
        "type": "http",
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", b"10485761"),
        ],
    }
    req_large = Request(large_scope, receive=receive_small)

    with pytest.raises(ValueError, match="Request payload too large"):
        await _parse_json_body(req_large)
