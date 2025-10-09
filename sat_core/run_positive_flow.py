import json
import time
from typing import Dict, Any

from sat_core.config import BASE_URL,DB_CONFIG
from sat_core.global_state import endpoint_tables
from sat_core.call_api import call_api
import psycopg2
from psycopg2.extras import RealDictCursor
from sat_core.ai_client import get_gemini_client
from sat_core.plan_execution_order import plan_execution_order



def run_positive_flow(execution_order: Any, execution_logs: Dict[str, Dict[str, Any]] | None = None) -> Dict[str, Any]:
    if execution_logs is None:
        execution_logs = {}

    BASE_URL_LOCAL = BASE_URL
    client = get_gemini_client()
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
        time.sleep(1)

    return execution_logs


def plan_and_run_positive_order():
    # Example run requires endpoint_tables pre-populated and cases persisted
    order = plan_execution_order()
    logs = run_positive_flow(order)
    print(json.dumps(logs, indent=2, default=str))



