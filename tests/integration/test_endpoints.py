from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.responses import Response

from app.dependencies import get_proxy_handler
from app.main import app


@pytest.mark.integration
class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "healthy"


@pytest.mark.integration
class TestProxyEndpoints:
    @pytest.mark.asyncio
    async def test_auth_proxy(self, client, mocker):
        mock_response = Response(
            content=b'{"message": "success"}',
            status_code=200,
            media_type="application/json"
        )

        mock_handler = MagicMock()
        mock_handler.proxy_request = AsyncMock(return_value=mock_response)

        app.dependency_overrides[get_proxy_handler] = lambda: mock_handler

        response = client.get("/auth/test")
        assert response.status_code == 200

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_depex_proxy(self, client, mocker):
        mock_response = Response(
            content=b'{"message": "success"}',
            status_code=200,
            media_type="application/json"
        )

        mock_handler = MagicMock()
        mock_handler.proxy_request = AsyncMock(return_value=mock_response)

        app.dependency_overrides[get_proxy_handler] = lambda: mock_handler

        response = client.get("/depex/graph/nodes")
        assert response.status_code == 200

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_vexgen_proxy(self, client, mocker):
        mock_response = Response(
            content=b'{"message": "success"}',
            status_code=200,
            media_type="application/json"
        )

        mock_handler = MagicMock()
        mock_handler.proxy_request = AsyncMock(return_value=mock_response)

        app.dependency_overrides[get_proxy_handler] = lambda: mock_handler

        response = client.post("/vexgen/vex/generate")
        assert response.status_code == 200

        app.dependency_overrides.clear()


@pytest.mark.integration
class TestRateLimiting:
    def test_rate_limit_health_endpoint(self, client):
        responses = []
        for _ in range(30):
            response = client.get("/health")
            responses.append(response.status_code)

        assert 429 in responses

    def test_rate_limit_proxy_endpoint(self, client, mocker):
        mock_response = Response(
            content=b'{"message": "success"}',
            status_code=200,
            media_type="application/json"
        )

        mock_handler = MagicMock()
        mock_handler.proxy_request = AsyncMock(return_value=mock_response)

        app.dependency_overrides[get_proxy_handler] = lambda: mock_handler

        responses = []
        for _ in range(80):
            response = client.get("/auth/test")
            responses.append(response.status_code)

        assert 429 in responses

        app.dependency_overrides.clear()


@pytest.mark.integration
class TestCORS:
    def test_cors_headers_present(self, client):
        response = client.get("/health", headers={"Origin": "http://example.com"})

        assert response.status_code == 200
        assert "access-control-allow-credentials" in response.headers
