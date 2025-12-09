from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, status
from httpx import AsyncClient
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.constants import RateLimit
from app.dependencies import get_json_encoder, get_openapi_manager, get_proxy_handler
from app.limiter import limiter
from app.middleware import LogRequestMiddleware
from app.settings import settings
from app.utils import JSONEncoder, OpenAPIManager, ProxyHandler

DESCRIPTION = """
A tool for managing and interacting with all microservices developed by Secure Chain.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    openapi_manager: OpenAPIManager = get_openapi_manager()
    async with AsyncClient() as client:
        try:
            auth = await client.get(f"{settings.AUTH_SERVICE_URL}/openapi.json")
            auth.raise_for_status()
            depex = await client.get(f"{settings.DEPEX_SERVICE_URL}/openapi.json")
            depex.raise_for_status()
            vexgen = await client.get(f"{settings.VEXGEN_SERVICE_URL}/openapi.json")
            vexgen.raise_for_status()
            auth_schema = auth.json()
            depex_schema = depex.json()
            vexgen_schema = vexgen.json()
            app.openapi_schema = openapi_manager.merge_schemas(
                auth_schema, depex_schema, vexgen_schema
            )
            app.openapi = lambda: app.openapi_schema or {
                "openapi": "3.1.0",
                "info": {"title": "Error", "version": "0.0.0"},
                "paths": {},
            }
        except Exception as e:
            print(f"Failed to fetch OpenAPI specs: {e}")
            app.openapi = lambda: {
                "openapi": "3.1.0",
                "info": {"title": "Error", "version": "0.0.0"},
                "paths": {},
            }
    yield

app = FastAPI(
    title="Secure Chain Gateway",
    description=DESCRIPTION,
    docs_url=settings.DOCS_URL,
    version="1.1.1",
    contact={
        "name": "Secure Chain Team",
        "url": "https://github.com/securechaindev",
        "email": "hi@securechain.dev",
    },
    license_info={
        "name": "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "url": "https://www.gnu.org/licenses/gpl-3.0.html",
    },
    lifespan=lifespan
)
app.add_middleware(LogRequestMiddleware)
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
    tags=["Secure Chain Gateway Health"],
)
@limiter.limit(RateLimit.HEALTH_CHECK)
async def health_check(
    request: Request,
    json_encoder: JSONEncoder = Depends(get_json_encoder),
):
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=json_encoder.encode(
            {
                "detail": "healthy",
            }
        ),
    )


@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(RateLimit.PROXY_AUTH)
async def proxy_auth(
    path: str,
    request: Request,
    proxy_handler: ProxyHandler = Depends(get_proxy_handler),
):
    url = f"{settings.AUTH_SERVICE_URL}/{path}"
    return await proxy_handler.proxy_request(url, request)


@app.api_route("/depex/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(RateLimit.PROXY_DEPEX)
async def proxy_depex(
    path: str,
    request: Request,
    proxy_handler: ProxyHandler = Depends(get_proxy_handler),
):
    url = f"{settings.DEPEX_SERVICE_URL}/{path}"
    return await proxy_handler.proxy_request(url, request)


@app.api_route("/vexgen/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(RateLimit.PROXY_VEXGEN)
async def proxy_vexgen(
    path: str,
    request: Request,
    proxy_handler: ProxyHandler = Depends(get_proxy_handler),
):
    url = f"{settings.VEXGEN_SERVICE_URL}/{path}"
    return await proxy_handler.proxy_request(url, request)
