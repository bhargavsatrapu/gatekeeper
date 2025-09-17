"""
Basic usage example for the API Testing Agent.

This example demonstrates how to use the refactored framework
to run API tests with minimal configuration.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents import get_api_testing_agent, create_initial_state
from config import update_config
from utils.logger import setup_logger


def basic_example():
    """Run a basic API testing workflow."""
    
    # Setup logging
    setup_logger("basic_example", level="INFO")
    
    # Update configuration for your setup
    update_config(
        swagger_file_path="/path/to/your/swagger.json",
        api={"base_url": "https://api.example.com"},
        database={
            "host": "localhost",
            "database": "SWAGGER_API",
            "user": "postgres",
            "password": "shirisha@123"
        }
    )
    
    # Get the agent
    agent = get_api_testing_agent()
    
    # Create initial state
    initial_state = create_initial_state()
    
    # Run the workflow
    print("Starting API testing workflow...")
    final_state = agent.run(initial_state)
    
    # Print results
    agent.print_workflow_summary()
    
    return final_state


def custom_configuration_example():
    """Example with custom configuration."""
    
    # Custom configuration
    custom_config = {
        "swagger_file_path": "/path/to/your/api-spec.json",
        "api": {
            "base_url": "https://your-api.com",
            "timeout": 60
        },
        "database": {
            "host": "your-db-host",
            "database": "your_db",
            "user": "your_user",
            "password": "your_password"
        },
        "llm": {
            "api_key": "your-gemini-api-key",
            "model": "gemini-2.5-flash"
        }
    }
    
    # Update configuration
    update_config(**custom_config)
    
    # Run with custom config
    agent = get_api_testing_agent()
    initial_state = create_initial_state()
    final_state = agent.run(initial_state)
    
    return final_state


def monitoring_example():
    """Example showing how to monitor workflow progress."""
    
    agent = get_api_testing_agent()
    initial_state = create_initial_state()
    
    # You can monitor progress by checking status
    status = agent.get_workflow_status()
    print(f"Initial status: {status}")
    
    # Run workflow
    final_state = agent.run(initial_state)
    
    # Check final status
    final_status = agent.get_workflow_status()
    print(f"Final status: {final_status}")
    
    # Get execution logs
    logs = agent.get_execution_logs()
    print(f"Executed {len(logs)} tests")
    
    # Get test results
    results = agent.get_test_results()
    if results:
        print(f"Test results available: {bool(results.get('summary'))}")
    
    return final_state


if __name__ == "__main__":
    print("API Testing Agent - Basic Usage Example")
    print("=" * 50)
    
    # Run basic example
    try:
        result = basic_example()
        print("\n✅ Basic example completed successfully!")
    except Exception as e:
        print(f"\n❌ Basic example failed: {e}")
    
    print("\n" + "=" * 50)
    print("For more examples, see the examples/ directory")
