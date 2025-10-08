"""
Database models and schema definitions for the API Testing Agent.

This module contains database table schemas, data models, and
database initialization functions.
"""

import psycopg2
from psycopg2.extras import Json
from typing import Dict, Any, List, Optional
from database.connection import get_db_manager
from utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseSchema:
    """Database schema definitions and operations."""
    
    @staticmethod
    def get_api_endpoints_schema() -> str:
        """
        Get the SQL schema for the api_endpoints table.
        
        Returns:
            SQL CREATE TABLE statement
        """
        return """
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(path, method)
        );
        """
    
    @staticmethod
    def get_test_cases_schema(table_name: str) -> str:
        """
        Get the SQL schema for test cases table.
        
        Args:
            table_name: Name of the test cases table
            
        Returns:
            SQL CREATE TABLE statement
        """
        return f"""
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
        );
        """
    
    @staticmethod
    def get_execution_logs_schema() -> str:
        """
        Get the SQL schema for execution logs table.
        
        Returns:
            SQL CREATE TABLE statement
        """
        return """
        CREATE TABLE execution_logs (
            id SERIAL PRIMARY KEY,
            endpoint_id INTEGER,
            test_case_id INTEGER,
            test_name VARCHAR(255),
            request_data JSONB,
            response_data JSONB,
            status_code INTEGER,
            execution_time_ms INTEGER,
            success BOOLEAN,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """


class DatabaseInitializer:
    """Handles database initialization and setup."""
    
    def __init__(self):
        """Initialize database initializer."""
        self.db_manager = get_db_manager()
    
    def initialize_database(self) -> bool:
        """
        Initialize the database with required tables.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing database schema")
            
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Drop existing tables (CASCADE to handle dependencies)
                    cur.execute("DROP TABLE IF EXISTS api_endpoints CASCADE;")
                    cur.execute("DROP TABLE IF EXISTS execution_logs CASCADE;")
                    
                    # Create api_endpoints table
                    cur.execute(DatabaseSchema.get_api_endpoints_schema())
                    
                    # Create execution_logs table
                    cur.execute(DatabaseSchema.get_execution_logs_schema())
                    
                    conn.commit()
                    logger.info("Database schema initialized successfully")
                    return True
                    
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
    
    def create_test_cases_table(self, table_name: str) -> bool:
        """
        Create a test cases table for a specific endpoint.
        
        Args:
            table_name: Name of the table to create
            
        Returns:
            True if creation successful, False otherwise
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Drop existing table if it exists
                    cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                    
                    # Create new table
                    cur.execute(DatabaseSchema.get_test_cases_schema(table_name))
                    conn.commit()
                    
                    logger.info(f"Created test cases table: {table_name}")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to create test cases table {table_name}: {e}")
            return False


