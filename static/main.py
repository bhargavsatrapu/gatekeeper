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

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Import console logging system
from console_logger import get_console_logs, clear_console


@app.get("/")
def home(request: Request, msg: str | None = None, show_view_btn: str | None = None):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "msg": msg,
        "show_view_btn": show_view_btn == "true"
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
    return RedirectResponse(url="/?msg=Testcases%20generated%20successfully&show_view_btn=true", status_code=303)


@app.post("/run-positive")
def run_positive():
    __run_only_positive_flow()
    return RedirectResponse(url="/?msg=Positive%20flow%20executed", status_code=303)


@app.post("/run-all-tests")
def run_all_tests():
    __execute_all_test_cases_differnt_endpoint()
    return RedirectResponse(url="/?msg=All%20tests%20execution%20triggered", status_code=303)


# Console API routes
@app.get("/api/console-logs")
def api_get_console_logs():
    return {"logs": get_console_logs()}

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


