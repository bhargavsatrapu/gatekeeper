import json
from typing import Dict, Any

from sat_core.global_state import generated_cases
from sat_core.ai_client import get_gemini_client


def validate_test_cases() -> Dict[str, Any]:
    client = get_gemini_client()

    validation_prompt = (
        "You are a senior QA reviewer.\n"
        "Review the following generated API test cases:\n"
        f"{json.dumps(generated_cases, indent=2)}\n\n"
        "Evaluation criteria:\n"
        "- All positive, negative, edge, and schema validation cases must be covered.\n"
        "- Testcases must be logically valid and executable.\n"
        "- IMPORTANT: No actual values should be used. All fields (headers, query_params, "
        "path_params, input_payload, expected_schema) must contain descriptive placeholders.\n"
        "Respond ONLY with JSON in this format:\n"
        "{ \"feedback\": \"Your feedback text\" }"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=validation_prompt,
    )

    cleaned_output = response.text.strip("`").strip()
    if cleaned_output.startswith(("json", "python")):
        cleaned_output = cleaned_output.split("\n", 1)[-1].strip()

    try:
        result = json.loads(cleaned_output)
    except Exception:
        result = {"feedback": "Validator returned invalid JSON"}

    print("🔎 Validator Feedback:", result.get("feedback", ""))
    return result


if __name__ == "__main__":
    validate_test_cases()


