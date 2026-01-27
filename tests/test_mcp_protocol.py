"""Tests for MCP protocol compliance.

This module also contains regression tests for REST documentation endpoints, so
we keep a stable, minimal REST surface aligned with the MCP tool surface.
"""

import re

import pytest


@pytest.mark.asyncio
async def test_rest_docs_endpoints_exist(test_app_client):
    """Docs endpoints should be deterministic."""
    for path in ("/api/v1/apidoc/swagger", "/api/v1/apidoc/redoc"):
        resp = await test_app_client.get(path)
        assert resp.status_code != 404, f"Expected REST docs endpoint at {path}"


@pytest.mark.asyncio
async def test_rest_redoc_references_openapi_json(test_app_client):
    """ReDoc must point at a reachable OpenAPI JSON spec.

    Regression test for a failure mode where the ReDoc page exists but points at
    a non-existent schema URL (e.g. /api/v1/schema returning 404).
    """

    redoc_resp = await test_app_client.get("/api/v1/apidoc/redoc")
    assert redoc_resp.status_code == 200

    html = redoc_resp.text

    # Extract the spec-url attribute.
    m = re.search(r"spec-url=['\"]([^'\"]+)['\"]", html)
    assert m, "ReDoc HTML does not contain a spec-url attribute"

    spec_url = m.group(1)

    # If the spec url is relative (e.g. ./openapi.json), resolve it from the redoc page.
    if spec_url.startswith("./"):
        spec_url = "/api/v1/apidoc/" + spec_url.removeprefix("./")
    elif spec_url.startswith("../"):
        # Conservative relative resolver (only needed for older versions).
        spec_url = "/api/v1/" + spec_url.removeprefix("../")

    spec_resp = await test_app_client.get(spec_url)
    assert spec_resp.status_code == 200, f"OpenAPI spec URL not reachable: {spec_url}"

    spec = spec_resp.json()
    # Minimal sanity checks for an OpenAPI document.
    assert "openapi" in spec or "swagger" in spec
    assert "paths" in spec


@pytest.mark.asyncio
async def test_mcp_endpoint_exists(test_app_client):
    """Test that the MCP endpoint is mounted."""
    # The MCP endpoint uses a special protocol, so we just verify it's there
    response = await test_app_client.post("/mcp/")
    # MCP endpoint won't return 404 - it may return a protocol error
    assert response.status_code != 404
