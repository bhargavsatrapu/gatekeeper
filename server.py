"""
FastAPI server exposing the API Testing Agent via HTTP endpoints.

Endpoints:
- POST /runs: start a new run
- GET /runs/{run_id}/status: get workflow status
- GET /runs/{run_id}/logs: get execution logs
- GET /runs/{run_id}/results: get test results
- POST /runs/{run_id}/cancel: cancel a running job (best-effort)
- GET /config, PUT /config: read/update app config
- GET /swagger: return current swagger spec
- POST /swagger/upload: upload a new swagger.json and set path
- GET /health, GET /health/db: health checks
"""

from __future__ import annotations

import json
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, List

from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import get_config, update_config
from agents import get_api_testing_agent, create_initial_state
from agents.workflow_nodes import get_workflow_nodes
from database import test_database_connection, get_endpoint_repository, get_db_initializer
from parsers.swagger_parser import SwaggerParser
from generators.test_case_generator import get_test_case_generator
from runners.test_executor import get_test_executor, get_execution_planner
from runners.api_client import get_api_client
from database.models import get_test_case_repository
from utils.logger import get_logger

logger = get_logger(__name__)

# Optional Allure integration
try:
    from reporters.allure_reporter import get_allure_reporter
    ALLURE_AVAILABLE = True
    logger.info("Allure reporting is available")
except ImportError as e:
    ALLURE_AVAILABLE = False
    logger.warning(f"Allure reporting not available: {e}")
    # Create a dummy function to avoid errors
    def get_allure_reporter():
        return None


app = FastAPI(title="Gatekeeper API Testing Server", version="0.1.0")

# Initialize database at server startup
@app.on_event("startup")
def _init_db_on_startup():
    try:
        initializer = get_db_initializer()
        initializer.initialize_database()
    except Exception:
        # Fail open: health/db can still report status
        pass

# CORS (open by default; tighten as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Serve a simple static UI
try:
    app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")
except Exception:
    # UI folder may not exist yet; ignore
    pass


# Redirect root to UI for convenience
@app.get("/")
def root_redirect():
    return RedirectResponse(url="/ui")


class RunState:
    def __init__(self):
        self.thread: Optional[threading.Thread] = None
        self.cancel_requested: bool = False
        self.exit_code: Optional[int] = None


RUNS: Dict[str, RunState] = {}
parser = SwaggerParser()

# Cache: holds the last generated mapping so execute routes can reuse it
# Shape: Dict[str, List[Dict[str, Any]]] mapping endpoint -> list of testcases
LAST_GENERATED_MAPPING: Optional[Dict[str, List[Dict[str, Any]]]] = None
# Cache last execution results for reporting
LAST_POSITIVE_RESULTS: Optional[Dict[str, Any]] = None
LAST_ALL_RESULTS: Optional[Dict[str, Any]] = None


def _run_agent(run_id: str) -> None:
    agent = get_api_testing_agent()
    initial_state = create_initial_state()
    agent.run(initial_state)
    # no explicit exit code; infer from errors
    RUNS[run_id].exit_code = 0 if not agent.get_errors() else 1


@app.post("/runs")
def start_run(
    background_tasks: BackgroundTasks,
    swagger_file_path: Optional[str] = None,
    base_url: Optional[str] = None,
    database_config: Optional[Dict[str, Any]] = None,
    llm_config: Optional[Dict[str, Any]] = None,
):
    # Apply optional config overrides
    cfg_updates: Dict[str, Any] = {}
    if swagger_file_path:
        cfg_updates["swagger_file_path"] = swagger_file_path
    if base_url:
        cfg_updates["api"] = {"base_url": base_url}
    if database_config:
        cfg_updates["database"] = database_config
    if llm_config:
        cfg_updates["llm"] = llm_config
    if cfg_updates:
        update_config(**cfg_updates)

    run_id = str(uuid.uuid4())
    RUNS[run_id] = RunState()
    background_tasks.add_task(_run_agent, run_id)
    return {"run_id": run_id}


def _get_agent_or_404() -> Any:
    try:
        return get_api_testing_agent()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent unavailable: {e}")


