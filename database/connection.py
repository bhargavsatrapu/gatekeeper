"""
Database connection management for the API Testing Agent.

This module provides database connection handling, connection pooling,
and context managers for safe database operations.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Generator, Dict, Any, Optional
from config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseConnectionManager:
    """Manages database connections and provides context managers."""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize database connection manager.
        
        Args:
            config_dict: Database configuration dictionary. If None, uses global config.
        """
        self.config = config_dict or get_config().database.to_dict()
        self._connection = None
    
    @contextmanager
    def get_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """
        Get a database connection with automatic cleanup.
        
        Yields:
            psycopg2 connection object
            
        Raises:
            psycopg2.Error: If connection fails
        """
        connection = None
        try:
            logger.debug("Establishing database connection")
            connection = psycopg2.connect(**self.config)
            yield connection
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                connection.close()
                logger.debug("Database connection closed")
    
    @contextmanager
    def get_cursor(self, cursor_factory=None) -> Generator[psycopg2.extensions.cursor, None, None]:
        """
        Get a database cursor with automatic cleanup.
        
        Args:
            cursor_factory: Cursor factory (e.g., RealDictCursor)
            
        Yields:
            psycopg2 cursor object
        """
        with self.get_connection() as conn:
            cursor = None
            try:
                cursor = conn.cursor(cursor_factory=cursor_factory)
                yield cursor
            finally:
                if cursor:
                    cursor.close()
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    logger.info("Database connection test successful")
                    return result[0] == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseConnectionManager()


def get_db_manager() -> DatabaseConnectionManager:
    """Get the global database manager instance."""
    return db_manager


def test_database_connection() -> bool:
    """Test the database connection."""
    return db_manager.test_connection()
