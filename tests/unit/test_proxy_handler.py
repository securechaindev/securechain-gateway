from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Request
from httpx import Response as HTTPXResponse

from app.utils import ProxyHandler


class TestProxyHandler:
    @pytest.fixture
    def proxy_handler(self):
        return ProxyHandler()

    def test_filter_request_headers(self, proxy_handler):
        headers = [
            ("host", "example.com"),
            ("user-agent", "test"),
            ("connection", "keep-alive"),
            ("content-length", "100"),
            ("authorization", "Bearer token"),
        ]

        filtered = proxy_handler.filter_request_headers(headers)

        assert "user-agent" in filtered
        assert "authorization" in filtered
        assert "host" not in filtered
        assert "connection" not in filtered
        assert "content-length" not in filtered

    def test_filter_response_headers(self, proxy_handler):
        upstream_headers = {
            "content-type": "application/json",
            "content-length": "100",
            "date": "Mon, 01 Jan 2024 00:00:00 GMT",
            "server": "nginx",
            "x-custom-header": "value",
        }

        filtered = proxy_handler.filter_response_headers(upstream_headers)

        assert "content-type" in filtered
        assert "x-custom-header" in filtered
        assert "content-length" not in filtered
        assert "date" not in filtered
        assert "server" not in filtered

    def test_extract_cookies_with_get_list(self, proxy_handler):
        mock_headers = Mock()
        mock_headers.get_list = Mock(return_value=["cookie1=value1", "cookie2=value2"])

        cookies = proxy_handler.extract_cookies(mock_headers)

        assert len(cookies) == 2
        assert "cookie1=value1" in cookies
        assert "cookie2=value2" in cookies

    def test_extract_cookies_with_raw_headers(self, proxy_handler):
        mock_headers = Mock()
        mock_headers.get_list = Mock(return_value=[])
        mock_headers.raw = [
            (b"set-cookie", b"cookie1=value1"),
            (b"content-type", b"application/json"),
            (b"set-cookie", b"cookie2=value2"),
        ]

        cookies = proxy_handler.extract_cookies(mock_headers)

        assert len(cookies) == 2
        assert "cookie1=value1" in cookies
        assert "cookie2=value2" in cookies

    @pytest.mark.asyncio
    async def test_proxy_request_success(self, proxy_handler, mocker):
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers.items = Mock(return_value=[("user-agent", "test")])
        mock_request.query_params = {}
        mock_request.body = AsyncMock(return_value=b"")

        mock_response = Mock(spec=HTTPXResponse)
        mock_response.content = b'{"status": "ok"}'
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        mocker.patch("app.utils.proxy_handler.AsyncClient", return_value=mock_client)

        response = await proxy_handler.proxy_request("http://test.com", mock_request)

        assert response.status_code == 200
        assert response.body == b'{"status": "ok"}'

    @pytest.mark.asyncio
    async def test_proxy_request_error(self, proxy_handler, mocker):
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers.items = Mock(return_value=[])
        mock_request.query_params = {}
        mock_request.body = AsyncMock(return_value=b"")

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(side_effect=Exception("Connection error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        mocker.patch("app.utils.proxy_handler.AsyncClient", return_value=mock_client)

        response = await proxy_handler.proxy_request("http://test.com", mock_request)

        assert response.status_code == 502