@app.get("/runs/{run_id}/status")
def get_status(run_id: str):
    if run_id not in RUNS:
        raise HTTPException(status_code=404, detail="Run not found")
    agent = _get_agent_or_404()
    status = agent.get_workflow_status()
    exit_code = RUNS[run_id].exit_code
    return {"status": status, "exit_code": exit_code}


@app.get("/runs/{run_id}/logs")
def get_logs(run_id: str):
    if run_id not in RUNS:
        raise HTTPException(status_code=404, detail="Run not found")
    agent = _get_agent_or_404()
    return {"execution_logs": agent.get_execution_logs()}


@app.get("/runs/{run_id}/results")
def get_results(run_id: str):
    if run_id not in RUNS:
        raise HTTPException(status_code=404, detail="Run not found")
    agent = _get_agent_or_404()
    results = agent.get_test_results() or {}
    return results


# Reporting endpoints
@app.get("/report/last")
def get_last_report():
    """Return a consolidated report of the most recent Execute Positive and Execute All runs."""
    return {
        "positive": LAST_POSITIVE_RESULTS or {},
        "all": LAST_ALL_RESULTS or {},
    }

@app.post("/report/generate")
def generate_report():
    """Return a summarized report with pass/fail counts and failed reasons for last runs."""
    def summarize(results: Optional[Dict[str, Any]]):
        if not results:
            return {"total": 0, "passed": 0, "failed": 0, "failed_details": []}
        logs = results.get("logs", {})
        failed_details = []
        for name, entry in logs.items():
            resp = (entry or {}).get("response", {})
            success = bool(resp.get("success"))
            if not success:
                failed_details.append({
                    "test_name": name,
                    "status_code": resp.get("status_code"),
                    "reason": resp.get("error") or resp.get("message") or "Failed",
                })
        total = int(results.get("summary", {}).get("total_tests") or results.get("executed") or 0)
        passed = int(results.get("summary", {}).get("passed_tests") or 0)
        failed = max(total - passed, 0)
        return {"total": total, "passed": passed, "failed": failed, "failed_details": failed_details}

    return {
        "positive": summarize(LAST_POSITIVE_RESULTS),
        "all": summarize(LAST_ALL_RESULTS),
    }


@app.post("/runs/{run_id}/cancel")
def cancel_run(run_id: str):
    run = RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    run.cancel_requested = True
    return {"ok": True}


@app.get("/config")
def read_config():
    cfg = get_config()
    # Serialize nested dataclasses via their dict representations
    return {
        "swagger_file_path": cfg.swagger_file_path,
        "log_level": cfg.log_level,
        "execution_delay": cfg.execution_delay,
        "database": cfg.database.to_dict(),
        "api": {"base_url": cfg.api.base_url, "timeout": cfg.api.timeout, "max_retries": cfg.api.max_retries},
        "llm": {"model": cfg.llm.model, "max_tokens": cfg.llm.max_tokens},
    }


@app.put("/config")
def update_app_config(payload: Dict[str, Any]):
    try:
        update_config(**payload)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/swagger")
