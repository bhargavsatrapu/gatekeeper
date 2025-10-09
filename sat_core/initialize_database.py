from sat_core.config import DB_CONFIG
import psycopg2


def initialize_database() -> None:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Reset the public schema to drop ALL existing tables and objects
    cur.execute("DROP SCHEMA IF EXISTS public CASCADE;")
    cur.execute("CREATE SCHEMA public;")

    # Recreate the main endpoints table
    cur.execute(
        """
        CREATE TABLE api_endpoints (
            id SERIAL PRIMARY KEY,
            path TEXT NOT NULL,
            method VARCHAR(10) NOT NULL,
            summary TEXT,
            description TEXT,
            tags TEXT[],
            operation_id TEXT,
            deprecated BOOLEAN DEFAULT FALSE,
            consumes TEXT[],
            produces TEXT[],
            parameters JSONB,
            request_body JSONB,
            responses JSONB,
            security JSONB,
            examples JSONB,
            external_docs JSONB,
            x_additional_metadata JSONB,
            UNIQUE(path, method)
        );
        """
    )

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database initialized")



