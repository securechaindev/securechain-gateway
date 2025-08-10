from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from httpx import AsyncClient
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.config import settings
from app.middleware import log_request_middleware
from app.utils import build_merged_openapi, proxy_request, json_encoder
from app.limiter import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncClient() as client:
        try:
            auth = await client.get("http://securechain-auth:8000/openapi.json")
            auth.raise_for_status()
            depex = await client.get("http://securechain-depex:8000/openapi.json")
            depex.raise_for_status()
            auth_schema = auth.json()
            depex_schema = depex.json()
            app.openapi_schema = build_merged_openapi(auth_schema, depex_schema)
            app.openapi = lambda: app.openapi_schema
        except Exception as e:
            print(f"Failed to fetch OpenAPI specs: {e}")
            app.openapi = lambda: {
                "openapi": "3.1.0",
                "info": {"title": "Error", "version": "0.0.0"},
                "paths": {},
            }
    yield

app = FastAPI(title="Secure Chain Gateway", docs_url=settings.DOCS_URL, lifespan=lifespan)
app.middleware("http")(log_request_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.GATEWAY_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    summary="Health Check",
    description="Check the status of the API.",
    response_description="API status.",
    tags=["Secure Chain Gateway Health"]
)
@limiter.limit("25/minute")
async def health_check(request: Request):
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=json_encoder(
            {
                "code": "healthy",
            }
        )
    )


@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("25/minute")
async def proxy_auth(path: str, request: Request):
    url = f"http://securechain-auth:8000/{path}"
    return await proxy_request(url, request)


@app.api_route("/depex/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("25/minute")
async def proxy_depex(path: str, request: Request):
    url = f"http://securechain-depex:8000/{path}"
    return await proxy_request(url, request)

