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
                
                # Test key tools for this agent type
                self._test_agent_mcp_tools()
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
                self.mcp_logger.info(f"🎯 CACHE HIT: {tool_id}.{method} - using cached result")
            return cached_result
        
        self.mcp_usage["cache_misses"] += 1
        
        # INTELLIGENT THROTTLING
        if self._should_throttle_call(tool_id, method, params, justification):
            self.mcp_usage["throttled_calls"] += 1
            throttle_msg = f"🚫 THROTTLED: {tool_id}.{method} - excessive usage detected"
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
                self.mcp_logger.error(f"❌ MCP CALL FAILED: {tool_id}")
                self.mcp_logger.error(f"Error: {result['error']}")
                self.mcp_logger.error(f"Duration: {duration:.2f}s")
        else:
            self.mcp_usage["successful_calls"] += 1
            # CACHE SUCCESSFUL RESULTS
            self._cache_result(cache_key, result, tool_id, method, params)
            if self.mcp_logger:
                self.mcp_logger.info(f"✅ MCP CALL SUCCESS: {tool_id}")
                self.mcp_logger.info(f"Duration: {duration:.2f}s")
                self.mcp_logger.info(f"Cached for future use")
        
        if self.mcp_logger:
            self.mcp_logger.debug(f"Full response: {json.dumps(result, indent=2)}")
        
        return result
    
    def _generate_cache_key(self, tool_id: str, method: str, params: Dict) -> str:
        """Generate a cache key for this MCP call."""
        import hashlib
        
        # For documentation tools, key by library name only
        if 'context7' in tool_id or 'documentation' in tool_id:
            if method == "resolve-library-id":
                library_name = params.get("libraryName", "unknown")
                return f"doc_resolve_{library_name}"
            elif method == "get-library-docs":
                library_id = params.get("context7CompatibleLibraryID", "unknown")
                topic = params.get("topic", "general")
                return f"doc_get_{library_id}_{topic}"
        
        # For sequential thinking, hash the problem text
        if 'sequential' in tool_id and method == "sequentialthinking":
            thought = params.get("thought", "")
            if len(thought) > 100:
                problem_hash = hashlib.md5(thought.encode()).hexdigest()[:12]
                return f"thinking_{problem_hash}"
        
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
        
        # Sequential thinking caching  
        if cache_key.startswith("thinking_"):
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
                self.mcp_logger.debug(f"📚 Cached documentation: {cache_key}")
        
        # Sequential thinking caching
        elif cache_key.startswith("thinking_"):
            cache["sequential_thinking"][cache_key] = result
            if self.mcp_logger:
                self.mcp_logger.debug(f"🧠 Cached thinking result: {cache_key}")
    
    def _should_throttle_call(self, tool_id: str, method: str, params: Dict, justification: str) -> bool:
        """Intelligent throttling to prevent wasteful MCP usage."""
        cache = BaseAgent._execution_cache
        current_count = cache["call_counts"].get(tool_id, 0)
        
        # CONTEXT7/DOCUMENTATION THROTTLING: Max 3 calls per unique library
        if 'context7' in tool_id or 'documentation' in tool_id:
            if method == "resolve-library-id":
                library_name = params.get("libraryName", "unknown")
                library_calls = sum(1 for key in cache["documentation"].keys() 
                                  if key.startswith(f"doc_resolve_{library_name}"))
                if library_calls >= 2:  # Already resolved this library
                    return True
            
            elif method == "get-library-docs":
                library_id = params.get("context7CompatibleLibraryID", "unknown")
                lib_doc_calls = sum(1 for key in cache["documentation"].keys() 
                                  if key.startswith(f"doc_get_{library_id}"))
                if lib_doc_calls >= 3:  # Max 3 doc calls per library
                    return True
        
        # SEQUENTIAL THINKING THROTTLING: Max 20 calls per execution
        if 'sequential' in tool_id and current_count >= 20:
            if not justification or len(justification) < 20:
                return True  # Require good justification for >20 calls
        
        # GENERAL THROTTLING: Max 50 calls per tool per execution
        if current_count >= 50:
            return True
        
        return False
    
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
            
            # USE UNIFIED INTERFACE with justification
            justification = f"Sequential thinking for: {problem[:50]}..."
            result = self.use_mcp_tool(reasoning_tool, "tools/call", {
                "name": "sequentialthinking",
                "arguments": params
            }, justification=justification)
            
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
            
            # First resolve the library ID using UNIFIED INTERFACE
            justification = f"Resolving library ID for: {library_name}"
            resolve_result = self.use_mcp_tool(doc_tool, "tools/call", {
                "name": "resolve-library-id",
                "arguments": {"libraryName": library_name}
            }, justification=justification)
            
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
            
            # Get the documentation using UNIFIED INTERFACE
            doc_params = {"context7CompatibleLibraryID": library_id}
            if topic:
                doc_params["topic"] = topic
            
            justification = f"Getting docs for {library_name} ({library_id})" + (f" topic: {topic}" if topic else "")
            doc_result = self.use_mcp_tool(doc_tool, "tools/call", {
                "name": "get-library-docs", 
                "arguments": doc_params
            }, justification=justification)
            
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
    
    def _read_project_files(self, project_dir: str) -> Dict:
        """Read all files in the project directory with enhanced analysis."""
        import os
        
        files = {}
        total_files = 0
        total_lines = 0
        
        try:
            for root, dirs, filenames in os.walk(project_dir):
                # Skip hidden directories and common ignore patterns
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.git']]
                
                for filename in filenames:
                    if filename.startswith('.'):
                        continue
                        
                    file_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_path, project_dir)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            lines = content.count('\n') + 1
                            
                        files[relative_path] = {
                            "content": content,
                            "lines": lines,
                            "size": len(content),
                            "extension": os.path.splitext(filename)[1],
                            "directory": os.path.dirname(relative_path)
                        }
                        
                        total_files += 1
                        total_lines += lines
                        
                    except Exception as e:
                        self.logger.warning(f"Could not read file {relative_path}: {e}")
                        continue
            
            # Perform structure analysis using the existing files
            structure_analysis = self._analyze_project_structure_with_llm(files)
            
            self.logger.info(f"Read {total_files} files with {total_lines} total lines")
            
            return {
                "files": files,
                "total_files": total_files,
                "total_lines": total_lines,
                "structure_analysis": structure_analysis
            }
            
        except Exception as e:
            self.logger.error(f"Error reading project files: {e}")
            return {
                "files": {},
                "total_files": 0,
                "total_lines": 0,
                "structure_analysis": {"status": "error", "issues": [f"Failed to read project: {e}"]}
            }
    
    def _analyze_project_structure_with_llm(self, existing_files: Dict) -> Dict:
        """Analyze project structure using LLM to identify issues and recommendations."""
        if not existing_files:
            return {
                "status": "empty",
                "issues": ["No files found in project"],
                "recommendations": ["Create initial project structure"]
            }
        
        # Prepare file structure summary for analysis
        file_structure = ""
        for file_path, file_info in existing_files.items():
            file_structure += f"- {file_path} ({file_info.get('lines', 0)} lines, {file_info.get('extension', 'no ext')})\n"
        
        prompt = f"""
        Analyze this project structure and identify any issues or improvements needed:
        
        PROJECT FILES:
        {file_structure}
        
        Please analyze for:
        1. Duplicate folder structures (e.g., python/python/, src/src/)
        2. Files in wrong locations for their type
        3. Missing important structure files (like __init__.py for Python)
        4. Inconsistent organization patterns
        5. Potential improvements to project organization
        
        Respond in this format:
        STATUS: [good/needs_improvement/poor]
        
        ISSUES:
        - [list any structural issues found]
        
        RECOMMENDATIONS:
        - [list specific recommendations]
        
        DUPLICATE_PATHS:
        - [list any duplicate folder structures]
        """
        
        try:
            if self.llm_provider:
                response = self.llm_provider.generate(prompt, max_tokens=1000)
                return self._parse_structure_analysis(response)
            else:
                return {
                    "status": "unknown",
                    "issues": ["No LLM provider available for analysis"],
                    "recommendations": ["Manual review recommended"]
                }
        except Exception as e:
            self.logger.error(f"Error analyzing project structure: {e}")
            return {
                "status": "unknown",
                "issues": [f"Analysis failed: {e}"],
                "recommendations": ["Manual review recommended"]
            }
    
    def _parse_structure_analysis(self, analysis_response: str) -> Dict:
        """Parse the structure analysis response from LLM."""
        result = {
            "status": "unknown",
            "issues": [],
            "recommendations": [],
            "duplicate_paths": []
        }
        
        try:
            lines = analysis_response.strip().split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('STATUS:'):
                    result["status"] = line.split(':', 1)[1].strip().lower()
                elif line.startswith('ISSUES:'):
                    current_section = "issues"
                elif line.startswith('RECOMMENDATIONS:'):
                    current_section = "recommendations"
                elif line.startswith('DUPLICATE_PATHS:'):
                    current_section = "duplicate_paths"
                elif line.startswith('- ') and current_section:
                    item = line[2:].strip()
                    if item:
                        result[current_section].append(item)
            
        except Exception as e:
            self.logger.error(f"Error parsing structure analysis: {e}")
        
        return result
    
    def _detect_target_technology(self) -> str:
        """Detect the target technology based on goal and context."""
        # This can be overridden by specific agents or enhanced with more logic
        goal_text = getattr(self, '_current_goal', '').lower()
        
        # Technology detection patterns
        if any(keyword in goal_text for keyword in ['python', 'django', 'flask', 'fastapi', 'pandas']):
            return "python"
        elif any(keyword in goal_text for keyword in ['javascript', 'js', 'node', 'react', 'vue', 'angular']):
            return "javascript"
        elif any(keyword in goal_text for keyword in ['web', 'html', 'css', 'website', 'frontend']):
            return "web"
        elif any(keyword in goal_text for keyword in ['java', 'spring', 'maven']):
            return "java"
        elif any(keyword in goal_text for keyword in ['c++', 'cpp', 'cmake']):
            return "cpp"
        else:
            return "python"  # Default to Python
    
    def _get_file_extension_for_technology(self, technology: str) -> str:
        """Get the appropriate file extension for a technology."""
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "web": ".html",
            "java": ".java",
            "cpp": ".cpp",
            "typescript": ".ts",
            "go": ".go",
            "rust": ".rs"
        }
        return extensions.get(technology, ".py")
    
    def _format_files_for_analysis(self, project_files: Dict) -> str:
        """Format project files for LLM analysis."""
        if not project_files:
            return "No files found in project."
        
        formatted = "PROJECT FILES:\n"
        for file_path, file_info in project_files.items():
            lines = file_info.get('lines', 0)
            size = file_info.get('size', 0)
            ext = file_info.get('extension', '')
            formatted += f"- {file_path} ({lines} lines, {size} bytes, {ext})\n"
        
        return formatted

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
