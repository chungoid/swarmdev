"""
Base Agent implementation for the SwarmDev platform.
This module provides the base agent class that all specialized agents inherit from.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime

class BaseAgent(ABC):
    """
    Base class for all agents in the swarm with MCP integration.
    
    This abstract class defines the standard interface that all agents
    must implement to be compatible with the SwarmDev platform, including
    MCP tool integration capabilities.
    """
    
    def __init__(self, agent_id: str, agent_type: str, llm_provider=None, mcp_manager=None, config: Optional[Dict] = None):
        """
        Initialize the base agent.
        
        Args:
            agent_id: Unique identifier for this agent
            agent_type: Type of agent (e.g., research, planning, development)
            llm_provider: LLM provider instance (optional)
            mcp_manager: MCP manager instance (optional)
            config: Optional configuration dictionary
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config or {}
        self.status = "initialized"
        self.llm_provider = llm_provider
        self.mcp_manager = mcp_manager
        
        # Enhanced MCP integration setup with detailed logging
        if mcp_manager:
            # Use the shared MCP logger with agent-specific context
            self.mcp_logger = logging.getLogger("swarmdev.mcp")
            
            # Track MCP tool usage for this agent
            self.mcp_usage = {
                "tools_used": {},
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "agent_id": agent_id,
                "agent_type": agent_type
            }
            
            self.mcp_logger.info(f"=== MCP AGENT INITIALIZATION ===")
            self.mcp_logger.info(f"Agent: {agent_type} ({agent_id})")
            self.mcp_logger.info(f"MCP Manager enabled: {self.mcp_manager.is_enabled()}")
            
            if self.mcp_manager.is_enabled():
                # Get detailed tool information
                available_tools = self.mcp_manager.get_available_tools()
                self.mcp_logger.info(f"Available MCP tools for {agent_type}: {available_tools}")
                
                # Log capabilities for each tool
                for tool_id in available_tools:
                    tool_info = self.mcp_manager.get_tool_info(tool_id)
                    if tool_info:
                        capabilities = tool_info.get("capabilities", [])
                        status = tool_info.get("status", "unknown")
                        self.mcp_logger.debug(f"  {tool_id}: {capabilities} (status: {status})")
                
                # Test key tools for this agent type
                self._test_agent_mcp_tools()
            else:
                self.mcp_logger.warning(f"MCP tools disabled for {agent_type} agent")
        else:
            self.mcp_logger = None
            self.mcp_usage = None
            # Create a basic logger for non-MCP agents
            basic_logger = logging.getLogger(f"swarmdev.{agent_type}_agent")
            basic_logger.info(f"Agent {agent_id} initialized without MCP support")
    
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
    
    def _test_agent_mcp_tools(self):
        """Test MCP tools relevant to this agent type."""
        if not self.mcp_manager or not self.mcp_manager.is_enabled():
            return
        
        self.mcp_logger.info(f"Testing MCP tools for {self.agent_type} agent...")
        
        # Test reasoning tools
        reasoning_tool = self.get_reasoning_tool()
        if reasoning_tool:
            self.mcp_logger.info(f"Found reasoning tool: {reasoning_tool}")
            # Quick test
            test_result = self.mcp_manager.call_tool(reasoning_tool, "tools/list", {})
            if test_result.get("error"):
                self.mcp_logger.error(f"Reasoning tool test failed: {test_result['error']}")
            else:
                self.mcp_logger.info(f"Reasoning tool test passed")
        else:
            self.mcp_logger.warning(f"No reasoning tool available for {self.agent_type}")
        
        # Test documentation tools
        doc_tool = self.get_documentation_tool()
        if doc_tool:
            self.mcp_logger.info(f"Found documentation tool: {doc_tool}")
            # Quick test
            test_result = self.mcp_manager.call_tool(doc_tool, "tools/list", {})
            if test_result.get("error"):
                self.mcp_logger.error(f"Documentation tool test failed: {test_result['error']}")
            else:
                self.mcp_logger.info(f"Documentation tool test passed")
        else:
            self.mcp_logger.warning(f"No documentation tool available for {self.agent_type}")
        
        self.mcp_logger.info(f"Agent MCP tool testing complete for {self.agent_type}")
    
    def use_mcp_tool(self, tool_id: str, method: str, params: Dict, timeout: Optional[int] = None) -> Dict:
        """
        Use an MCP tool with automatic logging and error handling.
        
        Args:
            tool_id: ID of the MCP tool to call
            method: JSON-RPC method name
            params: Parameters for the method call
            timeout: Optional timeout override
            
        Returns:
            Dict: Response from the MCP tool
        """
        if not self.mcp_manager:
            return {"error": "MCP manager not available"}
        
        if self.mcp_logger:
            self.mcp_logger.info(f"=== AGENT MCP CALL START ===")
            self.mcp_logger.info(f"Agent: {self.agent_type} ({self.agent_id})")
            self.mcp_logger.info(f"Tool: '{tool_id}', Method: '{method}'")
            self.mcp_logger.debug(f"Parameters: {json.dumps(params, indent=2)}")
        
        # Track usage
        if self.mcp_usage:
            self.mcp_usage["total_calls"] += 1
            if tool_id not in self.mcp_usage["tools_used"]:
                self.mcp_usage["tools_used"][tool_id] = 0
            self.mcp_usage["tools_used"][tool_id] += 1
        
        # Call the tool
        start_time = datetime.now()
        result = self.mcp_manager.call_tool(tool_id, method, params, timeout)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        # Log the result
        if self.mcp_logger:
            if result.get("error"):
                if self.mcp_usage:
                    self.mcp_usage["failed_calls"] += 1
                self.mcp_logger.error(f"=== AGENT MCP CALL FAILED ===")
                self.mcp_logger.error(f"Agent: {self.agent_type}, Tool: {tool_id}")
                self.mcp_logger.error(f"Error: {result['error']}")
                self.mcp_logger.error(f"Duration: {duration:.2f}s")
            else:
                if self.mcp_usage:
                    self.mcp_usage["successful_calls"] += 1
                self.mcp_logger.info(f"=== AGENT MCP CALL SUCCESS ===")
                self.mcp_logger.info(f"Agent: {self.agent_type}, Tool: {tool_id}")
                self.mcp_logger.info(f"Duration: {duration:.2f}s")
            
            self.mcp_logger.debug(f"Full response: {json.dumps(result, indent=2)}")
        
        return result
    
    def get_reasoning_tool(self) -> Optional[str]:
        """
        Get the best available reasoning tool for this agent.
        
        Returns:
            Optional[str]: Tool ID of the best reasoning tool, or None if unavailable
        """
        if not self.mcp_manager:
            return None
        
        reasoning_tools = self.mcp_manager.get_available_tools(['reasoning'])
        if reasoning_tools:
            # Prefer sequential thinking for complex reasoning
            for tool_id in reasoning_tools:
                if 'sequential' in tool_id.lower():
                    return tool_id
            return reasoning_tools[0]
        return None
    
    def get_context_tool(self) -> Optional[str]:
        """
        Get the best available context management tool.
        
        Returns:
            Optional[str]: Tool ID of the best context tool, or None if unavailable
        """
        if not self.mcp_manager:
            return None
        
        context_tools = self.mcp_manager.get_available_tools(['context_management'])
        return context_tools[0] if context_tools else None
    
    def get_documentation_tool(self) -> Optional[str]:
        """
        Get the best available documentation tool.
        
        Returns:
            Optional[str]: Tool ID of the best documentation tool, or None if unavailable
        """
        if not self.mcp_manager:
            return None
        
        doc_tools = self.mcp_manager.get_available_tools(['documentation'])
        return doc_tools[0] if doc_tools else None
    
    def think_sequentially(self, problem: str, context: Optional[Dict] = None) -> str:
        """
        Use sequential thinking tool for complex problem solving.
        
        Args:
            problem: Problem description to think about
            context: Optional context for the thinking process
            
        Returns:
            str: Sequential thinking result or LLM fallback
        """
        reasoning_tool = self.get_reasoning_tool()
        
        if reasoning_tool and self.mcp_logger:
            self.mcp_logger.info(f"Using sequential thinking for problem: {problem[:100]}...")
            
            # Let the MCP tool decide how many thoughts are needed
            params = {
                "thought": problem,
                "totalThoughts": 5,  # Start with a reasonable default, tool can adjust
                "thoughtNumber": 1,
                "nextThoughtNeeded": True
            }
            
            if context:
                params.update(context)
            
            result = self.mcp_manager.call_specific_tool(reasoning_tool, "sequentialthinking", params)
            
            if not result.get("error"):
                # Extract the actual thinking result
                content = result.get("result", {}).get("content", [])
                if content and len(content) > 0:
                    thinking_result = content[0].get("text", "")
                    if thinking_result:
                        if self.mcp_logger:
                            self.mcp_logger.info("Sequential thinking completed successfully")
                            self.mcp_logger.debug(f"Thinking result: {thinking_result[:200]}...")
                        return thinking_result
                    else:
                        if self.mcp_logger:
                            self.mcp_logger.warning("Sequential thinking returned empty text content")
                else:
                    if self.mcp_logger:
                        self.mcp_logger.warning("Sequential thinking returned empty content array")
                        self.mcp_logger.debug(f"Full result: {json.dumps(result, indent=2)}")
            else:
                if self.mcp_logger:
                    self.mcp_logger.warning(f"Sequential thinking failed: {result['error']}")
        
        # Fallback to LLM-based thinking
        if self.mcp_logger:
            self.mcp_logger.info("Using LLM fallback for sequential thinking")
        
        if self.llm_provider:
            prompt = f"Think step by step about this problem:\n\n{problem}"
            return self.llm_provider.generate_text(prompt, temperature=0.3)
        else:
            return f"Analysis needed for: {problem}"
    
    def lookup_documentation_for_technologies(self, goal_text: str) -> Dict[str, str]:
        """
        Dynamically identify and lookup documentation for technologies mentioned in the goal.
        
        Args:
            goal_text: The goal text to analyze for technologies
            
        Returns:
            Dict[str, str]: Mapping of technology names to their documentation
        """
        doc_tool = self.get_documentation_tool()
        documentation_results = {}
        
        if not doc_tool:
            if self.mcp_logger:
                self.mcp_logger.info("No documentation tool available for technology lookup")
            return documentation_results
        
        if not self.llm_provider:
            return documentation_results
        
        # Use LLM to identify technologies mentioned in the goal
        tech_detection_prompt = f"""
        Analyze this project goal and identify specific technologies, libraries, frameworks, or tools mentioned:
        
        GOAL: {goal_text}
        
        Extract ONLY the specific technology names that would benefit from documentation lookup.
        Focus on:
        - Programming languages (python, javascript, go, rust, etc.)
        - Frameworks (react, vue, django, fastapi, etc.)
        - Libraries (pandas, numpy, requests, etc.)
        - Tools (docker, kubernetes, git, etc.)
        - Platforms (aws, azure, gcp, etc.)
        
        Return a simple comma-separated list of technology names (no explanations).
        If no specific technologies are mentioned, return "none".
        """
        
        try:
            detected_technologies = self.llm_provider.generate_text(tech_detection_prompt, temperature=0.1)
            detected_technologies = detected_technologies.strip().lower()
            
            if detected_technologies == "none" or not detected_technologies:
                if self.mcp_logger:
                    self.mcp_logger.info("No specific technologies detected in goal")
                return documentation_results
            
            # Parse the technologies
            technologies = [tech.strip() for tech in detected_technologies.split(',') if tech.strip()]
            if self.mcp_logger:
                self.mcp_logger.info(f"Detected technologies: {technologies}")
            
            # Look up documentation for each technology
            for tech in technologies[:5]:  # Limit to avoid overwhelming
                if tech:
                    docs = self.lookup_documentation(tech)
                    if docs and "Error" not in docs:
                        documentation_results[tech] = docs
                        if self.mcp_logger:
                            self.mcp_logger.info(f"Retrieved documentation for {tech}")
                    else:
                        if self.mcp_logger:
                            self.mcp_logger.debug(f"Could not retrieve documentation for {tech}")
            
            return documentation_results
            
        except Exception as e:
            if self.mcp_logger:
                self.mcp_logger.error(f"Error in dynamic technology documentation lookup: {e}")
            return documentation_results
    
    def lookup_documentation(self, library_name: str, topic: Optional[str] = None) -> str:
        """
        Look up documentation for a specific library or topic.
        
        Args:
            library_name: Name of the library to look up
            topic: Optional specific topic within the library
            
        Returns:
            str: Documentation content or error message
        """
        doc_tool = self.get_documentation_tool()
        
        if doc_tool:
            if self.mcp_logger:
                self.mcp_logger.info(f"Looking up documentation for '{library_name}'" + 
                                   (f" (topic: {topic})" if topic else ""))
            
            # First resolve the library ID
            resolve_result = self.mcp_manager.call_specific_tool(doc_tool, "resolve-library-id", {"libraryName": library_name})
            
            if resolve_result.get("error"):
                return f"Error resolving library '{library_name}': {resolve_result['error']}"
            
            # Extract library ID from the result
            result_content = resolve_result.get("result", {})
            if "content" in result_content:
                library_id = result_content["content"][0].get("text", "").strip()
            else:
                # Try direct result field
                library_id = str(result_content.get("result", "")).strip()
            
            if not library_id:
                return f"Could not resolve library ID for '{library_name}'"
            
            if self.mcp_logger:
                self.mcp_logger.info(f"Resolved library ID: {library_id}")
            
            # Get the documentation
            doc_params = {"context7CompatibleLibraryID": library_id}
            if topic:
                doc_params["topic"] = topic
            
            doc_result = self.mcp_manager.call_specific_tool(doc_tool, "get-library-docs", doc_params)
            
            if not doc_result.get("error"):
                result_content = doc_result.get("result", {})
                if "content" in result_content:
                    content = result_content["content"]
                    if content:
                        return content[0].get("text", "No documentation content found")
                else:
                    # Try direct result field
                    return str(result_content.get("result", "No documentation content found"))
                return "Documentation lookup returned empty content"
            else:
                return f"Error looking up documentation: {doc_result['error']}"
        
        # Fallback
        if self.mcp_logger:
            self.mcp_logger.info("No documentation tool available, using LLM fallback")
        
        if self.llm_provider:
            prompt = f"Provide information about the {library_name} library" + (f" specifically about {topic}" if topic else "")
            return self.llm_provider.generate_text(prompt, temperature=0.3)
        else:
            return f"Documentation lookup not available for {library_name}"
    
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
            
            if self.mcp_logger:
                self.mcp_logger.debug(f"MCP assessment for {self.agent_type} task: {result}")
            return result
            
        except Exception as e:
            if self.mcp_logger:
                self.mcp_logger.error(f"Error in MCP assessment: {e}")
            # Default to using MCP tools if assessment fails but tools are available
            return len(self.mcp_manager.get_available_tools()) > 0
    
    def get_mcp_usage_stats(self) -> Dict:
        """Get MCP usage statistics for this agent."""
        return self.mcp_usage.copy() if self.mcp_usage else {}
    
    def log_mcp_usage_summary(self):
        """Log a summary of MCP tool usage for this agent."""
        if not self.mcp_logger or not self.mcp_usage:
            return
        
        self.mcp_logger.info(f"=== MCP Usage Summary for {self.agent_id} ===")
        self.mcp_logger.info(f"Total MCP calls: {self.mcp_usage['total_calls']}")
        self.mcp_logger.info(f"Successful calls: {self.mcp_usage['successful_calls']}")
        self.mcp_logger.info(f"Failed calls: {self.mcp_usage['failed_calls']}")
        
        if self.mcp_usage['tools_used']:
            self.mcp_logger.info("Tools used:")
            for tool_id, count in self.mcp_usage['tools_used'].items():
                self.mcp_logger.info(f"  {tool_id}: {count} calls")
