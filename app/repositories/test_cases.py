import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
# Simple JSON wrapper for PostgreSQL compatibility
Json = lambda x: x
from app.db.pool import get_conn, put_conn
from app.core.config import settings


def create_request_body(api_id: int, name: str, description: str, request_body: dict, cur) -> int:
    """Store a user-provided request body for an API"""
    cur.execute(
        """
        INSERT INTO request_bodies (api_id, name, description, request_body)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (api_id, name, description, Json(request_body))
    )
    return cur.fetchone()[0]


def get_request_bodies(api_id: int, cur) -> List[Dict]:
    """Get all request bodies for a specific API"""
    cur.execute(
        "SELECT id, name, description, request_body, is_valid, validation_errors FROM request_bodies WHERE api_id = %s ORDER BY created_at DESC",
        (api_id,)
    )
    rows = cur.fetchall()
    return [
        {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "request_body": row[3],
            "is_valid": row[4],
            "validation_errors": row[5]
        }
        for row in rows
    ]


def create_test_case(api_id: int, name: str, description: str, test_type: str, 
                     request_body: Optional[dict], expected_status: int, 
                     expected_response_schema: Optional[dict], cur) -> int:
    """Create a test case for an API"""
    cur.execute(
        """
        INSERT INTO test_cases (api_id, name, description, test_type, request_body, expected_status, expected_response_schema)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (api_id, name, description, test_type, 
         Json(request_body) if request_body else None, 
         expected_status, 
         Json(expected_response_schema) if expected_response_schema else None)
    )
    return cur.fetchone()[0]


def get_test_cases(api_id: int, cur) -> List[Dict]:
    """Get all test cases for a specific API"""
    cur.execute(
        "SELECT id, name, description, test_type, request_body, expected_status, expected_response_schema, created_at FROM test_cases WHERE api_id = %s ORDER BY created_at DESC",
        (api_id,)
    )
    rows = cur.fetchall()
    return [
        {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "test_type": row[3],
            "request_body": row[4],
            "expected_status": row[5],
            "expected_response_schema": row[6],
            "created_at": row[7].isoformat() if row[7] else None
        }
        for row in rows
    ]


def generate_test_cases(api_id: int, method: str, path: str, request_body_schema: Optional[dict], 
                       response_schemas: dict, cur) -> List[int]:
    """Automatically generate positive and negative test cases for an API"""
    test_case_ids = []
    
    # Generate positive test case
    positive_name = f"Valid {method.upper()} {path}"
    positive_description = f"Test with valid request data for {method.upper()} {path}"
    
    # Determine expected status based on method
    expected_status = 200 if method.upper() in ['GET', 'PUT', 'PATCH'] else 201 if method.upper() == 'POST' else 204 if method.upper() == 'DELETE' else 200
    
    positive_id = create_test_case(
        api_id, positive_name, positive_description, "positive", 
        None, expected_status, None, cur
    )
    test_case_ids.append(positive_id)
    
    # Generate negative test cases
    if method.upper() in ['POST', 'PUT', 'PATCH'] and request_body_schema:
        # Invalid data test case
        invalid_name = f"Invalid {method.upper()} {path} - Bad Data"
        invalid_description = f"Test with invalid request data for {method.upper()} {path}"
        
        invalid_id = create_test_case(
            api_id, invalid_name, invalid_description, "negative", 
            None, 400, None, cur
        )
        test_case_ids.append(invalid_id)
        
        # Missing required fields test case
        missing_name = f"Invalid {method.upper()} {path} - Missing Fields"
        missing_description = f"Test with missing required fields for {method.upper()} {path}"
        
        missing_id = create_test_case(
            api_id, missing_name, missing_description, "negative", 
            None, 400, None, cur
        )
        test_case_ids.append(missing_id)
    
    # Unauthorized access test case
    unauthorized_name = f"Invalid {method.upper()} {path} - Unauthorized"
    unauthorized_description = f"Test without proper authentication for {method.upper()} {path}"
    
    unauthorized_id = create_test_case(
        api_id, unauthorized_name, unauthorized_description, "negative", 
        None, 401, None, cur
    )
    test_case_ids.append(unauthorized_id)
    
    return test_case_ids


def create_test_run(name: str, description: str, cur) -> int:
    """Create a new test run"""
    cur.execute(
        """
        INSERT INTO test_runs (name, description)
        VALUES (%s, %s)
        RETURNING id
        """,
        (name, description)
    )
    return cur.fetchone()[0]


def update_test_run_stats(test_run_id: int, total: int, passed: int, failed: int, error: int, status: str, cur) -> None:
    """Update test run statistics"""
    completed_at = datetime.now() if status == 'completed' else None
    cur.execute(
        """
        UPDATE test_runs 
        SET total_tests = %s, passed_tests = %s, failed_tests = %s, error_tests = %s, 
            status = %s, completed_at = %s
        WHERE id = %s
        """,
        (total, passed, failed, error, status, completed_at, test_run_id)
    )


