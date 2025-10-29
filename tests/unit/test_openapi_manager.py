import pytest

from app.utils import OpenAPIManager


class TestOpenAPIManager:
    @pytest.fixture
    def openapi_manager(self):
        return OpenAPIManager()

    @pytest.fixture
    def sample_schema(self):
        return {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.1.0"},
            "paths": {
                "/health": {
                    "get": {
                        "summary": "Health check",
                        "responses": {"200": {"description": "OK"}},
                    }
                },
                "/users": {
                    "get": {
                        "summary": "List users",
                        "responses": {"200": {"description": "OK"}},
                    }
                },
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {"id": {"type": "integer"}},
                    }
                }
            },
        }

    def test_initialization_defaults(self):
        manager = OpenAPIManager()

        assert manager.title == "Secure Chain API Gateway"
        assert manager.version == "1.1.0"
        assert "Secure Chain Team" in manager.contact["name"]
        assert "GPL" in manager.license_info["name"]

    def test_initialization_custom(self):
        manager = OpenAPIManager(
            title="Custom Gateway",
            version="2.0.0",
            contact={"name": "Test Team"},
            license_info={"name": "MIT"},
        )

        assert manager.title == "Custom Gateway"
        assert manager.version == "2.0.0"
        assert manager.contact["name"] == "Test Team"
        assert manager.license_info["name"] == "MIT"

    def test_determine_tag_auth(self, openapi_manager):
        assert openapi_manager.determine_tag("/health", "Secure Chain Auth") == "Secure Chain Auth - Health"
        assert openapi_manager.determine_tag("/users", "Secure Chain Auth") == "Secure Chain Auth - User"

    def test_determine_tag_depex(self, openapi_manager):
        assert openapi_manager.determine_tag("/graph/nodes", "Secure Chain Depex") == "Secure Chain Depex - Graph"
        assert (
            openapi_manager.determine_tag("/operation/ssc/config", "Secure Chain Depex")
            == "Secure Chain Depex - Operation/SSC"
        )
        assert (
            openapi_manager.determine_tag("/operation/smt/upload", "Secure Chain Depex")
            == "Secure Chain Depex - Operation/SMT"
        )
        assert openapi_manager.determine_tag("/health", "Secure Chain Depex") == "Secure Chain Depex - Health"

    def test_determine_tag_vexgen(self, openapi_manager):
        assert openapi_manager.determine_tag("/vex/generate", "Secure Chain VEXGen") == "Secure Chain VEXGen - VEX"
        assert openapi_manager.determine_tag("/tix/create", "Secure Chain VEXGen") == "Secure Chain VEXGen - TIX"
        assert (
            openapi_manager.determine_tag("/vex_tix/combine", "Secure Chain VEXGen")
            == "Secure Chain VEXGen - VEX/TIX"
        )
        assert openapi_manager.determine_tag("/health", "Secure Chain VEXGen") == "Secure Chain VEXGen - Health"

    def test_prefix_and_tag_paths(self, openapi_manager, sample_schema):
        prefixed_paths, tags_used = openapi_manager.prefix_and_tag_paths(
            sample_schema, "/auth", "Secure Chain Auth"
        )

        assert "/auth/health" in prefixed_paths
        assert "/auth/users" in prefixed_paths
        assert "Secure Chain Auth - Health" in tags_used
        assert "Secure Chain Auth - User" in tags_used

        health_endpoint = prefixed_paths["/auth/health"]
        assert "get" in health_endpoint
        assert health_endpoint["get"]["tags"] == ["Secure Chain Auth - Health"]

    def test_merge_schemas(self, openapi_manager, sample_schema):
        auth_schema = sample_schema.copy()
        depex_schema = {
            "paths": {"/graph/nodes": {"get": {"summary": "Get nodes"}}},
            "components": {"schemas": {"Node": {"type": "object"}}},
        }
        vexgen_schema = {
            "paths": {"/vex/generate": {"post": {"summary": "Generate VEX"}}},
            "components": {"schemas": {"VEX": {"type": "object"}}},
        }

        merged = openapi_manager.merge_schemas(auth_schema, depex_schema, vexgen_schema)

        assert merged["openapi"] == "3.1.0"
        assert merged["info"]["title"] == "Secure Chain API Gateway"
        assert "/auth/health" in merged["paths"]
        assert "/depex/graph/nodes" in merged["paths"]
        assert "/vexgen/vex/generate" in merged["paths"]
        assert "User" in merged["components"]["schemas"]
        assert "Node" in merged["components"]["schemas"]
        assert "VEX" in merged["components"]["schemas"]
        assert len(merged["tags"]) > 0
