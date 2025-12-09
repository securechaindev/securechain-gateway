from typing import Any


class OpenAPIManager:
    def __init__(
        self,
        title: str = "Secure Chain API Gateway",
        version: str = "1.1.0",
        contact: dict[str, str] | None = None,
        license_info: dict[str, str] | None = None,
    ) -> None:
        self.title = title
        self.version = version
        self.contact = contact or {
            "name": "Secure Chain Team",
            "url": "https://github.com/securechaindev",
            "email": "hi@securechain.dev",
        }
        self.license_info = license_info or {
            "name": "GNU General Public License v3.0 or later (GPLv3+)",
            "url": "https://www.gnu.org/licenses/gpl-3.0.html",
        }

    def determine_tag(self, path: str, base_tag: str) -> str | None:
        match base_tag:
            case "Secure Chain Depex":
                if "/graph/" in path:
                    return f"{base_tag} - Graph"
                elif "/operation/ssc/" in path:
                    return f"{base_tag} - Operation/SSC"
                elif "/operation/smt/" in path:
                    return f"{base_tag} - Operation/SMT"
                else:
                    return f"{base_tag} - Health"

            case "Secure Chain VEXGen":
                if "/vex/" in path:
                    return f"{base_tag} - VEX"
                elif "/tix/" in path:
                    return f"{base_tag} - TIX"
                elif "/vex_tix/" in path:
                    return f"{base_tag} - VEX/TIX"
                else:
                    return f"{base_tag} - Health"

            case "Secure Chain Auth":
                if "/user" in path:
                    return f"{base_tag} - User"
                elif "/api-keys" in path:
                    return f"{base_tag} - API Keys"
                else:
                    return f"{base_tag} - Health"

    def prefix_and_tag_paths(
        self, schema: dict[str, Any], prefix: str, base_tag: str
    ) -> tuple[dict[str, Any], set[str]]:
        tagged_paths: dict[str, Any] = {}
        tags_used: set[str] = set()

        for path, methods in schema.get("paths", {}).items():
            full_path = path if path.startswith(prefix) else f"{prefix}{path}"
            tag = self.determine_tag(path, base_tag)
            if tag is not None:
                tags_used.add(tag)

            new_methods: dict[str, Any] = {}
            for method, details in methods.items():
                operation: dict[str, Any] = dict(details)
                operation["tags"] = [tag]
                new_methods[method] = operation

            tagged_paths[full_path] = new_methods

        return tagged_paths, tags_used

    def merge_schemas(
        self,
        auth_schema: dict[str, Any],
        depex_schema: dict[str, Any],
        vexgen_schema: dict[str, Any],
    ) -> dict[str, Any]:
        prefixed_auth_paths, auth_tags = self.prefix_and_tag_paths(
            auth_schema, "/auth", "Secure Chain Auth"
        )
        prefixed_depex_paths, depex_tags = self.prefix_and_tag_paths(
            depex_schema, "/depex", "Secure Chain Depex"
        )
        prefixed_vexgen_paths, vexgen_tags = self.prefix_and_tag_paths(
            vexgen_schema, "/vexgen", "Secure Chain VEXGen"
        )

        all_tags: list[str] = sorted(auth_tags.union(depex_tags).union(vexgen_tags))
        merged_tags: list[dict[str, str]] = [{"name": tag, "description": f"Endpoints for {tag}"} for tag in all_tags]

        merged: dict[str, Any] = {
            "openapi": "3.1.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "contact": self.contact,
                "license": self.license_info,
            },
            "paths": {
                **prefixed_auth_paths,
                **prefixed_depex_paths,
                **prefixed_vexgen_paths,
            },
            "components": {
                "schemas": {
                    **auth_schema.get("components", {}).get("schemas", {}),
                    **depex_schema.get("components", {}).get("schemas", {}),
                    **vexgen_schema.get("components", {}).get("schemas", {}),
                }
            },
            "tags": merged_tags,
        }

        return merged