def store_test_result(test_case_id: int, api_id: int, test_run_id: int, status: str, response_status: Optional[int],
                     response_body: Optional[dict], response_time_ms: int, error_message: Optional[str],
                     screenshot_path: Optional[str], test_duration_ms: int, cur) -> int:
    """Store the result of a test execution"""
    cur.execute(
        """
        INSERT INTO test_results (test_case_id, api_id, test_run_id, status, response_status, response_body, 
                                response_time_ms, error_message, screenshot_path, test_duration_ms)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (test_case_id, api_id, test_run_id, status, response_status, 
         Json(response_body) if response_body else None, response_time_ms, 
         error_message, screenshot_path, test_duration_ms)
    )
    return cur.fetchone()[0]


def execute_test_case(test_case_id: int, api_id: int, method: str, path: str, 
                     base_url: str, request_body: Optional[dict], 
                     expected_status: int, test_run_id: int, cur) -> Dict[str, Any]:
    """Execute a single test case and return results"""
    start_time = time.time()
    url = f"{base_url.rstrip('/')}{path}"
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Prepare request data
        kwargs = {
            'headers': headers,
            'timeout': settings.max_test_timeout
        }
        
        if request_body and method.upper() in ['POST', 'PUT', 'PATCH']:
            kwargs['json'] = request_body
        
        # Execute the request
        response = requests.request(method.upper(), url, **kwargs)
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Determine test status
        if response.status_code == expected_status:
            test_status = "passed"
        else:
            test_status = "failed"
        
        # Store test result
        result_id = store_test_result(
            test_case_id, api_id, test_run_id, test_status, response.status_code,
            response.json() if response.content else None, response_time_ms,
            None, None, response_time_ms, cur
        )
        
        return {
            "id": result_id,
            "status": test_status,
            "response_status": response.status_code,
            "response_body": response.json() if response.content else None,
            "response_time_ms": response_time_ms,
            "error_message": None
        }
        
    except requests.exceptions.Timeout:
        test_status = "error"
        error_message = "Request timeout"
        response_time_ms = int((time.time() - start_time) * 1000)
        
        result_id = store_test_result(
            test_case_id, api_id, test_run_id, test_status, None, None, response_time_ms,
            error_message, None, response_time_ms, cur
        )
        
        return {
            "id": result_id,
            "status": test_status,
            "response_status": None,
            "response_body": None,
            "response_time_ms": response_time_ms,
            "error_message": error_message
        }
        
    except Exception as e:
        test_status = "error"
        error_message = str(e)
        response_time_ms = int((time.time() - start_time) * 1000)
        
        result_id = store_test_result(
            test_case_id, api_id, test_run_id, test_status, None, None, response_time_ms,
            error_message, None, response_time_ms, cur
        )
        
        return {
            "id": result_id,
            "status": test_status,
            "response_status": None,
            "response_body": None,
            "response_time_ms": response_time_ms,
            "error_message": error_message
        }


def get_test_results(test_run_id: Optional[int] = None, api_id: Optional[int] = None) -> List[Dict]:
    """Get test results with optional filtering"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        query = """
        SELECT tr.id, tr.test_case_id, tr.api_id, tr.status, tr.response_status, 
               tr.response_body, tr.response_time_ms, tr.error_message, tr.screenshot_path,
               tr.executed_at, tr.test_duration_ms,
               tc.name as test_case_name, tc.test_type,
               aps.method, aps.path
        FROM test_results tr
        JOIN test_cases tc ON tr.test_case_id = tc.id
        JOIN api_specs aps ON tr.api_id = aps.id
        WHERE 1=1
        """
        params = []
        
        if test_run_id:
            query += " AND tr.test_run_id = %s"
            params.append(test_run_id)
        
        if api_id:
            query += " AND tr.api_id = %s"
            params.append(api_id)
        
        query += " ORDER BY tr.executed_at DESC"
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        return [
            {
                "id": row[0],
                "test_case_id": row[1],
                "api_id": row[2],
                "status": row[3],
                "response_status": row[4],
                "response_body": row[5],
                "response_time_ms": row[6],
                "error_message": row[7],
                "screenshot_path": row[8],
                "executed_at": row[9].isoformat() if row[9] else None,
                "test_duration_ms": row[10],
                "test_case_name": row[11],
                "test_type": row[12],
                "method": row[13],
                "path": row[14]
            }
            for row in rows
        ]
    finally:
        put_conn(conn)


def get_test_run_summary(test_run_id: int) -> Dict[str, Any]:
    """Get summary statistics for a test run"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        cur.execute(
            """
            SELECT name, description, total_tests, passed_tests, failed_tests, error_tests,
                   started_at, completed_at, status
            FROM test_runs WHERE id = %s
            """,
            (test_run_id,)
        )
        
        row = cur.fetchone()
        if not row:
            return {}
        
        return {
            "id": test_run_id,
            "name": row[0],
            "description": row[1],
            "total_tests": row[2],
            "passed_tests": row[3],
            "failed_tests": row[4],
            "error_tests": row[5],
            "started_at": row[6].isoformat() if row[6] else None,
            "completed_at": row[7].isoformat() if row[7] else None,
            "status": row[8]
        }
    finally:
        put_conn(conn)
