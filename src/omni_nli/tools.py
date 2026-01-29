"""Tool definitions and registry for Omni-NLI MCP integration.

This module defines the tools available via MCP, including NLI evaluation
and provider listing, along with the registry for managing tool registration.
"""

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Literal, Type

import mcp.types as types
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .errors import ErrorCode, ToolLogicError
from .providers import get_provider

_logger = logging.getLogger(__name__)


class EvaluateNLIArgs(BaseModel):
    """Arguments for the evaluate_nli tool.

    Validates and holds the input parameters for NLI evaluation requests.
    """

    model_config = ConfigDict(extra="forbid")

    premise: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="The base factual statement (premise).",
    )
    hypothesis: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="The statement to be tested against the premise (hypothesis).",
    )
    context: str | None = Field(
        None,
        max_length=8192,
        description="Optional background context to ground the inference.",
    )
    backend: Literal["ollama", "huggingface", "openrouter"] | None = Field(
        None,
        description="The backend provider to use. If None, uses configured default.",
    )
    model: str | None = Field(
        None,
        description="Specific model to use. If None, uses default for the backend.",
    )
    use_reasoning: bool = Field(
        False,
        description="If True, uses extended thinking/reasoning tokens.",
    )

    @field_validator("premise", "hypothesis")
    @classmethod
    def must_not_be_whitespace(cls, v: str) -> str:
        """Validate that premise/hypothesis are not whitespace-only."""
        if not v.strip():
            raise ValueError("Cannot be empty or whitespace only")
        return v


class ListProvidersArgs(BaseModel):
    """Arguments for the list_providers tool (currently empty)."""

    model_config = ConfigDict(extra="forbid")


# Keep this intentionally permissive so individual tools can type their args precisely.
ToolCallable = Callable[[Any], Awaitable[list[types.ContentBlock]]]


