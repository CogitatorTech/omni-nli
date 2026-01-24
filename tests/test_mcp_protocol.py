"""Tests for MCP protocol compliance."""

import pytest


@pytest.mark.asyncio
async def test_mcp_tools_list(test_app_client):
    """Test that MCP tools can be listed."""
    # This test verifies that the MCP endpoint is mounted and accessible
    # Full MCP protocol testing would require an MCP client
    response = await test_app_client.get("/api/v1/tools")
    assert response.status_code == 200
    tools = response.json()["tools"]

    # Verify evaluate_nli tool definition
    evaluate_nli = next((t for t in tools if t["name"] == "evaluate_nli"), None)
    assert evaluate_nli is not None
    assert "inputSchema" in evaluate_nli
    assert "premise" in str(evaluate_nli["inputSchema"])
    assert "hypothesis" in str(evaluate_nli["inputSchema"])


@pytest.mark.asyncio
async def test_mcp_endpoint_exists(test_app_client):
    """Test that the MCP endpoint is mounted."""
    # The MCP endpoint uses a special protocol, so we just verify it's there
    # A proper test would use an MCP client
    response = await test_app_client.post("/mcp/")
    # MCP endpoint won't return 404 - it may return a protocol error
    assert response.status_code != 404
