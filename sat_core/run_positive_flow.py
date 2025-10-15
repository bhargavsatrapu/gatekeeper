import json
import time
from typing import Dict, Any,Optional

from sat_core.config import BASE_URL,DB_CONFIG
from sat_core.global_state import endpoint_tables
from sat_core.call_api import call_api
import psycopg2
from psycopg2.extras import RealDictCursor
from sat_core.ai_client import get_gemini_client
from sat_core.plan_execution_order import plan_execution_order
from sat_core.db_utils import create_execution_results_table,insert_execution_result

# Add parent directory to path to import console logger
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from console_logger import log_to_console
from sat_core.reporting import (
    validate_response,
    write_allure_test_with_attachments,
    get_allure_results_dir,
    clean_allure_results
)
import shutil
import subprocess



def run_positive_flow(
    execution_order: Any,
    execution_logs: Dict[str, Dict[str, Any]] | None = None,
    results_dir: Optional[str] = None  # ✅ Added compatible typing
) -> Dict[str, Any]:
    if execution_logs is None:
        execution_logs = {}
    if results_dir is None:
        results_dir = get_allure_results_dir()
    clean_allure_results()

    log_to_console("🚀 Starting Positive Flow Execution", "info")
    log_to_console(f"📋 Processing {len(execution_order)} test cases", "info")
    
    BASE_URL_LOCAL = BASE_URL
    client = get_gemini_client()
    create_execution_results_table()
    print("execution_order is", execution_order)
    for current_id in execution_order:
        print("current_id is", current_id)
        print("End Point Tables are")
        print(endpoint_tables)
        table_name = endpoint_tables.get(current_id)
        if not table_name:
            continue
        print("table_name is", table_name)
        conn = psycopg2.connect(cursor_factory=RealDictCursor, **DB_CONFIG)
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {table_name} LIMIT 1")
        first_row = cur.fetchone()
        cur.close()
        conn.close()

        llm_input = {
            "url": first_row.get("url", ""),
            "headers": first_row.get("headers", {}),
            "query_params": first_row.get("query_params", {}),
            "input_payload": first_row.get("input_payload", {}),
        }

        llm_prompt = (
            "You are a smart test data generator.\n"
            "I will provide you with API request details that currently contain placeholders.\n"
            "You also have access to execution logs of previous API calls, which include real responses.\n\n"
            "Your task is:\n"
            "1. Replace placeholders with realistic dummy values if the field is independent.\n"
            "2. If the field depends on previous API responses (e.g., user_id, token, product_id), pick the actual value from the execution logs provided.\n"
            "3. Update the 'url' field using BASE_URL + ENDPOINT. This step is mandatory.\n\n"
            "⚠️ Rules:\n"
            "- Modify ONLY: url, headers, query_params, input_payload.\n"
            "- Do not remove or rename fields.\n"
            "- Keep JSON structure intact.\n"
            "- Output must be valid JSON only.\n\n"
            f"The Base URL of the API server is {BASE_URL_LOCAL}\n"
            f"Execution Logs:\n{json.dumps(execution_logs, indent=2)}\n\n"
            f"API Input with placeholders:\n{json.dumps(llm_input, indent=2)}\n\n"
            "Return JSON with placeholders replaced by actual values."
        )

        response = client.models.generate_content(model="gemini-2.5-flash", contents=llm_prompt)

        try:
            cleaned_output = response.text.strip("`").strip()
            if cleaned_output.startswith(("json", "python")):
                cleaned_output = cleaned_output.split("\n", 1)[-1].strip()
            enriched_fields = json.loads(cleaned_output)
        except Exception:
            enriched_fields = llm_input

        execution_case = {
            "url": enriched_fields.get("url"),
            "method": first_row["method"],
            "headers": enriched_fields.get("headers", first_row["headers"]),
            "query_params": enriched_fields.get("query_params", first_row["query_params"]),
            "payload": enriched_fields.get("input_payload", first_row["input_payload"]),
            "test_description": first_row["test_name"],
        }

        log_to_console(f"🔄 Executing test case: {execution_case['test_description']}", "test")
        result = call_api(
            execution_case["method"],
            execution_case["url"],
            execution_case["headers"],
            execution_case["query_params"],
            execution_case["payload"],
            execution_case["test_description"],
        )
        print("results are :", result)
        execution_logs[execution_case["url"]] = {"request": execution_case, "response": result}
        log_to_console(f"✅ Completed test case: {execution_case['test_description']}", "success")
        time.sleep(1)
        # Validate expected_status and expected_schema
        expected_status = None
        expected_schema = None
        try:
            expected_status = int(first_row.get("expected_status")) if first_row.get("expected_status") else None
        except Exception:
            expected_status = None
        try:
            schema_raw = first_row.get("expected_schema")
            if isinstance(schema_raw, str) and schema_raw.strip():
                expected_schema = json.loads(schema_raw)
            elif isinstance(schema_raw, dict):
                expected_schema = schema_raw
        except Exception:
            expected_schema = None

        passed, assertions = validate_response(result, expected_status, expected_schema)

        # Write Allure attachment
        write_allure_test_with_attachments(
        test_name=execution_case["test_description"],
        passed=passed,
        request=execution_case,
        response=result,
        assertions=assertions,
        description="Positive Testcase Execution",
        results_dir=get_allure_results_dir()  # <-- explicitly pass correct path
    )

        try:
            insert_execution_result(
                execution_case["test_description"],
                execution_case["method"],
                execution_case["url"],
                execution_case["headers"],
                execution_case["payload"],
                first_row["expected_status"],
                first_row["expected_schema"],
                result["status_code"],
                result["data"],
            )
        except:
            pass

    log_to_console("🎉 Positive Flow Execution Completed Successfully", "success")
    return execution_logs


def plan_and_run_positive_order():
    # ✅ Get base project directory dynamically
    base_dir = os.path.dirname(os.path.abspath(__file__))
    base_static_dir = os.path.join(base_dir, "static")

    # ✅ Ensure static directory exists (in case it’s missing)
    os.makedirs(base_static_dir, exist_ok=True)

    # Fixed folders for results & reports
    results_dir = os.path.join(base_static_dir, "allure-results")
    report_dir = os.path.join(base_static_dir, "allure-report")

    # Clean folders before execution
    if os.path.exists(results_dir):
        shutil.rmtree(results_dir)
    if os.path.exists(report_dir):
        shutil.rmtree(report_dir)
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)

    # Step 1: Determine execution order
    order = plan_execution_order()

    # Step 2: Run positive flow
    logs = run_positive_flow(order, results_dir=results_dir)

    # Step 3: Generate Allure report
    allure_exe = r"C:\nvm4w\nodejs\allure.cmd"
    cmd = [allure_exe, "generate", results_dir, "-o", report_dir, "--clean"]
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Allure report generated at: {report_dir}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Allure report generation failed: {e.stderr}")

    # Step 4: Save metadata for UI
    latest_run_meta = {
        "status": "ok",
        "type": "positive",
        "report_path": "/static/allure-report/index.html"
    }

    with open(os.path.join(base_static_dir, "latest_run.json"), "w") as f:
        json.dump(latest_run_meta, f, indent=2)

    print("💾 latest_run.json updated:", latest_run_meta["report_path"])
    return logs, report_dir




