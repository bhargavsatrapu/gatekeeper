from typing import Dict, Any
import psycopg2
from psycopg2.extras import Json

from sat_core.config import DB_CONFIG, SWAGGER_FILE
from sat_core.parse_swagger_file import parse_swagger
from sat_core.initialize_database import initialize_database


def insert_endpoint(ep: Dict[str, Any], conn) -> None:
    cur = conn.cursor()
    cur.execute(
        """
            INSERT INTO api_endpoints (
                path, method, summary, description, tags, operation_id, deprecated,
                consumes, produces, parameters, request_body, responses,
                security, examples, external_docs, x_additional_metadata
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            ON CONFLICT (path, method) DO UPDATE SET
                summary = EXCLUDED.summary,
                description = EXCLUDED.description,
                tags = EXCLUDED.tags,
                operation_id = EXCLUDED.operation_id,
                deprecated = EXCLUDED.deprecated,
                consumes = EXCLUDED.consumes,
                produces = EXCLUDED.produces,
                parameters = EXCLUDED.parameters,
                request_body = EXCLUDED.request_body,
                responses = EXCLUDED.responses,
                security = EXCLUDED.security,
                examples = EXCLUDED.examples,
                external_docs = EXCLUDED.external_docs,
                x_additional_metadata = EXCLUDED.x_additional_metadata;
        """,
        (
            ep["path"],
            ep["method"].upper(),
            ep.get("summary"),
            ep.get("description"),
            ep.get("tags", []),
            ep.get("operation_id"),
            ep.get("deprecated", False),
            ep.get("consumes", []),
            ep.get("produces", []),
            Json(ep.get("parameters")),
            Json(ep.get("request_body")),
            Json(ep.get("responses")),
            Json(ep.get("security")),
            Json(ep.get("examples")),
            Json(ep.get("external_docs")),
            Json(ep.get("x_additional_metadata")),
        ),
    )
    conn.commit()
    cur.close()


def insert_apis_into_db(swagger_file: str = SWAGGER_FILE) -> int:
    initialize_database()
    endpoints = parse_swagger(swagger_file)
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        for ep in endpoints:
            insert_endpoint(ep, conn)
    finally:
        conn.close()
    print(f"✅ Inserted {len(endpoints)} endpoints into DB (fully expanded schemas).")
    return len(endpoints)





