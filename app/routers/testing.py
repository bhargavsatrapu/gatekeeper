import json
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel

from app.db.pool import get_conn, put_conn
from app.repositories.api_specs import ensure_table
from app.repositories.test_cases import (
    create_request_body, get_request_bodies, create_test_case, get_test_cases,
    generate_test_cases, create_test_run, update_test_run_stats, execute_test_case,
    get_test_results, get_test_run_summary
)
from app.core.config import settings


router = APIRouter(prefix="/testing", tags=["API Testing"])


class RequestBodyCreate(BaseModel):
    name: str
    description: str
    request_body: dict


class TestCaseCreate(BaseModel):
    name: str
    description: str
    test_type: str
    request_body: Optional[dict] = None
    expected_status: int
    expected_response_schema: Optional[dict] = None


class TestRunCreate(BaseModel):
    name: str
    description: str


@router.post("/apis/{api_id}/request-bodies")
async def add_request_body(api_id: int, request_body_data: RequestBodyCreate) -> JSONResponse:
    """Add a request body for an API"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        ensure_table(cur)
        
        # Validate that the API exists
        cur.execute("SELECT id FROM api_specs WHERE id = %s", (api_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="API not found")
        
        # Store the request body
        body_id = create_request_body(
            api_id, request_body_data.name, request_body_data.description,
            request_body_data.request_body, cur
        )
        
        conn.commit()
        return JSONResponse({
            "message": "Request body created successfully",
            "id": body_id,
            "api_id": api_id
        })
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create request body: {str(e)}")
    finally:
        try:
            cur.close()
        finally:
            put_conn(conn)


@router.get("/apis/{api_id}/request-bodies")
async def list_request_bodies(api_id: int) -> JSONResponse:
    """Get all request bodies for an API"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        ensure_table(cur)
        
        bodies = get_request_bodies(api_id, cur)
        return JSONResponse({"request_bodies": bodies})
    finally:
        try:
            cur.close()
        finally:
            put_conn(conn)


@router.post("/apis/{api_id}/test-cases")
async def add_test_case(api_id: int, test_case_data: TestCaseCreate) -> JSONResponse:
    """Add a custom test case for an API"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        ensure_table(cur)
        
        # Validate that the API exists
        cur.execute("SELECT id FROM api_specs WHERE id = %s", (api_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="API not found")
        
        # Validate test type
        if test_case_data.test_type not in ['positive', 'negative']:
            raise HTTPException(status_code=400, detail="Test type must be 'positive' or 'negative'")
        
        # Create the test case
        test_case_id = create_test_case(
            api_id, test_case_data.name, test_case_data.description,
            test_case_data.test_type, test_case_data.request_body,
            test_case_data.expected_status, test_case_data.expected_response_schema, cur
        )
        
        conn.commit()
        return JSONResponse({
            "message": "Test case created successfully",
            "id": test_case_id,
            "api_id": api_id
        })
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create test case: {str(e)}")
    finally:
        try:
            cur.close()
        finally:
            put_conn(conn)


@router.get("/apis/{api_id}/test-cases")
async def list_test_cases(api_id: int) -> JSONResponse:
    """Get all test cases for an API"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        ensure_table(cur)
        
        test_cases = get_test_cases(api_id, cur)
        return JSONResponse({"test_cases": test_cases})
    finally:
        try:
            cur.close()
        finally:
            put_conn(conn)


@router.post("/apis/{api_id}/generate-test-cases")
async def auto_generate_test_cases(api_id: int) -> JSONResponse:
    """Automatically generate test cases for an API"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        ensure_table(cur)
        
        # Get API details
        cur.execute(
            "SELECT method, path, request_body, responses FROM api_specs WHERE id = %s",
            (api_id,)
        )
        api_data = cur.fetchone()
        
        if not api_data:
            raise HTTPException(status_code=404, detail="API not found")
        
        method, path, request_body_schema, responses = api_data
        
        # Generate test cases
        test_case_ids = generate_test_cases(
            api_id, method, path, request_body_schema, responses or {}, cur
        )
        
        conn.commit()
        return JSONResponse({
            "message": f"Generated {len(test_case_ids)} test cases",
            "test_case_ids": test_case_ids,
            "api_id": api_id
        })
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate test cases: {str(e)}")
    finally:
        try:
            cur.close()
        finally:
            put_conn(conn)


@router.post("/test-runs")
async def create_test_run(test_run_data: TestRunCreate) -> JSONResponse:
    """Create a new test run"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        ensure_table(cur)
        
        test_run_id = create_test_run(test_run_data.name, test_run_data.description, cur)
        conn.commit()
        
        return JSONResponse({
            "message": "Test run created successfully",
            "test_run_id": test_run_id
        })
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create test run: {str(e)}")
    finally:
        try:
            cur.close()
        finally:
            put_conn(conn)