def get_swagger():
    cfg = get_config()
    path = Path(cfg.swagger_file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Swagger not found at {cfg.swagger_file_path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return JSONResponse(content=data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid swagger.json")


@app.post("/swagger/upload")
def upload_swagger(file: UploadFile = File(...)):
    if not file.filename.endswith((".json",)):
        raise HTTPException(status_code=400, detail="Only .json swagger supported here")
    content = file.file.read()
    try:
        data = json.loads(content)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    dest = Path("swagger.json")
    dest.write_text(json.dumps(data, indent=2), encoding="utf-8")
    update_config(swagger_file_path=str(dest.resolve()))
    return {"path": str(dest.resolve())}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    ok = test_database_connection()
    return {"ok": ok}


# ---------- New modular routes for UI flows ----------

@app.get("/endpoints/preview")
def preview_endpoints():
    repo = get_endpoint_repository()
    endpoints = repo.get_all_endpoints()
    return {"count": len(endpoints), "endpoints": endpoints}


@app.post("/testcases/generate")
def generate_testcases():
    # Generate based on endpoints stored in DB (post-extract)
    repo = get_endpoint_repository()
    endpoints = repo.get_all_endpoints()
    generator = get_test_case_generator()
    mapping = generator.generate_test_cases(endpoints)
    generated_total = sum(len(v) for v in mapping.values())
    # Store in cache for subsequent executions
    global LAST_GENERATED_MAPPING
    LAST_GENERATED_MAPPING = mapping
    return {"total_endpoints": len(mapping), "generated_total": generated_total, "mapping": mapping}


@app.post("/testcases/persist")
def persist_testcases_to_db():
    """Persist the last generated testcases into DB tables keyed per endpoint."""
    global LAST_GENERATED_MAPPING
    if LAST_GENERATED_MAPPING is None:
        raise HTTPException(status_code=400, detail="No generated testcases available to persist. Generate first.")

    endpoint_repo = get_endpoint_repository()
    db_init = get_db_initializer()
    testcase_repo = get_test_case_repository()

    endpoints = endpoint_repo.get_all_endpoints()
    # Build key mapping method path -> endpoint
    key_to_endpoint = {f"{ep['method']} {ep['path']}": ep for ep in endpoints}

    endpoint_tables: Dict[int, str] = {}
    persisted_counts: Dict[str, int] = {}

    def _sanitize_table_name(path: str, method: str) -> str:
        import re as _re
        clean_path = _re.sub(r'[^a-zA-Z0-9_]', '_', path.strip("/"))
        return f"api_testcases_{clean_path.lower()}_{method.lower()}"

    for key, cases in LAST_GENERATED_MAPPING.items():
        ep = key_to_endpoint.get(key)
        if not ep or not cases:
            continue
        table_name = _sanitize_table_name(ep['path'], ep['method'])
        db_init.create_test_cases_table(table_name)
        count = 0
        for tc in cases:
            tc["endpoint_id"] = ep["id"]
            if testcase_repo.insert_test_case(table_name, tc):
                count += 1
        endpoint_tables[ep['id']] = table_name
        persisted_counts[key] = count

    return {
        "endpoints_processed": len(persisted_counts),
        "persisted_per_endpoint": persisted_counts,
        "endpoint_tables": endpoint_tables,
    }


@app.post("/swagger/extract")
def extract_swagger_to_db():
    """Parse current swagger file and persist endpoints into DB (no testcase generation)."""
    cfg = get_config()
    data = parser.load_swagger_file(cfg.swagger_file_path)
    paths_count = len((data or {}).get("paths", {}) or {})
    endpoints = parser.extract_endpoints(data)
    # Optional: recreate api_endpoints table for a fresh import
    try:
        initializer = get_db_initializer()
        initializer.initialize_database()
    except Exception:
        pass
    repo = get_endpoint_repository()
    stored = 0
    failures: List[Dict[str, Any]] = []
    for ep in endpoints:
        try:
            if repo.insert_endpoint(ep):
                stored += 1
        except Exception as e:
            failures.append({"path": ep.get("path"), "method": ep.get("method"), "error": str(e)})
    return {
        "swagger_file_path": cfg.swagger_file_path,
        "paths_detected": paths_count,
        "extracted_endpoints": len(endpoints),
        "stored": stored,
        "total": len(endpoints),
        "failures": failures,
    }


@app.post("/execute/testcases")
def execute_testcases(payload: Dict[str, Any]):
    # payload expects either a mapping of endpoint->cases, or a flat list under key "cases"
    executor = get_test_executor()
    planner = get_execution_planner()

    cases = payload.get("cases")
    if not cases:
        mapping = payload.get("mapping", {})
        cases = []
        for _, arr in mapping.items():
            cases.extend(arr)

    # Execute cases sequentially as provided
    results = {"executed": 0}
    results["generated_total"] = len(cases)
    for case in cases:
        request_data, resp = executor.execute_test_case(case)
        results.setdefault("logs", {})[case.get("test_name", "")] = {
            "request": request_data,
            "response": resp.to_dict(),
        }
        results["executed"] += 1

    summary = {
        "total_tests": results["executed"],
        "passed_tests": sum(1 for log in results["logs"].values() if log["response"].get("success")),
    }
    summary["failed_tests"] = summary["total_tests"] - summary["passed_tests"]
    results["summary"] = summary
    return results


@app.post("/execute/all")
def execute_all():
    cfg = get_config()
    # Connectivity pre-check with retries
    api_client = get_api_client()
    if not api_client.check_connectivity(cfg.api.base_url):
        raise HTTPException(status_code=503, detail=f"API base URL not reachable: {cfg.api.base_url}")
    global LAST_GENERATED_MAPPING
    mapping = LAST_GENERATED_MAPPING
    # If nothing in cache yet, generate once and cache it
    if mapping is None:
        data = parser.load_swagger_file(cfg.swagger_file_path)
        endpoints = parser.extract_endpoints(data)
        generator = get_test_case_generator()
        mapping = generator.generate_test_cases(endpoints)
        LAST_GENERATED_MAPPING = mapping

    # Flatten all cases
    all_cases = []
    for _, arr in mapping.items():
        all_cases.extend(arr)

    # Execute (client has internal retries)
    executor = get_test_executor()
    results = {"executed": 0}
    results["generated_total"] = len(all_cases)
    for case in all_cases:
        request_data, resp = executor.execute_test_case(case)
        results.setdefault("logs", {})[case.get("test_name", "")] = {
            "request": request_data,
            "response": resp.to_dict(),
            "case": case,
        }
        results["executed"] += 1

    summary = {
        "total_tests": results["executed"],
        "passed_tests": sum(1 for log in results["logs"].values() if log["response"].get("success")),
    }
    summary["failed_tests"] = summary["total_tests"] - summary["passed_tests"]
    results["summary"] = summary
    results["generated_counts"] = {k: len(v) for k, v in mapping.items()}
    # Cache for reporting
    global LAST_ALL_RESULTS
    LAST_ALL_RESULTS = results
    
    # Generate Allure report if available
    if ALLURE_AVAILABLE:
        try:
            from reporters.allure_reporter import AllureTestReporter
            allure_reporter = AllureTestReporter("allure-results-all")
            allure_reporter.clear_results()
            suite_uuid = allure_reporter.start_test_suite("Execute All Testcases")
            
            for test_name, log_entry in results.get("logs", {}).items():
                case = log_entry.get("case", {})
                request_data = log_entry.get("request", {})
                response_data = log_entry.get("response", {})
                success = response_data.get("success", False)
                
                allure_reporter.add_test_result(
                    test_name=test_name,
                    status="passed" if success else "failed",
                    description=case.get("description", ""),
                    method=case.get("method", ""),
                    url=case.get("url", ""),
                    expected_status=case.get("expected_status", ""),
                    request_data=request_data,
                    response_data=response_data,
                    error_message=response_data.get("error", "") if not success else "",
                    duration=response_data.get("execution_time_ms", 0)
                )
            
            allure_reporter.finalize_suite(suite_uuid)
            allure_reporter.generate_report()
            logger.info("Allure report generated for all tests")
        except Exception as e:
            logger.error(f"Failed to generate Allure report: {e}")
    
    return results


@app.post("/execute/positive")
def execute_positive_flow():
    cfg = get_config()
    # Optional connectivity pre-check
    api_client = get_api_client()
    if not api_client.check_connectivity(cfg.api.base_url):
        raise HTTPException(status_code=503, detail=f"API base URL not reachable: {cfg.api.base_url}")

    # Use cached mapping if available; otherwise generate and cache
    global LAST_GENERATED_MAPPING
    mapping = LAST_GENERATED_MAPPING
    if mapping is None:
        data = parser.load_swagger_file(cfg.swagger_file_path)
        endpoints = parser.extract_endpoints(data)
        generator = get_test_case_generator()
        mapping = generator.generate_test_cases(endpoints)
        LAST_GENERATED_MAPPING = mapping

    # Select exactly one testcase per endpoint (prefer test_type=="positive"; fallback to first)
    positive_cases = []
    for _, arr in mapping.items():
        if not arr:
            continue
        preferred = None
        for case in arr:
            if str(case.get("test_type", "")).lower() == "positive":
                preferred = case
                break
        positive_cases.append(preferred or arr[0])

    # Execute positives
    executor = get_test_executor()
    results: Dict[str, Any] = {"executed": 0}
    results["generated_total"] = len(positive_cases)
    print(f"[EXECUTE_POSITIVE] Total positive cases identified: {len(positive_cases)}")
    for case in positive_cases:
        request_data, resp = executor.execute_test_case(case)
        results.setdefault("logs", {})[case.get("test_name", "")] = {
            "request": request_data,
            "response": resp.to_dict(),
            "case": case,
        }
        results["executed"] += 1
    print(f"[EXECUTE_POSITIVE] Positive cases executed: {results['executed']}")

    summary = {
        "total_tests": results["executed"],
        "passed_tests": sum(1 for log in results["logs"].values() if log["response"].get("success")),
    }
    summary["failed_tests"] = summary["total_tests"] - summary["passed_tests"]
    results["summary"] = summary
    results["positive_executed"] = results["executed"]
    # Report how many candidates existed per endpoint and which were chosen
    results["generated_counts"] = {k: len(v) for k, v in mapping.items()}
    # Cache for reporting
    global LAST_POSITIVE_RESULTS
    LAST_POSITIVE_RESULTS = results
    
    # Generate Allure report for positive tests if available
    if ALLURE_AVAILABLE:
        try:
            from reporters.allure_reporter import AllureTestReporter
            allure_reporter = AllureTestReporter("allure-results-positive")
            allure_reporter.clear_results()
            suite_uuid = allure_reporter.start_test_suite("Execute Positive Testcases")
            
            for test_name, log_entry in results.get("logs", {}).items():
                case = log_entry.get("case", {})
                request_data = log_entry.get("request", {})
                response_data = log_entry.get("response", {})
                success = response_data.get("success", False)
                
                allure_reporter.add_test_result(
                    test_name=test_name,
                    status="passed" if success else "failed",
                    description=case.get("description", ""),
                    method=case.get("method", ""),
                    url=case.get("url", ""),
                    expected_status=case.get("expected_status", ""),
                    request_data=request_data,
                    response_data=response_data,
                    error_message=response_data.get("error", "") if not success else "",
                    duration=response_data.get("execution_time_ms", 0)
                )
            
            allure_reporter.finalize_suite(suite_uuid)
            allure_reporter.generate_report()
            logger.info("Allure report generated for positive tests")
        except Exception as e:
            logger.error(f"Failed to generate Allure report: {e}")
    
    return results


def _sse_event(data: Dict[str, Any]) -> bytes:
    return ("data: " + json.dumps(data) + "\n\n").encode("utf-8")


@app.get("/stream/positive")
def stream_execute_positive():
    cfg = get_config()
    api_client = get_api_client()
    if not api_client.check_connectivity(cfg.api.base_url):
        raise HTTPException(status_code=503, detail=f"API base URL not reachable: {cfg.api.base_url}")

    def _gen():
        # Use cached mapping or generate once
        global LAST_GENERATED_MAPPING
        mapping = LAST_GENERATED_MAPPING
        if mapping is None:
            data = parser.load_swagger_file(cfg.swagger_file_path)
            endpoints = parser.extract_endpoints(data)
            generator = get_test_case_generator()
            mapping = generator.generate_test_cases(endpoints)
            LAST_GENERATED_MAPPING = mapping

        # Use same logic as execute_positive_flow: one case per endpoint
        positive_cases = []
        for _, arr in mapping.items():
            if not arr:
                continue
            preferred = None
            for case in arr:
                if str(case.get("test_type", "")).lower() == "positive":
                    preferred = case
                    break
            positive_cases.append(preferred or arr[0])

        executor = get_test_executor()
        executed = 0
        passed = 0
        for idx, case in enumerate(positive_cases, start=1):
            request_data, resp = executor.execute_test_case(case)
            resp_dict = resp.to_dict()
            success = bool(resp_dict.get("success"))
            passed += 1 if success else 0
            executed += 1
            yield _sse_event({
                "type": "test",
                "seq": idx,
                "name": case.get("test_name"),
                "description": case.get("description"),
                "method": case.get("method"),
                "url": case.get("url"),
                "expected_status": case.get("expected_status"),
                "request": request_data,
                "response": resp_dict,
                "success": success,
            })
        yield _sse_event({
            "type": "summary",
            "executed": executed,
            "passed": passed,
            "failed": max(executed - passed, 0),
        })

    return StreamingResponse(_gen(), media_type="text/event-stream")


@app.get("/stream/all")
def stream_execute_all():
    cfg = get_config()
    api_client = get_api_client()
    if not api_client.check_connectivity(cfg.api.base_url):
        raise HTTPException(status_code=503, detail=f"API base URL not reachable: {cfg.api.base_url}")

    def _gen():
        global LAST_GENERATED_MAPPING
        mapping = LAST_GENERATED_MAPPING
        if mapping is None:
            data = parser.load_swagger_file(cfg.swagger_file_path)
            endpoints = parser.extract_endpoints(data)
            generator = get_test_case_generator()
            mapping = generator.generate_test_cases(endpoints)
            LAST_GENERATED_MAPPING = mapping

        # Flatten
        all_cases: List[Dict[str, Any]] = []
        for _, arr in mapping.items():
            all_cases.extend(arr)

        executor = get_test_executor()
        executed = 0
        passed = 0
        for idx, case in enumerate(all_cases, start=1):
            request_data, resp = executor.execute_test_case(case)
            resp_dict = resp.to_dict()
            success = bool(resp_dict.get("success"))
            passed += 1 if success else 0
            executed += 1
            yield _sse_event({
                "type": "test",
                "seq": idx,
                "name": case.get("test_name"),
                "description": case.get("description"),
                "method": case.get("method"),
                "url": case.get("url"),
                "expected_status": case.get("expected_status"),
                "request": request_data,
                "response": resp_dict,
                "success": success,
            })
        yield _sse_event({
            "type": "summary",
            "executed": executed,
            "passed": passed,
            "failed": max(executed - passed, 0),
        })

    return StreamingResponse(_gen(), media_type="text/event-stream")


@app.get("/allure/report/positive")
def open_allure_report_positive():
    """Open Allure report for positive testcases."""
    if not ALLURE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Allure reporting is not available. Please install allure-pytest and allure-python-commons.")
    
    from pathlib import Path
    results_dir = Path("allure-results-positive")
    
    if not results_dir.exists() or not any(results_dir.glob("*.json")):
        raise HTTPException(status_code=404, detail="No Allure report found. Please run positive tests first.")
    
    # Return the path to the Allure results directory
    return {
        "results_dir": str(results_dir),
        "message": "Allure report generated. Use 'allure serve' command to view the report.",
        "command": f"allure serve {results_dir}"
    }


@app.get("/allure/report/all")
def open_allure_report_all():
    """Open Allure report for all testcases."""
    if not ALLURE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Allure reporting is not available. Please install allure-pytest and allure-python-commons.")
    
    from pathlib import Path
    results_dir = Path("allure-results-all")
    
    if not results_dir.exists() or not any(results_dir.glob("*.json")):
        raise HTTPException(status_code=404, detail="No Allure report found. Please run all tests first.")
    
    # Return the path to the Allure results directory
    return {
        "results_dir": str(results_dir),
        "message": "Allure report generated. Use 'allure serve' command to view the report.",
        "command": f"allure serve {results_dir}"
    }


@app.post("/allure/serve")
def start_allure_server(request_data: dict = None):
    """Start Allure live server for real-time report viewing."""
    if not ALLURE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Allure reporting is not available. Please install allure-pytest and allure-python-commons.")
    
    import subprocess
    import threading
    import time
    from pathlib import Path
    
    # Get results directory from request or use default
    if request_data and "results_dir" in request_data:
        results_dir = Path(request_data["results_dir"])
    else:
        results_dir = Path("allure-results")
    
    if not results_dir.exists():
        raise HTTPException(status_code=404, detail=f"No Allure results directory found: {results_dir}")
    
    def run_allure_server():
        try:
            # Start Allure server on port 8080
            subprocess.run([
                "allure", "serve", str(results_dir), 
                "--port", "8080", 
                "--host", "localhost"
            ], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start Allure server: {e}")
        except FileNotFoundError:
            logger.error("Allure command not found. Please install Allure CLI.")
    
    # Start server in background thread
    server_thread = threading.Thread(target=run_allure_server, daemon=True)
    server_thread.start()
    
    # Give server time to start
    time.sleep(2)
    
    return {
        "message": "Allure server started successfully",
        "url": "http://localhost:8080",
        "results_dir": str(results_dir),
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)


