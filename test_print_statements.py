"""
Test script to verify print statements are working correctly.

This script tests the print statements in the refactored framework
without requiring a full database setup.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_print_statements():
    """Test that print statements are working in key components."""
    print("🧪 [TEST] Testing print statements in framework components...")
    print("=" * 60)
    
    try:
        # Test configuration
        print("📊 [TEST] Testing configuration...")
        from config import get_config
        config = get_config()
        print(f"✅ [TEST] Configuration loaded: {config.database.host}")
        
        # Test logging
        print("📝 [TEST] Testing logging...")
        from utils.logger import setup_logger
        logger = setup_logger("test_prints", level="INFO")
        logger.info("Test log message")
        print("✅ [TEST] Logging working")
        
        # Test state management
        print("📊 [TEST] Testing state management...")
        from agents.state import create_initial_state
        initial_state = create_initial_state()
        print(f"✅ [TEST] Initial state created with {len(initial_state)} fields")
        
        # Test agent creation
        print("🤖 [TEST] Testing agent creation...")
        from agents import get_api_testing_agent
        agent = get_api_testing_agent()
        print(f"✅ [TEST] Agent created: {type(agent).__name__}")
        
        # Test workflow status
        print("📊 [TEST] Testing workflow status...")
        status = agent.get_workflow_status()
        print(f"✅ [TEST] Workflow status: {status['completion_percentage']:.1f}% complete")
        
        print("\n🎉 [TEST] All print statement tests passed!")
        print("=" * 60)
        print("✅ The framework is ready with comprehensive print statements!")
        print("🚀 You can now run 'python main.py' to see detailed execution tracking!")
        
    except Exception as e:
        print(f"❌ [TEST] Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("🚀 Print Statement Test - API Testing Agent")
    print("=" * 60)
    
    success = test_print_statements()
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("🎯 Print statements are working correctly!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
