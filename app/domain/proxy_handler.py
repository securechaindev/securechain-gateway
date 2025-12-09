from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from httpx import AsyncClient

from app.constants import HOP_BY_HOP_HEADERS
from app.logger import logger


class ProxyHandler:
    def __init__(self, follow_redirects: bool = False) -> None:
        self.follow_redirects = follow_redirects

    def filter_request_headers(self, items: list[tuple[str, str]]) -> dict[str, str]:
        skip = HOP_BY_HOP_HEADERS | {"host", "content-length"}
        return {k: v for k, v in items if k.lower() not in skip}

    def filter_response_headers(self, upstream_headers: dict[str, Any]) -> dict[str, str]:
        skip = HOP_BY_HOP_HEADERS | {"content-length", "date", "server", "set-cookie"}
        filtered: dict[str, str] = {}
        for k, v in upstream_headers.items():
            if k.lower() not in skip:
                filtered[k] = v
        return filtered

    def extract_cookies(self, upstream_headers: Any) -> list[str]:
        set_cookies: list[str] = []

        if hasattr(upstream_headers, "get_list"):
            set_cookies = upstream_headers.get_list("set-cookie") or []

        if not set_cookies:
            raw = getattr(upstream_headers, "raw", None)
            if raw is not None:
                for k, v in raw:
                    name = k.decode("latin1") if isinstance(k, (bytes, bytearray)) else str(k)
                    if name.lower() == "set-cookie":
                        value = v.decode("latin1") if isinstance(v, (bytes, bytearray)) else str(v)
                        set_cookies.append(value)

        return set_cookies

    async def proxy_request(self, url: str, request: Request) -> Response:
        try:
            async with AsyncClient(follow_redirects=self.follow_redirects) as client:
                upstream = await client.request(
                    request.method,
                    url,
                    headers=self.filter_request_headers(request.headers.items()),
                    params=request.query_params,
                    content=await request.body(),
                )

            resp = Response(
                content=upstream.content,
                status_code=upstream.status_code,
                media_type=upstream.headers.get("content-type"),
            )

            filtered_headers = self.filter_response_headers(dict(upstream.headers))
            for k, v in filtered_headers.items():
                resp.headers[k] = v

            set_cookies = self.extract_cookies(upstream.headers)
            if set_cookies:
                raw_headers = list(resp.raw_headers)
                for cookie in set_cookies:
                    raw_headers.append((b"set-cookie", cookie.encode("latin1")))
                resp.raw_headers = raw_headers

            return resp

        except Exception as e:
            logger.error(f"Proxy request failed: {e}")
            return JSONResponse(status_code=502, content={"code": "internal_error"})