@router.post("/test-runs/{test_run_id}/execute")
async def execute_test_run(test_run_id: int, api_ids: Optional[List[int]] = None) -> JSONResponse:
    """Execute all test cases for specified APIs or all APIs if none specified"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        ensure_table(cur)
        
        # Get test run info
        cur.execute("SELECT name, description FROM test_runs WHERE id = %s", (test_run_id,))
        test_run = cur.fetchone()
        if not test_run:
            raise HTTPException(status_code=404, detail="Test run not found")
        
        # Get APIs to test
        if api_ids:
            cur.execute(
                "SELECT id, method, path FROM api_specs WHERE id = ANY(%s)",
                (api_ids,)
            )
        else:
            cur.execute("SELECT id, method, path FROM api_specs")
        
        apis = cur.fetchall()
        
        if not apis:
            return JSONResponse({"message": "No APIs found to test"})
        
        # Get test cases for each API
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0
        
        for api_id, method, path in apis:
            cur.execute("SELECT id, expected_status, request_body FROM test_cases WHERE api_id = %s", (api_id,))
            test_cases = cur.fetchall()
            
            for test_case_id, expected_status, request_body in test_cases:
                total_tests += 1
                
                # Execute the test case
                result = execute_test_case(
                    test_case_id, api_id, method, path,
                    settings.api_base_url, request_body, expected_status, test_run_id, cur
                )
                
                if result["status"] == "passed":
                    passed_tests += 1
                elif result["status"] == "failed":
                    failed_tests += 1
                else:
                    error_tests += 1
        
        # Update test run statistics
        update_test_run_stats(test_run_id, total_tests, passed_tests, failed_tests, error_tests, "completed", cur)
        
        conn.commit()
        
        return JSONResponse({
            "message": "Test run completed",
            "test_run_id": test_run_id,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "error_tests": error_tests
            }
        })
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to execute test run: {str(e)}")
    finally:
        try:
            cur.close()
        finally:
            put_conn(conn)


@router.get("/test-runs/{test_run_id}")
async def get_test_run_details(test_run_id: int) -> JSONResponse:
    """Get details of a test run"""
    summary = get_test_run_summary(test_run_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    return JSONResponse(summary)


@router.get("/test-runs/{test_run_id}/results")
async def get_test_run_results(test_run_id: int) -> JSONResponse:
    """Get all test results for a test run"""
    results = get_test_results(test_run_id=test_run_id)
    return JSONResponse({"results": results})


@router.get("/test-results")
async def list_test_results(api_id: Optional[int] = None) -> JSONResponse:
    """Get all test results with optional filtering by API"""
    results = get_test_results(api_id=api_id)
    return JSONResponse({"results": results})


@router.get("/test-runs")
async def list_test_runs() -> JSONResponse:
    """Get all test runs"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        ensure_table(cur)
        
        cur.execute(
            "SELECT id, name, description, total_tests, passed_tests, failed_tests, error_tests, status, started_at, completed_at FROM test_runs ORDER BY started_at DESC"
        )
        rows = cur.fetchall()
        
        test_runs = [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "total_tests": row[3],
                "passed_tests": row[4],
                "failed_tests": row[5],
                "error_tests": row[6],
                "status": row[7],
                "started_at": row[8].isoformat() if row[8] else None,
                "completed_at": row[9].isoformat() if row[9] else None
            }
            for row in rows
        ]
        
        return JSONResponse({"test_runs": test_runs})
    finally:
        try:
            cur.close()
        finally:
            put_conn(conn)


@router.get("/reports/{test_run_id}")
async def generate_test_report(test_run_id: int) -> HTMLResponse:
    """Generate an HTML report for a test run"""
    summary = get_test_run_summary(test_run_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    results = get_test_results(test_run_id=test_run_id)
    
    # Generate HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Report - {summary['name']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
            .summary {{ display: flex; gap: 20px; margin-bottom: 20px; }}
            .summary-item {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; text-align: center; flex: 1; }}
            .summary-item.failed {{ background-color: #ffe8e8; }}
            .summary-item.error {{ background-color: #fff3e8; }}
            .results {{ margin-top: 20px; }}
            .result-item {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
            .result-item.passed {{ border-left: 5px solid #4caf50; }}
            .result-item.failed {{ border-left: 5px solid #f44336; }}
            .result-item.error {{ border-left: 5px solid #ff9800; }}
            .status {{ font-weight: bold; }}
            .status.passed {{ color: #4caf50; }}
            .status.failed {{ color: #f44336; }}
            .status.error {{ color: #ff9800; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>API Test Report</h1>
            <h2>{summary['name']}</h2>
            <p>{summary['description'] or 'No description provided'}</p>
        </div>
        
        <div class="summary">
            <div class="summary-item">
                <h3>Total Tests</h3>
                <h2>{summary['total_tests']}</h2>
            </div>
            <div class="summary-item">
                <h3>Passed</h3>
                <h2 style="color: #4caf50;">{summary['passed_tests']}</h2>
            </div>
            <div class="summary-item failed">
                <h3>Failed</h3>
                <h2 style="color: #f44336;">{summary['failed_tests']}</h2>
            </div>
            <div class="summary-item error">
                <h3>Errors</h3>
                <h2 style="color: #ff9800;">{summary['error_tests']}</h2>
            </div>
        </div>
        
        <div class="results">
            <h3>Test Results</h3>
            {''.join([f'''
            <div class="result-item {result['status']}">
                <h4>{result['test_case_name']}</h4>
                <p><strong>API:</strong> {result['method']} {result['path']}</p>
                <p><strong>Type:</strong> {result['test_type']}</p>
                <p><strong>Status:</strong> <span class="status {result['status']}">{result['status'].upper()}</span></p>
                <p><strong>Response Status:</strong> {result['response_status'] or 'N/A'}</p>
                <p><strong>Response Time:</strong> {result['response_time_ms']}ms</p>
                {f'<p><strong>Error:</strong> {result["error_message"]}</p>' if result['error_message'] else ''}
                {f'<p><strong>Response Body:</strong> <pre>{json.dumps(result["response_body"], indent=2)}</pre></p>' if result['response_body'] else ''}
            </div>
            ''' for result in results])}
        </div>
        
        <div style="margin-top: 30px; text-align: center; color: #666;">
            <p>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)
