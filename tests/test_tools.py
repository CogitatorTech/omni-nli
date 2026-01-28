"""Tests for NLI tools and tool registry."""

import json
from unittest.mock import AsyncMock

import pytest
from mcp import types
from pydantic import BaseModel

from omni_nli.errors import ErrorCode, ToolLogicError
from omni_nli.providers.base import NLIResult
from omni_nli.tools import (
    ListProvidersArgs,
    ToolRegistry,
    list_providers_tool,
    setup_tools,
    tool_registry as global_tool_registry,
)


@pytest.fixture(autouse=True)
def clear_registry():
    """Clears the global tool registry before each test."""
    global_tool_registry._tools.clear()
    global_tool_registry._tool_definitions.clear()
    global_tool_registry._tool_models.clear()
    yield


@pytest.fixture
def tool_registry_fixture(mocker):
    """Provides a fresh ToolRegistry instance for isolated tests."""
    registry = ToolRegistry()
    mocker.patch("omni_nli.tools.tool_registry", registry)
    return registry


@pytest.fixture
def mock_nli_result():
    """Provides a mock NLI result for testing."""
    return NLIResult(
        label="contradiction",
        confidence=0.95,
        thinking_trace=None,

        model="llama3.2",
        backend="ollama",
    )


def test_register_and_list_tools(tool_registry_fixture: ToolRegistry):
    """Test that tools can be registered and listed."""
    tool_definition = types.Tool(
        name="test_tool",
        title="Test Tool",
        description="A tool for testing.",
        inputSchema={"type": "object", "properties": {}},
    )

    class TestArgs(BaseModel):
        pass

    @tool_registry_fixture.register(tool_definition, TestArgs)
    async def test_tool(_: TestArgs):
        return [types.TextContent(type="text", text="success")]

    listed_tools = tool_registry_fixture.list()
    assert len(listed_tools) == 1
    assert listed_tools[0] == tool_definition


@pytest.mark.asyncio
async def test_call_tool_success(tool_registry_fixture: ToolRegistry):
    """Test successful tool execution."""

    class TestArgs(BaseModel):
        message: str

    tool_definition = types.Tool(
        name="test_tool",
        title="Test",
        description="A test",
        inputSchema=TestArgs.model_json_schema(),
    )

    @tool_registry_fixture.register(tool_definition, TestArgs)
    async def test_tool(args: TestArgs):
        return [types.TextContent(type="text", text=args.message)]

    result = await tool_registry_fixture.call("test_tool", {"message": "hello"})
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    assert result[0].text == "hello"


@pytest.mark.asyncio
async def test_call_tool_validation_error(tool_registry_fixture: ToolRegistry):
    """Test that validation errors are properly raised."""

    class TestArgs(BaseModel):
        message: str

    tool_definition = types.Tool(
        name="test_tool",
        title="Test",
        description="A test",
        inputSchema=TestArgs.model_json_schema(),
    )

    @tool_registry_fixture.register(tool_definition, TestArgs)
    async def test_tool(args: TestArgs):
        return [types.TextContent(type="text", text=args.message)]

    with pytest.raises(ToolLogicError, match="Input validation failed"):
        await tool_registry_fixture.call("test_tool", {"wrong_arg": "hello"})


@pytest.mark.asyncio
async def test_call_unknown_tool(tool_registry_fixture: ToolRegistry):
    """Test that calling an unknown tool raises an error."""
    with pytest.raises(ToolLogicError, match="Unknown tool: unknown_tool"):
        await tool_registry_fixture.call("unknown_tool", {})


@pytest.mark.asyncio
async def test_evaluate_nli_success(mocker, mock_nli_result):
    """Test successful NLI evaluation."""
    setup_tools()

    # Mock the provider
    mock_provider = AsyncMock()
    mock_provider.evaluate.return_value = mock_nli_result
    mock_provider.supports_reasoning = False

    mocker.patch("omni_nli.tools.get_provider", return_value=mock_provider)

    result = await global_tool_registry.call(
        "evaluate_nli",
        {
            "premise": "A soccer player kicks a ball into the goal.",
            "hypothesis": "The soccer player is asleep on the field.",
        },
    )

    assert len(result) == 1
    result_data = json.loads(result[0].text)
    assert result_data["label"] == "contradiction"
    assert result_data["confidence"] == 0.95


