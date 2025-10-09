from typing import Dict, Any
import re
import psycopg2
from psycopg2.extras import RealDictCursor, Json

from sat_core.config import DB_CONFIG
from sat_core.global_state import endpoint_tables, generated_cases
from sat_core.fetch_endpoints import fetch_endpoints


def sanitize_table_name(path: str, method: str) -> str:
    clean_path = re.sub(r"[^a-zA-Z0-9_]", "_", path.strip("/"))
    return f"api_testcases_{clean_path.lower()}_{method.lower()}"


def persist_test_cases() -> Dict[int, str]:
    endpoints = fetch_endpoints()

    with psycopg2.connect(**DB_CONFIG) as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        for ep in endpoints:
            endpoint_id = ep["id"]
            method = ep["method"]
            path = ep["path"]
            endpoint_key = f"{method} {path}"

            cases = generated_cases.get(endpoint_key, [])
            if not cases:
                continue

            table_name = sanitize_table_name(path, method)
            endpoint_tables[endpoint_id] = table_name

            cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            cur.execute(
                f"""
                CREATE TABLE {table_name} (
                    id SERIAL PRIMARY KEY,
                    endpoint_id INTEGER NOT NULL,
                    test_type VARCHAR(50),
                    test_name VARCHAR(255),
                    method VARCHAR(10),
                    url TEXT,
                    headers JSONB,
                    query_params JSONB,
                    path_params JSONB,
                    input_payload JSONB,
                    expected_status VARCHAR(10),
                    expected_schema JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            for tc in cases:
                cur.execute(
                    f"""
                    INSERT INTO {table_name}
                    (endpoint_id, test_type, test_name, method, url, headers,
                     query_params, path_params, input_payload, expected_status, expected_schema)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        endpoint_id,
                        tc.get("test_type"),
                        tc.get("test_name"),
                        tc.get("method"),
                        tc.get("url"),
                        Json(tc.get("headers") or {}),
                        Json(tc.get("query_params") or {}),
                        Json(tc.get("path_params") or {}),
                        Json(tc.get("input_payload") or {}),
                        tc.get("expected_status"),
                        Json(tc.get("expected_schema") or {}),
                    ),
                )

        conn.commit()

    print("✅ endpoint_tables updated", endpoint_tables)
    return endpoint_tables


if __name__ == "__main__":
    persist_test_cases()