class EndpointRepository:
    """Repository for API endpoint operations."""
    
    def __init__(self):
        """Initialize endpoint repository."""
        self.db_manager = get_db_manager()
    
    def insert_endpoint(self, endpoint_data: Dict[str, Any]) -> bool:
        """
        Insert or update an API endpoint.
        
        Args:
            endpoint_data: Dictionary containing endpoint information
            
        Returns:
            True if operation successful, False otherwise
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
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
                            x_additional_metadata = EXCLUDED.x_additional_metadata,
                            updated_at = CURRENT_TIMESTAMP;
                    """, (
                        endpoint_data["path"],
                        endpoint_data["method"].upper(),
                        endpoint_data.get("summary"),
                        endpoint_data.get("description"),
                        endpoint_data.get("tags", []),
                        endpoint_data.get("operation_id"),
                        endpoint_data.get("deprecated", False),
                        endpoint_data.get("consumes", []),
                        endpoint_data.get("produces", []),
                        Json(endpoint_data.get("parameters")),
                        Json(endpoint_data.get("request_body")),
                        Json(endpoint_data.get("responses")),
                        Json(endpoint_data.get("security")),
                        Json(endpoint_data.get("examples")),
                        Json(endpoint_data.get("external_docs")),
                        Json(endpoint_data.get("x_additional_metadata"))
                    ))
                    conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to insert endpoint: {e}")
            return False
    
    def get_all_endpoints(self) -> List[Dict[str, Any]]:
        """
        Retrieve all API endpoints from the database.
        
        Returns:
            List of endpoint dictionaries
        """
        try:
            with self.db_manager.get_cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM api_endpoints ORDER BY id")
                endpoints = cur.fetchall()
                return [dict(endpoint) for endpoint in endpoints]
                
        except Exception as e:
            logger.error(f"Failed to retrieve endpoints: {e}")
            return []
    
    def get_endpoint_by_id(self, endpoint_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific endpoint by ID.
        
        Args:
            endpoint_id: ID of the endpoint to retrieve
            
        Returns:
            Endpoint dictionary or None if not found
        """
        try:
            with self.db_manager.get_cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM api_endpoints WHERE id = %s", (endpoint_id,))
                endpoint = cur.fetchone()
                return dict(endpoint) if endpoint else None
                
        except Exception as e:
            logger.error(f"Failed to retrieve endpoint {endpoint_id}: {e}")
            return None
    
    def clear_all_endpoints(self) -> int:
        """
        Clear all endpoints from the database.
        
        Returns:
            Number of endpoints deleted
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM api_endpoints")
                    deleted_count = cur.rowcount
                    conn.commit()
                    return deleted_count
                    
        except Exception as e:
            logger.error(f"Failed to clear endpoints: {e}")
            return 0


class TestCaseRepository:
    """Repository for test case operations."""
    
    def __init__(self):
        """Initialize test case repository."""
        self.db_manager = get_db_manager()
    
    def insert_test_case(self, table_name: str, test_case_data: Dict[str, Any]) -> bool:
        """
        Insert a test case into the specified table.
        
        Args:
            table_name: Name of the test cases table
            test_case_data: Dictionary containing test case information
            
        Returns:
            True if operation successful, False otherwise
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"""
                        INSERT INTO {table_name}
                        (endpoint_id, test_type, test_name, method, url, headers,
                         query_params, path_params, input_payload, expected_status, expected_schema)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        test_case_data.get("endpoint_id"),
                        test_case_data.get("test_type"),
                        test_case_data.get("test_name"),
                        test_case_data.get("method"),
                        test_case_data.get("url"),
                        Json(test_case_data.get("headers") or {}),
                        Json(test_case_data.get("query_params") or {}),
                        Json(test_case_data.get("path_params") or {}),
                        Json(test_case_data.get("input_payload") or {}),
                        test_case_data.get("expected_status"),
                        Json(test_case_data.get("expected_schema") or {}),
                    ))
                    conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to insert test case into {table_name}: {e}")
            return False
    
    def get_test_cases(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Retrieve all test cases from the specified table.
        
        Args:
            table_name: Name of the test cases table
            
        Returns:
            List of test case dictionaries
        """
        try:
            with self.db_manager.get_cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(f"SELECT * FROM {table_name} ORDER BY id")
                test_cases = cur.fetchall()
                return [dict(test_case) for test_case in test_cases]
                
        except Exception as e:
            logger.error(f"Failed to retrieve test cases from {table_name}: {e}")
            return []
    
    def get_test_case_by_id(self, table_name: str, test_case_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific test case by ID.
        
        Args:
            table_name: Name of the test cases table
            test_case_id: ID of the test case to retrieve
            
        Returns:
            Test case dictionary or None if not found
        """
        try:
            with self.db_manager.get_cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(f"SELECT * FROM {table_name} WHERE id = %s", (test_case_id,))
                test_case = cur.fetchone()
                return dict(test_case) if test_case else None
                
        except Exception as e:
            logger.error(f"Failed to retrieve test case {test_case_id} from {table_name}: {e}")
            return None
    
    def clear_all_testcases(self) -> int:
        """
        Clear all test cases from all test case tables.
        
        Returns:
            Number of test cases deleted
        """
        try:
            total_deleted = 0
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get all test case tables
                    cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name LIKE '%testcases%'
                    """)
                    tables = cur.fetchall()
                    
                    if not tables:
                        logger.info("No test case tables found to clear")
                        return 0
                    
                    # Clear each test case table
                    for table in tables:
                        table_name = table[0]
                        cur.execute(f"DELETE FROM {table_name}")
                        deleted_count = cur.rowcount
                        total_deleted += deleted_count
                        logger.info(f"Cleared {deleted_count} test cases from {table_name}")
                    
                    conn.commit()
                    return total_deleted
                    
        except Exception as e:
            logger.error(f"Failed to clear test cases: {e}")
            return 0
    
    def clear_all_tables(self) -> Dict[str, Any]:
        """
        Clear ALL tables from the database (complete reset).
        
        Returns:
            Dictionary with clearing results
        """
        try:
            cleared_tables = []
            total_records = 0
            
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get all tables in the public schema
                    cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        AND table_type = 'BASE TABLE'
                    """)
                    tables = cur.fetchall()
                    
                    if not tables:
                        logger.info("No tables found to clear")
                        return {
                            "status": "success",
                            "cleared_tables": [],
                            "total_records": 0,
                            "message": "No tables found to clear"
                        }
                    
                    logger.info(f"Found {len(tables)} tables to clear")
                    
                    # Clear each table
                    for table in tables:
                        table_name = table[0]
                        try:
                            # Get count before clearing
                            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                            record_count = cur.fetchone()[0]
                            
                            logger.info(f"Clearing table {table_name} with {record_count} records")
                            
                            # Clear the table (DELETE FROM)
                            cur.execute(f"DELETE FROM {table_name}")
                            deleted_count = cur.rowcount
                            
                            # Also drop the table completely to remove it from PostgreSQL
                            cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                            
                            cleared_tables.append({
                                "table_name": table_name,
                                "records_deleted": deleted_count,
                                "original_count": record_count,
                                "table_dropped": True
                            })
                            
                            total_records += deleted_count
                            logger.info(f"Successfully cleared and dropped table {table_name}")
                            
                        except Exception as table_error:
                            logger.error(f"Failed to clear table {table_name}: {table_error}")
                            cleared_tables.append({
                                "table_name": table_name,
                                "error": str(table_error),
                                "records_deleted": 0,
                                "table_dropped": False
                            })
                    
                    # Commit the transaction
                    conn.commit()
                    logger.info(f"Transaction committed. Total records cleared: {total_records}")
                    
                    return {
                        "status": "success",
                        "cleared_tables": cleared_tables,
                        "total_records": total_records,
                        "tables_cleared": len([t for t in cleared_tables if "error" not in t]),
                        "message": f"Successfully cleared {total_records} records from {len(cleared_tables)} tables"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to clear all tables: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to clear all tables"
            }
    
    def get_all_tables_info(self) -> Dict[str, Any]:
        """
        Get information about all tables in the database.
        
        Returns:
            Dictionary with table information
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get all tables in the public schema
                    cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """)
                    tables = cur.fetchall()
                    
                    table_info = []
                    total_records = 0
                    
                    for table in tables:
                        table_name = table[0]
                        try:
                            # Get record count for each table
                            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                            record_count = cur.fetchone()[0]
                            
                            table_info.append({
                                "table_name": table_name,
                                "record_count": record_count
                            })
                            
                            total_records += record_count
                            
                        except Exception as table_error:
                            table_info.append({
                                "table_name": table_name,
                                "record_count": 0,
                                "error": str(table_error)
                            })
                    
                    return {
                        "status": "success",
                        "tables": table_info,
                        "total_tables": len(tables),
                        "total_records": total_records,
                        "message": f"Found {len(tables)} tables with {total_records} total records"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to get table information"
            }
    
    def verify_tables_cleared(self) -> Dict[str, Any]:
        """
        Verify that all tables are actually empty after clearing.
        
        Returns:
            Dictionary with verification results
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get all tables in the public schema
                    cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        AND table_type = 'BASE TABLE'
                    """)
                    tables = cur.fetchall()
                    
                    verification_results = []
                    total_remaining_records = 0
                    
                    for table in tables:
                        table_name = table[0]
                        try:
                            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                            remaining_count = cur.fetchone()[0]
                            
                            verification_results.append({
                                "table_name": table_name,
                                "remaining_records": remaining_count,
                                "is_empty": remaining_count == 0
                            })
                            
                            total_remaining_records += remaining_count
                            
                        except Exception as table_error:
                            verification_results.append({
                                "table_name": table_name,
                                "error": str(table_error),
                                "remaining_records": -1,
                                "is_empty": False
                            })
                    
                    all_empty = all(result.get("is_empty", False) for result in verification_results)
                    
                    return {
                        "status": "success",
                        "all_tables_empty": all_empty,
                        "total_remaining_records": total_remaining_records,
                        "verification_results": verification_results,
                        "message": f"Verification complete. {total_remaining_records} records remaining across {len(tables)} tables"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to verify table clearing: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to verify table clearing"
            }


# Global repository instances
db_initializer = DatabaseInitializer()
endpoint_repository = EndpointRepository()
test_case_repository = TestCaseRepository()


def get_db_initializer() -> DatabaseInitializer:
    """Get the global database initializer instance."""
    return db_initializer


def get_endpoint_repository() -> EndpointRepository:
    """Get the global endpoint repository instance."""
    return endpoint_repository


def get_test_case_repository() -> TestCaseRepository:
    """Get the global test case repository instance."""
    return test_case_repository
