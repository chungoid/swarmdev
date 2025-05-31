"""
Base Agent implementation for the SwarmDev platform.
This module provides the base agent class that all specialized agents inherit from.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

class BaseAgent(ABC):
    """
    Base class for all agents in the swarm.
    
    This abstract class defines the standard interface that all agents
    must implement to be compatible with the SwarmDev platform.
    """
    
    def __init__(self, agent_id: str, agent_type: str, config: Optional[Dict] = None):
        """
        Initialize the base agent.
        
        Args:
            agent_id: Unique identifier for this agent
            agent_type: Type of agent (e.g., research, planning, development)
            config: Optional configuration dictionary
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config or {}
        self.status = "initialized"
    
    @abstractmethod
    def process_task(self, task: Dict) -> Dict:
        """
        Process a task assigned to this agent.
        
        Args:
            task: Task dictionary with details about the task
            
        Returns:
            Dict: Result of the task processing
        """
        pass
    
    def get_status(self) -> Dict:
        """
        Get the current status of this agent.
        
        Returns:
            Dict: Status information
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status
        }
    
    def initialize(self) -> bool:
        """
        Initialize the agent for task processing.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        self.status = "ready"
        return True
    
    def shutdown(self) -> bool:
        """
        Shutdown the agent and release resources.
        
        Returns:
            bool: True if shutdown was successful, False otherwise
        """
        self.status = "shutdown"
        return True
    
    def handle_error(self, error: Exception, task: Dict) -> Dict:
        """
        Handle an error that occurred during task processing.
        
        Args:
            error: The exception that occurred
            task: The task that was being processed
            
        Returns:
            Dict: Error information
        """
        self.status = "error"
        
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "task_id": task.get("task_id"),
            "agent_id": self.agent_id,
            "agent_type": self.agent_type
        }
        
        return error_info
