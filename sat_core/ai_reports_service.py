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
        """Get detailed information about failed tests"""
        failed_tests = []
        error_counts = {}
        
        for result in execution_data:
            if result.get('actual_status_code') != result.get('expected_status_code'):
                # Determine error type
                status_code = result.get('actual_status_code', 0)
                error_type = self._categorize_error_type(status_code)
                
                # Count error types
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
                
                # Get failure reason
                failure_reason = self._get_failure_reason(status_code, result)
                
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
    
    def _get_failure_reason(self, status_code: int, result: Dict[str, Any]) -> str:
        """Get human-readable failure reason with detailed explanations"""
        expected_status = result.get('expected_status_code', 0)
        actual_data = result.get('actual_data', {})
        endpoint = result.get('input_url', 'Unknown endpoint')
        method = result.get('input_method', 'Unknown method')
        
        # Base reason with detailed explanations
        if status_code == 401:
            return f"🔐 Authentication Failed: The API requires valid authentication credentials. Expected status {expected_status}, but got {status_code}. This usually means the API key, token, or authentication headers are missing, expired, or invalid."
        elif status_code == 403:
            return f"🚫 Access Forbidden: You don't have permission to access this resource. Expected status {expected_status}, but got {status_code}. The request was valid but the server is refusing to fulfill it due to insufficient permissions."
        elif status_code == 404:
            return f"🔍 Resource Not Found: The requested endpoint or resource doesn't exist. Expected status {expected_status}, but got {status_code}. Check if the URL path is correct and the resource exists on the server."
        elif status_code == 400:
            return f"❌ Bad Request: The request format or parameters are invalid. Expected status {expected_status}, but got {status_code}. This could be due to malformed JSON, missing required fields, or invalid parameter values."
        elif status_code == 422:
            return f"📝 Validation Error: The request data failed validation rules. Expected status {expected_status}, but got {status_code}. The request format is correct but the data doesn't meet the API's validation requirements."
        elif status_code >= 500:
            return f"🔥 Server Error: Internal server problem occurred. Expected status {expected_status}, but got {status_code}. This indicates a server-side issue that needs to be investigated by the API provider."
        elif status_code == 408:
            return f"⏰ Request Timeout: The server took too long to respond. Expected status {expected_status}, but got {status_code}. The request may be too complex or the server is overloaded."
        elif status_code == 429:
            return f"🚦 Rate Limit Exceeded: Too many requests sent to the API. Expected status {expected_status}, but got {status_code}. The API has rate limiting in place and the request limit has been exceeded."
        elif status_code == 503:
            return f"🔧 Service Unavailable: The API service is temporarily unavailable. Expected status {expected_status}, but got {status_code}. The server is down for maintenance or overloaded."
        else:
            return f"❓ Unexpected Response: Received status code {status_code} instead of expected {expected_status}. This is an unexpected response that may indicate a configuration issue or API change."
    
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
