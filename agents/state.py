"""
Agent state management for the API Testing Agent.

This module defines the state structure and management for the LangGraph agent
that orchestrates the API testing workflow.
"""

from typing import TypedDict, Dict, Any, List, Optional
from dataclasses import dataclass


class AgentState(TypedDict):
    """
    State structure for the API Testing Agent.
    
    This TypedDict defines all the data that flows through the agent's workflow,
    maintaining state between different processing nodes.
    """
    # API endpoints data
    endpoints: List[Dict[str, Any]]
    
    # Generated test cases
    generated_cases: Dict[str, List[Dict[str, Any]]]
    
    # Validation feedback
    feedback: str
    
    # Database table mappings
    endpoint_tables: Dict[int, str]
    
    # Execution planning
    execution_order: List[int]
    
    # Test execution logs
    execution_logs: Dict[str, Dict[str, Any]]
    
    # Test results and reporting
    test_results: Optional[Dict[str, Any]]
    
    # Error handling
    errors: List[str]
    
    # Processing status
    current_step: str
    completed_steps: List[str]


@dataclass
class AgentConfig:
    """Configuration for the API Testing Agent."""
    
    # Workflow control
    enable_validation: bool = True
    enable_regeneration: bool = True
    max_regeneration_attempts: int = 3
    
    # Execution control
    execution_delay_seconds: int = 10
    timeout_seconds: int = 30
    
    # Logging and reporting
    enable_detailed_logging: bool = True
    generate_reports: bool = True
    report_output_dir: str = "reports"
    
    # Database
    auto_initialize_db: bool = True
    cleanup_on_exit: bool = False


class StateManager:
    """Manages agent state throughout the workflow."""
    
    def __init__(self, initial_state: Optional[AgentState] = None):
        """
        Initialize state manager.
        
        Args:
            initial_state: Optional initial state
        """
        self.state = initial_state or self._create_initial_state()
        self.config = AgentConfig()
    
    def _create_initial_state(self) -> AgentState:
        """
        Create initial agent state.
        
        Returns:
            Initial agent state
        """
        return {
            "endpoints": [],
            "generated_cases": {},
            "feedback": "",
            "endpoint_tables": {},
            "execution_order": [],
            "execution_logs": {},
            "test_results": None,
            "errors": [],
            "current_step": "initialized",
            "completed_steps": []
        }
    
    def update_state(self, **kwargs) -> AgentState:
        """
        Update agent state with new values.
        
        Args:
            **kwargs: State fields to update
            
        Returns:
            Updated state
        """
        for key, value in kwargs.items():
            if key in self.state:
                self.state[key] = value
            else:
                raise ValueError(f"Unknown state field: {key}")
        
        return self.state
    
    def get_state(self) -> AgentState:
        """
        Get current agent state.
        
        Returns:
            Current agent state
        """
        return self.state.copy()
    
    def add_error(self, error: str):
        """
        Add an error to the state.
        
        Args:
            error: Error message to add
        """
        self.state["errors"].append(error)
    
    def clear_errors(self):
        """Clear all errors from the state."""
        self.state["errors"] = []
    
    def mark_step_completed(self, step_name: str):
        """
        Mark a workflow step as completed.
        
        Args:
            step_name: Name of the completed step
        """
        if step_name not in self.state["completed_steps"]:
            self.state["completed_steps"].append(step_name)
    
    def set_current_step(self, step_name: str):
        """
        Set the current workflow step.
        
        Args:
            step_name: Name of the current step
        """
        self.state["current_step"] = step_name
    
    def is_step_completed(self, step_name: str) -> bool:
        """
        Check if a step has been completed.
        
        Args:
            step_name: Name of the step to check
            
        Returns:
            True if step is completed, False otherwise
        """
        return step_name in self.state["completed_steps"]
    
    def get_completion_status(self) -> Dict[str, Any]:
        """
        Get workflow completion status.
        
        Returns:
            Dictionary with completion information
        """
        total_steps = [
            "database_initialization",
            "endpoint_parsing",
            "endpoint_storage",
            "test_case_generation",
            "test_case_validation",
            "test_case_persistence",
            "execution_planning",
            "test_execution",
            "report_generation"
        ]
        
        completed_steps = self.state["completed_steps"]
        current_step = self.state["current_step"]
        
        return {
            "total_steps": len(total_steps),
            "completed_steps": len(completed_steps),
            "current_step": current_step,
            "completion_percentage": (len(completed_steps) / len(total_steps)) * 100,
            "completed_step_names": completed_steps,
            "remaining_steps": [step for step in total_steps if step not in completed_steps]
        }
    
    def reset_state(self):
        """Reset state to initial values."""
        self.state = self._create_initial_state()
    
    def validate_state(self) -> List[str]:
        """
        Validate the current state for consistency.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        required_fields = ["endpoints", "generated_cases", "endpoint_tables", "execution_order"]
        for field in required_fields:
            if not self.state.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate endpoints
        if self.state.get("endpoints"):
            for i, endpoint in enumerate(self.state["endpoints"]):
                if not endpoint.get("path") or not endpoint.get("method"):
                    errors.append(f"Invalid endpoint at index {i}: missing path or method")
        
        # Validate generated cases
        if self.state.get("generated_cases"):
            for endpoint_key, test_cases in self.state["generated_cases"].items():
                if not isinstance(test_cases, list):
                    errors.append(f"Invalid test cases for {endpoint_key}: not a list")
        
        # Validate execution order
        if self.state.get("execution_order"):
            if not isinstance(self.state["execution_order"], list):
                errors.append("Execution order must be a list")
        
        return errors


# Global state manager instance
state_manager = StateManager()


def get_state_manager() -> StateManager:
    """Get the global state manager instance."""
    return state_manager


def create_initial_state() -> AgentState:
    """
    Create a new initial agent state.
    
    Returns:
        Initial agent state
    """
    return state_manager._create_initial_state()