"""
Main API Testing Agent using LangGraph.

This module contains the main agent class that orchestrates the entire
API testing workflow using LangGraph for state management and execution flow.
"""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from config import get_config
from utils.logger import get_logger
from agents.state import AgentState, get_state_manager
from agents.workflow_nodes import get_workflow_nodes

logger = get_logger(__name__)


class APITestingAgent:
    """
    Main API Testing Agent that orchestrates the complete testing workflow.
    
    This agent uses LangGraph to manage state and control the flow of execution
    through various stages of API testing including parsing, generation,
    validation, and execution.
    """
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """
        Initialize the API Testing Agent.
        
        Args:
            config_override: Optional configuration overrides
        """
        self.config = get_config()
        self.state_manager = get_state_manager()
        self.workflow_nodes = get_workflow_nodes()
        
        # Override config if provided
        if config_override:
            for key, value in config_override.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
        
        # Initialize the workflow graph
        self.graph = self._build_workflow_graph()
        self.compiled_graph = self.graph.compile()
        
        logger.info("API Testing Agent initialized")
    
    def _build_workflow_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow for API testing.
        
        Returns:
            Configured StateGraph
        """
        logger.info("Building workflow graph")
        
        # # Create the state graph
        graph = StateGraph(AgentState)
        
        # Add all workflow nodes
        graph.add_node("initialize_database", self.workflow_nodes.initialize_database_node)
        graph.add_node("parse_swagger_file", self.workflow_nodes.parse_swagger_file_node)
        graph.add_node("store_endpoints", self.workflow_nodes.store_endpoints_node)
        graph.add_node("fetch_endpoints", self.workflow_nodes.fetch_endpoints_node)
        graph.add_node("generate_test_cases", self.workflow_nodes.generate_test_cases_node)
        # graph.add_node("validate_test_cases", self.workflow_nodes.validate_test_cases_node)
        # graph.add_node("regenerate_test_cases", self.workflow_nodes.generate_test_cases_node)
        graph.add_node("persist_test_cases", self.workflow_nodes.persist_test_cases_node)
        graph.add_node("plan_execution_order", self.workflow_nodes.plan_execution_order_node)
        graph.add_node("run_positive_flow", self.workflow_nodes.run_positive_flow_node)
        graph.add_node("run_all_possible_tests", self.workflow_nodes.run_all_possible_tests_node)
        graph.add_node("generate_report", self.workflow_nodes.generate_report_node)
        
        # Define the workflow edges
        graph.add_edge(START, "initialize_database")
        graph.add_edge("initialize_database", "parse_swagger_file")
        graph.add_edge("parse_swagger_file", "store_endpoints")
        graph.add_edge("store_endpoints", "fetch_endpoints")
        graph.add_edge("fetch_endpoints", "generate_test_cases")
        graph.add_edge("generate_test_cases", "persist_test_cases")
        
        # Conditional edge for validation feedback
        # graph.add_conditional_edges(
        #     "validate_test_cases",
        #     self._validation_decision_function,
        #     {
        #         "regenerate": "regenerate_test_cases",
        #         "persist": "persist_test_cases"
        #     }
        # )
        
        # graph.add_edge("regenerate_test_cases", "validate_test_cases")
        # graph.add_edge("initialize_database", "fetch_endpoints")
        graph.add_edge("persist_test_cases", "plan_execution_order")
        graph.add_edge("plan_execution_order", "run_positive_flow")
        graph.add_edge("run_positive_flow", "run_all_possible_tests")
        graph.add_edge("run_all_possible_tests", "generate_report")
        graph.add_edge("generate_report", END)
        
        logger.info("Workflow graph built successfully")

        #         # Create the state graph
        # graph = StateGraph(AgentState)
        
        # # Add all workflow nodes
        # # graph.add_node("initialize_database", self.workflow_nodes.initialize_database_node)
        # graph.add_node("parse_swagger_file", self.workflow_nodes.parse_swagger_file_node)
        # graph.add_node("store_endpoints", self.workflow_nodes.store_endpoints_node)
        # graph.add_node("fetch_endpoints", self.workflow_nodes.fetch_endpoints_node)
        # graph.add_node("generate_test_cases", self.workflow_nodes.generate_test_cases_node)
        # # graph.add_node("validate_test_cases", self.workflow_nodes.validate_test_cases_node)
        # # graph.add_node("regenerate_test_cases", self.workflow_nodes.generate_test_cases_node)
        # graph.add_node("persist_test_cases", self.workflow_nodes.persist_test_cases_node)
        # graph.add_node("plan_execution_order", self.workflow_nodes.plan_execution_order_node)
        # graph.add_node("run_positive_flow", self.workflow_nodes.run_positive_flow_node)
        # graph.add_node("run_all_possible_tests", self.workflow_nodes.run_all_possible_tests_node)
        # graph.add_node("generate_report", self.workflow_nodes.generate_report_node)
        
        # # Define the workflow edges
        # # graph.add_edge(START, "initialize_database")
        # # graph.add_edge("initialize_database", "parse_swagger_file")
        # # graph.add_edge("parse_swagger_file", "store_endpoints")
        # graph.add_edge(START, "fetch_endpoints")
        # # graph.add_edge("fetch_endpoints", "generate_test_cases")
        # # graph.add_edge("generate_test_cases", "persist_test_cases")
        
        # # Conditional edge for validation feedback
        # # graph.add_conditional_edges(
        # #     "validate_test_cases",
        # #     self._validation_decision_function,
        # #     {
        # #         "regenerate": "regenerate_test_cases",
        # #         "persist": "persist_test_cases"
        # #     }
        # # )
        
        # # graph.add_edge("regenerate_test_cases", "validate_test_cases")
        # # graph.add_edge("initialize_database", "fetch_endpoints")
        # graph.add_edge("fetch_endpoints", "plan_execution_order")
        # graph.add_edge("plan_execution_order", "run_positive_flow")
        # graph.add_edge("run_positive_flow", "run_all_possible_tests")
        # graph.add_edge("run_all_possible_tests", "generate_report")
        # graph.add_edge("generate_report", END)
        
        # logger.info("Workflow graph built successfully")
        return graph
    
    def _validation_decision_function(self, state: AgentState) -> str:
        """
        Decision function for validation feedback routing.
        
        Args:
            state: Current agent state
            
        Returns:
            Next node name based on validation feedback
        """
        feedback = state.get("feedback", "").lower()
        
        # Check if regeneration is needed
        if self.workflow_nodes.should_regenerate_test_cases(state):
            logger.info("Validation feedback indicates regeneration needed")
            return "regenerate"
        else:
            logger.info("Validation feedback is acceptable, proceeding to persistence")
            return "persist"
    
    def run(self, initial_state: Optional[AgentState] = None) -> AgentState:
        """
        Run the complete API testing workflow.
        
        Args:
            initial_state: Optional initial state (uses default if not provided)
            
        Returns:
            Final agent state after workflow completion
        """
        print("🚀 [AGENT] Starting API testing workflow...")
        logger.info("Starting API testing workflow")
        
        try:
            # Use provided state or create initial state
            if initial_state is None:
                print("📊 [AGENT] Creating initial state...")
                initial_state = self.state_manager._create_initial_state()
            
            # Reset state manager
            self.state_manager.state = initial_state
            print(f"📊 [AGENT] Initial state created with {len(initial_state)} fields")
            
            # Execute the workflow
            print("🔄 [AGENT] Executing workflow graph...")
            logger.info("Executing workflow graph")
            final_state = self.compiled_graph.invoke(initial_state)
            
            # Update state manager with final state
            self.state_manager.state = final_state
            
            print("✅ [AGENT] API testing workflow completed successfully")
            logger.info("API testing workflow completed successfully")
            return final_state
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {e}"
            print(f"❌ [AGENT] {error_msg}")
            logger.error(error_msg)
            self.state_manager.add_error(error_msg)
            return self.state_manager.get_state()
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """
        Get current workflow status and progress.
        
        Returns:
            Dictionary containing workflow status information
        """
        return self.state_manager.get_completion_status()
    
    def get_execution_logs(self) -> Dict[str, Any]:
        """
        Get execution logs from the current state.
        
        Returns:
            Dictionary containing execution logs
        """
        return self.state_manager.state.get("execution_logs", {})
    
    def get_test_results(self) -> Optional[Dict[str, Any]]:
        """
        Get test results from the current state.
        
        Returns:
            Test results dictionary or None if not available
        """
        return self.state_manager.state.get("test_results")
    
    def get_errors(self) -> list:
        """
        Get any errors that occurred during execution.
        
        Returns:
            List of error messages
        """
        return self.state_manager.state.get("errors", [])
    
    def print_workflow_summary(self):
        """Print a summary of the workflow execution."""
        status = self.get_workflow_status()
        errors = self.get_errors()
        test_results = self.get_test_results()
        
        print("\n" + "=" * 60)
        print("API TESTING AGENT - WORKFLOW SUMMARY")
        print("=" * 60)
        
        print(f"Completion: {status['completion_percentage']:.1f}%")
        print(f"Current Step: {status['current_step']}")
        print(f"Completed Steps: {status['completed_steps']}")
        
        if errors:
            print(f"\nErrors ({len(errors)}):")
            for error in errors:
                print(f"  ❌ {error}")
        
        if test_results and test_results.get("summary"):
            summary = test_results["summary"]
            print(f"\nTest Results:")
            print(f"  Total Tests: {summary.get('total_tests', 0)}")
            print(f"  Passed: {summary.get('passed_tests', 0)}")
            print(f"  Failed: {summary.get('failed_tests', 0)}")
            print(f"  Success Rate: {summary.get('success_rate', 0)}%")
        
        print("=" * 60)
    
    def visualize_workflow(self) -> str:
        """
        Generate ASCII visualization of the workflow graph.
        
        Returns:
            ASCII representation of the workflow
        """
        try:
            return self.compiled_graph.get_graph().draw_ascii()
        except Exception as e:
            logger.error(f"Failed to generate workflow visualization: {e}")
            return "Workflow visualization not available"


# Global agent instance
api_testing_agent = APITestingAgent()


def get_api_testing_agent() -> APITestingAgent:
    """Get the global API testing agent instance."""
    return api_testing_agent


def create_api_testing_agent(config_override: Optional[Dict[str, Any]] = None) -> APITestingAgent:
    """
    Create a new API testing agent instance.
    
    Args:
        config_override: Optional configuration overrides
        
    Returns:
        New API testing agent instance
    """
    return APITestingAgent(config_override)
