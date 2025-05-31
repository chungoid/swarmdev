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
        
        # Set up basic logging
        self.logger = logging.getLogger(f"swarmdev.{agent_type}_agent")
        
        # EXECUTION-SCOPED CACHE (shared across all agents in same execution)
        if not hasattr(BaseAgent, '_execution_cache'):
            BaseAgent._execution_cache = {
                'documentation': {},  # tech_name -> docs
                'sequential_thinking': {},  # problem_hash -> result  
                'execution_id': None,
                'call_counts': {}  # tool_id -> count
            }
        
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
                "cache_hits": 0,
                "cache_misses": 0,
                "throttled_calls": 0,
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
                
                # MCP tools available
            else:
                self.mcp_logger.warning(f"MCP tools disabled for {agent_type} agent")
        else:
            self.mcp_logger = None
            self.mcp_usage = None
            # Basic logger already set up above
            self.logger.info(f"Agent {agent_id} initialized without MCP support")
    
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
    

    
    def use_mcp_tool(self, tool_id: str, method: str, params: Dict, timeout: Optional[int] = None, justification: str = None) -> Dict:
        """
        UNIFIED MCP TOOL INTERFACE - The ONLY way agents should call MCP tools.
        
        Features:
        - Intelligent caching to prevent wasteful repeat calls
        - Usage throttling to prevent spam
        - Single source of truth for all MCP metrics
        - Fail loudly instead of hiding issues with fallbacks
        
        Args:
            tool_id: ID of the MCP tool to call
            method: JSON-RPC method name
            params: Parameters for the method call
            timeout: Optional timeout override
            justification: Why this call is necessary (for debugging wasteful usage)
            
        Returns:
            Dict: Response from the MCP tool or cached result
        """
        if not self.mcp_manager:
            raise Exception("MCP manager not available - agents MUST have MCP support")
        
        # INTELLIGENT CACHING CHECKS
        cache_key = self._generate_cache_key(tool_id, method, params)
        cached_result = self._check_cache(cache_key, tool_id, method, params)
        if cached_result:
            self.mcp_usage["cache_hits"] += 1
            if self.mcp_logger:
                self.mcp_logger.info(f"CACHE HIT: {tool_id}.{method} - using cached result")
            return cached_result
        
        self.mcp_usage["cache_misses"] += 1
        
        # INTELLIGENT THROTTLING
        if self._should_throttle_call(tool_id, method, params, justification):
            self.mcp_usage["throttled_calls"] += 1
            throttle_msg = f"THROTTLED: {tool_id}.{method} - excessive usage detected"
            if self.mcp_logger:
                self.mcp_logger.warning(throttle_msg)
                self.mcp_logger.warning(f"Justification: {justification or 'None provided'}")
            return {"error": throttle_msg, "throttled": True}
        
        # USAGE LOGGING
        if self.mcp_logger:
            self.mcp_logger.info(f"=== INTELLIGENT MCP CALL ===")
            self.mcp_logger.info(f"Agent: {self.agent_type} ({self.agent_id})")
            self.mcp_logger.info(f"Tool: '{tool_id}', Method: '{method}'")
            self.mcp_logger.info(f"Justification: {justification or 'None provided'}")
            self.mcp_logger.debug(f"Parameters: {json.dumps(params, indent=2)}")
        
        # TRACK USAGE BEFORE CALL
        self.mcp_usage["total_calls"] += 1
        if tool_id not in self.mcp_usage["tools_used"]:
            self.mcp_usage["tools_used"][tool_id] = 0
        self.mcp_usage["tools_used"][tool_id] += 1
        
        # INCREMENT EXECUTION-WIDE COUNTER
        if tool_id not in BaseAgent._execution_cache["call_counts"]:
            BaseAgent._execution_cache["call_counts"][tool_id] = 0
        BaseAgent._execution_cache["call_counts"][tool_id] += 1
        
        # MAKE THE ACTUAL CALL
        start_time = datetime.now()
        result = self.mcp_manager.call_tool(tool_id, method, params, timeout)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        # UPDATE METRICS
        if result.get("error"):
            self.mcp_usage["failed_calls"] += 1
            if self.mcp_logger:
                self.mcp_logger.error(f"MCP CALL FAILED: {tool_id}")
                self.mcp_logger.error(f"Error: {result['error']}")
                self.mcp_logger.error(f"Duration: {duration:.2f}s")
        else:
            self.mcp_usage["successful_calls"] += 1
            # CACHE SUCCESSFUL RESULTS
            self._cache_result(cache_key, result, tool_id, method, params)
            if self.mcp_logger:
                self.mcp_logger.info(f"MCP CALL SUCCESS: {tool_id}")
                self.mcp_logger.info(f"Duration: {duration:.2f}s")
                self.mcp_logger.info(f"Cached for future use")
        
        if self.mcp_logger:
            self.mcp_logger.debug(f"Full response: {json.dumps(result, indent=2)}")
        
        return result
    
    def _generate_cache_key(self, tool_id: str, method: str, params: Dict) -> str:
        """Generate a cache key for this MCP call."""
        import hashlib
        
        # Get tool capabilities to determine caching strategy
        if self.mcp_manager:
            tool_info = self.mcp_manager.get_tool_info(tool_id)
            if tool_info:
                capabilities = tool_info.get("capabilities", [])
                
                # For documentation-capable tools
                if "documentation" in capabilities:
                    # Key by library/tech name for documentation tools
                    lib_name = params.get("arguments", {}).get("libraryName") or params.get("library_name") or params.get("tech_name")
                    if lib_name:
                        return f"doc_{tool_id}_{lib_name}"
                
                # For reasoning-capable tools
                if "reasoning" in capabilities:
                    # Key by input content hash for reasoning tools
                    input_text = params.get("arguments", {}).get("input") or params.get("input", "")
                    if len(input_text) > 100:
                        content_hash = hashlib.md5(input_text.encode()).hexdigest()[:12]
                        return f"reasoning_{tool_id}_{content_hash}"
        
        # Default: hash all parameters
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:12]
        return f"{tool_id}_{method}_{param_hash}"
    
    def _check_cache(self, cache_key: str, tool_id: str, method: str, params: Dict) -> Optional[Dict]:
        """Check if we have a cached result for this call."""
        cache = BaseAgent._execution_cache
        
        # Documentation caching
        if cache_key.startswith("doc_"):
            return cache["documentation"].get(cache_key)
        
        # Reasoning caching  
        if cache_key.startswith("reasoning_"):
            return cache["sequential_thinking"].get(cache_key)
        
        return None
    
    def _cache_result(self, cache_key: str, result: Dict, tool_id: str, method: str, params: Dict):
        """Cache a successful result."""
        if result.get("error"):
            return  # Don't cache errors
        
        cache = BaseAgent._execution_cache
        
        # Documentation caching
        if cache_key.startswith("doc_"):
            cache["documentation"][cache_key] = result
            if self.mcp_logger:
                self.mcp_logger.debug(f"Cached documentation: {cache_key}")
        
        # Reasoning caching
        elif cache_key.startswith("reasoning_"):
            cache["sequential_thinking"][cache_key] = result
            if self.mcp_logger:
                self.mcp_logger.debug(f"Cached reasoning result: {cache_key}")
    
    def _should_throttle_call(self, tool_id: str, method: str, params: Dict, justification: str) -> bool:
        """Intelligent throttling to prevent wasteful MCP usage."""
        cache = BaseAgent._execution_cache
        current_count = cache["call_counts"].get(tool_id, 0)
        
        # Get tool capabilities for intelligent throttling
        if self.mcp_manager:
            tool_info = self.mcp_manager.get_tool_info(tool_id)
            if tool_info:
                capabilities = tool_info.get("capabilities", [])
                
                # DOCUMENTATION THROTTLING: Max 3 calls per unique library
                if "documentation" in capabilities:
                    lib_name = params.get("arguments", {}).get("libraryName") or params.get("library_name") or params.get("tech_name")
                    if lib_name:
                        library_calls = sum(1 for key in cache["documentation"].keys() 
                                          if key.startswith(f"doc_{tool_id}_{lib_name}"))
                        if library_calls >= 3:  # Max 3 doc calls per library per tool
                            return True
                
                # REASONING THROTTLING: Max 20 calls per execution
                if "reasoning" in capabilities and current_count >= 20:
                    if not justification or len(justification) < 20:
                        return True  # Require good justification for >20 calls
        
        # GENERAL THROTTLING: Max 50 calls per tool per execution
        if current_count >= 50:
            return True
        
        return False
    

    

    

    
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
        """Log summary of MCP tool usage by this agent."""
        if not self.mcp_manager or not self.mcp_manager.is_enabled():
            return
        
        self.mcp_logger.info(f"=== {self.agent_type.upper()} AGENT MCP USAGE SUMMARY ===")
        self.mcp_logger.info(f"Total MCP calls: {self.mcp_usage['total_calls']}")
        self.mcp_logger.info(f"Successful calls: {self.mcp_usage['successful_calls']}")
        self.mcp_logger.info(f"Failed calls: {self.mcp_usage['failed_calls']}")
        self.mcp_logger.info(f"Cache hits: {self.mcp_usage['cache_hits']}")
        self.mcp_logger.info(f"Cache misses: {self.mcp_usage['cache_misses']}")
        self.mcp_logger.info(f"Throttled calls: {self.mcp_usage['throttled_calls']}")
        
        if self.mcp_usage['total_calls'] > 0:
            success_rate = (self.mcp_usage['successful_calls'] / self.mcp_usage['total_calls']) * 100
            self.mcp_logger.info(f"Success rate: {success_rate:.1f}%")
            
            if self.mcp_usage['cache_hits'] + self.mcp_usage['cache_misses'] > 0:
                cache_rate = (self.mcp_usage['cache_hits'] / (self.mcp_usage['cache_hits'] + self.mcp_usage['cache_misses'])) * 100
                self.mcp_logger.info(f"Cache efficiency: {cache_rate:.1f}%")
        
        if self.mcp_usage['tools_used']:
            self.mcp_logger.info("Per-tool usage:")
            for tool_id, count in self.mcp_usage['tools_used'].items():
                self.mcp_logger.info(f"  {tool_id}: {count} calls")
        
        self.mcp_logger.info("=== END MCP USAGE SUMMARY ===")
    
    def collect_mcp_metrics(self) -> Dict:
        """
        Collect MCP metrics for status reporting.
        
        Returns:
            Dict: MCP usage metrics including tool-specific counts
        """
        # Get agent-level metrics
        agent_metrics = self.mcp_usage.copy() if self.mcp_usage else {}
        
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
    
    def discover_and_use_capability(self, capability: str, task_description: str, context: Dict = None) -> Dict:
        """
        FULLY DYNAMIC MCP USAGE - Discover actual tools from MCP servers and use them intelligently.
        
        Args:
            capability: The capability needed (e.g., "reasoning", "documentation")
            task_description: What we're trying to accomplish
            context: Additional context for the task
            
        Returns:
            Dict: Result from using the discovered tool
        """
        if not self.mcp_manager or not self.mcp_manager.is_enabled():
            return {"error": "MCP manager not available or disabled"}
        
        # Find MCP servers with this capability
        servers = self.mcp_manager.get_tools_by_capability(capability)
        if not servers:
            return {"error": f"No MCP servers found with capability: {capability}"}
        
        if self.mcp_logger:
            self.mcp_logger.info(f"Found {len(servers)} servers with '{capability}' capability: {servers}")
        
        # For each server, get the actual tool names available
        all_server_tools = {}
        for server_id in servers:
            actual_tools = self.mcp_manager.get_actual_tool_names(server_id)
            if actual_tools:
                all_server_tools[server_id] = actual_tools
                if self.mcp_logger:
                    tool_names = [t["name"] for t in actual_tools]
                    self.mcp_logger.info(f"Server '{server_id}' has tools: {tool_names}")
        
        if not all_server_tools:
            return {"error": f"No actual tools found on {capability} servers"}
        
        if self.llm_provider:
            # Let LLM intelligently select and use the appropriate tool
            selection_prompt = f"""
            I need to accomplish this task using MCP tools:
            
            TASK: {task_description}
            CONTEXT: {context or {}}
            CAPABILITY NEEDED: {capability}
            
            Available MCP servers and their actual tools:
            {json.dumps(all_server_tools, indent=2)}
            
            Choose the most appropriate tool and construct the call. Consider:
            1. Which tool best matches the task requirements
            2. What parameters the tool's input schema expects
            3. How to format the task description for the tool
            
            Return ONLY a JSON object with this exact format:
            {{
                "server_id": "exact_server_name", 
                "tool_name": "exact_tool_name",
                "arguments": {{
                    "parameter_name": "parameter_value"
                }}
            }}
            """
            
            try:
                selection = self.llm_provider.generate_text(selection_prompt, temperature=0.1)
                # Clean up the response to extract JSON
                selection = selection.strip()
                if selection.startswith("```json"):
                    selection = selection[7:]
                if selection.endswith("```"):
                    selection = selection[:-3]
                
                call_info = json.loads(selection.strip())
                
                server_id = call_info.get("server_id")
                tool_name = call_info.get("tool_name")
                arguments = call_info.get("arguments", {})
                
                if server_id and tool_name:
                    # Use the MCP manager's tool calling method
                    if hasattr(self.mcp_manager, 'call_specific_tool'):
                        result = self.mcp_manager.call_specific_tool(server_id, tool_name, arguments)
                    else:
                        # Fallback to direct tool call
                        result = self.use_mcp_tool(server_id, "tools/call", {
                            "name": tool_name,
                            "arguments": arguments
                        }, justification=f"LLM-selected {capability} tool: {tool_name}")
                    
                    if self.mcp_logger:
                        self.mcp_logger.info(f"Called {capability} tool: {server_id}.{tool_name}")
                    
                    return result
                else:
                    if self.mcp_logger:
                        self.mcp_logger.error(f"Invalid tool selection: {call_info}")
                    
            except json.JSONDecodeError as e:
                if self.mcp_logger:
                    self.mcp_logger.error(f"Failed to parse LLM tool selection: {e}")
                    self.mcp_logger.debug(f"Raw LLM response: {selection}")
            except Exception as e:
                if self.mcp_logger:
                    self.mcp_logger.error(f"Error in LLM tool selection: {e}")
        
        # Fallback: try the first available tool on the first server
        if all_server_tools:
            server_id = list(all_server_tools.keys())[0]
            first_tool = all_server_tools[server_id][0]
            tool_name = first_tool["name"]
            
            if self.mcp_logger:
                self.mcp_logger.warning(f"Falling back to first available tool: {server_id}.{tool_name}")
            
            # Try with basic input format
            basic_args = {"input": task_description}
            
            try:
                if hasattr(self.mcp_manager, 'call_specific_tool'):
                    result = self.mcp_manager.call_specific_tool(server_id, tool_name, basic_args)
                else:
                    result = self.use_mcp_tool(server_id, "tools/call", {
                        "name": tool_name,
                        "arguments": basic_args
                    }, justification=f"Fallback {capability} tool call")
                
                if not result.get("error"):
                    return result
            except Exception as e:
                if self.mcp_logger:
                    self.mcp_logger.error(f"Fallback tool call failed: {e}")
        
        return {"error": f"Could not successfully use any {capability} tools"}

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


    

