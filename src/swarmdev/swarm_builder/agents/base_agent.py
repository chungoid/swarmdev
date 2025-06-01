"""
Base Agent implementation for the SwarmDev platform.
This module provides the base agent class that all specialized agents inherit from.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

from ...utils.agent_logger import AgentLogger

class BaseAgent(ABC):
    """
    Base class for all agents in the swarm with MCP integration.
    
    This abstract class defines the standard interface that all agents
    must implement to be compatible with the SwarmDev platform, including
    MCP tool integration capabilities.
    """
    
    def __init__(self, agent_id: str, agent_type: str, llm_provider=None, mcp_manager=None, config: Optional[Dict] = None):
        """Initialize a base agent with LLM and MCP capabilities."""
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.llm_provider = llm_provider
        self.mcp_manager = mcp_manager
        self.config = config or {}
        
        # Agent state
        self.current_task = None
        self.task_history = []
        self.performance_metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_execution_time": 0.0,
            "llm_calls": 0,
            "llm_tokens_used": 0,
            "mcp_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Initialize logging
        self.logger = AgentLogger.get_logger(agent_type, agent_id)
        self.logger.info(f"Initializing {agent_type} agent: {agent_id}")
        
        # MCP Integration - SIMPLIFIED: Just make tools available directly
        if self.mcp_manager:
            self.logger.info("=== MCP AGENT INITIALIZATION ===")
            self.logger.info(f"Agent: {agent_type} ({agent_id})")
            self.logger.info(f"MCP Manager enabled: {self.mcp_manager.is_enabled()}")
            
            # Get ALL available tools - no capability filtering
            available_tools = self.mcp_manager.get_available_tools()
            self.logger.info(f"Available MCP tools for {agent_type}: {available_tools}")
            
            # Store direct tool access for natural usage
            self.mcp_tools = {}
            for tool_id in available_tools:
                tool_info = self.mcp_manager.get_tool_info(tool_id)
                if tool_info:
                    self.mcp_tools[tool_id] = tool_info
                    capabilities = tool_info.get("capabilities", [])
                    status = tool_info.get("status", "unknown")
                    self.logger.debug(f"  {tool_id}: {capabilities} (status: {status})")
        else:
            self.mcp_tools = {}
            self.logger.info("No MCP manager - agent will work without external tools")
    
    def get_available_mcp_tools(self) -> List[str]:
        """Get list of available MCP tools - simple and direct."""
        return list(self.mcp_tools.keys())
    
    def call_mcp_tool(self, tool_id: str, method: str, params: Dict, timeout: Optional[int] = None, justification: str = None) -> Dict:
        """
        Call an MCP tool directly - no capability checking, just use it.
        This is how MCP should work - simple and direct.
        """
        if not self.mcp_manager:
            return {"error": "No MCP manager available"}
        
        if tool_id not in self.mcp_tools:
            available = list(self.mcp_tools.keys())
            return {"error": f"Tool '{tool_id}' not available. Available: {available}"}
        
        justification = justification or f"Agent {self.agent_type} using {tool_id} tool"
        self.logger.info(f"🔧 Using MCP tool: {tool_id} - {justification}")
        
        # Direct tool call - no complex logic
        result = self.mcp_manager.call_tool(tool_id, method, params, timeout)
        
        # Update metrics
        self.performance_metrics["mcp_calls"] += 1
        
        if result.get("error"):
            self.logger.warning(f"MCP tool {tool_id} failed: {result['error']}")
        else:
            self.logger.info(f"MCP tool {tool_id} succeeded")
        
        return result
    
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
    
    # MCP Integration Methods
    
    def should_use_mcp_for_task(self, task: Dict) -> bool:
        """
        Determine if MCP tools should be used for a specific task.
        
        Args:
            task: Task dictionary
            
        Returns:
            bool: True if MCP tools would be beneficial
        """
        if not self.mcp_manager or not self.mcp_manager.is_enabled():
            return False
        
        # Check if the task has MCP recommendations
        mcp_recommendations = task.get("mcp_recommendations", [])
        if mcp_recommendations:
            return True
        
        # Check based on task complexity and agent type
        goal = task.get("goal", "")
        
        # Use LLM to intelligently determine if MCP tools would be beneficial
        return self._intelligent_mcp_assessment(goal, task)
    
    def _intelligent_mcp_assessment(self, goal: str, task: Dict) -> bool:
        """
        Use LLM to intelligently assess whether MCP tools would be beneficial.
        
        Args:
            goal: The goal text
            task: Task dictionary
            
        Returns:
            bool: True if MCP tools would be beneficial
        """
        if not self.llm_provider:
            # Default to using MCP tools if available but no LLM for assessment
            return len(self.mcp_manager.get_available_tools()) > 0
        
        try:
            available_tools = self.mcp_manager.get_available_tools()
            if not available_tools:
                return False
            
            # Get capabilities of available tools
            tool_capabilities = []
            for tool_id in available_tools:
                tool_info = self.mcp_manager.get_tool_info(tool_id)
                if tool_info:
                    capabilities = tool_info.get("capabilities", [])
                    tool_capabilities.extend(capabilities)
            
            if not tool_capabilities:
                return False
            
            assessment_prompt = f"""
            Analyze if MCP tools would be beneficial for this task:
            
            GOAL: {goal}
            AGENT TYPE: {self.agent_type}
            TASK CONTEXT: {task.get("context", {})}
            
            AVAILABLE MCP CAPABILITIES: {set(tool_capabilities)}
            
            Would any of these MCP capabilities significantly improve the quality or effectiveness of this task?
            Consider:
            - Task complexity and scope
            - Whether reasoning/planning tools would help break down the problem
            - Whether documentation lookup would provide valuable context
            - Whether the task involves technical concepts that benefit from external knowledge
            
            Return only "YES" if MCP tools would be beneficial, "NO" if standard LLM processing is sufficient.
            """
            
            assessment = self.llm_provider.generate_text(assessment_prompt, temperature=0.1)
            result = assessment.strip().upper() == "YES"
            
            if self.logger:
                self.logger.debug(f"MCP assessment for {self.agent_type} task: {result}")
            return result
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in MCP assessment: {e}")
            # Default to using MCP tools if assessment fails but tools are available
            return len(self.mcp_manager.get_available_tools()) > 0
    
    def get_mcp_usage_stats(self) -> Dict:
        """Get MCP usage statistics for this agent."""
        return self.performance_metrics.copy()
    
    def log_mcp_usage_summary(self):
        """Log summary of MCP tool usage by this agent."""
        if not self.mcp_manager or not self.mcp_manager.is_enabled():
            return
        
        self.logger.info(f"=== {self.agent_type.upper()} AGENT MCP USAGE SUMMARY ===")
        self.logger.info(f"Total MCP calls: {self.performance_metrics['mcp_calls']}")
        self.logger.info(f"Cache hits: {self.performance_metrics['cache_hits']}")
        self.logger.info(f"Cache misses: {self.performance_metrics['cache_misses']}")
        
        if self.performance_metrics['mcp_calls'] > 0:
            success_rate = (self.performance_metrics['mcp_calls'] - self.performance_metrics['tasks_failed']) / self.performance_metrics['mcp_calls'] * 100
            self.logger.info(f"Success rate: {success_rate:.1f}%")
            
            if self.performance_metrics['cache_hits'] + self.performance_metrics['cache_misses'] > 0:
                cache_rate = (self.performance_metrics['cache_hits'] / (self.performance_metrics['cache_hits'] + self.performance_metrics['cache_misses'])) * 100
                self.logger.info(f"Cache efficiency: {cache_rate:.1f}%")
        
        self.logger.info("=== END MCP USAGE SUMMARY ===")
    
    def collect_mcp_metrics(self) -> Dict:
        """
        Collect MCP metrics for status reporting.
        
        Returns:
            Dict: MCP usage metrics including tool-specific counts
        """
        # Get agent-level metrics
        agent_metrics = self.performance_metrics.copy()
        
        # Get MCP manager metrics if available
        manager_metrics = {}
        if self.mcp_manager and self.mcp_manager.is_enabled():
            try:
                if hasattr(self.mcp_manager, 'get_metrics'):
                    manager_metrics = self.mcp_manager.get_metrics()
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.warning(f"Failed to get MCP manager metrics: {e}")
        
        # Combine metrics with server/tool details
        combined_metrics = {
            "agent_metrics": agent_metrics,
            "manager_metrics": manager_metrics,
            "agent_type": self.agent_type,
            "agent_id": self.agent_id
        }
        
        # Add server names and tool details
        if self.mcp_manager and hasattr(self.mcp_manager, 'mcp_tools'):
            server_calls = {}
            try:
                for tool_id, tool_info in self.mcp_manager.mcp_tools.items():
                    # Get usage count from agent metrics first, then manager
                    usage_count = agent_metrics.get("tools_used", {}).get(tool_id, 0)
                    if usage_count == 0:
                        usage_count = manager_metrics.get("tools_used", {}).get(tool_id, 0)
                    
                    server_name = tool_info.get("name", tool_id)
                    server_calls[server_name] = server_calls.get(server_name, 0) + usage_count
                
                combined_metrics["server_calls"] = server_calls
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.warning(f"Failed to get server call details: {e}")
        
        return combined_metrics
    
    def get_tools_by_capability(self, capability: str) -> List[str]:
        """
        Get all MCP tools that have the specified capability.
        
        Args:
            capability: The capability to search for (e.g., "reasoning", "documentation")
            
        Returns:
            List[str]: List of tool IDs with that capability
        """
        if not self.mcp_manager or not self.mcp_manager.is_enabled():
            return []
        
        # Check if mcp_manager has get_tools_by_capability method
        if hasattr(self.mcp_manager, 'get_tools_by_capability'):
            return self.mcp_manager.get_tools_by_capability(capability)
        
        # Fallback: manually check tool info
        tools = []
        available_tools = self.mcp_manager.get_available_tools()
        for tool_id in available_tools:
            tool_info = self.mcp_manager.get_tool_info(tool_id)
            if tool_info and capability in tool_info.get("capabilities", []):
                tools.append(tool_id)
        
        return tools
    
    def get_tool_methods(self, tool_id: str) -> List[Dict]:
        """
        Get available methods/functions for an MCP tool dynamically.
        
        Args:
            tool_id: The MCP tool ID
            
        Returns:
            List[Dict]: List of method info with names, parameters, descriptions
        """
        if not self.mcp_manager:
            return []
        
        # Try to get method list from MCP manager
        if hasattr(self.mcp_manager, 'get_tool_methods'):
            return self.mcp_manager.get_tool_methods(tool_id)
        
        # Try to call list_tools or similar discovery method
        try:
            result = self.mcp_manager.call_tool(tool_id, "list_tools", {})
            if not result.get("error"):
                return result.get("tools", [])
        except:
            pass
        
        return []
    
    def collect_llm_metrics(self) -> Dict:
        """
        Collect LLM metrics for status reporting.
        
        Returns:
            Dict: LLM usage metrics including model and token counts
        """
        llm_metrics = {
            "agent_type": self.agent_type,
            "agent_id": self.agent_id,
            "model": "unknown",
            "provider": "unknown",
            "total_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0
        }
        
        # Get model and provider info from LLM provider
        if self.llm_provider:
            try:
                if hasattr(self.llm_provider, 'model'):
                    llm_metrics["model"] = self.llm_provider.model
                
                if hasattr(self.llm_provider, '__class__'):
                    provider_name = self.llm_provider.__class__.__name__.replace('Provider', '')
                    llm_metrics["provider"] = provider_name
                
                # Try to get usage metrics if the provider supports it
                if hasattr(self.llm_provider, 'get_usage_metrics'):
                    usage = self.llm_provider.get_usage_metrics()
                    llm_metrics.update(usage)
                
            except Exception as e:
                self.logger.warning(f"Failed to get LLM provider metrics: {e}")
        
        return llm_metrics
    
    # Common Project File Operations
    
    def investigate_project(self, project_dir: str) -> str:
        """
        Simple method for LLM to investigate a project directory.
        
        Args:
            project_dir: Project directory path
            
        Returns:
            str: Just the project directory path - LLM can investigate it directly
        """
        if not os.path.exists(project_dir):
            raise Exception(f"Project directory does not exist: {project_dir}")
        
        self.logger.info(f"Project investigation target: {project_dir}")
        return project_dir
    
    @classmethod
    def log_execution_cache_summary(cls):
        """Log summary of execution-wide cache usage."""
        cache = cls._execution_cache
        logger = logging.getLogger("swarmdev.mcp")
        
        logger.info("=== EXECUTION CACHE SUMMARY ===")
        logger.info(f"Documentation cache entries: {len(cache['documentation'])}")
        logger.info(f"Sequential thinking cache entries: {len(cache['sequential_thinking'])}")
        
        logger.info("Call counts by tool:")
        for tool_id, count in cache['call_counts'].items():
            logger.info(f"  {tool_id}: {count} calls")
        
        if cache['documentation']:
            logger.info("Cached documentation:")
            for key in cache['documentation'].keys():
                logger.info(f"  {key}")
        
        if cache['sequential_thinking']:
            logger.info("Cached thinking problems:")
            for key in cache['sequential_thinking'].keys():
                logger.info(f"  {key}")
        
        logger.info("=== END CACHE SUMMARY ===")
    
    @classmethod
    def clear_execution_cache(cls):
        """Clear the execution cache (for new builds)."""
        cls._execution_cache = {
            'documentation': {},
            'sequential_thinking': {},
            'execution_id': None,
            'call_counts': {}
        }


    