class ToolRegistry:
    """Registry for managing MCP tool definitions and handlers.

    Provides registration, lookup, validation, and invocation of tools.
    """

    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: dict[str, ToolCallable] = {}
        self._tool_definitions: dict[str, types.Tool] = {}
        self._tool_models: dict[str, Type[BaseModel]] = {}

    def register(
        self, tool_definition: types.Tool, model: Type[BaseModel]
    ) -> Callable[[ToolCallable], ToolCallable]:
        """Create a decorator for registering a tool handler.

        Args:
            tool_definition: The MCP tool definition.
            model: Pydantic model for argument validation.

        Returns:
            Decorator function that registers the wrapped function.
        """

        def decorator(func: ToolCallable) -> ToolCallable:
            self.register_tool(tool_definition, model, func)
            return func

        return decorator

    def register_tool(
        self,
        tool_definition: types.Tool,
        model: Type[BaseModel],
        func: ToolCallable,
    ) -> None:
        """Register a tool with its definition, model, and handler.

        Args:
            tool_definition: The MCP tool definition.
            model: Pydantic model for argument validation.
            func: Async handler function for the tool.

        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        name = tool_definition.name
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered.")
        self._tools[name] = func
        self._tool_definitions[name] = tool_definition
        self._tool_models[name] = model

    async def call_validated(
        self, name: str, validated_args: BaseModel
    ) -> list[types.ContentBlock]:
        """Call a tool with pre-validated arguments.

        Args:
            name: The tool name.
            validated_args: Already-validated Pydantic model instance.

        Returns:
            List of content blocks from the tool.

        Raises:
            ToolLogicError: If the tool is not found.
        """
        if name not in self._tools:
            raise ToolLogicError(
                code=ErrorCode.UNKNOWN_TOOL,
                message=f"Unknown tool: {name}",
            )
        return await self._tools[name](validated_args)

    async def call(self, name: str, arguments: dict) -> list[types.ContentBlock]:
        """Call a tool by name with raw arguments.

        Validates arguments using the registered model before calling.

        Args:
            name: The tool name.
            arguments: Raw argument dictionary.

        Returns:
            List of content blocks from the tool.

        Raises:
            ToolLogicError: If tool not found or validation fails.
        """
        if name not in self._tools:
            raise ToolLogicError(
                code=ErrorCode.UNKNOWN_TOOL,
                message=f"Unknown tool: {name}",
            )

        model = self._tool_models.get(name)
        if not model:
            raise ToolLogicError(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"No validation model registered for tool: {name}",
            )

        try:
            validated_args = model(**arguments)
        except Exception as e:
            raise ToolLogicError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Input validation failed.",
                details=str(e),
            ) from e

        return await self._tools[name](validated_args)

    def list(self) -> list[types.Tool]:
        """List all registered tool definitions.

        Returns:
            List of MCP Tool definitions.
        """
        return list(self._tool_definitions.values())


tool_registry = ToolRegistry()


async def evaluate_nli(args: EvaluateNLIArgs) -> list[types.ContentBlock]:
    """Evaluate NLI relationship between premise and hypothesis.

    Args:
        args: Validated NLI evaluation arguments.

    Returns:
        List containing a TextContent block with JSON result.

    Raises:
        ToolLogicError: If provider unavailable or evaluation fails.
    """
    premise_preview = args.premise[:50] + ("..." if len(args.premise) > 50 else "")
    _logger.info(f"Evaluating NLI: premise='{premise_preview}'")

    try:
        provider = await get_provider(backend=args.backend)
    except ValueError as e:
        raise ToolLogicError(
            code=ErrorCode.PROVIDER_ERROR,
            message=str(e),
        ) from e

    try:
        result = await provider.evaluate(
            premise=args.premise,
            hypothesis=args.hypothesis,
            context=args.context,
            model=args.model,
            use_reasoning=args.use_reasoning,
        )
    except Exception as e:
        _logger.error(f"NLI evaluation failed: {e}")
        raise ToolLogicError(
            code=ErrorCode.PROVIDER_ERROR,
            message=f"NLI evaluation failed: {e}",
        ) from e

    return [types.TextContent(type="text", text=result.model_dump_json(exclude_none=True))]


async def list_providers_tool(args: ListProvidersArgs) -> list[types.ContentBlock]:
    """List available NLI providers and their configuration.

    Args:
        args: Empty argument model (no arguments needed).

    Returns:
        List containing a TextContent block with provider info JSON.
    """
    from .providers import list_available_providers
    from .settings import settings

    providers = list_available_providers()
    providers["default_backend"] = settings.default_backend
    return [types.TextContent(type="text", text=json.dumps(providers, indent=2))]


def setup_tools() -> None:
    """Register all NLI tools with the global registry.

    Clears any existing registrations and registers fresh tool definitions.
    """
    _logger.info("Setting up NLI tools...")

    tool_registry._tools.clear()
    tool_registry._tool_definitions.clear()
    tool_registry._tool_models.clear()

    evaluate_nli_definition = types.Tool(
        name="evaluate_nli",
        title="Evaluate NLI Logic",
        description=(
            "Analyzes a premise and hypothesis to determine their logical relationship: "
            "entailment (hypothesis follows from premise), contradiction (hypothesis "
            "conflicts with premise), or neutral (neither)."
        ),
        inputSchema=EvaluateNLIArgs.model_json_schema(),
    )
    tool_registry.register_tool(evaluate_nli_definition, EvaluateNLIArgs, evaluate_nli)

    list_providers_definition = types.Tool(
        name="list_providers",
        title="List NLI Providers",
        description=(
            "Lists available NLI backend providers (Ollama, HuggingFace, or OpenRouter) "
            "and their configuration status."
        ),
        inputSchema=ListProvidersArgs.model_json_schema(),
    )
    tool_registry.register_tool(list_providers_definition, ListProvidersArgs, list_providers_tool)

    _logger.info(f"Registered {len(tool_registry._tools)} tools")


def setup_cache() -> None:
    """Initialize any caching mechanisms (currently a no-op)."""
    pass