@pytest.mark.asyncio
async def test_evaluate_nli_with_reasoning(mocker):
    """Test NLI evaluation with reasoning enabled."""
    setup_tools()

    mock_result = NLIResult(
        label="entailment",
        confidence=0.92,
        thinking_trace="Let me analyze this step by step...",

        model="claude-3.5-sonnet",
        backend="openrouter",
    )

    mock_provider = AsyncMock()
    mock_provider.evaluate.return_value = mock_result
    mock_provider.supports_reasoning = True

    mocker.patch("omni_nli.tools.get_provider", return_value=mock_provider)
    mocker.patch("omni_nli.providers.base.settings.return_thinking_trace", True)

    result = await global_tool_registry.call(
        "evaluate_nli",
        {
            "premise": "If it rains, the ground gets wet. It is raining.",
            "hypothesis": "The ground is wet.",
            "use_reasoning": True,
        },
    )

    result_data = json.loads(result[0].text)
    assert result_data["label"] == "entailment"
    assert result_data["thinking_trace"] is not None


@pytest.mark.asyncio
async def test_evaluate_nli_with_context(mocker, mock_nli_result):
    """Test NLI evaluation with context provided."""
    setup_tools()

    mock_provider = AsyncMock()
    mock_provider.evaluate.return_value = mock_nli_result
    mock_provider.supports_reasoning = False

    mocker.patch("omni_nli.tools.get_provider", return_value=mock_provider)

    await global_tool_registry.call(
        "evaluate_nli",
        {
            "premise": "The player castled.",
            "hypothesis": "The king moved.",
            "context": "In chess, castling involves moving the king two squares.",
        },
    )

    # Verify provider was called with the context
    mock_provider.evaluate.assert_called_once()
    call_args = mock_provider.evaluate.call_args
    assert call_args.kwargs["context"] == "In chess, castling involves moving the king two squares."


@pytest.mark.asyncio
async def test_evaluate_nli_with_backend_override(mocker, mock_nli_result):
    """Test NLI evaluation with explicit backend override."""
    setup_tools()

    mock_provider = AsyncMock()
    mock_provider.evaluate.return_value = mock_nli_result
    mock_provider.supports_reasoning = False

    mock_get_provider = mocker.patch(
        "omni_nli.tools.get_provider", return_value=mock_provider
    )

    await global_tool_registry.call(
        "evaluate_nli",
        {
            "premise": "The cat is on the mat.",
            "hypothesis": "The mat has a cat on it.",
            "backend": "openrouter",
        },
    )

    # Verify provider was called with the right backend
    mock_get_provider.assert_called_once_with(backend="openrouter")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_data, expected_error",
    [
        ({"premise": "", "hypothesis": "test"}, "at least 1 character"),
        ({"premise": "test", "hypothesis": ""}, "at least 1 character"),
        ({"premise": "   ", "hypothesis": "test"}, "empty or whitespace"),
        ({}, "Field required"),
    ],
)
async def test_evaluate_nli_validation_errors(invalid_data, expected_error):
    """Test that input validation errors are properly raised."""
    setup_tools()
    with pytest.raises(ToolLogicError) as exc_info:
        await global_tool_registry.call("evaluate_nli", invalid_data)
    assert exc_info.value.error.code == ErrorCode.VALIDATION_ERROR
    assert expected_error in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_providers():
    """Test listing available providers."""
    result = await list_providers_tool(ListProvidersArgs())
    assert len(result) == 1
    providers = json.loads(result[0].text)
    assert "ollama" in providers
    assert "huggingface" in providers
    assert "openrouter" in providers
