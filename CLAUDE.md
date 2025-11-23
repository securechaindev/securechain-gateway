# Project Context - Secure Chain Gateway

This document serves as memory and context for AI agents working on this project across different sessions.

## General Project Information

- **Name**: Secure Chain Gateway
- **Version**: 1.1.1
- **License**: GPL-3.0-or-later
- **Python**: >= 3.13
- **Framework**: FastAPI 0.116.1
- **Package Manager**: uv (recommended for dependency management)
- **Repository**: https://github.com/securechaindev/securechain-gateway

## Project Purpose

Secure Chain Gateway is an **API Gateway** that acts as a single, centralized entry point to manage access to all microservices in the Secure Chain platform. It provides a unified API interface with security features, rate limiting, and logging.

## Architecture

### Integrated Microservices

The gateway proxies to three main microservices:

1. **securechain-auth** (internal port 8000)
   - Authentication and user management
   - Endpoints under `/auth/*`
   - Uses JWT for authentication

2. **securechain-depex** (internal port 8000)
   - Dependency analysis and graphs
   - Endpoints under `/depex/*`
   - Categories:
     - `/graph/*` - Graph operations
     - `/operation/ssc/*` - Supply Chain Configuration
     - `/operation/file/*` - File operations
     - `/operation/config/*` - Configuration

3. **securechain-vexgen** (internal port 8000)
   - VEX (Vulnerability Exploitability eXchange) generation
   - TIX (Threat Intelligence eXchange) generation
   - Endpoints under `/vexgen/*`
   - Categories:
     - `/vex/*` - VEX endpoints
     - `/tix/*` - TIX endpoints
     - `/vex_tix/*` - Combined endpoints

### Networking

- **Docker Network**: `securechain` (must exist before deployment)
- **Exposed Port**: 8000
- **Internal Communication**: HTTP between containers

## Code Structure

```
securechain-gateway/
├── app/
│   ├── main.py              # Main entry point, route definitions
│   ├── settings.py          # Configuration with Pydantic Settings
│   ├── middleware.py        # Custom middleware for logging
│   ├── limiter.py          # Rate limiting configuration (SlowAPI)
│   ├── logger.py           # Logging configuration
│   ├── constants.py        # Project constants (e.g., HOP_BY_HOP_HEADERS)
│   ├── dependencies.py     # Dependency injection with ServiceContainer
│   └── utils/
│       ├── __init__.py      # Exports for utilities
│       ├── json_encoder.py  # Custom JSON encoder
│       └── openapi_merge.py # ProxyHandler and OpenAPIManager classes
├── tests/
│   ├── conftest.py         # Shared fixtures and test configuration
│   ├── unit/               # Unit tests (12 tests)
│   │   ├── test_proxy_handler.py
│   │   └── test_openapi_manager.py
│   └── integration/        # Integration tests (9 tests)
│       ├── test_endpoints.py
│       └── test_openapi.py
├── dev/
│   ├── docker-compose.yml   # Compose for development
│   └── Dockerfile          # Development Dockerfile
├── Dockerfile              # Production Dockerfile
├── pyproject.toml          # Project configuration and dependencies
├── template.env            # Environment variables template
└── README.md               # Main documentation
```

## Dependency Injection

The project uses a **Singleton ServiceContainer** pattern for dependency injection with FastAPI's `Depends()`:

### ServiceContainer Pattern

**File**: `app/dependencies.py`

The `ServiceContainer` class manages all service instances as a singleton:
- Ensures only one instance of each service exists
- Uses lazy initialization (creates services on first access)
- Provides a `reset()` method for testing

```python
class ServiceContainer:
    instance: Optional["ServiceContainer"] = None
    json_encoder_obj: Optional[JSONEncoder] = None
    proxy_handler_obj: Optional[ProxyHandler] = None
    openapi_manager_obj: Optional[OpenAPIManager] = None
    
    def __new__(cls):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance
    
    @property
    def json_encoder(self) -> JSONEncoder:
        if self.json_encoder_obj is None:
            self.json_encoder_obj = JSONEncoder()
        return self.json_encoder_obj
```

### Usage in Endpoints

Services are injected using FastAPI's `Depends()`:

```python
@app.get("/health")
async def health_check(
    encoder: JSONEncoder = Depends(get_json_encoder)
):
    return encoder.encode_response({"status": "healthy"})

@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_auth(
    path: str,
    request: Request,
    proxy_handler: ProxyHandler = Depends(get_proxy_handler),
):
    url = f"http://securechain-auth:8000/{path}"
    return await proxy_handler.proxy_request(url, request)
```

### Testing with Dependency Overrides

Tests can override dependencies using `app.dependency_overrides`:

```python
from unittest.mock import AsyncMock, MagicMock
from app.dependencies import get_proxy_handler

mock_handler = MagicMock()
mock_handler.proxy_request = AsyncMock(return_value=mock_response)
app.dependency_overrides[get_proxy_handler] = lambda: mock_handler
```

