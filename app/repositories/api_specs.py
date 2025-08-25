from typing import Dict, List

# Simple JSON wrapper for PostgreSQL compatibility
Json = lambda x: x


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

TEST_CASES_DDL = (
    """
    CREATE TABLE IF NOT EXISTS test_cases (
        id SERIAL PRIMARY KEY,
        api_id INTEGER REFERENCES api_specs(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        description TEXT,
        test_type TEXT NOT NULL CHECK (test_type IN ('positive', 'negative')),
        request_body JSONB,
        expected_status INTEGER,
        expected_response_schema JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
)

REQUEST_BODIES_DDL = (
    """
    CREATE TABLE IF NOT EXISTS request_bodies (
        id SERIAL PRIMARY KEY,
        api_id INTEGER REFERENCES api_specs(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        description TEXT,
        request_body JSONB NOT NULL,
        is_valid BOOLEAN DEFAULT true,
        validation_errors JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
)

TEST_RESULTS_DDL = (
    """
    CREATE TABLE IF NOT EXISTS test_results (
        id SERIAL PRIMARY KEY,
        test_case_id INTEGER REFERENCES test_cases(id) ON DELETE CASCADE,
        api_id INTEGER REFERENCES api_specs(id) ON DELETE CASCADE,
        test_run_id INTEGER REFERENCES test_runs(id) ON DELETE CASCADE,
        status TEXT NOT NULL CHECK (status IN ('passed', 'failed', 'error')),
        response_status INTEGER,
        response_body JSONB,
        response_time_ms INTEGER,
        error_message TEXT,
        screenshot_path TEXT,
        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        test_duration_ms INTEGER
    );
    """
)

TEST_RUNS_DDL = (
    """
    CREATE TABLE IF NOT EXISTS test_runs (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        total_tests INTEGER DEFAULT 0,
        passed_tests INTEGER DEFAULT 0,
        failed_tests INTEGER DEFAULT 0,
        error_tests INTEGER DEFAULT 0,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        status TEXT DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed'))
    );
    """
)


def ensure_table(cur) -> None:
    cur.execute(DDL)
    cur.execute(TEST_CASES_DDL)
    cur.execute(REQUEST_BODIES_DDL)
    cur.execute(TEST_RESULTS_DDL)
    cur.execute(TEST_RUNS_DDL)


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


