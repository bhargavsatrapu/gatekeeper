from typing import Optional

from psycopg2.pool import SimpleConnectionPool  # type: ignore

from app.core.config import settings


_pool: Optional[SimpleConnectionPool] = None


def init_pool() -> None:
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            dbname=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            host=settings.db_host,
            port=settings.db_port,
        )


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


def get_conn():
    if _pool is None:
        raise RuntimeError("DB pool not initialized")
    return _pool.getconn()


def put_conn(conn) -> None:
    if _pool is not None and conn is not None:
        _pool.putconn(conn)


