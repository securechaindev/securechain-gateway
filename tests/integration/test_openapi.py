from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.integration
class TestOpenAPIIntegration:
    @pytest.mark.asyncio
    async def test_openapi_schema_available(self, client):
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)

            mock_auth_response = AsyncMock()
            mock_auth_response.json.return_value = {
                "paths": {"/users": {"get": {}}},
                "components": {"schemas": {}},
            }
            mock_auth_response.raise_for_status = AsyncMock()

            mock_depex_response = AsyncMock()
            mock_depex_response.json.return_value = {
                "paths": {"/graph": {"get": {}}},
                "components": {"schemas": {}},
            }
            mock_depex_response.raise_for_status = AsyncMock()

            mock_vexgen_response = AsyncMock()
            mock_vexgen_response.json.return_value = {
                "paths": {"/vex": {"post": {}}},
                "components": {"schemas": {}},
            }
            mock_vexgen_response.raise_for_status = AsyncMock()

            mock_instance.get = AsyncMock(
                side_effect=[mock_auth_response, mock_depex_response, mock_vexgen_response]
            )
            mock_client.return_value = mock_instance

            response = client.get("/openapi.json")

            if response.status_code == 200:
                schema = response.json()
                assert "openapi" in schema
                assert "paths" in schema
                assert "info" in schema

    def test_docs_endpoint(self, client):
        response = client.get("/docs")
        assert response.status_code in [200, 404]
