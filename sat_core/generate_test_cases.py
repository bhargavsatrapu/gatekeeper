import json
from typing import Dict, Any

from sat_core.global_state import generated_cases
from sat_core.ai_client import get_gemini_client
from sat_core.fetch_endpoints import fetch_endpoints
from sat_core.persist_test_cases import persist_test_cases


def generate_test_cases(api_details: Any) -> Dict[str, Any]:
    client = get_gemini_client()

    expected_structure = {
        "test_name": "string",
        "test_type": "positive|negative|edge|schema|auth",
        "method": "string",
        "url": "string",
        "headers": {"key": "description of expected value"},
        "query_params": {"param": "description of expected value"},
        "path_params": {"param": "description of expected value"},
        "input_payload": {"field": "description of expected value"},
        "expected_status": "string",
        "expected_schema": {"field": "description of expected type/value"},
    }

    prompt = (
        "You are an API testing expert.\n"
        "I will provide API details in JSON format. The input may contain one or more API endpoints, "
        "including method, parameters, request body, possible responses, and response schema.\n"
        f"Here are the endpoints: {api_details}\n\n"
        "Your task is to generate comprehensive API test cases covering:\n"
        "- Positive cases\n"
        "- Negative cases\n"
        "- Edge cases\n"
        "- Schema validation\n"
        "- Authentication and authorization (e.g., valid token, missing token, expired token, invalid token)\n\n"
        "⚠️ IMPORTANT RULES:\n"
        "- Do NOT insert real values like 'abc123' or 'test@example.com'.\n"
        "- For each field, provide a placeholder with its type and data source:\n"
        "   1. If the field expects RANDOM data → describe it (e.g., 'string - random valid email').\n"
        "   2. If the field depends on another API response → describe as "
        "'pick from an existing API response' with its type.\n\n"
        "Examples:\n"
        "  { \"username\": \"string - random valid username\" }\n"
        "  { \"email\": \"string - random valid email\" }\n"
        "  { \"token\": \"string - pick from an existing API response\" }\n"
        "  { \"user_id\": \"integer - pick from an existing API response\" }\n\n"
        "OUTPUT FORMAT:\n"
        "Return the output strictly as a JSON dictionary where:\n"
        "- Each key is the endpoint path with its method (e.g., \"POST /users/register\").\n"
        "- The value is an array of test case dictionaries.\n\n"
        f"Each test case dictionary must strictly follow this structure:\n{expected_structure}\n\n"
        "Formatting rules:\n"
        "- Use double quotes for all keys and values.\n"
        "- Do not include markdown, comments, or code fences.\n"
        "- Ensure the final output is valid JSON and directly parsable.\n"
    )

    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)

    cleaned_output = response.text.strip("`").strip()
    if cleaned_output.startswith(("json", "python")):
        cleaned_output = cleaned_output.split("\n", 1)[-1].strip()

    cases = json.loads(cleaned_output)

    generated_cases.clear()
    generated_cases.update(cases)
    print("✅ generated_cases updated")
    return cases


def generate_test_case_and_store_in_db():
    eps = fetch_endpoints()
    generate_test_cases(eps)
    persist_test_cases()







