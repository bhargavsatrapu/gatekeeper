import ast
import json
from typing import List

from sat_core.ai_client import get_gemini_client
from sat_core.fetch_endpoints import fetch_endpoints


def plan_execution_order() -> List[int]:
    endpoints = fetch_endpoints()
    client = get_gemini_client()

    planning_prompt = (
        "You are an experienced API test planner.\n"
        "You are given API endpoints in JSON format.\n"
        "Think carefully about dependencies (e.g., register before login, login before update, create before get/delete).\n"
        "Your job is to decide the most logical execution order for testing.\n"
        "Return ONLY a valid Python list of integers (endpoint IDs).\n\n"
        f"Endpoints:\n{json.dumps(endpoints, indent=2, default=str)}\n\n"
        "Execution order (Python list of int IDs):"
    )

    response = client.models.generate_content(model="gemini-2.5-flash", contents=planning_prompt)
    cleaned_output = response.text.strip("`").strip()
    if cleaned_output.startswith(("json", "python")):
        cleaned_output = cleaned_output.split("\n", 1)[-1].strip()

    try:
        order = ast.literal_eval(cleaned_output)
        if not isinstance(order, list):
            raise ValueError("Execution order is not a list")
        order = [int(x) for x in order]
    except Exception:
        import re
        order = [int(x) for x in re.findall(r"\d+", cleaned_output)]

    print("Final execution order:", order)
    return order


if __name__ == "__main__":
    plan_execution_order()


