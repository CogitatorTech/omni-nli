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

    # Provider defaults are per-backend (no global default_model).
    assert data["ollama"]["default_model"]
    assert data["huggingface"]["default_model"]
    assert data["openrouter"]["default_model"]


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
