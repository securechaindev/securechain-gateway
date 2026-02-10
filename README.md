# Secure Chain Gateway

Secure Chain Gateway is an API Gateway that provides a unified interface for all Secure Chain microservices. It acts as a single entry point with features like rate limiting, CORS management, request logging, and unified OpenAPI documentation.

## Features

- 🚪 **Single Entry Point** - Unified API interface for all microservices
- 🔒 **Rate Limiting** - Configurable limits per endpoint (25-75 req/min)
- 🌐 **CORS Management** - Configurable cross-origin resource sharing
- 📝 **Request Logging** - Detailed logging with timing information
- 📚 **Unified OpenAPI** - Merged documentation from all microservices
- 🔄 **Transparent Proxy** - Smart header filtering and cookie preservation
- ⚡ **High Performance** - Async/await throughout, tested with 90% coverage
- 🎯 **Type Safe** - Complete type hints for better IDE support

## Architecture

The gateway proxies requests to three microservices:

- **securechain-auth** (`/auth/*`) - Authentication and user management
- **securechain-depex** (`/depex/*`) - Dependency analysis and graphs
- **securechain-vexgen** (`/vexgen/*`) - VEX/TIX generation

## Development requirements

1. [Docker](https://www.docker.com/) to deploy the tool
2. [Docker Compose](https://docs.docker.com/compose/) for container orchestration
3. Python 3.13 or higher
4. [uv](https://github.com/astral-sh/uv) (recommended for faster dependency management)
5. The Neo4J browser interface is available at [localhost:7474](http://0.0.0.0:7474/browser/)
6. [MongoDB Compass](https://www.mongodb.com/en/products/compass) recommended for database GUI

### Database Access

- **Neo4j Browser**: http://localhost:7474
- **MongoDB**: Use [MongoDB Compass](https://www.mongodb.com/products/compass)

## Deployment with docker

### 1. Clone the repository
Clone the repository from the official GitHub repository:
```bash
git clone https://github.com/securechaindev/securechain-gateway.git
cd securechain-gateway
```

### 2. Configure environment variables
Create a `.env` file from the `.env.template` file and place it inside app directory.

#### Get API Keys

- How to get a *GitHub* [API key](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

- Modify the **Json Web Token (JWT)** secret key and algorithm with your own. You can generate your own secret key with the command **openssl rand -base64 32**.

### 3. Create Docker network
Ensure you have the `securechain` Docker network created. If not, create it with:
```bash
docker network create securechain
```

### 4. Databases containers

For graphs and vulnerabilities information you need to download the zipped [data dumps](https://doi.org/10.5281/zenodo.16739080) from Zenodo. Once you have unzipped the dumps, inside the root folder run the command:
```bash
docker compose up --build
```

The containerized databases will also be seeded automatically.

### 5. Start the application
Run the command from the project root:
```bash
docker compose -f dev/docker-compose.yml up --build
```

### 6. Access the application
The API will be available at [http://localhost:8080](http://localhost:8080). You can access the API documentation at [http://localhost:8080/docs](http://localhost:8080/docs).

## Development Environment

The project uses Python 3.14 and [uv](https://github.com/astral-sh/uv) as the package manager for faster and more reliable dependency management.

### Setting up the development environment with uv

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Activate virtual environment
uv venv
source .venv/bin/activate

# Install dependencies (automatically creates venv)
uv sync

```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=app --cov-report=term-missing

# Run specific test file
uv run pytest tests/integration/test_endpoints.py -v
```

### Code Quality

```bash
# Install linter
uv sync --extra dev

# Linting
uv run ruff check app/

# Formatting
uv run ruff format app/
```

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License
[GNU General Public License 3.0](https://www.gnu.org/licenses/gpl-3.0.html)

## Links
- [Secure Chain Team](mailto:hi@securechain.dev)
- [Secure Chain Organization](https://github.com/securechaindev)
- [Secure Chain Documentation](https://securechaindev.github.io/)
