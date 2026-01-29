"""MCP (Model Context Protocol) server implementation for Omni-NLI.

This module configures the MCP server with tool handlers for NLI
evaluation, enabling AI assistants to use NLI as a tool.
"""

import logging

import mcp.types as types
from mcp.server.lowlevel import Server

from .tools import tool_registry

_logger = logging.getLogger(__name__)

app = Server("omni-nli")


@app.call_tool()
async def call_tool_handler(name: str, arguments: dict) -> list[types.ContentBlock]:
    """Handle incoming MCP tool call requests.

    Args:
        name: The name of the tool to invoke.
        arguments: The arguments to pass to the tool.

    Returns:
        List of content blocks containing the tool's output.
    """
    _logger.debug(f"MCP tool call received: {name} with arguments: {arguments}")
    return await tool_registry.call(name, arguments)


@app.list_tools()
async def list_tools_handler() -> list[types.Tool]:
    """Handle MCP list_tools requests.

    Returns:
        List of available tool definitions.
    """
    _logger.debug("MCP tool list requested.")
    return tool_registry.list()
