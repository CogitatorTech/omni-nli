"""Tests for REST API module."""

import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

from omni_nli.rest import setup_rest_routes, _parse_json_body, _error


class TestRestHelpers:
    """Tests for REST API helper functions."""

    def test_error_response_format(self):
        """Test that _error creates properly formatted error responses."""
        response = _error(
            code="TEST_ERROR",
            message="Test error message",
            details={"field": "value"},
            status_code=400,
        )

        assert response.status_code == 400
        body = response.body.decode()
        assert "TEST_ERROR" in body
        assert "Test error message" in body
        assert "field" in body

    def test_error_response_default_status(self):
        """Test that _error uses 400 as default status code."""
        response = _error(code="TEST", message="Test")
        assert response.status_code == 400

    def test_error_response_without_details(self):
        """Test that _error works without details."""
        response = _error(code="TEST", message="Test message")
        assert response.status_code == 400
        body = response.body.decode()
        assert "TEST" in body
        assert "Test message" in body


class TestParseJsonBody:
    """Tests for JSON body parsing."""

    @pytest.fixture
    def app(self) -> Starlette:
        """Create a test Starlette app."""
        from starlette.responses import JSONResponse
        from starlette.routing import Route

        async def test_endpoint(request):
            try:
                data = await _parse_json_body(request)
                return JSONResponse({"success": True, "data": data})
            except ValueError as e:
                return JSONResponse({"error": str(e)}, status_code=400)

        return Starlette(routes=[Route("/test", test_endpoint, methods=["POST"])])

    def test_parse_valid_json(self, app: Starlette):
        """Test parsing valid JSON body."""
        client = TestClient(app)
        response = client.post(
            "/test",
            json={"premise": "test", "hypothesis": "test"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["data"]["premise"] == "test"

    def test_parse_empty_body(self, app: Starlette):
        """Test parsing empty body returns empty dict."""
        client = TestClient(app)
        response = client.post(
            "/test",
            content=b"",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert response.json()["data"] == {}

    def test_parse_wrong_content_type(self, app: Starlette):
        """Test that wrong content type is rejected."""
        client = TestClient(app)
        response = client.post(
            "/test",
            content=b"test",
            headers={"Content-Type": "text/plain"},
        )
        assert response.status_code == 400
        assert "Content-Type" in response.json()["error"]

    def test_parse_invalid_json(self, app: Starlette):
        """Test that invalid JSON is rejected."""
        client = TestClient(app)
        response = client.post(
            "/test",
            content=b"{invalid json}",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400


class TestRestRoutes:
    """Tests for REST route setup."""

    def test_setup_rest_routes_returns_routes(self):
        """Test that setup_rest_routes returns route list."""
        routes = setup_rest_routes()

        assert len(routes) == 3

        paths = [r.path for r in routes]
        assert "/nli/evaluate" in paths
        assert "/providers" in paths
        assert "/apidoc/redoc" in paths

    def test_routes_have_correct_methods(self):
        """Test that routes have correct HTTP methods."""
        routes = setup_rest_routes()

        route_methods = {r.path: r.methods for r in routes}

        assert "POST" in route_methods["/nli/evaluate"]
        assert "GET" in route_methods["/providers"]
        assert "GET" in route_methods["/apidoc/redoc"]
