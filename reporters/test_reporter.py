"""
Test reporter for the API Testing Agent.

This module provides functionality for generating test reports,
collecting execution statistics, and formatting results.
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class TestResult:
    """Represents the result of a single test execution."""
    
    def __init__(
        self,
        test_name: str,
        test_type: str,
        endpoint: str,
        method: str,
        success: bool,
        status_code: Optional[int] = None,
        execution_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize test result.
        
        Args:
            test_name: Name of the test
            test_type: Type of test (positive, negative, edge, auth)
            endpoint: API endpoint
            method: HTTP method
            success: Whether the test passed
            status_code: HTTP status code
            execution_time_ms: Execution time in milliseconds
            error_message: Error message if test failed
            request_data: Request data
            response_data: Response data
        """
        self.test_name = test_name
        self.test_type = test_type
        self.endpoint = endpoint
        self.method = method
        self.success = success
        self.status_code = status_code
        self.execution_time_ms = execution_time_ms
        self.error_message = error_message
        self.request_data = request_data or {}
        self.response_data = response_data or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert test result to dictionary.
        
        Returns:
            Dictionary representation of the test result
        """
        return {
            "test_name": self.test_name,
            "test_type": self.test_type,
            "endpoint": self.endpoint,
            "method": self.method,
            "success": self.success,
            "status_code": self.status_code,
            "execution_time_ms": self.execution_time_ms,
            "error_message": self.error_message,
            "request_data": self.request_data,
            "response_data": self.response_data,
            "timestamp": self.timestamp
        }


class TestSuiteReport:
    """Represents a complete test suite report."""
    
    def __init__(self, suite_name: str = "API Test Suite"):
        """
        Initialize test suite report.
        
        Args:
            suite_name: Name of the test suite
        """
        self.suite_name = suite_name
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.test_results: List[TestResult] = []
        self.summary: Dict[str, Any] = {}
    
    def add_test_result(self, test_result: TestResult):
        """
        Add a test result to the report.
        
        Args:
            test_result: Test result to add
        """
        self.test_results.append(test_result)
    
    def finalize(self):
        """Finalize the report and calculate summary statistics."""
        self.end_time = datetime.now()
        self._calculate_summary()
    
    def _calculate_summary(self):
        """Calculate summary statistics for the test suite."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - passed_tests
        
        # Group by test type
        test_types = {}
        for result in self.test_results:
            test_type = result.test_type
            if test_type not in test_types:
                test_types[test_type] = {"total": 0, "passed": 0, "failed": 0}
            
            test_types[test_type]["total"] += 1
            if result.success:
                test_types[test_type]["passed"] += 1
            else:
                test_types[test_type]["failed"] += 1
        
        # Calculate execution time statistics
        execution_times = [r.execution_time_ms for r in self.test_results if r.execution_time_ms]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        # Calculate success rate
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": round(success_rate, 2),
            "test_types": test_types,
            "execution_time": {
                "total_duration_seconds": (self.end_time - self.start_time).total_seconds(),
                "average_test_time_ms": round(avg_execution_time, 2),
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat()
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert report to dictionary.
        
        Returns:
            Dictionary representation of the report
        """
        return {
            "suite_name": self.suite_name,
            "summary": self.summary,
            "test_results": [result.to_dict() for result in self.test_results]
        }


class TestReporter:
    """Generates and formats test reports."""
    
    def __init__(self):
        """Initialize test reporter."""
        self.current_report: Optional[TestSuiteReport] = None
    
    def start_test_suite(self, suite_name: str = "API Test Suite") -> TestSuiteReport:
        """
        Start a new test suite report.
        
        Args:
            suite_name: Name of the test suite
            
        Returns:
            New test suite report
        """
        self.current_report = TestSuiteReport(suite_name)
        logger.info(f"Started test suite: {suite_name}")
        return self.current_report
    
    def add_execution_logs(self, execution_logs: Dict[str, Dict[str, Any]]):
        """
        Add execution logs to the current report.
        
        Args:
            execution_logs: Dictionary of execution logs
        """
        if not self.current_report:
            logger.warning("No active test suite report")
            return
        
        for test_name, log_data in execution_logs.items():
            request_data = log_data.get("request", {})
            response_data = log_data.get("response", {})
            
            # Extract test information
            test_type = self._extract_test_type(test_name)
            endpoint = request_data.get("url", "Unknown")
            method = request_data.get("method", "Unknown")
            
            # Determine success
            success = response_data.get("success", False)
            status_code = response_data.get("status_code")
            execution_time_ms = response_data.get("execution_time_ms")
            error_message = response_data.get("error")
            
            # Create test result
            test_result = TestResult(
                test_name=test_name,
                test_type=test_type,
                endpoint=endpoint,
                method=method,
                success=success,
                status_code=status_code,
                execution_time_ms=execution_time_ms,
                error_message=error_message,
                request_data=request_data,
                response_data=response_data
            )
            
            self.current_report.add_test_result(test_result)
        
        logger.info(f"Added {len(execution_logs)} test results to report")
    
    def _extract_test_type(self, test_name: str) -> str:
        """
        Extract test type from test name.
        
        Args:
            test_name: Name of the test
            
        Returns:
            Test type (positive, negative, edge, auth, or unknown)
        """
        test_name_lower = test_name.lower()
        
        if any(keyword in test_name_lower for keyword in ["positive", "valid", "success"]):
            return "positive"
        elif any(keyword in test_name_lower for keyword in ["negative", "invalid", "error", "fail"]):
            return "negative"
        elif any(keyword in test_name_lower for keyword in ["edge", "boundary", "limit"]):
            return "edge"
        elif any(keyword in test_name_lower for keyword in ["auth", "token", "login", "permission"]):
            return "auth"
        else:
            return "unknown"
    
    def finalize_report(self) -> Optional[TestSuiteReport]:
        """
        Finalize the current report.
        
        Returns:
            Finalized test suite report or None if no active report
        """
        if not self.current_report:
            logger.warning("No active test suite report to finalize")
            return None
        
        self.current_report.finalize()
        logger.info("Test suite report finalized")
        return self.current_report
    
    def generate_json_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate a JSON report.
        
        Args:
            output_path: Optional output file path
            
        Returns:
            JSON report content
        """
        if not self.current_report:
            logger.warning("No active test suite report")
            return "{}"
        
        report_data = self.current_report.to_dict()
        json_content = json.dumps(report_data, indent=2, default=str)
        
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_content)
            
            logger.info(f"JSON report saved to: {output_path}")
        
        return json_content
    
    def generate_text_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate a human-readable text report.
        
        Args:
            output_path: Optional output file path
            
        Returns:
            Text report content
        """
        if not self.current_report:
            logger.warning("No active test suite report")
            return "No test results available"
        
        report = self.current_report
        summary = report.summary
        
        # Build text report
        lines = []
        lines.append("=" * 60)
        lines.append(f"TEST SUITE REPORT: {report.suite_name}")
        lines.append("=" * 60)
        lines.append("")
        
        # Summary section
        lines.append("SUMMARY")
        lines.append("-" * 20)
        lines.append(f"Total Tests: {summary['total_tests']}")
        lines.append(f"Passed: {summary['passed_tests']}")
        lines.append(f"Failed: {summary['failed_tests']}")
        lines.append(f"Success Rate: {summary['success_rate']}%")
        lines.append(f"Total Duration: {summary['execution_time']['total_duration_seconds']:.2f} seconds")
        lines.append(f"Average Test Time: {summary['execution_time']['average_test_time_ms']:.2f} ms")
        lines.append("")
        
        # Test type breakdown
        lines.append("TEST TYPE BREAKDOWN")
        lines.append("-" * 20)
        for test_type, stats in summary['test_types'].items():
            lines.append(f"{test_type.title()}: {stats['passed']}/{stats['total']} passed")
        lines.append("")
        
        # Failed tests section
        failed_tests = [r for r in report.test_results if not r.success]
        if failed_tests:
            lines.append("FAILED TESTS")
            lines.append("-" * 20)
            for test_result in failed_tests:
                lines.append(f"❌ {test_result.test_name}")
                lines.append(f"   Endpoint: {test_result.method} {test_result.endpoint}")
                lines.append(f"   Status: {test_result.status_code}")
                if test_result.error_message:
                    lines.append(f"   Error: {test_result.error_message}")
                lines.append("")
        
        # All test results
        lines.append("ALL TEST RESULTS")
        lines.append("-" * 20)
        for test_result in report.test_results:
            status_icon = "✅" if test_result.success else "❌"
            lines.append(f"{status_icon} {test_result.test_name}")
            lines.append(f"   Type: {test_result.test_type}")
            lines.append(f"   Endpoint: {test_result.method} {test_result.endpoint}")
            lines.append(f"   Status: {test_result.status_code}")
            lines.append(f"   Time: {test_result.execution_time_ms}ms")
            lines.append("")
        
        text_content = "\n".join(lines)
        
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            logger.info(f"Text report saved to: {output_path}")
        
        return text_content
    
    def print_summary(self):
        """Print a summary of the current report to console."""
        if not self.current_report:
            logger.warning("No active test suite report")
            return
        
        summary = self.current_report.summary
        print("\n" + "=" * 50)
        print(f"TEST SUITE SUMMARY: {self.current_report.suite_name}")
        print("=" * 50)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']}%")
        print(f"Duration: {summary['execution_time']['total_duration_seconds']:.2f}s")
        print("=" * 50)


# Global reporter instance
test_reporter = TestReporter()


def get_test_reporter() -> TestReporter:
    """Get the global test reporter instance."""
    return test_reporter
