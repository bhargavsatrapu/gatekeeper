"""
AI Reports Service for SmartAPI Tester
Analyzes execution results and generates comprehensive reports
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sat_core.db_utils import DatabaseUtils
from sat_core.ai_client import get_gemini_client
from sat_core.config import DB_CONFIG

logger = logging.getLogger(__name__)

class AIReportsService:
    """Service for generating AI-powered test execution reports"""
    
    def __init__(self):
        self.db_utils = DatabaseUtils(DB_CONFIG)
        self.ai_client = None
        
    def _get_ai_client(self):
        """Get AI client instance"""
        if not self.ai_client:
            self.ai_client = get_gemini_client()
        return self.ai_client
    
    def _serialize_execution_data(self, execution_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Serialize execution data by converting datetime objects to strings
        
        Args:
            execution_data: List of execution result dictionaries
            
        Returns:
            List of serialized execution result dictionaries
        """
        serialized_data = []
        
        for result in execution_data:
            serialized_result = {}
            for key, value in result.items():
                if isinstance(value, datetime):
                    # Convert datetime to ISO format string
                    serialized_result[key] = value.isoformat()
                elif isinstance(value, dict):
                    # Recursively serialize nested dictionaries
                    serialized_result[key] = self._serialize_dict(value)
                else:
                    serialized_result[key] = value
            serialized_data.append(serialized_result)
        
        return serialized_data
    
    def _serialize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively serialize a dictionary, converting datetime objects to strings"""
        serialized = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                serialized[key] = self._serialize_dict(value)
            else:
                serialized[key] = value
        return serialized
    
    def get_execution_data(self) -> List[Dict[str, Any]]:
        """
        Fetch execution results from database
        
        Returns:
            List of execution result dictionaries
        """
        try:
            # Get all execution results (table contains latest results only)
            results = self.db_utils.get_execution_results(limit=1000)
            return results
            
        except Exception as e:
            logger.error(f"Error fetching execution data: {e}")
            return []
    
    def analyze_with_ai(self, execution_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze execution data using AI
        
        Args:
            execution_data: List of execution results
            
        Returns:
            AI analysis results
        """
        try:
            if not execution_data:
                return self._get_empty_analysis()
            
            # For now, use fallback analysis to avoid AI issues
            # TODO: Re-enable AI analysis once issues are resolved
            logger.info("Using fallback analysis (AI temporarily disabled)")
            return self._get_fallback_analysis(execution_data)
            
            # AI Analysis (temporarily disabled)
            # Prepare data for AI analysis (convert datetime objects to strings)
            # serialized_data = self._serialize_execution_data(execution_data)
            # analysis_prompt = self._create_analysis_prompt(serialized_data)
            
            # # Get AI client and generate analysis
            # try:
            #     client = self._get_ai_client()
            #     logger.info("AI client obtained successfully")
                
            #     response = client.models.generate_content(
            #         model="gemini-2.5-flash",
            #         contents=analysis_prompt
            #     )
            #     logger.info("AI response received successfully")
                
            #     # Parse AI response
            #     ai_response = response.text.strip()
            #     logger.info(f"AI response length: {len(ai_response)} characters")
                
            #     # Try to parse as JSON, fallback to structured parsing
            #     try:
            #         analysis_result = json.loads(ai_response)
            #         logger.info("AI response parsed as JSON successfully")
            #     except json.JSONDecodeError as json_error:
            #         logger.warning(f"Failed to parse AI response as JSON: {json_error}")
            #         analysis_result = self._parse_ai_response(ai_response, execution_data)
                
            #     return analysis_result
                
            # except Exception as ai_error:
            #     logger.error(f"Error in AI processing: {ai_error}")
            #     # Fallback to basic analysis if AI fails
            #     return self._get_fallback_analysis(execution_data)
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return self._get_fallback_analysis(execution_data)
    
    def _create_analysis_prompt(self, execution_data: List[Dict[str, Any]]) -> str:
        """Create AI analysis prompt"""
        
        # Calculate basic metrics
        total_tests = len(execution_data)
        passed_tests = sum(1 for result in execution_data 
                          if result.get('actual_status_code') == result.get('expected_status_code'))
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Categorize failures
        failure_categories = self._categorize_failures(execution_data)
        
        # Analyze endpoints
        endpoint_analysis = self._analyze_endpoints(execution_data)
        
        prompt = f"""
        Analyze the following API test execution data and provide a comprehensive report in JSON format.
        
        Test Execution Data:
        - Total Tests: {total_tests}
        - Passed Tests: {passed_tests}
        - Failed Tests: {failed_tests}
        - Pass Rate: {pass_rate:.1f}%
        
        Failure Categories:
        {json.dumps(failure_categories, indent=2)}
        
        Endpoint Analysis:
        {json.dumps(endpoint_analysis, indent=2)}
        
        Detailed Results:
        {json.dumps(execution_data[:10], indent=2)}  # First 10 results for context
        
        Please provide a JSON response with the following structure:
        {{
            "summary_metrics": {{
                "total_tests": {total_tests},
                "passed_tests": {passed_tests},
                "failed_tests": {failed_tests},
                "blocked_tests": 0,
                "pass_rate": {pass_rate}
            }},
            "failure_categories": {{
                "authentication_errors": 0,
                "schema_mismatches": 0,
                "server_errors": 0,
                "timeout_errors": 0,
                "validation_errors": 0,
                "other_errors": 0
            }},
            "endpoint_stability": [
                {{
                    "endpoint": "string",
                    "failure_rate": 0.0,
                    "priority": "Critical|Major|Minor",
                    "common_issues": ["string"],
                    "total_tests": 0,
                    "failed_tests": 0
                }}
            ],
            "schema_issues": [
                {{
                    "endpoint": "string",
                    "issue_type": "string",
                    "field_name": "string",
                    "expected_type": "string",
                    "actual_type": "string",
                    "description": "string"
                }}
            ],
            "ai_insights": {{
                "narrative": "string - 2-3 sentence summary of test health and key issues",
                "recommendations": ["string - actionable recommendations"],
                "suggested_fixes": [
                    {{
                        "issue": "string",
                        "fix": "string",
                        "priority": "High|Medium|Low"
                    }}
                ]
            }}
        }}
        
        Focus on:
        1. Identifying patterns in failures
        2. Ranking endpoints by stability
        3. Detecting schema validation issues
        4. Providing actionable recommendations
        5. Categorizing errors by type and severity
        """
        
        return prompt
    
    def _categorize_failures(self, execution_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize test failures by type"""
        categories = {
            "authentication_errors": 0,
            "schema_mismatches": 0,
            "server_errors": 0,
            "timeout_errors": 0,
            "validation_errors": 0,
            "other_errors": 0
        }
        
        for result in execution_data:
            if result.get('actual_status_code') != result.get('expected_status_code'):
                status_code = result.get('actual_status_code', 0)
                
                if status_code == 401 or status_code == 403:
                    categories["authentication_errors"] += 1
                elif status_code >= 500:
                    categories["server_errors"] += 1
                elif status_code == 408:
                    categories["timeout_errors"] += 1
                elif status_code == 400 or status_code == 422:
                    categories["validation_errors"] += 1
                else:
                    categories["other_errors"] += 1
        
        return categories
    
    def _analyze_endpoints(self, execution_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze endpoint stability"""
        endpoint_stats = {}
        
        for result in execution_data:
            endpoint = result.get('input_url', 'Unknown')
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {
                    'total_tests': 0,
                    'failed_tests': 0,
                    'status_codes': []
                }
            
            endpoint_stats[endpoint]['total_tests'] += 1
            endpoint_stats[endpoint]['status_codes'].append(result.get('actual_status_code'))
            
            if result.get('actual_status_code') != result.get('expected_status_code'):
                endpoint_stats[endpoint]['failed_tests'] += 1
        
        # Calculate failure rates and priorities
        endpoint_analysis = []
        for endpoint, stats in endpoint_stats.items():
            failure_rate = (stats['failed_tests'] / stats['total_tests'] * 100) if stats['total_tests'] > 0 else 0
            
            # Determine priority
            if failure_rate > 50:
                priority = "Critical"
            elif failure_rate > 20:
                priority = "Major"
            else:
                priority = "Minor"
            
            endpoint_analysis.append({
                "endpoint": endpoint,
                "failure_rate": round(failure_rate, 1),
                "priority": priority,
                "total_tests": stats['total_tests'],
                "failed_tests": stats['failed_tests'],
                "common_issues": self._get_common_issues(stats['status_codes'])
            })
        
        # Sort by failure rate descending
        endpoint_analysis.sort(key=lambda x: x['failure_rate'], reverse=True)
        return endpoint_analysis
    
    def _get_common_issues(self, status_codes: List[int]) -> List[str]:
        """Get common issues from status codes"""
        issues = []
        status_counts = {}
        
        for code in status_codes:
            status_counts[code] = status_counts.get(code, 0) + 1
        
        # Find most common error codes
        for code, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
            if code != 200:  # Skip success codes
                if code == 401:
                    issues.append("Authentication required")
                elif code == 403:
                    issues.append("Access forbidden")
                elif code == 404:
                    issues.append("Resource not found")
                elif code == 500:
                    issues.append("Internal server error")
                elif code == 400:
                    issues.append("Bad request")
                elif code == 422:
                    issues.append("Validation error")
                else:
                    issues.append(f"HTTP {code} error")
        
        return issues[:3]  # Return top 3 issues
    
    def _get_failed_tests_details(self, execution_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get detailed information about failed tests with batch AI analysis"""
        failed_tests = []
        error_counts = {}
        failed_results = []
        
        # First pass: collect all failed tests and categorize errors
        for result in execution_data:
            if result.get('actual_status_code') != result.get('expected_status_code'):
                # Determine error type
                status_code = result.get('actual_status_code', 0)
                error_type = self._categorize_error_type(status_code)
                
                # Count error types
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
                
                # Store failed result for batch processing
                failed_results.append(result)
        
        # Batch AI analysis for all failed tests
        failure_reasons = self._get_batch_failure_reasons(failed_results)
        
        # Second pass: create failed test objects with AI-generated reasons
        for i, result in enumerate(failed_results):
            status_code = result.get('actual_status_code', 0)
            error_type = self._categorize_error_type(status_code)
            failure_reason = failure_reasons[i] if i < len(failure_reasons) else "AI analysis failed"
            
            failed_test = {
                "test_name": result.get('test_name', 'Unknown'),
                "endpoint": result.get('input_url', 'Unknown'),
                "method": result.get('input_method', 'Unknown'),
                "expected_status": result.get('expected_status_code', 0),
                "actual_status": status_code,
                "error_type": error_type,
                "failure_reason": failure_reason,
                "timestamp": result.get('created_at', 'Unknown'),
                "actual_data": result.get('actual_data', {})
            }
            failed_tests.append(failed_test)
        
        # Sort by timestamp (most recent first)
        failed_tests.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Get most common error
        most_common_error = max(error_counts.items(), key=lambda x: x[1])[0] if error_counts else "None"
        
        return {
            "failed_tests": failed_tests,
            "total_failed_count": len(failed_tests),
            "most_common_error": most_common_error,
            "error_counts": error_counts
        }
    
    def _categorize_error_type(self, status_code: int) -> str:
        """Categorize error type based on status code"""
        if status_code == 401 or status_code == 403:
            return "Authentication"
        elif status_code >= 500:
            return "Server Error"
        elif status_code == 408:
            return "Timeout"
        elif status_code == 400 or status_code == 422:
            return "Validation"
        elif status_code == 404:
            return "Not Found"
        else:
            return "Other"
    
    def _get_batch_failure_reasons(self, failed_results: List[Dict[str, Any]]) -> List[str]:
        """Get AI-generated failure reasons for all failed tests in a single batch call"""
        if not failed_results:
            return []
        
        try:
            from sat_core.ai_client import get_gemini_client
            client = get_gemini_client()
            
            # Create batch prompt for all failed tests
            batch_prompt = f"""
You are an expert API testing analyst. Analyze these {len(failed_results)} test failures and provide detailed, comprehensive failure descriptions for each one.

**Failed Tests to Analyze:**

"""
            
            # Add each failed test to the prompt
            for i, result in enumerate(failed_results, 1):
                expected_status = result.get('expected_status_code', 0)
                actual_status = result.get('actual_status_code', 0)
                endpoint = result.get('input_url', 'Unknown endpoint')
                method = result.get('input_method', 'Unknown method')
                request_body = result.get('request_body', {})
                request_headers = result.get('request_headers', {})
                actual_data = result.get('actual_data', {})
                test_name = result.get('test_name', f'Test {i}')
                
                batch_prompt += f"""
**Test {i}: {test_name}**
- Endpoint: {endpoint}
- HTTP Method: {method}
- Expected Status Code: {expected_status}
- Actual Status Code: {actual_status}
- Request Body: {request_body}
- Request Headers: {request_headers}
- Response Data: {actual_data}

"""
            
            batch_prompt += """
**Your Task:**
For each test failure above, provide a detailed analysis in 6-7 lines that includes:
1. What the test was trying to accomplish based on the request
2. Why it failed (root cause analysis considering request payload)
3. What the status code means in context of the request
4. Potential impact on the system
5. Recommendations for fixing the issue (considering request data)

**CRITICAL: Response Format Requirements:**
You MUST respond in EXACTLY this format with NO additional text before or after:

Test 1: [Your detailed analysis here - 6-7 lines]
Test 2: [Your detailed analysis here - 6-7 lines]
Test 3: [Your detailed analysis here - 6-7 lines]

Do NOT include any introductory text, headers, or explanations. Start directly with "Test 1:" and end with the last test analysis. Each analysis should be 6-7 lines of detailed, professional QA engineer analysis.
"""
            
            # Get AI response for all tests at once
            response = client.models.generate_content(model="gemini-2.5-flash", contents=batch_prompt)
            ai_response = response.text.strip()
            
            # Parse the response to extract individual failure reasons
            failure_reasons = self._parse_batch_ai_response(ai_response, len(failed_results))
            
            return failure_reasons
            
        except Exception as e:
            # Fallback: generate basic reasons for each test
            fallback_reasons = []
            for result in failed_results:
                status_code = result.get('actual_status_code', 0)
                expected_status = result.get('expected_status_code', 0)
                fallback_reason = f"Unexpected Response: Received status code {status_code} instead of expected {expected_status}. This is an unexpected response that may indicate a configuration issue or API change. Error generating AI analysis: {str(e)}"
                fallback_reasons.append(fallback_reason)
            return fallback_reasons
    
    def _parse_batch_ai_response(self, ai_response: str, expected_count: int) -> List[str]:
        """Parse batch AI response to extract individual failure reasons"""
        failure_reasons = []
        
        # Try multiple parsing strategies
        import re
        
        # Strategy 1: Split by "Test X:" pattern
        test_sections = re.split(r'Test \d+:', ai_response)
        
        # Remove empty first element if it exists
        if test_sections and not test_sections[0].strip():
            test_sections = test_sections[1:]
        
        # Strategy 2: If that doesn't work well, try splitting by "**Test X:" pattern
        if len(test_sections) < expected_count or any(len(s.strip()) < 10 for s in test_sections[:expected_count]):
            test_sections = re.split(r'\*\*Test \d+:', ai_response)
            if test_sections and not test_sections[0].strip():
                test_sections = test_sections[1:]
        
        # Strategy 3: If still not working, try to split by double newlines and look for test patterns
        if len(test_sections) < expected_count or any(len(s.strip()) < 10 for s in test_sections[:expected_count]):
            paragraphs = ai_response.split('\n\n')
            test_sections = []
            for para in paragraphs:
                if re.search(r'Test \d+', para) or re.search(r'\*\*Test \d+', para):
                    test_sections.append(para)
        
        # Extract failure reasons from each section
        for i, section in enumerate(test_sections):
            if i < expected_count:
                # Clean up the section
                reason = section.strip()
                # Remove any remaining markdown formatting
                reason = re.sub(r'\*\*([^*]+)\*\*', r'\1', reason)  # Remove **bold**
                reason = re.sub(r'^Test \d+:\s*', '', reason)  # Remove "Test X:" prefix
                reason = re.sub(r'^\*\*Test \d+:\s*', '', reason)  # Remove "**Test X:" prefix
                
                if reason and len(reason) > 20:  # Ensure it's substantial content
                    failure_reasons.append(reason)
                else:
                    # Fallback if section is empty or too short
                    fallback_reason = f"AI analysis for test {i+1} was incomplete or too short."
                    failure_reasons.append(fallback_reason)
            else:
                break
        
        # If we don't have enough reasons, pad with fallback messages
        while len(failure_reasons) < expected_count:
            fallback_reason = f"AI analysis for test {len(failure_reasons)+1} was not provided."
            failure_reasons.append(fallback_reason)
        
        return failure_reasons[:expected_count]  # Ensure we don't exceed expected count

    def _get_failure_reason(self, status_code: int, result: Dict[str, Any]) -> str:
        """Get AI-generated detailed failure reason with comprehensive analysis"""
        expected_status = result.get('expected_status_code', 0)
        actual_data = result.get('actual_data', {})
        endpoint = result.get('input_url', 'Unknown endpoint')
        method = result.get('input_method', 'Unknown method')
        request_body = result.get('request_body', {})
        request_headers = result.get('request_headers', {})
        
        try:
            from sat_core.ai_client import get_gemini_client
            client = get_gemini_client()
            
            # Create AI prompt for detailed failure analysis
            ai_prompt = f"""
You are an expert API testing analyst. Analyze this test failure and provide a detailed, comprehensive failure description in 6-7 lines.

**Test Context:**
- Endpoint: {endpoint}
- HTTP Method: {method}
- Expected Status Code: {expected_status}
- Actual Status Code: {status_code}
- Request Body: {request_body}
- Request Headers: {request_headers}
- Response Data: {actual_data}

**Your Task:**
Generate a detailed failure analysis that includes:
1. What the test was trying to accomplish based on the request
2. Why it failed (root cause analysis considering request payload)
3. What the status code means in context of the request
4. Potential impact on the system
5. Recommendations for fixing the issue (considering request data)

Make it sound like a professional QA engineer's analysis. Be specific and actionable, considering both the request payload and response.
"""
            
            # Get AI response
            response = client.models.generate_content(model="gemini-2.5-flash", contents=ai_prompt)
            ai_failure_reason = response.text.strip()
            
            return ai_failure_reason
            
        except Exception as e:
            # Fallback to basic reason if AI fails
            return f"Unexpected Response: Received status code {status_code} instead of expected {expected_status}. This is an unexpected response that may indicate a configuration issue or API change. Error generating AI analysis: {str(e)}"
    
    def _parse_ai_response(self, ai_response: str, execution_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse AI response when JSON parsing fails"""
        # Fallback to basic analysis
        return self._get_fallback_analysis(execution_data)
    
    def _get_fallback_analysis(self, execution_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get fallback analysis when AI fails"""
        total_tests = len(execution_data)
        passed_tests = sum(1 for result in execution_data 
                          if result.get('actual_status_code') == result.get('expected_status_code'))
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        failure_categories = self._categorize_failures(execution_data)
        endpoint_analysis = self._analyze_endpoints(execution_data)
        
        return {
            "summary_metrics": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "blocked_tests": 0,
                "pass_rate": round(pass_rate, 1)
            },
            "failure_categories": failure_categories,
            "endpoint_stability": endpoint_analysis[:10],  # Top 10 endpoints
            "schema_issues": [],
            "ai_insights": {
                "narrative": f"Test execution completed with {pass_rate:.1f}% pass rate. {failed_tests} out of {total_tests} tests failed.",
                "recommendations": [
                    "Review failed test cases for common patterns",
                    "Check authentication and authorization setup",
                    "Validate API response schemas"
                ],
                "suggested_fixes": []
            },
            "failed_tests_details": self._get_failed_tests_details(execution_data)
        }
    
    def _get_empty_analysis(self) -> Dict[str, Any]:
        """Get empty analysis when no data is available"""
        return {
            "summary_metrics": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "blocked_tests": 0,
                "pass_rate": 0
            },
            "failure_categories": {
                "authentication_errors": 0,
                "schema_mismatches": 0,
                "server_errors": 0,
                "timeout_errors": 0,
                "validation_errors": 0,
                "other_errors": 0
            },
            "endpoint_stability": [],
            "schema_issues": [],
            "ai_insights": {
                "narrative": "No test execution data available for analysis. Run some tests to generate AI insights.",
                "recommendations": [
                    "Execute API tests to generate data for analysis",
                    "Upload Swagger specification and generate test cases",
                    "Run positive flow tests to populate execution results"
                ],
                "suggested_fixes": []
            },
            "failed_tests_details": {
                "failed_tests": [],
                "total_failed_count": 0,
                "most_common_error": "None",
                "error_counts": {}
            }
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate complete AI report
        
        Returns:
            Complete AI analysis report
        """
        try:
            logger.info("Starting AI report generation")
            
            # Get execution data
            execution_data = self.get_execution_data()
            logger.info(f"Retrieved {len(execution_data)} execution records")
            
            if not execution_data:
                logger.warning("No execution data found, returning empty analysis")
                return self._get_empty_analysis()
            
            # Analyze with AI
            logger.info("Starting AI analysis")
            analysis_result = self.analyze_with_ai(execution_data)
            logger.info("AI analysis completed")
            
            # Add metadata
            analysis_result["metadata"] = {
                "generated_at": datetime.now().isoformat(),
                "total_records_analyzed": len(execution_data)
            }
            
            logger.info("AI report generation completed successfully")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error generating AI report: {e}", exc_info=True)
            return self._get_empty_analysis()


# Convenience function
def generate_ai_report() -> Dict[str, Any]:
    """
    Generate AI report - convenience function
    
    Returns:
        AI analysis report
    """
    service = AIReportsService()
    return service.generate_report()
