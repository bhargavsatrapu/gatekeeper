import json
import time
from typing import Dict, Any, List

import psycopg2
from psycopg2.extras import RealDictCursor
from sat_core.config import BASE_URL, DB_CONFIG
from sat_core.ai_client import get_gemini_client
from sat_core.fetch_endpoints import fetch_endpoints
from sat_core.global_state import endpoint_tables
from sat_core.call_api import call_api


def order_testcases_and_execute(endpoints_list: List[int]) -> List[Dict[str, int]]:
    client = get_gemini_client()
    all_endpoints = fetch_endpoints()

    execution_orders: List[Dict[str, int]] = []
    executions_logs: Dict[str, Dict[str, Any]] = {}
    BASE_URL_LOCAL = BASE_URL

    if len(endpoints_list) == 0 :
        endpoints_to_test=endpoint_tables
    else:
        endpoints_to_test = {k: endpoint_tables[k] for k in endpoints_list if k in endpoint_tables}


    for endpoint_id, table_name in endpoints_to_test.items():
        conn = psycopg2.connect(cursor_factory=RealDictCursor, **DB_CONFIG)
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT * FROM {table_name}")
            all_testcases = cur.fetchall()
        except Exception:
            all_testcases = []
        finally:
            cur.close()
            conn.close()
        print("\n\n\n=====================================================================")
        print("############## ",table_name," ##############")
        print("############## ",all_testcases[0]["url"]," ##############")
        print("=====================================================================\n\n\n")
        llm_prompt = (
            "You are an expert API test execution planner.\n"
            "I will provide you with two things:\n"
            "1. A list of all available API endpoints with their primary keys.\n"
            "2. A list of all possible testcases for a single endpoint with their primary keys.\n\n"

            "Your task:\n"
            "1. Create the correct execution order for the given endpoint's testcases.\n"
            "   - If a testcase depends on data (e.g., token, user_id, product_id), "
            "insert the appropriate provider API(s) from the endpoint list before running it.\n"
            "   - Auth flows: login must run before protected APIs, logout must run last if applicable.\n"
            "   - Data dependencies: create/register/add must run before get/update/delete.\n"
            "   - Negative cases must run after their corresponding positive case.\n"
            "   - Edge cases should run after positive flows but before destructive cases.\n"
            "   - Authentication-related negetive api tests should run after all tests\n"
            "2. Use endpoints only for setup (data creation or authentication) if required.\n"
            "3. Do not drop any testcases. Every testcase must appear exactly once in the final order.\n\n"

            "⚠️ Rules:\n"
            "- Return valid JSON only.\n"
            "- The output must be a list of dictionaries.\n"
            "- Each dictionary must have exactly one key-value pair.\n"
            "- Use the key 'all_endpoints' when the entry comes from endpoints.\n"
            "- Use the key 'all_testcases' when the entry comes from testcases.\n"
            "- The value must be the primary key of the row (integer).\n\n"

            f"Here are all endpoints with primary keys:\n{json.dumps(all_endpoints, indent=2, default=str)}\n\n"
            f"Here are all possible testcases with primary keys:\n{json.dumps(all_testcases, indent=2, default=str)}\n\n"

            "Return JSON like this:\n"
            "[\n"
            "  {\"all_endpoints\": 2},\n"
            "  {\"all_endpoints\": 101},\n"
            "  {\"all_testcases\": 7},\n"
            "  {\"all_testcases\": 201},\n"
            "  {\"all_endpoints\": 202}\n"
            "]"
        )

        response = client.models.generate_content(model="gemini-2.5-flash", contents=llm_prompt)
        cleaned_output = response.text.strip("`").strip()
        if cleaned_output.startswith(("json", "python")):
            cleaned_output = cleaned_output.split("\n", 1)[-1].strip()

        try:
            order = json.loads(cleaned_output)
        except Exception:
            order = []

        # execute the produced order
        for item in order:
            if "all_endpoints" in item:
                # pick any one testcase for that endpoint to generate data/logs
                dep_table = endpoint_tables.get(item["all_endpoints"])  # could be None
                if not dep_table:
                    continue
                conn = psycopg2.connect(cursor_factory=RealDictCursor, **DB_CONFIG)
                cur = conn.cursor()
                cur.execute(f"SELECT * FROM {dep_table} LIMIT 1")
                testcase = cur.fetchone()
                cur.close()
                conn.close()
            else:
                # direct testcase id from current table
                pk = item.get("all_testcases")
                conn = psycopg2.connect(cursor_factory=RealDictCursor, **DB_CONFIG)
                cur = conn.cursor()
                cur.execute(f"SELECT * FROM {table_name} WHERE id = %s", (pk,))
                testcase = cur.fetchone()
                cur.close()
                conn.close()

            if not testcase:
                continue

            llm_input = {
                    "test_descriptsion": testcase.get("test_name", ""),
                    "endpoint": testcase.get("url", ""),
                    "headers": testcase.get("headers", {}),
                    "query_params": testcase.get("query_params", {}),
                    "input_payload": testcase.get("input_payload", {})
                }

            llm_prompt = (
                "You are a smart test data generator for API testing.\n"
                "I will provide you with API request details containing placeholders, along with execution logs of previous API calls.\n\n"
                "Your job is to replace the placeholders with values appropriate to the test case type (positive, negative, edge, or auth).\n\n"
                "Instructions:\n"
                "1. Positive test cases:\n"
                "   - Replace placeholders with realistic dummy values if independent (e.g., username → 'valid_user123').\n"
                "   - If the field depends on previous API responses (e.g., user_id, token), you MUST pick the exact value from the execution logs' 'response' section.\n\n"
                "2. Negative test cases:\n"
                "   - Use invalid, malformed, or out-of-range values (e.g., email → 'invalid-email', age → -1, token → 'wrong_token').\n"
                "   - If the case involves missing fields, set the placeholder to an empty string or null but keep the field name.\n\n"
                "3. Edge test cases:\n"
                "   - Use boundary values or extreme inputs (e.g., string length = 0 or very long, max int, special characters).\n"
                "   - Still keep valid JSON structure.\n\n"
                "4. Auth test cases:\n"
                "   - For **valid authentication**, you MUST always extract the token only from the 'response' part of the proper authentication API in execution logs.\n"
                "   - Ignore tokens found in 'request' or 'url'.\n"
                "   - Execution logs may also contain expired or invalid tokens in the 'response'. You must only use the valid token from the correct authentication API 'response'.\n"
                "   - For **invalid authentication**, you may use expired tokens, an empty string, or a deliberately wrong token (e.g., 'wrong_token').\n"
                "   - Never invent new valid tokens. Always reuse real ones found in the 'response' of execution logs when valid authentication is required.\n\n"
                "⚠️ Rules:\n"
                "- Modify ONLY: url, headers, query_params, input_payload.\n"
                "- Do not remove or rename fields.\n"
                "- Keep JSON structure intact.\n"
                "- If multiple valid values exist in execution logs, pick any one.\n"
                "- Output must be valid JSON only.\n"
                "- Authentication tokens MUST come only from the 'response' of execution logs, and only from the correct authentication API response when valid authentication is required.\n\n"
                f"Base URL of the API server: {BASE_URL_LOCAL}, Provided API details contain only endpoints. Please return proper test data.\n\n"
                f"Execution Logs:\n{json.dumps(executions_logs, indent=2)}\n\n"
                f"API Input with placeholders:\n{json.dumps(llm_input, indent=2)}\n\n"
                "Return JSON with placeholders replaced by appropriate values based on the test case type.\n"
                "Use realistic values for positive cases, invalid/edge/expired values for negative/auth/edge cases.\n"
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=llm_prompt
            )

            try:
                cleaned_output = response.text.strip("`").strip()
                if cleaned_output.startswith(("json", "python")):
                    cleaned_output = cleaned_output.split("\n", 1)[-1].strip()
                enriched_fields = json.loads(cleaned_output)
            except Exception as e:
                print("⚠️ Failed to parse LLM response:", e)
                enriched_fields = llm_input

            req = {
                "url": enriched_fields.get("url", testcase["url"]),
                "method": testcase["method"],
                "headers": enriched_fields.get("headers", testcase["headers"]),
                "query_params": enriched_fields.get("query_params", testcase["query_params"]),
                "payload": enriched_fields.get("input_payload", testcase["input_payload"]),
                "test_description": testcase["test_name"],
            }
            res = call_api(req["method"], req["url"], req["headers"], req["query_params"], req["payload"], req["test_description"]) 
            executions_logs[testcase.get("test_name", req["url"])] = {"request": req, "response": res}
            time.sleep(1)

        execution_orders.extend(order)

    print("✅ Final execution order:", execution_orders)
    return execution_orders



