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
async def test_list_providers(test_app_client):
    """Test that providers endpoint returns provider metadata."""
    response = await test_app_client.get("/api/v1/providers")
    assert response.status_code == 200
    data = response.json()
    assert "ollama" in data
    assert "huggingface" in data
    assert "openrouter" in data
    assert "default_backend" in data
    assert "default_model" in data


@pytest.mark.asyncio
async def test_evaluate_nli_validation_error(test_app_client):
    """Test that validation errors return 400."""
    response = await test_app_client.post(
        "/api/v1/nli/evaluate",
        json={"premise": "", "hypothesis": "test"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_list_models_missing_backend(test_app_client):
    """Test that /models requires backend query param."""
    response = await test_app_client.get("/api/v1/models")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "BAD_REQUEST"


@pytest.mark.asyncio
async def test_list_models_unknown_backend(test_app_client):
    response = await test_app_client.get("/api/v1/models?backend=unknown")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "BAD_REQUEST"
