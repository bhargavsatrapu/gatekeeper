from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import sys
import io
import threading
from datetime import datetime
from typing import List, Dict
import subprocess
import shutil

# Import your backend interface functions (kept untouched)
from backend_interface import (
    __upload_swagger_document,
    __generate_testcases_for_every_endpoint,
    __run_only_positive_flow,
    __execute_all_test_cases_differnt_endpoint,
)

app = FastAPI(title="Smart API Test Runner")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Fixed Allure directories
ALLURE_RESULTS_DIR = os.path.join(STATIC_DIR, "allure-results")
ALLURE_REPORT_DIR = os.path.join(STATIC_DIR, "allure-report")

# Ensure directories exist
os.makedirs(ALLURE_RESULTS_DIR, exist_ok=True)
os.makedirs(ALLURE_REPORT_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Import console logging system
from console_logger import get_console_logs, clear_console, log_to_console

# Import AI reports service
from sat_core.ai_reports_service import generate_ai_report

def serialize_for_json(obj):
    """Recursively serialize objects for JSON, converting datetime to strings"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    else:
        return obj

def clean_allure_dirs():
    """Clear previous Allure results and report before each run."""
    if os.path.exists(ALLURE_RESULTS_DIR):
        shutil.rmtree(ALLURE_RESULTS_DIR)
    if os.path.exists(ALLURE_REPORT_DIR):
        shutil.rmtree(ALLURE_REPORT_DIR)
    os.makedirs(ALLURE_RESULTS_DIR, exist_ok=True)
    os.makedirs(ALLURE_REPORT_DIR, exist_ok=True)



@app.get("/")
def home(request: Request, msg: str | None = None, show_view_btn: str | None = None, tab: str | None = None):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "msg": msg,
        "show_view_btn": show_view_btn == "true",
        "active_tab": tab
    })


@app.post("/upload-swagger")
async def upload_swagger(request: Request, swagger_file: UploadFile = File(...)):
    # Persist uploaded file then call your function
    content = await swagger_file.read()
    save_path = os.path.join(BASE_DIR, "swagger.json")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(content)

    # Call provided function
    __upload_swagger_document()
    return RedirectResponse(url="/?msg=Swagger%20uploaded%20successfully", status_code=303)


@app.post("/generate-testcases")
def generate_testcases():
    __generate_testcases_for_every_endpoint()
    return RedirectResponse(url="/?msg=Testcases%20generated%20successfully&show_view_btn=true&tab=generate", status_code=303)


@app.post("/run-positive")
def run_positive():
    clean_allure_dirs()  # ✅ Clean before execution, not inside the thread
    def run_positive_background():
        try:
            log_to_console("Starting positive flow execution", "info")
            __run_only_positive_flow()  # Remove clean_allure_dirs() from here
            log_to_console("Positive flow execution completed successfully", "success")
        except Exception as e:
            log_to_console(f"Positive flow execution failed: {str(e)}", "error")
        
    # Start background thread
    thread = threading.Thread(target=run_positive_background, daemon=True)
    thread.start()
    
    return RedirectResponse(url="/?msg=Positive%20flow%20execution%20started&tab=console", status_code=303)


@app.post("/run-all-tests")
def run_all_tests():
    clean_allure_dirs()
    def run_all_tests_background():
        try:
            log_to_console("Starting all tests execution", "info")
            __execute_all_test_cases_differnt_endpoint()
            log_to_console("All tests execution completed successfully", "success")
        except Exception as e:
            log_to_console(f"All tests execution failed: {str(e)}", "error")
    
    # Start background thread
    thread = threading.Thread(target=run_all_tests_background, daemon=True)
    thread.start()
    
    return RedirectResponse(url="/?msg=All%20tests%20execution%20started&tab=console", status_code=303)


@app.post("/run-individual-endpoints")
async def run_individual_endpoints(request: Request):
    from pydantic import BaseModel
    from typing import List
    
    class EndpointRequest(BaseModel):
        endpoint_ids: List[int]
    
    try:
        body = await request.json()
        endpoint_ids = body.get("endpoint_ids", [])
        
        if not endpoint_ids:
            return JSONResponse(
                status_code=400,
                content={"error": "No endpoint IDs provided"}
            )
        
        # Start execution in background thread to allow real-time log updates
        def run_tests_background():
            clean_allure_dirs()
            try:
                log_to_console(f"Starting test execution for {len(endpoint_ids)} endpoints", "info")
                __execute_all_test_cases_differnt_endpoint(endpoint_ids)
                log_to_console("Test execution completed successfully", "success")
            except Exception as e:
                log_to_console(f"Test execution failed: {str(e)}", "error")
        
        # Start background thread
        thread = threading.Thread(target=run_tests_background, daemon=True)
        thread.start()
        
        return JSONResponse(
            status_code=200,
            content={"message": f"Test execution started for {len(endpoint_ids)} endpoints"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# Console API routes
@app.get("/api/console-logs")
def api_get_console_logs():
    return {"logs": get_console_logs()}

@app.get("/api/positive-apis")
def get_positive_apis():
    from sat_core.db_utils import DatabaseUtils
    
    positive_apis = []
    
    try:
        db = DatabaseUtils()
        connection = db.get_connection()
        cursor = connection.cursor()
        
        # Get all endpoints from api_endpoints table
        endpoints_query = "SELECT id, path, method, summary FROM api_endpoints"
        cursor.execute(endpoints_query)
        endpoints = cursor.fetchall()
        
        if not endpoints:
            cursor.close()
            connection.close()
            return {"positive_apis": [], "message": "No endpoints found. Please generate test cases first."}
        
        # For each endpoint, try to find its corresponding test case table
        for endpoint in endpoints:
            endpoint_id, endpoint_path, method, description = endpoint
            
            # Construct the expected table name based on the pattern we saw
            # Format: api_testcases_{path_with_underscores}_{method_lower}
            # Remove leading slash and replace remaining slashes with underscores
            clean_path = endpoint_path.lstrip('/').replace('/', '_')
            table_name = f"api_testcases_{clean_path}_{method.lower()}"
            
            try:
                # Check if the table exists and get the first row (positive test case)
                query = f"SELECT * FROM {table_name} LIMIT 1"
                cursor.execute(query)
                result = cursor.fetchall()
                
                if result:
                    # Get the first row
                    first_row = result[0]
                    
                    # Get column names
                    columns_query = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position"
                    cursor.execute(columns_query)
                    columns_result = cursor.fetchall()
                    columns = [col[0] for col in columns_result]
                    
                    # Create a dictionary with column names and values
                    api_data = {}
                    for i, column in enumerate(columns):
                        api_data[column] = first_row[i]
                    
                    # Add endpoint information
                    api_data['endpoint_id'] = endpoint_id
                    api_data['endpoint'] = endpoint_path
                    api_data['method'] = method
                    api_data['description'] = description
                    api_data['table_name'] = table_name
                    
                    positive_apis.append(api_data)
                    
            except Exception as e:
                print(f"Error fetching data from table {table_name}: {str(e)}")
                continue
        
        cursor.close()
        connection.close()
                
    except Exception as e:
        print(f"Error in get_positive_apis: {str(e)}")
        return {"error": str(e)}
    
    return {"positive_apis": positive_apis}

@app.post("/api/clear-console")
def api_clear_console():
    clear_console()
    return {"status": "cleared"}

# Endpoints API route
@app.get("/api/endpoints")
def get_endpoints():
    from sat_core.fetch_endpoints import fetch_endpoints
    try:
        endpoints = fetch_endpoints()
        # Convert to list of dicts for JSON serialization
        endpoints_list = []
        for endpoint in endpoints:
            endpoints_list.append({
                "id": endpoint["id"],
                "path": endpoint["path"],
                "method": endpoint["method"],
                "summary": endpoint["summary"],
                "description": endpoint["description"],
                "tags": endpoint["tags"] if endpoint["tags"] else [],
                "operation_id": endpoint["operation_id"],
                "deprecated": endpoint["deprecated"]
            })
        return {"endpoints": endpoints_list}
    except Exception as e:
        return {"error": str(e), "endpoints": []}

# Testcases API route
@app.get("/api/testcases")
def get_testcases():
    from sat_core.global_state import endpoint_tables
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from sat_core.config import DB_CONFIG
    
    try:
        testcases = {}
        
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for endpoint_id, table_name in endpoint_tables.items():
                    try:
                        cur.execute(f"SELECT * FROM {table_name}")
                        testcases_list = cur.fetchall()
                        
                        # Convert to list of dicts for JSON serialization
                        testcases[table_name] = []
                        for testcase in testcases_list:
                            testcases[table_name].append({
                                "id": testcase["id"],
                                "endpoint_id": testcase["endpoint_id"],
                                "test_type": testcase["test_type"],
                                "test_name": testcase["test_name"],
                                "method": testcase["method"],
                                "url": testcase["url"],
                                "headers": testcase["headers"],
                                "query_params": testcase["query_params"],
                                "path_params": testcase["path_params"],
                                "input_payload": testcase["input_payload"],
                                "expected_status": testcase["expected_status"],
                                "expected_schema": testcase["expected_schema"]
                            })
                    except Exception as e:
                        print(f"Error fetching from table {table_name}: {e}")
                        testcases[table_name] = []
        
        return {"testcases": testcases}
    except Exception as e:
        return {"error": str(e), "testcases": {}}


# AI Reports API Endpoints
@app.get("/api/ai-reports/analysis")
async def get_ai_analysis():
    """Get AI analysis of execution results"""
    try:
        log_to_console("Generating AI analysis for latest execution results", "info")
        analysis_result = generate_ai_report()
        log_to_console("AI analysis completed successfully", "success")
        
        # Ensure the result is JSON serializable
        serialized_result = serialize_for_json(analysis_result)
        return JSONResponse(content=serialized_result)
    except Exception as e:
        log_to_console(f"Error generating AI analysis: {str(e)}", "error")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to generate AI analysis: {str(e)}"}
        )


@app.post("/api/ai-reports/regenerate")
async def regenerate_ai_analysis(request: Request):
    """Regenerate AI analysis with fresh data"""
    try:
        log_to_console("Regenerating AI analysis with fresh data", "info")
        analysis_result = generate_ai_report()
        log_to_console("AI analysis regenerated successfully", "success")
        
        # Ensure the result is JSON serializable
        serialized_result = serialize_for_json(analysis_result)
        return JSONResponse(content=serialized_result)
    except Exception as e:
        log_to_console(f"Error regenerating AI analysis: {str(e)}", "error")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to regenerate AI analysis: {str(e)}"}
        )


@app.get("/api/ai-reports/endpoint-stability")
async def get_endpoint_stability():
    """Get endpoint stability analysis"""
    try:
        analysis_result = generate_ai_report()
        endpoint_stability = analysis_result.get("endpoint_stability", [])
        
        # Ensure the result is JSON serializable
        serialized_result = serialize_for_json({"endpoint_stability": endpoint_stability})
        return JSONResponse(content=serialized_result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get endpoint stability: {str(e)}"}
        )


@app.get("/api/ai-reports/schema-issues")
async def get_schema_issues():
    """Get schema validation issues"""
    try:
        analysis_result = generate_ai_report()
        schema_issues = analysis_result.get("schema_issues", [])
        
        # Ensure the result is JSON serializable
        serialized_result = serialize_for_json({"schema_issues": schema_issues})
        return JSONResponse(content=serialized_result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get schema issues: {str(e)}"}
        )

# ✅ Allure Report Builder
# ======================================================
@app.post("/api/build-allure")
def api_build_allure():
    if not os.path.exists(ALLURE_RESULTS_DIR):
        return JSONResponse({
            "status": "no_results",
            "message": f"No allure-results folder found at {ALLURE_RESULTS_DIR}"
        }, status_code=400)

    # Clean previous report
    if os.path.exists(ALLURE_REPORT_DIR):
        shutil.rmtree(ALLURE_REPORT_DIR)
    os.makedirs(ALLURE_REPORT_DIR, exist_ok=True)

    allure_exe = r"C:\nvm4w\nodejs\allure.cmd"
    # allure_exe = "allure"
    cmd = [allure_exe, "generate", ALLURE_RESULTS_DIR, "-o", ALLURE_REPORT_DIR, "--clean"]

    try:
        subprocess.run(cmd, check=True)
        report_url = "/static/allure-report/index.html"
        return {"status": "ok", "report_path": report_url}
    except subprocess.CalledProcessError as e:
        return JSONResponse({
            "status": "error",
            "message": f"Allure generation failed: {e}"
        }, status_code=500)



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
