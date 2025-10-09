from typing import Any, Dict, List
import json
from sat_core.config import SWAGGER_FILE


def resolve_ref(ref: str, swagger: dict):
    if not ref.startswith("#/"):
        return None
    parts = ref.lstrip("#/").split("/")
    node = swagger
    for p in parts:
        node = node.get(p)
        if node is None:
            return None
    return node


def resolve_schema(schema, swagger, seen=None):
    if seen is None:
        seen = set()

    if isinstance(schema, dict):
        if "$ref" in schema:
            ref = schema["$ref"]
            if ref in seen:
                return {"$ref": ref}
            seen.add(ref)

            resolved = resolve_ref(ref, swagger)
            if resolved is None:
                return schema
            return resolve_schema(resolved, swagger, seen)

        return {k: resolve_schema(v, swagger, seen) for k, v in schema.items()}

    elif isinstance(schema, list):
        return [resolve_schema(item, swagger, seen) for item in schema]

    return schema


def parse_swagger(swagger_file: str = SWAGGER_FILE) -> List[Dict[str, Any]]:
    with open(swagger_file, "r", encoding="utf-8") as f:
        swagger = json.load(f)

    endpoints: List[Dict[str, Any]] = []
    paths = swagger.get("paths", {})

    for path, methods in paths.items():
        for method, details in methods.items():
            if "requestBody" in details:
                content = details["requestBody"].get("content", {})
                for mt, obj in content.items():
                    schema = obj.get("schema")
                    if schema:
                        details["requestBody"]["content"][mt]["schema"] = resolve_schema(schema, swagger)

            responses = details.get("responses", {})
            for status, resp in responses.items():
                if "schema" in resp:
                    resp["schema"] = resolve_schema(resp["schema"], swagger)
                elif "content" in resp:
                    for mt, obj in resp.get("content", {}).items():
                        if "schema" in obj:
                            obj["schema"] = resolve_schema(obj["schema"], swagger)

            parameters = details.get("parameters", [])
            for param in parameters:
                if "schema" in param:
                    param["schema"] = resolve_schema(param["schema"], swagger)

            ep = {
                "path": path,
                "method": method,
                "summary": details.get("summary"),
                "description": details.get("description"),
                "tags": details.get("tags", []),
                "operation_id": details.get("operationId"),
                "deprecated": details.get("deprecated", False),
                "consumes": details.get("consumes", []),
                "produces": details.get("produces", []),
                "parameters": details.get("parameters"),
                "request_body": details.get("requestBody"),
                "responses": details.get("responses"),
                "security": details.get("security"),
                "examples": details.get("examples"),
                "external_docs": details.get("externalDocs"),
                "x_additional_metadata": {k: v for k, v in details.items() if k.startswith("x-")},
            }

            endpoints.append(ep)

    return endpoints


if __name__ == "__main__":
    eps = parse_swagger()
    print(f"Parsed {len(eps)} endpoints")


