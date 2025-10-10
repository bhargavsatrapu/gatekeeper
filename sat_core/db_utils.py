"""
Database utility functions for SmartAPI Tester
Handles execution results storage and retrieval
"""

import psycopg2
import json
from typing import Dict, Any, Optional
import logging
from sat_core.config import DB_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseUtils:
    """Database utility class for managing execution results"""
    
    def __init__(self, db_config: Optional[Dict[str, str]] = None):
        """
        Initialize database connection
        
        Args:
            db_config: Database configuration dictionary with keys:
                      host, port, database, user, password
        """
        if db_config is None:
            # Use configuration from config.py
            self.db_config = DB_CONFIG.copy()
            # Add port if not present in config
            if 'port' not in self.db_config:
                self.db_config['port'] = '5432'
        else:
            self.db_config = db_config
    
    def get_connection(self):
        """Get database connection"""
        try:
            connection = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            return connection
        except psycopg2.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def create_execution_results_table(self):
        """
        Create the execution_results table in the database.
        If the table already exists, it will drop and recreate it.
        
        Returns:
            bool: True if table was created successfully, False otherwise
        """
        connection = None
        cursor = None
        
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Drop table if it exists
            drop_table_sql = """
                DROP TABLE IF EXISTS execution_results CASCADE;
            """
            cursor.execute(drop_table_sql)
            logger.info("Dropped existing execution_results table if it existed")
            
            # Create the execution_results table
            create_table_sql = """
                CREATE TABLE execution_results (
                    id SERIAL PRIMARY KEY,
                    test_name VARCHAR(255) NOT NULL,
                    input_method VARCHAR(10) NOT NULL,
                    input_url TEXT NOT NULL,
                    input_headers JSONB,
                    input_payload JSONB,
                    expected_status_code INTEGER,
                    expected_schema JSONB,
                    actual_status_code INTEGER,
                    actual_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            
            cursor.execute(create_table_sql)
            
            # Create indexes for better performance
            index_sql = """
                CREATE INDEX idx_execution_results_test_name ON execution_results(test_name);
                CREATE INDEX idx_execution_results_method ON execution_results(input_method);
                CREATE INDEX idx_execution_results_created_at ON execution_results(created_at);
            """
            cursor.execute(index_sql)
            
            connection.commit()
            logger.info("Successfully created execution_results table with indexes")
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Error creating execution_results table: {e}")
            if connection:
                connection.rollback()
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating execution_results table: {e}")
            if connection:
                connection.rollback()
            return False
            
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def insert_execution_result(self, 
                              test_name: str,
                              input_method: str,
                              input_url: str,
                              input_headers: Optional[Dict[str, Any]] = None,
                              input_payload: Optional[Dict[str, Any]] = None,
                              expected_status_code: Optional[int] = None,
                              expected_schema: Optional[Dict[str, Any]] = None,
                              actual_status_code: Optional[int] = None,
                              actual_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Insert a record into the execution_results table.
        
        Args:
            test_name: Name of the test case
            input_method: HTTP method (GET, POST, PUT, DELETE, etc.)
            input_url: The URL that was tested
            input_headers: Request headers as dictionary
            input_payload: Request payload/body as dictionary
            expected_status_code: Expected HTTP status code
            expected_schema: Expected response schema as dictionary
            actual_status_code: Actual HTTP status code received
            actual_data: Actual response data as dictionary
            
        Returns:
            bool: True if record was inserted successfully, False otherwise
        """
        connection = None
        cursor = None
        
        try:
            # Validate required parameters
            if not test_name or not input_method or not input_url:
                logger.warning("Missing required parameters for insert_execution_result")
                return False
            
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Prepare the insert SQL
            insert_sql = """
                INSERT INTO execution_results (
                    test_name, input_method, input_url, input_headers, 
                    input_payload, expected_status_code, expected_schema,
                    actual_status_code, actual_data
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                );
            """
            
            # Convert dictionaries to JSON strings for JSONB columns
            try:
                input_headers_json = json.dumps(input_headers) if input_headers else None
                input_payload_json = json.dumps(input_payload) if input_payload else None
                expected_schema_json = json.dumps(expected_schema) if expected_schema else None
                actual_data_json = json.dumps(actual_data) if actual_data else None
            except (TypeError, ValueError) as json_error:
                logger.error(f"Error serializing JSON data: {json_error}")
                return False
            
            # Execute the insert
            cursor.execute(insert_sql, (
                test_name,
                input_method,
                input_url,
                input_headers_json,
                input_payload_json,
                expected_status_code,
                expected_schema_json,
                actual_status_code,
                actual_data_json
            ))
            
            connection.commit()
            logger.info(f"Successfully inserted execution result for test: {test_name}")
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Error inserting execution result: {e}")
            if connection:
                connection.rollback()
            return False
        except Exception as e:
            logger.error(f"Unexpected error inserting execution result: {e}")
            if connection:
                connection.rollback()
            return False
            
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def get_execution_results(self, test_name: Optional[str] = None, limit: int = 100) -> list:
        """
        Retrieve execution results from the database.
        
        Args:
            test_name: Optional filter by test name
            limit: Maximum number of results to return
            
        Returns:
            list: List of execution result dictionaries
        """
        connection = None
        cursor = None
        
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            if test_name:
                select_sql = """
                    SELECT * FROM execution_results 
                    WHERE test_name = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s;
                """
                cursor.execute(select_sql, (test_name, limit))
            else:
                select_sql = """
                    SELECT * FROM execution_results 
                    ORDER BY created_at DESC 
                    LIMIT %s;
                """
                cursor.execute(select_sql, (limit,))
            
            # Fetch all results
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            columns = [desc[0] for desc in cursor.description]
            result_list = []
            
            for row in results:
                result_dict = dict(zip(columns, row))
                # Parse JSONB columns back to dictionaries
                for jsonb_col in ['input_headers', 'input_payload', 'expected_schema', 'actual_data']:
                    if result_dict[jsonb_col]:
                        result_dict[jsonb_col] = json.loads(result_dict[jsonb_col])
                result_list.append(result_dict)
            
            logger.info(f"Retrieved {len(result_list)} execution results")
            return result_list
            
        except psycopg2.Error as e:
            logger.error(f"Error retrieving execution results: {e}")
            return []
            
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def delete_execution_results(self, test_name: Optional[str] = None) -> bool:
        """
        Delete execution results from the database.
        
        Args:
            test_name: Optional filter by test name. If None, deletes all results.
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        connection = None
        cursor = None
        
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            if test_name:
                delete_sql = "DELETE FROM execution_results WHERE test_name = %s;"
                cursor.execute(delete_sql, (test_name,))
            else:
                delete_sql = "DELETE FROM execution_results;"
                cursor.execute(delete_sql)
            
            connection.commit()
            deleted_count = cursor.rowcount
            logger.info(f"Successfully deleted {deleted_count} execution results")
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Error deleting execution results: {e}")
            if connection:
                connection.rollback()
            return False
            
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if result and result[0] == 1:
                logger.info("Database connection test successful")
                return True
            else:
                logger.error("Database connection test failed")
                return False
                
        except psycopg2.Error as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Convenience functions for easy usage
def create_execution_results_table(db_config: Optional[Dict[str, str]] = None) -> bool:
    """
    Convenience function to create execution results table.
    
    Args:
        db_config: Optional database configuration
        
    Returns:
        bool: True if table was created successfully
    """
    try:
        db_utils = DatabaseUtils(db_config)
        return db_utils.create_execution_results_table()
    except Exception as e:
        logger.error(f"Error in create_execution_results_table convenience function: {e}")
        return False


def insert_execution_result(test_name: str,
                          input_method: str,
                          input_url: str,
                          input_headers: Optional[Dict[str, Any]] = None,
                          input_payload: Optional[Dict[str, Any]] = None,
                          expected_status_code: Optional[int] = None,
                          expected_schema: Optional[Dict[str, Any]] = None,
                          actual_status_code: Optional[int] = None,
                          actual_data: Optional[Dict[str, Any]] = None,
                          db_config: Optional[Dict[str, str]] = None) -> bool:
    """
    Convenience function to insert execution result.
    
    Args:
        test_name: Name of the test case
        input_method: HTTP method
        input_url: The URL that was tested
        input_headers: Request headers
        input_payload: Request payload
        expected_status_code: Expected HTTP status code
        expected_schema: Expected response schema
        actual_status_code: Actual HTTP status code
        actual_data: Actual response data
        db_config: Optional database configuration
        
    Returns:
        bool: True if record was inserted successfully
    """
    try:
        db_utils = DatabaseUtils(db_config)
        return db_utils.insert_execution_result(
            test_name=test_name,
            input_method=input_method,
            input_url=input_url,
            input_headers=input_headers,
            input_payload=input_payload,
            expected_status_code=expected_status_code,
            expected_schema=expected_schema,
            actual_status_code=actual_status_code,
            actual_data=actual_data
        )
    except Exception as e:
        logger.error(f"Error in insert_execution_result convenience function: {e}")
        return False


# Example usage
if __name__ == "__main__":
    # Create database utils instance using config from config.py
    db_utils = DatabaseUtils()
    
    # Test connection
    if db_utils.test_connection():
        print("Database connection successful!")
        
        # Create table
        if db_utils.create_execution_results_table():
            print("Execution results table created successfully!")
            
            # Insert sample data
            sample_result = db_utils.insert_execution_result(
                test_name="Test GET /api/users",
                input_method="GET",
                input_url="http://localhost:8000/api/users",
                input_headers={"Authorization": "Bearer token123"},
                input_payload=None,
                expected_status_code=200,
                expected_schema={"type": "object", "properties": {"users": {"type": "array"}}},
                actual_status_code=200,
                actual_data={"users": [{"id": 1, "name": "John Doe"}]}
            )
            
            if sample_result:
                print("Sample execution result inserted successfully!")
                
                # Retrieve results
                results = db_utils.get_execution_results()
                print(f"Retrieved {len(results)} execution results")
                
        else:
            print("Failed to create execution results table!")
    else:
        print("Database connection failed!")



