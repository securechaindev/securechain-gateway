from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from httpx import AsyncClient


async def proxy_request(url: str, request: Request) -> Response:
    async with AsyncClient() as client:
        method = request.method
        headers = dict(request.headers)
        body = await request.body()
        try:
            proxied_response = await client.request(
                method, url, headers=headers, content=body, params=request.query_params
            )
            return Response(
                content=proxied_response.content,
                status_code=proxied_response.status_code,
                headers=dict(proxied_response.headers),
                media_type=proxied_response.headers.get("content-type"),
            )
        except Exception as e:
            return JSONResponse(status_code=502, content={"error": str(e)})


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
                tag = base_tag
        else:
            tag = base_tag
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
    title: str = "Secure Chain API Gateway",
    version: str = "1.0.0"
) -> dict[str, Any]:
    from .openapi_merge import prefix_and_tag_paths
    prefixed_auth_paths, auth_tags = prefix_and_tag_paths(auth_schema, "/auth", "Secure Chain Auth")
    prefixed_depex_paths, depex_tags = prefix_and_tag_paths(depex_schema, "/depex", "Secure Chain Depex")
    all_tags = sorted(auth_tags.union(depex_tags))
    merged_tags = [{"name": tag, "description": f"Endpoints for {tag}"} for tag in all_tags]
    merged = {
        "openapi": "3.1.0",
        "info": {"title": title, "version": version},
        "paths": {**prefixed_auth_paths, **prefixed_depex_paths},
        "components": {
            "schemas": {
                **auth_schema.get("components", {}).get("schemas", {}),
                **depex_schema.get("components", {}).get("schemas", {}),
            }
        },
        "tags": merged_tags
    }
    return merged
