"""
Test executor for the API Testing Agent.

This module handles the execution of test cases, including data generation,
test execution, and result collection.
"""

import json
import time
import re
from typing import Dict, Any, List, Optional, Tuple
import google.generativeai as genai
from config import get_config
from utils.logger import get_logger
from runners.api_client import get_api_client, APIResponse
from database.models import get_test_case_repository, get_endpoint_repository

logger = get_logger(__name__)


class TestDataGenerator:
    """Generates realistic test data for API requests using LLM."""
    
    def __init__(self):
        """Initialize test data generator."""
        self.config = get_config()
        genai.configure(api_key=self.config.llm.api_key)
        self.client = genai.GenerativeModel(self.config.llm.model)
    
    def generate_test_data(
        self,
        test_case: Dict[str, Any],
        execution_logs: Dict[str, Dict[str, Any]],
        base_url: str
    ) -> Dict[str, Any]:
        """
        Generate realistic test data for a test case.
        
        Args:
            test_case: Test case dictionary
            execution_logs: Previous execution logs for dependency resolution
            base_url: Base URL of the API
            
        Returns:
            Dictionary with generated test data
        """
        logger.info(f"Generating test data for test case: {test_case.get('test_name', 'Unknown')}")
        
        try:
            # Extract test case details for LLM
            llm_input = {
                "test_description": test_case.get("test_name", ""),
                "url": test_case.get("url", ""),
                "headers": test_case.get("headers", {}),
                "query_params": test_case.get("query_params", {}),
                "input_payload": test_case.get("input_payload", {})
            }
            
            prompt = self._build_data_generation_prompt(
                llm_input, execution_logs, base_url, test_case.get("test_type", "positive")
            )
            
            response = self.client.generate_content(prompt)
            
            generated_data = self._parse_generation_response(response.text, llm_input)
            logger.info("Test data generation completed")
            return generated_data
            
        except Exception as e:
            logger.error(f"Error generating test data: {e}")
            return llm_input
    
    def _build_data_generation_prompt(
        self,
        llm_input: Dict[str, Any],
        execution_logs: Dict[str, Dict[str, Any]],
        base_url: str,
        test_type: str
    ) -> str:
        """
        Build the prompt for test data generation.
        
        Args:
            llm_input: Test case input data
            execution_logs: Previous execution logs
            base_url: Base URL of the API
            test_type: Type of test (positive, negative, edge, auth)
            
        Returns:
            Formatted prompt string
        """
        return (
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
            f"Base URL of the API server: {base_url}, Provided API details contain only endpoints. Please return proper test data.\n\n"
            f"Execution Logs:\n{json.dumps(execution_logs, indent=2)}\n\n"
            f"API Input with placeholders:\n{json.dumps(llm_input, indent=2)}\n\n"
            "Return JSON with placeholders replaced by appropriate values based on the test case type.\n"
            "Use realistic values for positive cases, invalid/edge/expired values for negative/auth/edge cases.\n"
        )
    
    def _parse_generation_response(self, response_text: str, fallback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the LLM response and extract generated data.
        
        Args:
            response_text: Raw response text from LLM
            fallback_data: Fallback data if parsing fails
            
        Returns:
            Dictionary with generated test data
        """
        try:
            # Clean the response text
            cleaned_output = response_text.strip("`").strip()
            
            # Remove code block markers if present
            if cleaned_output.startswith(("json", "python")):
                cleaned_output = cleaned_output.split("\n", 1)[-1].strip()
            
            # Parse JSON
            generated_data = json.loads(cleaned_output)
            logger.debug("Successfully parsed generated test data")
            return generated_data
            
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in generation response: {e}")
            logger.warning("Using fallback data")
            return fallback_data
        except Exception as e:
            logger.error(f"Error parsing generation response: {e}")
            return fallback_data


class ExecutionPlanner:
    """Plans the execution order of test cases based on dependencies."""
    
    def __init__(self):
        """Initialize execution planner."""
        self.config = get_config()
        genai.configure(api_key=self.config.llm.api_key)
        self.client = genai.GenerativeModel(self.config.llm.model)
    
    def plan_execution_order(
        self,
        endpoints: List[Dict[str, Any]],
        test_cases: List[Dict[str, Any]]
    ) -> List[Dict[str, int]]:
        """
        Plan the execution order for test cases.
        
        Args:
            endpoints: List of API endpoints
            test_cases: List of test cases
            
        Returns:
            List of execution order items with endpoint/test case IDs
        """
        logger.info("Planning test execution order")
        
        try:
            prompt = self._build_planning_prompt(endpoints, test_cases)
            response = self.client.generate_content(prompt)
            
            execution_order = self._parse_planning_response(response.text)
            logger.info(f"Execution order planned: {len(execution_order)} items")
            return execution_order
            
        except Exception as e:
            logger.error(f"Error planning execution order: {e}")
            return []
    
    def _build_planning_prompt(
        self,
        endpoints: List[Dict[str, Any]],
        test_cases: List[Dict[str, Any]]
    ) -> str:
        """
        Build the prompt for execution planning.
        
        Args:
            endpoints: List of API endpoints
            test_cases: List of test cases
            
        Returns:
            Formatted planning prompt
        """
        return (
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
            "   - Authentication-related negative api tests should run after all tests\n"
            "2. Use endpoints only for setup (data creation or authentication) if required.\n"
            "3. Do not drop any testcases. Every testcase must appear exactly once in the final order.\n\n"
            "⚠️ Rules:\n"
            "- Return valid JSON only.\n"
            "- The output must be a list of dictionaries.\n"
            "- Each dictionary must have exactly one key-value pair.\n"
            "- Use the key 'all_endpoints' when the entry comes from endpoints.\n"
            "- Use the key 'all_testcases' when the entry comes from testcases.\n"
            "- The value must be the primary key of the row (integer).\n\n"
            f"Here are all endpoints with primary keys:\n{json.dumps(endpoints, indent=2, default=str)}\n\n"
            f"Here are all possible testcases with primary keys:\n{json.dumps(test_cases, indent=2, default=str)}\n\n"
            "Return JSON like this:\n"
            "[\n"
            "  {\"all_endpoints\": 2},\n"
            "  {\"all_endpoints\": 101},\n"
            "  {\"all_testcases\": 7},\n"
            "  {\"all_testcases\": 201},\n"
            "  {\"all_endpoints\": 202}\n"
            "]"
        )
    
    def _parse_planning_response(self, response_text: str) -> List[Dict[str, int]]:
        """
        Parse the planning response and extract execution order.
        
        Args:
            response_text: Raw response text from LLM
            
        Returns:
            List of execution order items
        """
        try:
            # Clean the response text
            cleaned_output = response_text.strip("`").strip()
            
            # Remove code block markers if present
            if cleaned_output.startswith(("json", "python")):
                cleaned_output = cleaned_output.split("\n", 1)[-1].strip()
            
            # Parse JSON
            execution_order = json.loads(cleaned_output)
            
            if not isinstance(execution_order, list):
                raise ValueError("Execution order is not a list")
            
            logger.debug("Successfully parsed execution order")
            return execution_order
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in planning response: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing planning response: {e}")
            return []


class TestExecutor:
    """Executes test cases and collects results."""
    
    def __init__(self):
        """Initialize test executor."""
        self.config = get_config()
        self.api_client = get_api_client()
        self.data_generator = TestDataGenerator()
        self.execution_planner = ExecutionPlanner()
        self.test_case_repository = get_test_case_repository()
        self.endpoint_repository = get_endpoint_repository()
        self.execution_logs: Dict[str, Dict[str, Any]] = {}
    
    def execute_test_case(
        self,
        test_case: Dict[str, Any],
        execution_logs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Tuple[Dict[str, Any], APIResponse]:
        """
        Execute a single test case.
        
        Args:
            test_case: Test case dictionary
            execution_logs: Previous execution logs for dependency resolution
            
        Returns:
            Tuple of (request_data, response)
        """
        logger.info(f"Executing test case: {test_case.get('test_name', 'Unknown')}")
        
        # Use provided logs or instance logs
        logs = execution_logs or self.execution_logs
        
        # Generate test data
        generated_data = self.data_generator.generate_test_data(
            test_case, logs, self.config.api.base_url
        )
        
        # Prepare request
        request_data = {
            "url": generated_data.get("url", test_case["url"]),
            "method": test_case["method"],
            "headers": generated_data.get("headers", test_case["headers"]),
            "query_params": generated_data.get("query_params", test_case["query_params"]),
            "payload": generated_data.get("input_payload", test_case["input_payload"])
        }
        
        # Make API request
        response = self.api_client.make_request(
            method=request_data["method"],
            url=request_data["url"],
            headers=request_data["headers"],
            query_params=request_data["query_params"],
            payload=request_data["payload"]
        )
        
        # Log execution
        execution_log = {
            "request": request_data,
            "response": response.to_dict()
        }
        
        self.execution_logs[test_case["test_name"]] = execution_log
        
        logger.info(f"Test case executed: {response.status_code} in {response.execution_time_ms}ms")
        return request_data, response
    
    def execute_test_suite(
        self,
        execution_order: List[Dict[str, int]],
        endpoint_tables: Dict[int, str]
    ) -> Dict[str, Any]:
        """
        Execute a complete test suite based on execution order.
        
        Args:
            execution_order: List of execution order items
            endpoint_tables: Mapping of endpoint IDs to table names
            
        Returns:
            Dictionary containing execution results
        """
        logger.info(f"Executing test suite with {len(execution_order)} items")
        
        results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "execution_logs": {},
            "summary": {}
        }
        
        for item in execution_order:
            for key, value in item.items():
                if key == "all_endpoints":
                    # Execute endpoint setup
                    self._execute_endpoint_setup(value, endpoint_tables)
                elif key == "all_testcases":
                    # Execute test case
                    self._execute_test_case_by_id(value, endpoint_tables)
        
        # Calculate summary
        results["total_tests"] = len(self.execution_logs)
        results["passed_tests"] = sum(
            1 for log in self.execution_logs.values()
            if log["response"].get("success", False)
        )
        results["failed_tests"] = results["total_tests"] - results["passed_tests"]
        results["execution_logs"] = self.execution_logs
        
        logger.info(f"Test suite completed: {results['passed_tests']}/{results['total_tests']} passed")
        return results
    
    def _execute_endpoint_setup(self, endpoint_id: int, endpoint_tables: Dict[int, str]):
        """Execute endpoint setup (get first test case)."""
        if endpoint_id not in endpoint_tables:
            logger.warning(f"Endpoint {endpoint_id} not found in tables mapping")
            return
        
        table_name = endpoint_tables[endpoint_id]
        test_cases = self.test_case_repository.get_test_cases(table_name)
        
        if test_cases:
            # Execute the first test case as setup
            first_test_case = test_cases[0]
            self.execute_test_case(first_test_case)
            time.sleep(self.config.execution_delay)
    
    def _execute_test_case_by_id(self, test_case_id: int, endpoint_tables: Dict[int, str]):
        """Execute a specific test case by ID."""
        # Find the test case in all tables
        for table_name in endpoint_tables.values():
            test_case = self.test_case_repository.get_test_case_by_id(table_name, test_case_id)
            if test_case:
                self.execute_test_case(test_case)
                time.sleep(self.config.execution_delay)
                return
        
        logger.warning(f"Test case {test_case_id} not found in any table")
    
    def get_execution_logs(self) -> Dict[str, Dict[str, Any]]:
        """Get current execution logs."""
        return self.execution_logs.copy()
    
    def clear_execution_logs(self):
        """Clear execution logs."""
        self.execution_logs.clear()
        logger.info("Execution logs cleared")


# Global instances
test_data_generator = TestDataGenerator()
execution_planner = ExecutionPlanner()
test_executor = TestExecutor()


def get_test_data_generator() -> TestDataGenerator:
    """Get the global test data generator instance."""
    return test_data_generator


def get_execution_planner() -> ExecutionPlanner:
    """Get the global execution planner instance."""
    return execution_planner


def get_test_executor() -> TestExecutor:
    """Get the global test executor instance."""
    return test_executor