### Code Style

- **No underscore prefixes** for attributes (except special methods like `__new__`)
- **Minimal documentation** - code should be self-explanatory
- **No private methods** - all methods are public

## Main Features

### 1. Rate Limiting
- Health check: 25 requests/minute
- Proxy endpoints: 75 requests/minute
- Implemented with SlowAPI
- **Centralized in constants**: `RateLimit` enum in `app/constants.py`
  - `HEALTH_CHECK = "25/minute"`
  - `PROXY_AUTH = "75/minute"`
  - `PROXY_DEPEX = "75/minute"`
  - `PROXY_VEXGEN = "75/minute"`

### 2. CORS
- Configured via `GATEWAY_ALLOWED_ORIGINS` in `.env`
- Allows credentials, all methods and headers

### 3. Logging
- Custom middleware `LogRequestMiddleware`
- Logs all incoming requests with timing information
- Rotating file handler (5MB per file, 5 backups)
- Located in `logs/errors.log`

### 4. Unified OpenAPI
- On startup, the gateway fetches OpenAPI schemas from all 3 microservices
- Merges them into a single schema with organized prefixes and tags
- Available at `/docs` (if `DOCS_URL` is not disabled)

### 5. Transparent Proxy
- `ProxyHandler` class in `utils/openapi_merge.py`
- Filters hop-by-hop headers (defined in `app/constants.py`)
- Preserves cookies (including multiple Set-Cookie headers)
- Error handling with 502 status code

### 6. Class-Based Architecture
- **ProxyHandler**: Handles HTTP proxying with header filtering
  - `filter_request_headers()` - Filters incoming headers
  - `filter_response_headers()` - Filters outgoing headers
  - `extract_cookies()` - Handles Set-Cookie headers
  - `proxy_request()` - Main proxy method (async)
  
- **OpenAPIManager**: Manages OpenAPI schema merging
  - `determine_tag()` - Organizes endpoints by service
  - `prefix_and_tag_paths()` - Adds prefixes to paths
  - `merge_schemas()` - Combines schemas from all services

### 7. Configurable Microservices URLs
- All microservice URLs are configurable via environment variables
- `AUTH_SERVICE_URL` - Default: `http://securechain-auth:8000`
- `DEPEX_SERVICE_URL` - Default: `http://securechain-depex:8000`
- `VEXGEN_SERVICE_URL` - Default: `http://securechain-vexgen:8000`
- No hardcoded URLs in the codebase

## Environment Variables

Configured in `.env` file (see `template.env`):

### Gateway Configuration
- `DOCS_URL`: Documentation URL (None to disable in production)
- `GATEWAY_ALLOWED_ORIGINS`: Allowed origins for CORS (JSON array as string)

### Microservices URLs
- `AUTH_SERVICE_URL`: Base URL for authentication microservice
- `DEPEX_SERVICE_URL`: Base URL for dependency analysis microservice
- `VEXGEN_SERVICE_URL`: Base URL for VEX/TIX generation microservice

## Main Dependencies

### Production
- `fastapi==0.116.1` - Web framework
- `uvicorn==0.35.0` - ASGI server
- `httpx==0.28.1` - Async HTTP client
- `slowapi==0.1.9` - Rate limiting
- `pydantic-settings==2.10.1` - Configuration management

### Development
- `ruff==0.14.0` - Linter and formatter

### Testing
- `pytest==8.4.2`
- `pytest-asyncio==1.2.0`
- `pytest-cov>=7.0.0`

## Dependency Management with uv

This project uses **uv** as the recommended package manager for faster and more reliable dependency management.

### Installing uv

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Common uv Commands

```bash
# Install dependencies from pyproject.toml
uv pip install -e .

# Install development dependencies
uv pip install -e ".[dev]"

# Install test dependencies
uv pip install -e ".[test]"

# Install all optional dependencies
uv pip install -e ".[dev,test]"

# Add a new dependency
uv pip install package-name

# Sync dependencies (ensures exact versions)
uv pip sync

# Create a virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

### Why uv?

- **Fast**: 10-100x faster than pip
- **Reliable**: Better dependency resolution
- **Drop-in replacement**: Compatible with pip commands
- **Modern**: Built in Rust, actively maintained

## Deployment

### Development
```bash
docker compose -f dev/docker-compose.yml up --build
```

### Production
The main Dockerfile is optimized for production.

### Prerequisites
1. Docker network `securechain` created
2. All 3 microservices (auth, depex, vexgen) must be running
3. Databases (MongoDB, Neo4J) operational

## Testing

### Test Organization
- **22 tests total** with **90% code coverage**
- Unit tests: 12 tests (ProxyHandler: 7, OpenAPIManager: 5)
- Integration tests: 10 tests (endpoints, rate limiting, CORS, OpenAPI)

### Test Structure
```
tests/
├── conftest.py              # Shared fixtures (client, reset_limiter)
├── unit/
│   ├── test_proxy_handler.py      # 7 tests - 100% coverage
│   └── test_openapi_manager.py    # 10 tests - 100% coverage
└── integration/
    ├── test_endpoints.py           # 7 tests (health, proxy, rate limits, CORS)
    └── test_openapi.py             # 2 tests (schema, docs)
