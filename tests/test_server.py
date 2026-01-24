"""Tests for the REST API server."""

import pytest


@pytest.mark.asyncio
async def test_health_check(test_app_client):
    """Test that the health check endpoint returns OK."""
    response = await test_app_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_list_tools(test_app_client):
    """Test that listing tools returns available NLI tools."""
    response = await test_app_client.get("/api/v1/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    tool_names = [t["name"] for t in data["tools"]]
    assert "evaluate_nli" in tool_names
    assert "list_providers" in tool_names


@pytest.mark.asyncio
async def test_invoke_unknown_tool(test_app_client):
    """Test that invoking an unknown tool returns 404."""
    response = await test_app_client.post(
        "/api/v1/tools/unknown_tool/invoke",
        json={},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_invoke_tool_validation_error(test_app_client):
    """Test that validation errors return 400."""
    response = await test_app_client.post(
        "/api/v1/tools/evaluate_nli/invoke",
        json={"premise": "", "hypothesis": "test"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_list_providers_tool(test_app_client):
    """Test invoking the list_providers tool."""
    response = await test_app_client.post(
        "/api/v1/tools/list_providers/invoke",
        json={},
    )
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    providers = data["content"][0]["data"]
    assert "ollama" in providers
