"""
Test case generator for the API Testing Agent.

This module handles the generation of comprehensive test cases for API endpoints
using LLM (Large Language Model) capabilities.
"""

import json
from typing import Dict, Any, List
import google.generativeai as genai
from config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)


class TestCaseGenerator:
    """Generates comprehensive test cases for API endpoints using LLM."""
    
    def __init__(self):
        """Initialize test case generator."""
        self.config = get_config()
        genai.configure(api_key=self.config.llm.api_key)
        self.client = genai.GenerativeModel(self.config.llm.model)
        self.expected_structure = self._get_expected_test_case_structure()
    
    def _get_expected_test_case_structure(self) -> Dict[str, str]:
        """Get the expected structure for test cases."""
        return {
            "test_name": "string",
            "test_type": "positive|negative|edge|schema|auth",
            "method": "string",
            "url": "string",
            "headers": {"key": "description of expected value"},
            "query_params": {"param": "description of expected value"},
            "path_params": {"param": "description of expected value"},
            "input_payload": {"field": "description of expected value"},
            "expected_status": "string",
            "expected_schema": {"field": "description of expected type/value"}
        }
    
    def generate_test_cases(self, endpoints: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate comprehensive test cases for the given endpoints."""
        print(f"🤖 [GENERATOR] Starting test case generation for {len(endpoints)} endpoints...")
        logger.info(f"Generating test cases for {len(endpoints)} endpoints")
        try:
            print("📝 [GENERATOR] Building generation prompt...")
            prompt = self._build_generation_prompt(endpoints)
            print(f"🤖 [GENERATOR] Calling LLM with prompt length: {len(prompt)} characters")
            response = self.client.generate_content(prompt)
            print(f"✅ [GENERATOR] LLM response received: {len(response.text)} characters")
            logger.info("Test case generation completed")
            result = self._parse_generation_response(response.text)
            print(f"📊 [GENERATOR] Generated test cases for {len(result)} endpoints")
            return result
        except Exception as e:
            print(f"❌ [GENERATOR] Error generating test cases: {e}")
            logger.error(f"Error generating test cases: {e}")
            raise
    
    def _build_generation_prompt(self, endpoints: List[Dict[str, Any]]) -> str:
        """Build the prompt for test case generation."""
        return (
            "You are an API testing expert.\n"
            "I will provide API details in JSON format. The input may contain one or more API endpoints, "
            "including method, parameters, request body, possible responses, and response schema.\n"
            f"Here are the endpoints: {endpoints}\n\n"
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
            f"Each test case dictionary must strictly follow this structure:\n"
            f"{self.expected_structure}\n\n"
            "Formatting rules:\n"
            "- Use double quotes for all keys and values.\n"
            "- Do not include markdown, comments, or code fences.\n"
            "- Ensure the final output is valid JSON and directly parsable.\n"
            "- BE CARE FULL DURING FROMATTING SHOULD NOT MAKE ANY MISTAKES, IT SHOULD BE PARSABLE.\n"
        )
    
    def _parse_generation_response(self, response_text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Parse the LLM response and extract test cases."""
        print("🔍 [GENERATOR] Parsing LLM response...")
        try:
            cleaned_output = response_text.strip("`").strip()
            if cleaned_output.startswith(("json", "python")):
                cleaned_output = cleaned_output.split("\n", 1)[-1].strip()
            print(f"📝 [GENERATOR] Cleaned response length: {len(cleaned_output)} characters")
            logger.debug(f"Cleaned LLM response: {cleaned_output[:200]}...")
            test_cases = json.loads(cleaned_output)
            if not isinstance(test_cases, dict):
                raise ValueError("LLM response is not a dictionary")
            total_cases = sum(len(cases) for cases in test_cases.values())
            print(f"✅ [GENERATOR] Successfully parsed {total_cases} test cases for {len(test_cases)} endpoints")
            logger.info(f"Successfully parsed {total_cases} test cases")
            return test_cases
        except json.JSONDecodeError as e:
            print(f"❌ [GENERATOR] Invalid JSON in LLM response: {e}")
            logger.error(f"Invalid JSON in LLM response: {e}")
            logger.error(f"Response text: {response_text}")
            raise ValueError("Generator returned invalid JSON") from e
        except Exception as e:
            print(f"❌ [GENERATOR] Error parsing generation response: {e}")
            logger.error(f"Error parsing generation response: {e}")
            raise


class TestCaseValidator:
    """Validates generated test cases for quality and completeness."""
    
    def __init__(self):
        """Initialize test case validator."""
        self.config = get_config()
        genai.configure(api_key=self.config.llm.api_key)
        self.client = genai.GenerativeModel(self.config.llm.model)
    
    def validate_test_cases(self, test_cases: Dict[str, List[Dict[str, Any]]]) -> str:
        """Validate generated test cases using LLM."""
        logger.info("Validating generated test cases")
        try:
            prompt = self._build_validation_prompt(test_cases)
            response = self.client.generate_content(prompt)
            feedback = self._parse_validation_response(response.text)
            logger.info("Test case validation completed")
            return feedback
        except Exception as e:
            logger.error(f"Error validating test cases: {e}")
            return "Validation failed due to an error"
    
    def _build_validation_prompt(self, test_cases: Dict[str, List[Dict[str, Any]]]) -> str:
        """Build the prompt for test case validation."""
        return (
            "You are a senior QA reviewer.\n"
            "Review the following generated API test cases:\n"
            f"{json.dumps(test_cases, indent=2)}\n\n"
            "Evaluation criteria:\n"
            "- All positive, negative, edge, and schema validation cases must be covered.\n"
            "- Testcases must be logically valid and executable.\n"
            "- IMPORTANT: No actual values should be used. All fields (headers, query_params, "
            "path_params, input_payload, expected_schema) must contain descriptive placeholders.\n"
            "  ✅ Example: { \"email\": \"string - valid email address\" }\n"
            "  ❌ Wrong:   { \"email\": \"test@example.com\" }\n\n"
            "Respond ONLY with JSON in this format:\n"
            "{ \"feedback\": \"Your feedback text\" }"
        )
    
    def _parse_validation_response(self, response_text: str) -> str:
        """Parse the validation response and extract feedback."""
        try:
            cleaned_output = response_text.strip("`").strip()
            if cleaned_output.startswith(("json", "python")):
                cleaned_output = cleaned_output.split("\n", 1)[-1].strip()
            result = json.loads(cleaned_output)
            feedback = result.get("feedback", "No feedback provided")
            logger.info(f"Validation feedback: {feedback[:100]}...")
            return feedback
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in validation response, using raw text")
            return response_text
        except Exception as e:
            logger.error(f"Error parsing validation response: {e}")
            return "Validation response parsing failed"
    
    def should_regenerate(self, feedback: str) -> bool:
        """Determine if test cases should be regenerated based on feedback."""
        negative_keywords = [
            "actual value",
            "real value",
            "specific value",
            "hardcoded",
            "concrete value"
        ]
        feedback_lower = feedback.lower()
        should_regenerate = any(keyword in feedback_lower for keyword in negative_keywords)
        if should_regenerate:
            logger.info("Regeneration needed based on validation feedback")
        else:
            logger.info("Test cases passed validation")
        return should_regenerate


# Global instances
test_case_generator = TestCaseGenerator()
test_case_validator = TestCaseValidator()


def get_test_case_generator() -> TestCaseGenerator:
    """Get the global test case generator instance."""
    return test_case_generator


def get_test_case_validator() -> TestCaseValidator:
    """Get the global test case validator instance."""
    return test_case_validator
