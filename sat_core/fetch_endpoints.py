from typing import List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from sat_core.config import DB_CONFIG


def fetch_endpoints() -> List[Dict[str, Any]]:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM api_endpoints")
    eps = cur.fetchall()
    cur.close()
    conn.close()
    return eps


if __name__ == "__main__":
    endpoints = fetch_endpoints()
    print(f"Fetched {len(endpoints)} endpoints")


