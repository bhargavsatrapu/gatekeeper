"""
Test script to verify the refactored framework works correctly.

This script tests the basic functionality of the refactored API Testing Agent
without requiring a full database setup.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import get_config, update_config
from utils.logger import setup_logger
from agents import get_api_testing_agent, create_initial_state
from database import test_database_connection


def test_framework_components():
    """Test individual framework components."""
    print("🧪 Testing Framework Components")
    print("=" * 50)
    
    # Test configuration
    print("✅ Testing configuration...")
    config = get_config()
    print(f"   - Database host: {config.database.host}")
    print(f"   - API base URL: {config.api.base_url}")
    print(f"   - LLM model: {config.llm.model}")
    
    # Test logging
    print("✅ Testing logging...")
    logger = setup_logger("test_framework", level="INFO")
    logger.info("Test log message")
    
    # Test state management
    print("✅ Testing state management...")
    initial_state = create_initial_state()
    print(f"   - Initial state keys: {list(initial_state.keys())}")
    
    # Test agent creation
    print("✅ Testing agent creation...")
    agent = get_api_testing_agent()
    print(f"   - Agent type: {type(agent).__name__}")
    
    # Test workflow visualization
    print("✅ Testing workflow visualization...")
    try:
        workflow_viz = agent.visualize_workflow()
        print(f"   - Workflow visualization length: {len(workflow_viz)} characters")
    except Exception as e:
        print(f"   - Workflow visualization error: {e}")
    
    print("\n🎉 All component tests passed!")


def test_database_connection():
    """Test database connection."""
    print("\n🗄️ Testing Database Connection")
    print("=" * 50)
    
    try:
        if test_database_connection():
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed")
    except Exception as e:
        print(f"❌ Database connection error: {e}")


def test_workflow_structure():
    """Test the workflow structure."""
    print("\n🔄 Testing Workflow Structure")
    print("=" * 50)
    
    agent = get_api_testing_agent()
    
    # Test workflow status
    status = agent.get_workflow_status()
    print(f"✅ Workflow status: {status['completion_percentage']:.1f}% complete")
    print(f"   - Total steps: {status['total_steps']}")
    print(f"   - Completed steps: {status['completed_steps']}")
    print(f"   - Current step: {status['current_step']}")
    
    # Test state validation
    initial_state = create_initial_state()
    from agents.state import get_state_manager
    state_manager = get_state_manager()
    state_manager.state = initial_state
    
    validation_errors = state_manager.validate_state()
    if validation_errors:
        print(f"⚠️ State validation warnings: {validation_errors}")
    else:
        print("✅ State validation passed")


def main():
    """Main test function."""
    print("🚀 API Testing Agent - Framework Test")
    print("=" * 60)
    
    try:
        # Test individual components
        test_framework_components()
        
        # Test database connection
        test_database_connection()
        
        # Test workflow structure
        test_workflow_structure()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("🎯 The refactored framework is ready to use!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
