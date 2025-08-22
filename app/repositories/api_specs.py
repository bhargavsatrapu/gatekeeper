from typing import Dict, List

from psycopg2.extras import Json  # type: ignore


DDL = (
    """
    CREATE TABLE IF NOT EXISTS api_specs (
        id SERIAL PRIMARY KEY,
        method TEXT,
        path TEXT,
        summary TEXT,
        parameters JSONB,
        request_body JSONB,
        responses JSONB,
        response_refs JSONB,
        response_refs_resolved JSONB,
        auth JSONB
    );
    """
)


def ensure_table(cur) -> None:
    cur.execute(DDL)


def insert_operations(swagger: dict, cur) -> int:
    inserted = 0
    for path, methods in (swagger.get("paths", {}) or {}).items():
        if not isinstance(methods, dict):
            continue
        for method, details in methods.items():
            if not isinstance(details, dict):
                continue
            summary = details.get("summary", "")
            parameters = details.get("parameters", [])
            request_body = details.get("requestBody", {})
            responses = details.get("responses", {})
            auth = details.get("security", [])

            ref_values: List[str] = []
            resolved_values: List[dict] = []

            for _, resp in (responses or {}).items():
                schema = (
                    (resp or {}).get("content", {})
                    .get("application/json", {})
                    .get("schema", {})
                )
                if isinstance(schema, dict):
                    if "$ref" in schema:
                        ref_values.append(schema["$ref"])  # type: ignore
                        resolved_values.append(_resolve_ref(swagger, schema["$ref"]))  # type: ignore
                    else:
                        items = schema.get("items") if isinstance(schema.get("items"), dict) else None
                        if items and "$ref" in items:
                            ref_values.append(items["$ref"])  # type: ignore
                            resolved_values.append(_resolve_ref(swagger, items["$ref"]))  # type: ignore

            cur.execute(
                """
                INSERT INTO api_specs (
                    method, path, summary, parameters, request_body,
                    responses, response_refs, response_refs_resolved, auth
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(method).upper(),
                    path,
                    summary,
                    Json(parameters),
                    Json(request_body),
                    Json(responses),
                    Json(ref_values),
                    Json(resolved_values),
                    Json(auth),
                ),
            )
            inserted += 1
    return inserted


def _resolve_ref(swagger: dict, ref: str) -> dict:
    parts = ref.lstrip("#/").split("/")
    node: dict = swagger
    for part in parts:
        node = node.get(part, {}) if isinstance(node, dict) else {}
    return node


