import json
import os
import uuid
import shutil
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from jsonschema import Draft7Validator, ValidationError


def _ensure_dir(path: str) -> None:
    """Ensure a directory exists."""
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)

def get_allure_results_dir() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(base_dir, "static", "allure-results")
    os.makedirs(results_dir, exist_ok=True)
    return results_dir

def get_allure_report_dir() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    report_dir = os.path.join(base_dir, "static", "allure-report")
    os.makedirs(report_dir, exist_ok=True)
    return report_dir

def clean_allure_results(results_dir: Optional[str] = None) -> None:
    """Delete all previous Allure results before a new run."""
    if results_dir is None:
        results_dir = get_allure_results_dir()
    if os.path.exists(results_dir):
        shutil.rmtree(results_dir)
    os.makedirs(results_dir, exist_ok=True)
    print(f"🧹 Cleaned Allure results at: {results_dir}")

# ======================================================
# ✅ Validation Helpers
# ======================================================

def validate_response(result, expected_status, expected_schema):
    details = {"status_validation": None, "schema_validation": None, "errors": []}
    passed = True

    # Status validation
    status_ok = result.get("status_code") == expected_status
    details["status_validation"] = {
        "expected": expected_status,
        "actual": result.get("status_code"),
        "passed": status_ok,
    }
    if not status_ok:
        passed = False

    # Schema validation
    if expected_schema:
        if not status_ok:
            details["schema_validation"] = {"passed": False}
            details["errors"].append(
                f"Schema skipped due to failed status code ({result.get('status_code')})"
            )
        elif result.get("data") is None:
            details["schema_validation"] = {"passed": False}
            details["errors"].append("Response data missing or None.")
        else:
            try:
                Draft7Validator(expected_schema).validate(result.get("data"))
                details["schema_validation"] = {"passed": True}
            except ValidationError as e:
                details["schema_validation"] = {"passed": False}
                details["errors"].append(str(e))
                passed = False

    return passed, details

# ======================================================
# ✅ Allure Helpers
# ======================================================

def write_allure_result(
    name: str,
    status: str,
    steps: Optional[list] = None,
    attachments: Optional[list] = None,
    description: Optional[str] = None,
    results_dir: Optional[str] = None
) -> None:
    """Write a single Allure result JSON file."""
    if results_dir is None:
        results_dir = get_allure_results_dir()
    else:
        _ensure_dir(results_dir)

    test_uuid = str(uuid.uuid4())
    now = int(datetime.now().timestamp() * 1000)

    test_result = {
        "uuid": test_uuid,
        "historyId": test_uuid,
        "fullName": name,
        "name": name,
        "status": status,
        "stage": "finished",
        "start": now,
        "stop": now,
        "steps": steps or [],
        "attachments": attachments or [],
        "description": description or "",
        "labels": [],
    }

    output_file = os.path.join(results_dir, f"{test_uuid}-result.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(test_result, f, indent=2)

    print(f"✅ Allure result created: {output_file}")

def make_attachment(
    name: str,
    source_basename: str,
    content: Any,
    content_type: str = "application/json",
    results_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Create an Allure attachment file and return reference."""
    if results_dir is None:
        results_dir = get_allure_results_dir()
    else:
        _ensure_dir(results_dir)

    source = f"{source_basename}-{uuid.uuid4()}.txt"
    path = os.path.join(results_dir, source)

    # Convert to string or JSON
    if isinstance(content, (dict, list)):
        payload = json.dumps(content, indent=2, default=str)
    else:
        payload = str(content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(payload)

    print(f"📎 Created attachment: {name} -> {path}")
    return {"name": name, "source": source, "type": content_type}

def write_allure_test_with_attachments(
    test_name: str,
    passed: bool,
    request: Dict[str, Any],
    response: Dict[str, Any],
    assertions: Dict[str, Any],
    description: Optional[str] = None,
    results_dir: Optional[str] = None
) -> None:
    """
    Helper that writes a complete Allure test result with request, response, and assertion attachments.
    """
    # Create Allure attachments
    req_att = make_attachment("Request", "request", request, results_dir=results_dir)
    res_att = make_attachment("Response", "response", response, results_dir=results_dir)
    asr_att = make_attachment("Assertions", "assertions", assertions, results_dir=results_dir)

    # Write final Allure test result
    write_allure_result(
        name=test_name,
        status="passed" if passed else "failed",
        attachments=[req_att, res_att, asr_att],
        description=description,
        results_dir=results_dir
    )

    print(f"🏁 Test '{test_name}' logged in Allure ({'PASSED' if passed else 'FAILED'})")
