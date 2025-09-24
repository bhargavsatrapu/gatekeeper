"""
Allure reporter for generating test execution reports.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class AllureTestReporter:
    """Allure reporter for API test execution results."""
    
    def __init__(self, results_dir: str = "allure-results"):
        """Initialize Allure reporter."""
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.test_results: List[Dict[str, Any]] = []
        self.containers: List[Dict[str, Any]] = []
        
    def start_test_suite(self, suite_name: str) -> str:
        """Start a new test suite."""
        container_uuid = str(uuid.uuid4())
        container = {
            "uuid": container_uuid,
            "name": suite_name,
            "start": int(datetime.now().timestamp() * 1000),
            "children": [],
            "befores": [],
            "afters": []
        }
        self.containers.append(container)
        return container_uuid
        
    def add_test_result(
        self,
        test_name: str,
        status: str,
        description: str = "",
        method: str = "",
        url: str = "",
        expected_status: str = "",
        request_data: Dict[str, Any] = None,
        response_data: Dict[str, Any] = None,
        error_message: str = "",
        duration: int = 0
    ) -> str:
        """Add a test result to the report."""
        test_uuid = str(uuid.uuid4())
        
        # Map status
        allure_status = "passed"
        if status.lower() in ["fail", "failed", "failure"]:
            allure_status = "failed"
        elif status.lower() in ["skip", "skipped"]:
            allure_status = "skipped"
        elif status.lower() in ["broken"]:
            allure_status = "broken"
            
        # Create test result
        test_result = {
            "uuid": test_uuid,
            "name": test_name,
            "fullName": f"{test_name}",
            "status": allure_status,
            "start": int(datetime.now().timestamp() * 1000),
            "stop": int(datetime.now().timestamp() * 1000 + duration),
            "description": description,
            "labels": [
                {"name": "suite", "value": "API Testing"},
                {"name": "testClass", "value": "APITestCase"},
                {"name": "method", "value": method},
                {"name": "url", "value": url}
            ],
            "parameters": [],
            "attachments": [],
            "steps": []
        }
        
        # Add parameters
        if request_data:
            test_result["parameters"].extend([
                {"name": "Request Headers", "value": json.dumps(request_data.get("headers", {}), indent=2)},
                {"name": "Request Body", "value": json.dumps(request_data.get("payload", {}), indent=2)},
                {"name": "Query Params", "value": json.dumps(request_data.get("query_params", {}), indent=2)}
            ])
            
        if response_data:
            test_result["parameters"].extend([
                {"name": "Response Status", "value": str(response_data.get("status_code", ""))},
                {"name": "Response Body", "value": json.dumps(response_data.get("data", {}), indent=2)}
            ])
            
        if expected_status:
            test_result["parameters"].append({
                "name": "Expected Status", 
                "value": expected_status
            })
        
        # Add attachments
        if request_data:
            self._add_attachment(test_result, "Request Data", json.dumps(request_data, indent=2))
            
        if response_data:
            self._add_attachment(test_result, "Response Data", json.dumps(response_data, indent=2))
            
        if error_message:
            test_result["statusDetails"] = {"message": error_message}
            self._add_attachment(test_result, "Error Details", error_message)
        
        self.test_results.append(test_result)
        logger.info(f"Added test result: {test_name} ({allure_status}) - Total tests: {len(self.test_results)}")
        return test_uuid
        
    def _add_attachment(self, test_result: Dict[str, Any], name: str, content: str):
        """Add attachment to test result."""
        attachment_uuid = str(uuid.uuid4())
        attachment = {
            "name": name,
            "source": attachment_uuid,
            "type": "text/plain"
        }
        test_result["attachments"].append(attachment)
        
        # Write attachment file
        attachment_file = self.results_dir / f"{attachment_uuid}-attachment.txt"
        attachment_file.write_text(content, encoding="utf-8")
        
    def finalize_suite(self, container_uuid: str):
        """Finalize test suite."""
        for container in self.containers:
            if container["uuid"] == container_uuid:
                container["stop"] = int(datetime.now().timestamp() * 1000)
                break
                
    def generate_report(self) -> str:
        """Generate Allure report files."""
        logger.info(f"Generating Allure report with {len(self.test_results)} test results and {len(self.containers)} containers")
        
        # Write test results
        for test_result in self.test_results:
            result_file = self.results_dir / f"{test_result['uuid']}-result.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(test_result, f, indent=2)
            logger.info(f"Written test result: {result_file}")
                
        # Write containers
        for container in self.containers:
            container_file = self.results_dir / f"{container['uuid']}-container.json"
            with open(container_file, 'w', encoding='utf-8') as f:
                json.dump(container, f, indent=2)
            logger.info(f"Written container: {container_file}")
                
        logger.info(f"Allure results generated in {self.results_dir}")
        return str(self.results_dir)
        
    def clear_results(self):
        """Clear previous results."""
        for file in self.results_dir.glob("*.json"):
            file.unlink()
        for file in self.results_dir.glob("*-attachment.txt"):
            file.unlink()
        self.test_results.clear()
        self.containers.clear()


# Global instance
allure_reporter = AllureTestReporter()


def get_allure_reporter() -> AllureTestReporter:
    """Get the global Allure reporter instance."""
    return allure_reporter
