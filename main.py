"""
Main entry point for the API Testing Agent.

This module provides the main entry point for running the API testing agent
and serves as an example of how to use the refactored framework.
"""

import sys
from pathlib import Path
from typing import Optional

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import get_config, update_config
from utils.logger import get_logger, setup_logger
from agents import get_api_testing_agent, create_initial_state
from database import test_database_connection

logger = get_logger(__name__)


def main():
    """
    Main entry point for the API Testing Agent.
    
    This function demonstrates how to use the refactored framework
    to run a complete API testing workflow.
    """
    try:
        print("🚀 [MAIN] Starting API Testing Agent...")
        # Setup logging
        setup_logger(
            name="api_testing_agent",
            level="INFO",
            log_file="logs/api_testing_agent.log"
        )
        
        print("📝 [MAIN] Logging setup completed")
        logger.info("Starting API Testing Agent")
        
        # Test database connection
        print("🗄️ [MAIN] Testing database connection...")
        logger.info("Testing database connection...")
        if not test_database_connection():
            print("❌ [MAIN] Database connection failed")
            logger.error("Database connection failed. Please check your database configuration.")
            return 1
        
        print("✅ [MAIN] Database connection successful")
        logger.info("Database connection successful")
        
        # Get the API testing agent
        print("🤖 [MAIN] Getting API testing agent...")
        agent = get_api_testing_agent()
        
        # Print workflow visualization
        print("\n📊 [MAIN] Workflow Graph:")
        print(agent.visualize_workflow())
        
        # Create initial state
        print("📊 [MAIN] Creating initial state...")
        initial_state = create_initial_state()
        
        # Run the complete workflow
        print("🔄 [MAIN] Running API testing workflow...")
        logger.info("Running API testing workflow...")
        final_state = agent.run(initial_state)
        
        # Print workflow summary
        print("📊 [MAIN] Printing workflow summary...")
        agent.print_workflow_summary()
        
        # Check for errors
        print("🔍 [MAIN] Checking for errors...")
        errors = agent.get_errors()
        if errors:
            print(f"❌ [MAIN] Workflow completed with {len(errors)} errors")
            logger.error(f"Workflow completed with {len(errors)} errors:")
            for error in errors:
                print(f"  ❌ {error}")
                logger.error(f"  - {error}")
            return 1
        
        # Print test results summary
        print("📊 [MAIN] Getting test results...")
        test_results = agent.get_test_results()
        if test_results and test_results.get("summary"):
            summary = test_results["summary"]
            print("📈 [MAIN] Test execution completed:")
            print(f"  📊 Total Tests: {summary.get('total_tests', 0)}")
            print(f"  ✅ Passed: {summary.get('passed_tests', 0)}")
            print(f"  ❌ Failed: {summary.get('failed_tests', 0)}")
            print(f"  📈 Success Rate: {summary.get('success_rate', 0)}%")
            logger.info(f"Test execution completed:")
            logger.info(f"  Total Tests: {summary.get('total_tests', 0)}")
            logger.info(f"  Passed: {summary.get('passed_tests', 0)}")
            logger.info(f"  Failed: {summary.get('failed_tests', 0)}")
            logger.info(f"  Success Rate: {summary.get('success_rate', 0)}%")
        
        print("✅ [MAIN] API Testing Agent completed successfully")
        logger.info("API Testing Agent completed successfully")
        return 0
        
    except KeyboardInterrupt:
        print("⚠️ [MAIN] Workflow interrupted by user")
        logger.info("Workflow interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ [MAIN] Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        return 1


def run_with_custom_config(
    swagger_file_path: str,
    base_url: str,
    database_config: Optional[dict] = None,
    llm_config: Optional[dict] = None
) -> int:
    """
    Run the API testing agent with custom configuration.
    
    Args:
        swagger_file_path: Path to the Swagger/OpenAPI file
        base_url: Base URL of the API to test
        database_config: Optional database configuration overrides
        llm_config: Optional LLM configuration overrides
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Update configuration
        config_updates = {
            "swagger_file_path": swagger_file_path,
            "api": {"base_url": base_url}
        }
        
        if database_config:
            config_updates["database"] = database_config
        
        if llm_config:
            config_updates["llm"] = llm_config
        
        update_config(**config_updates)
        
        # Create agent with custom config
        agent = get_api_testing_agent()
        
        # Run workflow
        initial_state = create_initial_state()
        final_state = agent.run(initial_state)
        
        # Print results
        agent.print_workflow_summary()
        
        return 0 if not agent.get_errors() else 1
        
    except Exception as e:
        logger.error(f"Error running with custom config: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
