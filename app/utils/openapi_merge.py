from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from httpx import AsyncClient

from app.logger import logger

HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

def _filtered_request_headers(items: list[tuple[str, str]]) -> dict:
    skip = HOP_BY_HOP | {"host", "content-length"}
    return {k: v for k, v in items if k.lower() not in skip}


async def proxy_request(url: str, request: Request) -> Response:
    try:
        async with AsyncClient(follow_redirects=False) as client:
            upstream = await client.request(
                request.method,
                url,
                headers=_filtered_request_headers(request.headers.items()),
                params=request.query_params,
                content=await request.body(),
            )
        resp = Response(
            content=upstream.content,
            status_code=upstream.status_code,
            media_type=upstream.headers.get("content-type"),
        )
        skip_out = HOP_BY_HOP | {"content-length", "date", "server", "set-cookie"}
        for k, v in upstream.headers.items():
            if k.lower() in skip_out:
                continue
            resp.headers[k] = v
        set_cookies: list[str] = []
        if hasattr(upstream.headers, "get_list"):
            set_cookies = upstream.headers.get_list("set-cookie") or []
        if not set_cookies:
            raw = getattr(upstream.headers, "raw", None)
            if raw is not None:
                for k, v in raw:
                    name = k.decode("latin1") if isinstance(k, (bytes, bytearray)) else str(k)
                    if name.lower() == "set-cookie":
                        value = v.decode("latin1") if isinstance(v, (bytes, bytearray)) else str(v)
                        set_cookies.append(value)
        if set_cookies:
            raw_headers = list(resp.raw_headers)
            for sc in set_cookies:
                raw_headers.append((b"set-cookie", sc.encode("latin1")))
            resp.raw_headers = tuple(raw_headers)
        return resp
    except Exception as e:
        logger.error(f"Proxy request failed: {e}")
        return JSONResponse(status_code=502, content={"code":"internal_error"})


def prefix_and_tag_paths(
    schema: dict, prefix: str, base_tag: str
) -> tuple[dict, set]:
    tagged_paths = {}
    tags_used = set()
    for path, methods in schema["paths"].items():
        full_path = path if path.startswith(prefix) else f"{prefix}{path}"
        if base_tag == "Secure Chain Depex":
            if "/graph/" in path:
                tag = f"{base_tag} - Graph"
            elif "/operation/file/" in path:
                tag = f"{base_tag} - Operation/File"
            elif "/operation/config/" in path:
                tag = f"{base_tag} - Operation/Config"
            else:
                tag = f"{base_tag} Health"
        elif base_tag == "Secure Chain VEXGen":
            if "/vex/" in path:
                tag = f"{base_tag} - VEX"
            elif "/tix/" in path:
                tag = f"{base_tag} - TIX"
            elif "/vex_tix/" in path:
                tag = f"{base_tag} - VEX/TIX"
            else:
                tag = f"{base_tag} - Health"
        else:
            if "/health" in path:
                tag = f"{base_tag} - Health"
            else:
                tag = f"{base_tag}"
        tags_used.add(tag)
        new_methods = {}
        for method, details in methods.items():
            operation = dict(details)
            operation["tags"] = [tag]
            new_methods[method] = operation
        tagged_paths[full_path] = new_methods
    return tagged_paths, tags_used


def build_merged_openapi(
    auth_schema: dict[str, Any],
    depex_schema: dict[str, Any],
    vexgen_schema: dict[str, Any],
    title: str = "Secure Chain API Gateway",
    version: str = "1.0.0"
) -> dict[str, Any]:
    from .openapi_merge import prefix_and_tag_paths
    prefixed_auth_paths, auth_tags = prefix_and_tag_paths(auth_schema, "/auth", "Secure Chain Auth")
    prefixed_depex_paths, depex_tags = prefix_and_tag_paths(depex_schema, "/depex", "Secure Chain Depex")
    prefixed_vexgen_paths, vexgen_tags = prefix_and_tag_paths(vexgen_schema, "/vexgen", "Secure Chain VEXGen")
    all_tags = sorted(auth_tags.union(depex_tags).union(vexgen_tags))
    merged_tags = [{"name": tag, "description": f"Endpoints for {tag}"} for tag in all_tags]
    merged = {
        "openapi": "3.1.0",
        "info": {
            "title": title,
            "version": version,
            "contact": {
                "name": "Secure Chain Team",
                "url": "https://github.com/securechaindev",
                "email": "hi@securechain.dev",
            },
            "license": {
                "name": "GNU General Public License v3.0 or later (GPLv3+)",
                "url": "https://www.gnu.org/licenses/gpl-3.0.html",
            },
        },
        "paths": {**prefixed_auth_paths, **prefixed_depex_paths, **prefixed_vexgen_paths},
        "components": {
            "schemas": {
                **auth_schema.get("components", {}).get("schemas", {}),
                **depex_schema.get("components", {}).get("schemas", {}),
                **vexgen_schema.get("components", {}).get("schemas", {}),
            }
        },
        "tags": merged_tags
    }
    return merged
