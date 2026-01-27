"""Tests for MCP protocol compliance."""

import pytest


@pytest.mark.asyncio
async def test_rest_docs_endpoint_exists(test_app_client):
    """Test that the REST docs endpoint is mounted (Spectree swagger UI)."""
    # Depending on Spectree/starlette plugin version, docs may mount at one of these URLs.
    candidate_paths = ["/api/v1/docs", "/api/v1/apidoc/swagger", "/api/v1/apidoc/redoc",
                       "/api/v1/redoc"]

    for path in candidate_paths:
        resp = await test_app_client.get(path)
        if resp.status_code != 404:
            return

    assert False, "No REST docs endpoint found under expected paths"


@pytest.mark.asyncio
async def test_mcp_endpoint_exists(test_app_client):
    """Test that the MCP endpoint is mounted."""
    # The MCP endpoint uses a special protocol, so we just verify it's there
    response = await test_app_client.post("/mcp/")
    # MCP endpoint won't return 404 - it may return a protocol error
    assert response.status_code != 404