```

### Running Tests
```bash
# Run all tests with coverage
pytest tests/ -v --cov=app

# Run specific test types
pytest tests/unit/ -v          # Unit tests only
pytest tests/integration/ -v   # Integration tests only

# Run with markers
pytest -m unit                 # Tests marked as @pytest.mark.unit
pytest -m integration          # Tests marked as @pytest.mark.integration
```

### Test Features
- **AsyncMock** for async method testing
- **Dependency overrides** for mocking services
- **Rate limiter reset** fixture between tests
- **100% pass rate** maintained

### Coverage Report
- Overall: 90%
- ProxyHandler: 96%
- OpenAPIManager: 100%
- Dependencies: 81% (reset method not used in production)

## Deployment

### Development
```bash
docker compose -f dev/docker-compose.yml up --build
```

### Production
The main Dockerfile is optimized for production.

### Prerequisites
1. Docker network `securechain` created
2. All 3 microservices (auth, depex, vexgen) must be running
3. Databases (MongoDB, Neo4J) operational
## Linting and Formatting

Configured with Ruff:
```bash
ruff check app/     # Check for linting errors
ruff format app/    # Format code
```

## Code Style and Best Practices

### Type Hints
- **Complete type hints** on all functions and methods
- **No `dict` without types** - Always use `dict[str, Any]` or specific types
- **Return types explicit** - All methods indicate return type (including `-> None`)
- **Variable annotations** - Important variables have type hints
- Examples:
  ```python
  def filter_response_headers(self, upstream_headers: dict[str, Any]) -> dict[str, str]:
      filtered: dict[str, str] = {}
      ...
  
  async def dispatch(self, request: Request, call_next: Callable) -> Response:
      ...
  
  def __init__(...) -> None:
      ...
  ```

### Naming Conventions
- **No private methods/attributes** - No underscore prefix on methods or properties
- **Exception**: Special methods like `__init__`, `__new__`, `__all__` are allowed
- **Public API** - All methods and properties are public
- Examples:
  - ✅ `json_encoder_obj` (not `_json_encoder_obj`)
  - ✅ `filter_headers()` (not `_filter_headers()`)
  - ✅ `proxy_request()` (not `_proxy_request()`)

### Documentation Style
- **Minimal documentation** - Code should be self-explanatory
- **No docstrings unless necessary** - Focus on clear naming
- **Type hints as documentation** - Types explain what functions do
- **Comments only for complex logic** - Avoid obvious comments

### Async/Await
- **Proper async/await usage** throughout
- **AsyncMock** for testing async methods
- **async with** for context managers (AsyncClient)
- All I/O operations are async

## Important Notes

1. **Lifecycle Management**: The gateway attempts to connect to microservices on startup. If it fails, it uses an empty OpenAPI schema to avoid crashes.

2. **Headers Filtering**: Hop-by-hop and other problematic headers are filtered to ensure a clean proxy.

3. **Cookie Handling**: Special implementation to preserve multiple Set-Cookie headers.

4. **Tag Organization**: Endpoints are automatically organized by categories in the OpenAPI documentation.

5. **Error Handling**: Proxy errors return 502 with `{"code":"internal_error"}`.

6. **Rate Limits as Constants**: All rate limits defined in `RateLimit` enum for easy maintenance.

7. **Configurable URLs**: No hardcoded microservice URLs - all configurable via environment variables.

## Contact Information

- **Email**: hi@securechain.dev
- **Organization**: https://github.com/securechaindev
- **Documentation**: https://securechaindev.github.io/

## Important Change History

### v1.1.1 (Current)
- Current project version
- Python 3.13 as minimum requirement
- Migration to uv for dependency management (recommended)
- Refactored to class-based architecture:
  - `ProxyHandler` class for HTTP proxying
  - `OpenAPIManager` class for OpenAPI schema management
- Added comprehensive test suite:
  - 22 tests total (12 unit + 10 integration)
  - 90% code coverage
  - Automatic rate limiter reset between tests
- Dependency injection with ServiceContainer singleton pattern
- Constants extracted to `app/constants.py`:
  - `HOP_BY_HOP_HEADERS` set
  - `RateLimit` enum for all rate limits
- Configurable microservice URLs via environment variables
- Complete type hints across all files
- No private methods/attributes (no underscore prefix)
- Improved logging with detailed request tracking

---

**Last updated**: October 29, 2025
**Test Coverage**: 90% (22/22 tests passing)
**Code Quality**: 0 linting errors, complete type hints
