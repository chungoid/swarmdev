"""
SwarmDev Collaborative Agent - Ultimate Human-in-the-Loop Experience

This agent provides a conversational interface that can:
- Start and manage workflows in the background
- Maintain persistent memory and context
- Interrupt and resume workflows based on human feedback
- Use MCP tools naturally for enhanced capabilities
- Provide real-time status and progress updates
- Learn user preferences and adapt behavior
"""

import json
import asyncio
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from queue import Queue, Empty
import uuid

from ..goal_processor.builder import SwarmBuilder
from ..utils.llm_provider import LLMProviderInterface
from ..utils.mcp_manager import MCPManager


@dataclass
class ConversationMessage:
    """Represents a message in the conversation."""
    id: str
    timestamp: str
    sender: str  # 'human' or 'agent'
    content: str
    message_type: str  # 'chat', 'status', 'request', 'confirmation'
    context: Dict = None
    attachments: List[Dict] = None


@dataclass
class WorkflowState:
    """Tracks the state of a running workflow."""
    workflow_id: str
    execution_id: str
    status: str  # 'running', 'paused', 'completed', 'failed', 'cancelled'
    progress: Dict
    can_interrupt: bool
    requires_input: bool
    current_phase: str
    started_at: str
    paused_at: Optional[str] = None
    human_input_requested: Optional[str] = None





@dataclass
class ToolRetryState:
    """Track retry attempts for tools."""
    tool_id: str
    last_attempt: float
    consecutive_failures: int
    last_error: str
    cooldown_until: float = 0.0


class CollaborativeAgent:
    """
    Ultimate human-in-the-loop collaborative agent for SwarmDev.
    
    Features:
    - Persistent conversational interface
    - Background workflow execution with real-time monitoring
    - Intelligent interruption and resumption
    - Natural MCP tool usage for enhanced capabilities
    - Learning user preferences and adapting behavior
    - Memory persistence across sessions
    - Enhanced tool retry logic and error recovery
    """
    
    def __init__(self, 
                 llm_provider: LLMProviderInterface,
                 mcp_manager: Optional[MCPManager] = None,
                 project_dir: str = ".",
                 config: Optional[Dict] = None):
        
        self.llm_provider = llm_provider
        self.mcp_manager = mcp_manager
        self.project_dir = project_dir
        self.config = config or {}
        self.verbose = self.config.get("verbose", False)
        
        # Recursion guard to prevent infinite loops
        self._recursion_depth = 0
        self._max_recursion_depth = 3
        
        # Set up logging
        self.logger = logging.getLogger(f"swarmdev.collaborative_agent")
        if self.verbose:
            self.logger.setLevel(logging.DEBUG)
        
        # Session state
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_workflow: Optional[WorkflowState] = None
        self.is_active = False
        
        # Communication state
        self.conversation_history: List[ConversationMessage] = []
        
        # Tool retry management
        self.tool_retry_states: Dict[str, ToolRetryState] = {}
        self.max_retries = 3
        self.base_cooldown = 30.0  # 30 seconds base cooldown
        
        # Build MCP tool catalog (stolen from BaseAgent)
        if self.mcp_manager:
            self.mcp_tool_catalog = self._build_tool_catalog()
        else:
            self.mcp_tool_catalog = {}
        
        # Log MCP tool availability on startup
        self._log_mcp_initialization()
        
        # Core agent state
        self.workflow_builder: Optional[SwarmBuilder] = None
        
        # Communication channels
        self.message_queue = Queue()
        self.response_queue = Queue()
        self.status_callbacks: List[Callable] = []
        
        # Memory and context
        self.conversation_context = []
        
        # Background execution
        self.workflow_thread: Optional[threading.Thread] = None
        self.monitor_thread: Optional[threading.Thread] = None
        
        self.logger.info(f"Collaborative Agent initialized - Session: {self.session_id}")
    
    def _build_tool_catalog(self) -> Dict:
        """Build tool catalog for MCP tools (stolen from BaseAgent)."""
        catalog = {}
        
        if not self.mcp_manager:
            return catalog
        
        available_tools = self.mcp_manager.get_available_tools()
        for tool_id in available_tools:
            try:
                tool_info = self.mcp_manager.get_tool_info(tool_id)
                capabilities = self.mcp_manager.get_server_capabilities(tool_id)
                
                catalog[tool_id] = {
                    "status": "available", 
                    "description": f"MCP tool: {tool_id}",
                    "capabilities": capabilities,
                    "tools": capabilities.get("tools", []) if capabilities else []
                }
            except Exception as e:
                catalog[tool_id] = {
                    "status": "error",
                    "description": f"MCP tool: {tool_id} (failed to load)",
                    "error": str(e)
                }
        
        return catalog
    
    def call_mcp_tool(self, tool_id: str, method_name: str, parameters: Dict, timeout: Optional[int] = None) -> Dict:
        """Call any MCP tool with standard interface (stolen from BaseAgent)."""
        if self.verbose:
            self.logger.info(f"COLLAB DEBUG: call_mcp_tool({tool_id}, {method_name}, {parameters})")
        
        if not self.mcp_manager:
            error = "No MCP manager available"
            if self.verbose:
                self.logger.error(f"COLLAB DEBUG: {error}")
            return {"error": error}
        
        if tool_id not in self.mcp_tool_catalog:
            available = list(self.mcp_tool_catalog.keys())
            error = f"Tool '{tool_id}' not available. Available: {available}"
            if self.verbose:
                self.logger.error(f"COLLAB DEBUG: {error}")
            return {"error": error}
        
        try:
            call_params = {
                "name": method_name,
                "arguments": parameters
            }
            if self.verbose:
                self.logger.info(f"COLLAB DEBUG: Calling mcp_manager.call_tool({tool_id}, 'tools/call', {call_params})")
            
            result = self.mcp_manager.call_tool(
                tool_id, 
                "tools/call", 
                call_params, 
                timeout,
                agent_id="collaborative_agent"
            )
            
            if self.verbose:
                success = result and not result.get("error")
                self.logger.info(f"COLLAB DEBUG: call_mcp_tool result - Success: {success}, Result: {str(result)[:200]}...")
            
            return result
        except Exception as e:
            error = str(e)
            if self.verbose:
                self.logger.error(f"COLLAB DEBUG: Exception in call_mcp_tool: {error}")
            return {"error": error}
    
    def _get_simple_tool_call(self, tool_id: str, message: str) -> tuple:
        """Get simple method name and params for a tool (much simpler than the complex logic)."""
        # Basic tool name and parameter mappings
        tool_mappings = {
            "sequential-thinking": ("sequentialthinking", {
                "thought": f"Help analyze: {message[:200]}",
                "nextThoughtNeeded": False,
                "thoughtNumber": 1,
                "totalThoughts": 1
            }),
            "memory": ("read_graph", {}),
            "time": ("get_current_time", {"timezone": "UTC"}),
            "git": ("git_status", {"repo_path": "."}),
            "fetch": ("fetch", {
                "url": "https://httpbin.org/json",
                "max_length": 1000
            }),
            "filesystem": ("list_directory", {"path": "."}),
            "context7": ("resolve-library-id", {"libraryName": "python"})
        }
        
        if tool_id in tool_mappings:
            return tool_mappings[tool_id]
        else:
            # Generic fallback
            return ("process", {"query": message[:100]})
    
    def _log_mcp_initialization(self):
        """Enhanced MCP initialization logging."""
        if self.verbose and self.mcp_manager:
            self.logger.info(f"COLLABORATIVE AGENT: Initializing with MCP tools")
            available_tools = self.mcp_manager.get_available_tools()
            self.logger.info(f"COLLABORATIVE AGENT: Available MCP tools: {available_tools}")
            
            # Check tool health on startup
            self._check_tool_health()
            
        elif not self.mcp_manager:
            self.logger.info(f"COLLABORATIVE AGENT: No MCP manager provided")
        else:
            available_count = len(self.mcp_manager.get_available_tools()) if self.mcp_manager else 0
            self.logger.info(f"COLLABORATIVE AGENT: Initialized with {available_count} MCP tools")
    
    def _check_tool_health(self):
        """Check the health status of all available tools."""
        if not self.mcp_manager:
            return
            
        available_tools = self.mcp_manager.get_available_tools()
        for tool_id in available_tools:
            try:
                # Quick health check with minimal timeout
                result = self._quick_tool_test(tool_id)
                if result.get("error"):
                    error_msg = result["error"]
                    
                    # Don't immediately penalize tools with known initialization issues
                    if self._is_recoverable_error(error_msg):
                        # Mark as degraded but still usable
                        self._record_degraded_tool(tool_id, error_msg)
                        if self.verbose:
                            self.logger.info(f"Tool {tool_id} has connectivity issues but marked as recoverable: {error_msg}")
                    else:
                        self._record_tool_failure(tool_id, error_msg)
                        if self.verbose:
                            self.logger.warning(f"Tool {tool_id} initial health check failed: {error_msg}")
            except Exception as e:
                error_msg = str(e)
                if self._is_recoverable_error(error_msg):
                    self._record_degraded_tool(tool_id, error_msg)
                else:
                    self._record_tool_failure(tool_id, error_msg)
                if self.verbose:
                    self.logger.warning(f"Tool {tool_id} initial health check exception: {e}")
    
    def _is_recoverable_error(self, error_msg: str) -> bool:
        """Determine if an error is likely recoverable and the tool should remain available."""
        error_lower = error_msg.lower()
        
        # These are typically Docker/container startup issues that may resolve
        recoverable_patterns = [
            "initialization timeout",
            "empty response",
            "connection timeout", 
            "connection refused",
            "container not ready",
            "startup timeout",
            "failed to connect",
            "no response"
        ]
        
        return any(pattern in error_lower for pattern in recoverable_patterns)
    
    def _record_degraded_tool(self, tool_id: str, error: str):
        """Record a tool as degraded but still potentially usable."""
        # Don't put in cooldown, but track the issue
        if tool_id not in self.tool_retry_states:
            self.tool_retry_states[tool_id] = ToolRetryState(
                tool_id=tool_id,
                last_attempt=time.time(),
                consecutive_failures=0,  # Don't count as failure yet
                last_error=error,
                cooldown_until=0.0  # No cooldown for degraded tools
            )
    
    def _quick_tool_test(self, tool_id: str) -> Dict:
        """Perform a quick connectivity test for a tool."""
        simple_tests = {
            "time": {"name": "get_current_time", "arguments": {"timezone": "UTC"}},
            "memory": {"name": "read_graph", "arguments": {}},
            "sequential-thinking": {
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "Quick test",
                    "nextThoughtNeeded": False,
                    "thoughtNumber": 1,
                    "totalThoughts": 1
                }
            },
            "git": {"name": "git_status", "arguments": {"repo_path": "."}},
            "fetch": {"name": "fetch", "arguments": {"url": "https://httpbin.org/json", "max_length": 100}},
            "filesystem": {"name": "list_directory", "arguments": {"path": "."}},
            "context7": {"name": "resolve-library-id", "arguments": {"libraryName": "python"}}
        }
        
        test_params = simple_tests.get(tool_id)
        if not test_params:
            return {"error": "No test available"}
        
        try:
            return self.mcp_manager.call_tool(
                tool_id,
                "tools/call",
                test_params,
                timeout=3
            )
        except Exception as e:
            return {"error": str(e)}
    
    def _record_tool_failure(self, tool_id: str, error: str):
        """Record a tool failure for retry logic."""
        current_time = time.time()
        
        if tool_id not in self.tool_retry_states:
            self.tool_retry_states[tool_id] = ToolRetryState(
                tool_id=tool_id,
                last_attempt=current_time,
                consecutive_failures=1,
                last_error=error
            )
        else:
            state = self.tool_retry_states[tool_id]
            state.consecutive_failures += 1
            state.last_attempt = current_time
            state.last_error = error
            
            # Exponential backoff with jitter
            backoff_time = min(self.base_cooldown * (2 ** (state.consecutive_failures - 1)), 300)  # Cap at 5 minutes
            state.cooldown_until = current_time + backoff_time
    
    def _record_tool_success(self, tool_id: str):
        """Record a tool success, resetting failure count."""
        if tool_id in self.tool_retry_states:
            self.tool_retry_states[tool_id].consecutive_failures = 0
            self.tool_retry_states[tool_id].cooldown_until = 0.0
    
    def _is_tool_in_cooldown(self, tool_id: str) -> bool:
        """Check if a tool is currently in cooldown."""
        if tool_id not in self.tool_retry_states:
            return False
        
        state = self.tool_retry_states[tool_id]
        return time.time() < state.cooldown_until
    
    def _get_available_tools_with_fallbacks(self) -> List[str]:
        """Get available tools, excluding those in cooldown, with fallback suggestions."""
        if not self.mcp_manager:
            return []
        
        all_tools = self.mcp_manager.get_available_tools()
        available_now = []
        
        for tool_id in all_tools:
            if not self._is_tool_in_cooldown(tool_id):
                available_now.append(tool_id)
            elif self.verbose:
                state = self.tool_retry_states.get(tool_id)
                if state:
                    cooldown_remaining = state.cooldown_until - time.time()
                    self.logger.debug(f"Tool {tool_id} in cooldown for {cooldown_remaining:.1f}s more")
        
        return available_now
    
    def _generate_tool_status_fallback(self, attempted_tools: List[str]) -> str:
        """Generate an informative fallback message based on tool status."""
        if not self.mcp_manager:
            return "My external tools aren't available right now. Let me answer based on what I know..."
        
        all_tools = self.mcp_manager.get_available_tools()
        available_tools = self._get_available_tools_with_fallbacks()
        
        # Count different tool states
        working_count = len(available_tools)
        cooldown_count = sum(1 for tool in all_tools if self._is_tool_in_cooldown(tool))
        failed_count = len(all_tools) - working_count
        
        if self.verbose:
            print(f"[DEBUG] Tool status: {working_count} working, {cooldown_count} cooling down, {failed_count} failed")
        
        # Generate appropriate message
        if working_count == 0:
            if cooldown_count > 0:
                return f"My tools are temporarily cooling down after connection issues. I'll retry them automatically in a bit. For now, let me answer based on what I know..."
            else:
                return f"My external tools are having connection issues right now. This usually resolves quickly. Let me answer based on what I know..."
        elif cooldown_count > 0:
            return f"Some of my tools are temporarily unavailable after connection issues, but {working_count} are working. I tried using the best available tools but they had issues. Let me answer based on what I know..."
        else:
            return f"I tried using my tools to help with that, but they're having temporary connection issues. This usually resolves after a moment. Let me answer based on what I know..."
    
    def _get_tool_retry_summary(self) -> str:
        """Get a summary of tool retry states for debugging."""
        if not self.tool_retry_states:
            return "No tool retry history"
        
        summary = []
        current_time = time.time()
        
        for tool_id, state in self.tool_retry_states.items():
            if state.consecutive_failures > 0:
                if state.cooldown_until > current_time:
                    cooldown_remaining = state.cooldown_until - current_time
                    summary.append(f"{tool_id}: {state.consecutive_failures} failures, cooling down for {cooldown_remaining:.1f}s")
                else:
                    summary.append(f"{tool_id}: {state.consecutive_failures} failures, ready to retry")
        
        return "; ".join(summary) if summary else "All tools healthy"
    
    def refresh_tool_health(self) -> str:
        """Manually refresh tool health status and reset cooldowns for recovered tools."""
        if not self.mcp_manager:
            return "No MCP manager available"
        
        print("Refreshing tool health status...")
        
        # Test all tools that are currently in cooldown or have failed
        recovery_results = {}
        tested_count = 0
        recovered_count = 0
        
        for tool_id in self.mcp_manager.get_available_tools():
            state = self.tool_retry_states.get(tool_id)
            
            # Test tools that have had failures or are in cooldown
            if state and (state.consecutive_failures > 0 or self._is_tool_in_cooldown(tool_id)):
                tested_count += 1
                print(f"  → Testing {tool_id}...", end=" ", flush=True)
                
                result = self._quick_tool_test(tool_id)
                if not result.get("error"):
                    print("Recovered!", flush=True)
                    self._record_tool_success(tool_id)
                    recovery_results[tool_id] = "recovered"
                    recovered_count += 1
                else:
                    print("Still failing", flush=True)
                    recovery_results[tool_id] = result["error"]
        
        if tested_count == 0:
            return "All tools are healthy - no refresh needed!"
        
        # Generate summary
        summary = f"Tested {tested_count} tools, {recovered_count} recovered"
        if recovered_count > 0:
            recovered_tools = [tool for tool, status in recovery_results.items() if status == "recovered"]
            summary += f"\nRecovered: {', '.join(recovered_tools)}"
        
        still_failing = [tool for tool, status in recovery_results.items() if status != "recovered"]
        if still_failing:
            summary += f"\nStill having issues: {', '.join(still_failing)}"
        
        return summary
    
    def start_session(self) -> str:
        """Start a new collaborative session."""
        self.is_active = True
        
        # Start monitoring thread for real-time updates
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        # Generate welcome message with context awareness
        welcome = self._generate_contextual_welcome()
        
        self._add_conversation_message("agent", welcome, "chat")
        return welcome
    
    def send_message(self, human_message: str) -> str:
        """
        Send a message to the agent and get a response.
        This is the main interaction method.
        """
        if not self.is_active:
            return "Please start a session first by calling start_session()"
        
        if self.verbose:
            print(f"[DEBUG] send_message called with: {human_message[:50]}...", flush=True)
        
        # Add human message to conversation
        self._add_conversation_message("human", human_message, "chat")
        
        # Analyze message and determine response strategy
        response_strategy = self._analyze_message_intent(human_message)
        if self.verbose:
            print(f"[DEBUG] Message intent analysis: {response_strategy}", flush=True)
        
        # Generate intelligent response based on strategy
        response = self._generate_intelligent_response(human_message, response_strategy)
        
        # Add agent response to conversation
        self._add_conversation_message("agent", response, "chat")
        
        return response
    
    def start_workflow(self, goal: str, workflow_type: str = "standard_project") -> str:
        """Start a workflow in the background while maintaining conversational ability."""
        if self.current_workflow and self.current_workflow.status == "running":
            return "I'm already working on a project. Would you like me to pause it and start something new, or continue with the current work?"
        
        try:
            # Use MCP sequential thinking to plan the workflow approach
            workflow_plan = self._plan_workflow_with_reasoning(goal, workflow_type)
            
            # Create workflow builder
            self.workflow_builder = SwarmBuilder(
                project_dir=self.project_dir,
                goal_file=None,
                config={
                    "workflow": workflow_type,
                    "llm": {"provider": "auto"},
                    "mcp": {"enabled": True}
                }
            )
            
            # Create workflow state
            execution_id = str(uuid.uuid4())
            self.current_workflow = WorkflowState(
                workflow_id=workflow_type,
                execution_id=execution_id,
                status="running",
                progress={},
                can_interrupt=True,
                requires_input=False,
                current_phase="initialization",
                started_at=datetime.now().isoformat()
            )
            
            # Start workflow in background
            self.workflow_thread = threading.Thread(
                target=self._execute_workflow_background,
                args=(goal,),
                daemon=True
            )
            self.workflow_thread.start()
            
            return f"I've started working on your project: '{goal[:50]}...'\n\nI'm running a {workflow_type} workflow in the background. I'll keep you updated on progress and ask for your input when needed. Feel free to chat with me anytime - I can multitask!"
            
        except Exception as e:
            self.logger.error(f"Failed to start workflow: {e}")
            return f"I encountered an issue starting the workflow: {e}. Let me know how you'd like to proceed."
    
    def pause_workflow(self) -> str:
        """Pause the current workflow."""
        if not self.current_workflow or self.current_workflow.status != "running":
            return "No active workflow to pause."
        
        self.current_workflow.status = "paused"
        self.current_workflow.paused_at = datetime.now().isoformat()
        
        return "Workflow paused. I'm here to chat or help with anything else. Just say 'resume' when you're ready to continue."
    
    def resume_workflow(self) -> str:
        """Resume a paused workflow."""
        if not self.current_workflow or self.current_workflow.status != "paused":
            return "No paused workflow to resume."
        
        self.current_workflow.status = "running"
        self.current_workflow.paused_at = None
        
        return "Resuming workflow! I'll pick up where I left off."
    
    def get_status(self) -> Dict:
        """Get comprehensive status of the agent and any running workflows."""
        # Enhanced tool status with retry information
        all_tools = self.mcp_manager.get_available_tools() if self.mcp_manager else []
        available_tools = self._get_available_tools_with_fallbacks()
        cooldown_tools = [tool for tool in all_tools if self._is_tool_in_cooldown(tool)]
        
        status = {
            "session_id": self.session_id,
            "is_active": self.is_active,
            "current_workflow": asdict(self.current_workflow) if self.current_workflow else None,
            "conversation_length": len(self.conversation_context),
            "mcp_tools": {
                "total_available": all_tools,
                "currently_working": available_tools,
                "in_cooldown": cooldown_tools,
                "retry_summary": self._get_tool_retry_summary()
            },
            "conversation_length": len(self.conversation_context)
        }
        
        if self.workflow_builder:
            try:
                workflow_status = self.workflow_builder.get_status()
                status["workflow_details"] = workflow_status
            except:
                pass
        
        return status
    
    def add_feedback(self, feedback: str) -> str:
        """Add user feedback that can influence current or future workflows."""
        # Use MCP reasoning to analyze feedback impact
        feedback_analysis = self._analyze_feedback_with_reasoning(feedback)
        
        # Apply feedback to current workflow if running
        if self.current_workflow and self.current_workflow.status == "running":
            adjustment_response = self._apply_feedback_to_workflow(feedback, feedback_analysis)
            return f"Thanks for the feedback! {adjustment_response}"
        
        return f"I've noted your feedback: '{feedback}'. I'll apply this to future work and remember your preferences."
    
    def stop_session(self) -> str:
        """Stop the session and clean up resources."""
        self.is_active = False
        
        # Pause any running workflow
        if self.current_workflow and self.current_workflow.status == "running":
            self.current_workflow.status = "paused"
        
        return "Session ended. See you next time!"
    
    # Private implementation methods
    

    
    def _generate_contextual_welcome(self) -> str:
        """Generate a contextual welcome message based on session history and current state."""
        
        base_welcome = """Hello! I'm your SwarmDev Collaborative Agent - your intelligent development partner.

I can help you with:
• **Goal Planning** - Refine ideas into actionable projects
• **Workflow Execution** - Run development workflows in the background
• **Real-time Collaboration** - Chat while I work, give feedback, adjust course
• **Smart Tool Usage** - Leverage reasoning, documentation, and research tools
• **Progress Tracking** - Keep you updated every step of the way

"""
        
        # Check for MCP tools
        if self.mcp_manager:
            available_tools = self.mcp_manager.get_available_tools()
            base_welcome += f"\nI have {len(available_tools)} tools ready to help when needed."
        
        base_welcome += "\n\nWhat would you like to work on together? You can start with a goal, ask questions, or just chat!"
        
        return base_welcome
    
    def _analyze_message_intent(self, message: str) -> Dict:
        """Analyze user message to determine intent and response strategy."""
        if not self.llm_provider:
            return {"intent": "general_chat", "confidence": 0.5}
        
        analysis_prompt = f"""
        Analyze this user message to determine intent and response strategy:
        
        MESSAGE: {message}
        
        CURRENT CONTEXT:
        - Active workflow: {self.current_workflow.status if self.current_workflow else "none"}
        - Session length: {len(self.conversation_context)} messages
        - Available tools: {self.mcp_manager.get_available_tools() if self.mcp_manager else "none"}
        
        Determine:
        1. Primary intent (goal_definition, workflow_control, feedback, question, general_chat)
        2. Urgency level (low, medium, high)
        3. Requires workflow action (true/false)
        4. Suggested response approach
        
        Return as JSON with: intent, urgency, workflow_action, approach
        """
        
        try:
            response = self.llm_provider.generate_text(analysis_prompt, temperature=0.1)
            # Try to parse JSON, fallback to default if fails
            try:
                return json.loads(response)
            except:
                pass
        except:
            pass
        
        # Fallback analysis
        message_lower = message.lower()
        if any(word in message_lower for word in ["goal", "project", "build", "create", "develop"]):
            return {"intent": "goal_definition", "urgency": "medium", "workflow_action": True}
        elif any(word in message_lower for word in ["pause", "stop", "resume", "status"]):
            return {"intent": "workflow_control", "urgency": "high", "workflow_action": True}
        elif any(word in message_lower for word in ["feedback", "change", "adjust", "different"]):
            return {"intent": "feedback", "urgency": "medium", "workflow_action": True}
        else:
            return {"intent": "general_chat", "urgency": "low", "workflow_action": False}
    
    def _generate_intelligent_response(self, message: str, strategy: Dict) -> str:
        """Generate an intelligent response based on the message and strategy."""
        if not self.llm_provider:
            return "I understand your message, but I need an LLM provider to give you a detailed response."
        
        # Recursion guard
        self._recursion_depth += 1
        if self._recursion_depth > self._max_recursion_depth:
            self._recursion_depth = 0
            if self.verbose:
                print(f"[DEBUG] Recursion limit reached, using fallback response", flush=True)
            return "I understand your request, but I'm experiencing some processing issues. Let me give you a basic response."
        
        try:
            # Check if this might benefit from MCP tool usage
            should_use_tools = self._should_use_mcp_tools(message, strategy)
            if self.verbose:
                print(f"[DEBUG] _generate_intelligent_response: should_use_tools = {should_use_tools}", flush=True)
            
            if should_use_tools:
                if self.verbose:
                    print(f"[DEBUG] Calling _generate_response_with_tools", flush=True)
                result = self._generate_response_with_tools(message, strategy)
                self._recursion_depth = 0  # Reset on success
                return result
        finally:
            self._recursion_depth -= 1
        
        if self.verbose:
            print(f"[DEBUG] Using standard LLM response (no tools)", flush=True)
        
        # Build context for response generation
        context = self._build_response_context(message, strategy)
        
        response_prompt = f"""
        As SwarmDev's Collaborative Agent, respond to this user message naturally and helpfully:
        
        USER MESSAGE: {message}
        INTENT ANALYSIS: {strategy}
        
        CONTEXT:
        {context}
        
        RESPONSE GUIDELINES:
        - Be conversational and friendly
        - Show awareness of current workflow state
        - Consider if tools could enhance your response (sequential-thinking for analysis, context7 for docs, fetch for research)
        - Offer concrete next steps when appropriate
        - Keep responses focused but comprehensive
        - If suggesting actions, be specific about what I can do
        - Proactively use available tools when they would provide better information or analysis
        
        TOOL USAGE PHILOSOPHY:
        - Default to using tools when they can improve response quality
        - Use sequential-thinking for complex analysis or step-by-step reasoning
        - Use context7 for technical documentation and library information
        - Use fetch for current information and research
        - Combine tools intelligently (e.g., context7 + sequential-thinking for technical analysis)
        
        Generate a helpful, natural response:
        """
        
        try:
            response = self.llm_provider.generate_text(response_prompt, temperature=0.3)
            return response.strip()
        except Exception as e:
            return f"I want to help, but I'm having trouble generating a response right now: {e}"
    
    def _build_response_context(self, message: str, strategy: Dict) -> str:
        """Build context for response generation."""
        context_parts = []
        
        # Current workflow context
        if self.current_workflow:
            context_parts.append(f"Current workflow: {self.current_workflow.status} {self.current_workflow.workflow_id}")
            context_parts.append(f"Phase: {self.current_workflow.current_phase}")
        else:
            context_parts.append("No active workflow")
        
        # Recent conversation context
        if self.conversation_context:
            recent_msgs = self.conversation_context[-3:]  # Last 3 messages
            context_parts.append(f"Recent conversation: {len(recent_msgs)} recent exchanges")
        
        # Enhanced tool awareness
        if self.mcp_manager:
            tools = self.mcp_manager.get_available_tools()
            context_parts.append(f"Available tools for enhanced responses: {', '.join(tools)}")
            context_parts.append("Tool usage philosophy: Be proactive - use tools to provide better, more comprehensive answers")
        

        
        return "\n".join(context_parts)
    
    def _plan_workflow_with_reasoning(self, goal: str, workflow_type: str) -> Dict:
        """Use MCP sequential thinking to plan workflow approach."""
        if not self.mcp_manager or "sequential-thinking" not in self.mcp_manager.get_available_tools():
            return {"plan": "Standard workflow execution", "method": "basic"}
        
        planning_problem = f"""
        Plan the execution approach for this development goal:
        
        GOAL: {goal}
        WORKFLOW TYPE: {workflow_type}
        PROJECT DIRECTORY: {self.project_dir}
        
        Consider:
        1. How to break this down into manageable phases
        2. When to check in with the human for feedback
        3. What information gathering is needed upfront
        4. How to maintain progress visibility
        5. Potential decision points requiring human input
        
        Plan a collaborative approach that maximizes autonomy while keeping human informed and engaged.
        """
        
        try:
            result = self.mcp_manager.call_tool(
                "sequential-thinking",
                "tools/call",
                {
                    "name": "sequential_thinking", 
                    "arguments": {
                        "thought": planning_problem,
                        "nextThoughtNeeded": True,
                        "thoughtNumber": 1,
                        "totalThoughts": 3
                    }
                },
                timeout=20
            )
            
            if not result.get("error"):
                return {"plan": result, "method": "mcp_reasoning"}
        except Exception as e:
            self.logger.warning(f"MCP planning failed: {e}")
        
        return {"plan": "Standard collaborative workflow", "method": "basic"}
    
    def _execute_workflow_background(self, goal: str):
        """Execute workflow in background thread while maintaining responsiveness."""
        try:
            self.logger.info(f"Starting background workflow execution for: {goal[:50]}...")
            
            # Update phase
            self.current_workflow.current_phase = "goal_processing"
            
            # Store goal and start build
            goal_file = f"{self.project_dir}/goal.txt"
            with open(goal_file, 'w') as f:
                f.write(goal)
            
            # Execute build with periodic status updates
            execution_id = self.workflow_builder.build()
            
            # Monitor execution with status callbacks
            self._monitor_workflow_execution(execution_id)
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            if self.current_workflow:
                self.current_workflow.status = "failed"
            
            # Notify user of failure
            self._add_conversation_message(
                "agent", 
                f"I encountered an issue with the workflow: {e}. I'm still here to help - what would you like to do?", 
                "status"
            )
    
    def _monitor_workflow_execution(self, execution_id: str):
        """Monitor workflow execution and provide updates."""
        last_status = None
        
        while self.current_workflow and self.current_workflow.status == "running":
            try:
                # Get current status
                status = self.workflow_builder.get_status()
                
                # Check if status changed significantly
                if status != last_status:
                    self._process_status_update(status)
                    last_status = status
                
                # Check if workflow completed
                if status.get("status") == "completed":
                    self.current_workflow.status = "completed"
                    self._handle_workflow_completion(status)
                    break
                
                # Sleep before next check
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error monitoring workflow: {e}")
                break
    
    def _process_status_update(self, status: Dict):
        """Process workflow status updates and notify user if significant."""
        if not status:
            return
        
        current_phase = status.get("current_task", {}).get("agent_type", "unknown")
        
        # Update workflow state
        if self.current_workflow:
            self.current_workflow.current_phase = current_phase
            self.current_workflow.progress = status
        
        # Determine if this is worth notifying the user about
        if self._should_notify_user(status):
            notification = self._generate_status_notification(status)
            self._add_conversation_message("agent", notification, "status")
    
    def _should_notify_user(self, status: Dict) -> bool:
        """Determine if a status update is worth notifying the user about."""
        # Notify on phase changes, completions, or errors
        phase_changes = ["research", "planning", "development", "documentation"]
        current_task = status.get("current_task", {})
        agent_type = current_task.get("agent_type", "")
        
        return any(phase in agent_type.lower() for phase in phase_changes)
    
    def _generate_status_notification(self, status: Dict) -> str:
        """Generate a friendly status notification for the user."""
        current_task = status.get("current_task", {})
        agent_type = current_task.get("agent_type", "unknown")
        
        phase_messages = {
            "research": "I'm researching technologies and gathering information...",
            "planning": "I'm creating a detailed implementation plan...", 
            "development": "I'm implementing the solution and writing code...",
            "documentation": "I'm creating documentation for the project...",
            "analysis": "I'm analyzing the current state and planning improvements..."
        }
        
        for phase, message in phase_messages.items():
            if phase in agent_type.lower():
                return f"{message}\n\nFeel free to chat with me if you have questions or want to check progress!"
        
        return f"Working on {agent_type} phase... I'll keep you posted!"
    
    def _handle_workflow_completion(self, final_status: Dict):
        """Handle workflow completion and notify user."""
        completion_message = f"""**Workflow Completed!**

I've finished working on your project. Here's what I accomplished:

{self._summarize_workflow_results(final_status)}

The project files are ready in `{self.project_dir}`. Would you like me to:
- Show you what I created
- Start working on improvements  
- Begin a new project
- Just chat about the results

What would you like to do next?"""
        
        self._add_conversation_message("agent", completion_message, "status")
    
    def _summarize_workflow_results(self, status: Dict) -> str:
        """Summarize the results of the completed workflow."""
        if not self.llm_provider:
            return "Project completed successfully"
        
        summary_prompt = f"""
        Create a brief, user-friendly summary of this completed workflow:
        
        STATUS: {json.dumps(status, indent=2)}
        
        Focus on:
        - What was accomplished
        - Key files or components created
        - Notable achievements or features
        
        Keep it concise and celebratory - this is a success message!
        """
        
        try:
            return self.llm_provider.generate_text(summary_prompt, temperature=0.3)
        except:
            return "Project completed with all phases executed successfully!"
    
    def _analyze_feedback_with_reasoning(self, feedback: str) -> Dict:
        """Use MCP reasoning to analyze feedback impact."""
        if not self.mcp_manager or "sequential-thinking" not in self.mcp_manager.get_available_tools():
            return {"analysis": feedback, "method": "basic"}
        
        try:
            result = self.mcp_manager.call_tool(
                "sequential-thinking",
                "tools/call", 
                {
                    "name": "sequential_thinking",
                    "arguments": {
                        "thought": f"Analyze this user feedback and determine how to apply it: {feedback}",
                        "nextThoughtNeeded": False,
                        "thoughtNumber": 1,
                        "totalThoughts": 1
                    }
                },
                timeout=15
            )
            
            if not result.get("error"):
                return {"analysis": result, "method": "mcp_reasoning"}
        except Exception as e:
            self.logger.warning(f"Feedback analysis failed: {e}")
        
        return {"analysis": feedback, "method": "basic"}
    
    def _apply_feedback_to_workflow(self, feedback: str, analysis: Dict) -> str:
        """Apply user feedback to current workflow."""
        if not self.current_workflow or self.current_workflow.status != "running":
            return "I'll remember this feedback for future work."
        
        # For now, log the feedback and acknowledge
        self.logger.info(f"User feedback received: {feedback}")
        
        # In a full implementation, this would:
        # 1. Pause current workflow
        # 2. Analyze feedback impact on current phase
        # 3. Adjust parameters or approach
        # 4. Resume with modifications
        
        return "I've noted your feedback and will adjust my approach accordingly. The workflow continues with your input in mind."
    
    def _monitor_loop(self):
        """Background monitoring loop for real-time updates."""
        while self.is_active:
            try:
                # Check for any status updates to broadcast
                # Process any queued messages
                # Update memory periodically
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")
    
    def _add_conversation_message(self, sender: str, content: str, msg_type: str):
        """Add a message to the conversation history."""
        message = ConversationMessage(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            sender=sender,
            content=content,
            message_type=msg_type
        )
        
        self.conversation_context.append(message)
        

    

    

    

    
    def _should_use_mcp_tools(self, message: str, strategy: Dict) -> bool:
        """Determine if this message would benefit from MCP tool usage."""
        if not self.mcp_manager:
            if self.verbose:
                print("[DEBUG] No MCP manager available")
            return False
        
        message_lower = message.lower()
        available_tools = self._get_available_tools_with_fallbacks()
        
        if self.verbose:
            print(f"[DEBUG] _should_use_mcp_tools called with message: {message[:50]}...")
            print(f"[DEBUG] Available tools (not in cooldown): {available_tools}")
        
        # If no tools available due to cooldowns, skip tool usage
        if not available_tools:
            if self.verbose:
                print(f"[DEBUG] No tools available (all in cooldown)")
            return False
        
        # PROACTIVE APPROACH: Default to using tools unless it's clearly simple chat
        
        # First check for explicit tool name mentions (like "use context7")
        for tool in available_tools:
            tool_name_variations = [
                tool,
                tool.replace("-", " "),
                tool.replace("-", ""),
            ]
            
            for variation in tool_name_variations:
                if variation in message_lower:
                    if self.verbose:
                        print(f"[DEBUG] Found explicit tool mention: {tool} (via '{variation}')")
                    return True
        
        # Skip tools ONLY for very simple greetings and basic chat
        simple_chat_patterns = [
            "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
            "how are you", "what's up", "thanks", "thank you", "bye", "goodbye",
            "ok", "okay", "yes", "no", "sure", "alright"
        ]
        
        # If the message is ONLY a simple greeting, skip tools
        message_clean = message_lower.strip().rstrip('!.?')
        if message_clean in simple_chat_patterns or len(message_clean) < 5:
            if self.verbose:
                print(f"[DEBUG] Detected simple chat, skipping tools: '{message_clean}'")
            return False
        
        # For everything else, consider tools! This makes the agent much more proactive
        proactive_categories = {
            # Technical questions - use context7 for docs + sequential-thinking for analysis
            "technical": ["how", "what", "why", "best way", "how to", "implement", "code", "programming", 
                         "error", "bug", "debug", "optimize", "performance", "security", "database",
                         "api", "framework", "library", "language", "syntax", "function", "method"],
            
            # Research questions - use fetch + sequential-thinking  
            "research": ["research", "find", "lookup", "search", "latest", "current", "recent", "news",
                        "compare", "comparison", "versus", "vs", "difference", "which is better",
                        "recommend", "suggestion", "alternative", "options"],
            
            # Analysis questions - use sequential-thinking
            "analysis": ["analyze", "think about", "consider", "evaluate", "assess", "review",
                        "pros and cons", "advantages", "disadvantages", "trade-offs", "implications",
                        "strategy", "approach", "plan", "solution", "problem", "issue"],
            
            # Documentation requests - use context7
            "documentation": ["documentation", "docs", "manual", "guide", "tutorial", "example",
                             "reference", "specification", "syntax", "usage", "parameters"],
            
            # Memory/context requests - use memory
            "memory": ["remember", "store", "save", "recall", "previous", "earlier", "before",
                      "conversation", "context", "history"]
        }
        
        for category, keywords in proactive_categories.items():
            if any(keyword in message_lower for keyword in keywords):
                if self.verbose:
                    print(f"[DEBUG] Proactive tool usage triggered by {category} category: {[k for k in keywords if k in message_lower]}")
                return True
        
        # For questions (indicated by question words or ?)
        question_indicators = ["what", "how", "why", "when", "where", "who", "which", "can", "could", "would", "should", "is", "are", "do", "does", "?"]
        if any(indicator in message_lower for indicator in question_indicators):
            if self.verbose:
                print(f"[DEBUG] Detected question, enabling proactive tool usage")
            return True
        
        # For longer, substantive messages (likely need analysis/research)
        if len(message.split()) > 10:
            if self.verbose:
                print(f"[DEBUG] Longer message ({len(message.split())} words), enabling proactive tool usage")
            return True
        
        if self.verbose:
            print("[DEBUG] No tool usage indicators found")
        return False
    
    def _generate_response_with_tools(self, message: str, strategy: Dict) -> str:
        """Generate a response using MCP tools with clean UI indicators."""
        try:
            # Show clean tool usage indicator
            if self.verbose:
                print("[DEBUG] Entering tool usage mode")
                print(f"[DEBUG] Message: {message[:100]}...")
                print(f"[DEBUG] Strategy: {strategy}")
            
            # Determine which tools to use
            tools_to_use = self._determine_tools_for_message(message)
            
            if self.verbose:
                print(f"[DEBUG] Tools selected for use: {tools_to_use}")
                available_tools = self.mcp_manager.get_available_tools() if self.mcp_manager else []
                print(f"[DEBUG] All available tools: {available_tools}")
            
            # If no explicit tools mentioned, let LLM decide what tools to use
            if not tools_to_use:
                if self.verbose:
                    print(f"[DEBUG] No explicit tools requested, letting LLM decide")
                return self._generate_response_with_llm_tool_selection(message, strategy)
            
            # Filter tools to only those actually available and not in cooldown
            available_tools = self._get_available_tools_with_fallbacks()
            working_tools = [tool for tool in tools_to_use if tool in available_tools]
            cooldown_tools = [tool for tool in tools_to_use if tool in self.mcp_manager.get_available_tools() and self._is_tool_in_cooldown(tool)]
            unavailable_tools = [tool for tool in tools_to_use if tool not in self.mcp_manager.get_available_tools()]
            
            if unavailable_tools:
                print(f"Note: These tools are not available: {', '.join(unavailable_tools)}")
            if cooldown_tools:
                print(f"Note: These tools are temporarily cooling down: {', '.join(cooldown_tools)}")
            
            if not working_tools:
                if cooldown_tools:
                    return f"The tools I wanted to use are temporarily cooling down after recent issues. Let me answer based on what I know, or you can wait a moment and try again."
                else:
                    return f"The tools I wanted to use are currently unavailable. Let me answer based on what I know..."
            
            results = {}
            for tool_id in working_tools:
                # Show clean, Cursor-style tool usage indicator with immediate flush
                action_description = self._get_tool_action_description(tool_id, message)
                print(f"Using {tool_id} to {action_description}", flush=True)
                
                if self.verbose:
                    print(f"[DEBUG] About to call tool {tool_id}", flush=True)
                    tool_info = self.mcp_manager.get_tool_info(tool_id) if self.mcp_manager else {}
                    print(f"[DEBUG] Tool info: {tool_info}", flush=True)
                
                # Show connection status for better UX
                print(f"  → Connecting to {tool_id}...", end=" ", flush=True)
                
                # Simple summary instead of log spam
                if self.mcp_manager:
                    # Temporarily disable console output for MCP operations
                    import logging
                    mcp_logger = logging.getLogger("swarmdev.mcp")
                    original_level = None
                    for handler in mcp_logger.handlers:
                        if isinstance(handler, logging.StreamHandler):
                            original_level = handler.level
                            handler.setLevel(logging.CRITICAL)  # Suppress console output
                            break
                
                result = self._call_tool_safely(tool_id, message)
                
                # Restore console logging level
                if self.mcp_manager and original_level is not None:
                    for handler in mcp_logger.handlers:
                        if isinstance(handler, logging.StreamHandler):
                            handler.setLevel(original_level)
                            break
                
                # Immediate feedback on connection result
                if result and not result.get("error"):
                    print("✓", flush=True)
                    self._record_tool_success(tool_id)
                else:
                    print("✗", flush=True)
                    error_msg = result.get("error", "unknown error") if result else "no response"
                    self._record_tool_failure(tool_id, error_msg)
                
                if self.verbose:
                    print(f"[DEBUG] Tool {tool_id} returned: {type(result)} with keys: {list(result.keys()) if isinstance(result, dict) else 'not dict'}")
                    if isinstance(result, dict):
                        if result.get("error"):
                            print(f"[DEBUG] Tool error: {result['error']}")
                        else:
                            print(f"[DEBUG] Tool success: {str(result)[:200]}...")
                
                if result and not result.get("error"):
                    results[tool_id] = result
                    # Only show verbose success details in debug mode
                    if self.verbose:
                        success_info = self._get_success_info(tool_id, result)
                        if success_info:
                            print(f"[DEBUG] Success: {success_info}")
                        else:
                            print(f"[DEBUG] Tool completed successfully")
                else:
                    # Show brief error indicator (always visible)
                    error_msg = result.get("error", "unknown error") if result else "no response"
                    if "timeout" in error_msg.lower():
                        print(f"   Warning: Connection timeout - will auto-retry later")
                    elif "retry" in error_msg.lower():
                        print(f"   Warning: Initialization in progress")
                    elif "empty response" in error_msg.lower():
                        print(f"   Warning: Tool not responding - will retry later")
                    else:
                        print(f"   Error: {error_msg[:50]}...")
                        
                    if self.verbose:
                        print(f"[DEBUG] Full error details: {error_msg}")
                        state = self.tool_retry_states.get(tool_id)
                        if state:
                            print(f"[DEBUG] Tool failure count: {state.consecutive_failures}")
                            if state.cooldown_until > time.time():
                                cooldown_remaining = state.cooldown_until - time.time()
                                print(f"[DEBUG] Cooldown period: {cooldown_remaining:.1f}s")
            
            if self.verbose:
                print(f"[DEBUG] Final results: {list(results.keys())}")
            
            # Generate response incorporating tool results
            if results:
                print(f"  → Synthesizing results into response...", end=" ", flush=True)
                response = self._synthesize_tool_results(message, results)
                print("✓", flush=True)
                return response
            else:
                # Generate informative fallback message based on tool status
                return self._generate_tool_status_fallback(working_tools)
                
        except Exception as e:
            if self.verbose:
                print(f"[DEBUG] Exception in tool usage: {e}")
                import traceback
                traceback.print_exc()
            return f"I encountered an issue while using my tools: {e}. Let me try to help without them."
    
    def _determine_tools_for_message(self, message: str) -> List[str]:
        """Determine which tools are most relevant for this message."""
        message_lower = message.lower()
        available_tools = self.mcp_manager.get_available_tools() if self.mcp_manager else []
        
        # Only detect explicit tool name mentions by user
        tools_to_use = []
        for tool in available_tools:
            tool_name_variations = [
                tool,
                tool.replace("-", " "),
                tool.replace("-", ""),
            ]
            
            for variation in tool_name_variations:
                if variation in message_lower:
                    tools_to_use.append(tool)
                    if self.verbose:
                        print(f"[DEBUG] User explicitly requested tool: {tool}")
                    break
        
        # If user explicitly mentioned tools, use only those (limit to 2 for performance)
        if tools_to_use:
            return tools_to_use[:2]
        
        # Otherwise, let the LLM decide which tools to use
        return []
    
    def _call_tool_safely(self, tool_id: str, message: str) -> Dict:
        """Call tool with retry logic using standard MCP interface."""
        if self.verbose:
            self.logger.info(f"COLLAB DEBUG: _call_tool_safely({tool_id}, '{message[:50]}...')")
        
        if tool_id in self.tool_retry_states:
            retry_state = self.tool_retry_states[tool_id]
            
            # Check if tool is in cooldown
            if self._is_tool_in_cooldown(tool_id):
                error = f"Tool {tool_id} is in cooldown"
                if self.verbose:
                    self.logger.warning(f"COLLAB DEBUG: {error}")
                return {"error": error}
        
        # Use simple standard interface with basic tool name mapping
        method_name, params = self._get_simple_tool_call(tool_id, message)
        if self.verbose:
            self.logger.info(f"COLLAB DEBUG: Using method='{method_name}', params={params}")
        
        result = self.call_mcp_tool(tool_id, method_name, params, timeout=15)
        
        if self.verbose:
            success = result and not result.get("error")
            self.logger.info(f"COLLAB DEBUG: _call_tool_safely result - Success: {success}")
            if not success:
                self.logger.error(f"COLLAB DEBUG: Tool call failed: {result.get('error') if result else 'No result'}")
        
        return result
    
    def _call_tool_with_recovery_strategy(self, tool_id: str, message: str, retry_state: ToolRetryState) -> Dict:
        """Call a tool with special recovery strategy for known problematic tools."""
        max_retries = 2  # Try twice for problematic tools
        base_timeout = 15
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                if self.verbose:
                    print(f"  → Retry {attempt}/{max_retries}...", end=" ", flush=True)
                time.sleep(1)  # Brief pause between retries
            
            # Increase timeout for problematic tools
            timeout = base_timeout + (attempt * 5)  # 15, 20, 25 seconds
            
            try:
                result = self._call_tool_standard(tool_id, message, timeout=timeout)
                
                if result and not result.get("error"):
                    # Success! Reset any failure state
                    if self.verbose and attempt > 0:
                        print(f"✓ (recovered on attempt {attempt + 1})", flush=True)
                    return result
                elif attempt < max_retries:
                    # Failed but we have more retries
                    error = result.get("error", "unknown") if result else "no response"
                    if self.verbose:
                        print(f"✗ {error[:30]}...", end=" ", flush=True)
                else:
                    # Final attempt failed
                    return result
                    
            except Exception as e:
                if attempt < max_retries:
                    if self.verbose:
                        print(f"✗ {str(e)[:30]}...", end=" ", flush=True)
                else:
                    return {"error": str(e)}
        
        return {"error": "All retry attempts failed"}
    
    def _call_tool_standard(self, tool_id: str, message: str, timeout: int = 15) -> Dict:
        """Generic tool calling logic that works with any MCP tool."""
        try:
            if self.verbose:
                self.logger.info(f"COLLABORATIVE: Generic tool call for {tool_id}")
            
            # Get tool info dynamically from MCP manager
            tool_info = self.mcp_manager.get_tool_info(tool_id) if self.mcp_manager else {}
            
            # Generate tool call parameters dynamically
            tool_params = self._generate_tool_params(tool_id, message, tool_info)
            
            if not tool_params:
                return {"error": f"Could not generate parameters for tool {tool_id}"}
            
            # Make the generic tool call
            start_time = time.time()
            result = self.mcp_manager.call_tool(
                tool_id,
                "tools/call", 
                tool_params,
                timeout=timeout
            )
            
            elapsed = time.time() - start_time
            if elapsed > 0.5:
                print(f"({elapsed:.1f}s)", end=" ", flush=True)
            
            if self.verbose:
                self.logger.info(f"COLLABORATIVE: Tool {tool_id} returned: {type(result)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"COLLABORATIVE: Tool call failed for {tool_id}: {e}")
            if self.verbose:
                print(f"[DEBUG] Exception in tool call for {tool_id}: {e}")
            return {"error": str(e)}
    
    def _generate_tool_params(self, tool_id: str, message: str, tool_info: Dict) -> Optional[Dict]:
        """Generate appropriate parameters for any MCP tool dynamically."""
        try:
            # Get the first available tool method name from the tool info
            tool_capabilities = tool_info.get("capabilities", {})
            available_tools = tool_capabilities.get("tools", [])
            
            if not available_tools:
                # Fallback: use common tool names based on tool_id
                tool_name = self._guess_tool_name(tool_id)
                if not tool_name:
                    return None
            else:
                # Use the first available tool
                tool_name = available_tools[0].get("name", tool_id)
            
            # Generate basic arguments based on the tool and message
            arguments = self._generate_tool_arguments(tool_id, tool_name, message)
            
            return {
                "name": tool_name,
                "arguments": arguments
            }
            
        except Exception as e:
            if self.verbose:
                print(f"[DEBUG] Failed to generate params for {tool_id}: {e}")
            return None
    
    def _guess_tool_name(self, tool_id: str) -> Optional[str]:
        """Guess appropriate tool name when tool info is not available."""
        # Common patterns for tool names
        name_mappings = {
            "sequential-thinking": "sequential_thinking",
            "time": "get_current_time", 
            "git": "git_status",
            "memory": "read_graph",
            "fetch": "fetch",
            "filesystem": "list_directory",
            "context7": "resolve-library-id"
        }
        return name_mappings.get(tool_id)
    
    def _generate_tool_arguments(self, tool_id: str, tool_name: str, message: str) -> Dict:
        """Generate appropriate arguments for a tool based on context."""
        # Very basic argument generation - can be enhanced
        if "thinking" in tool_name.lower():
            return {
                "thought": f"Help with: {message}",
                "nextThoughtNeeded": False,
                "thoughtNumber": 1,
                "totalThoughts": 1
            }
        elif "time" in tool_name.lower():
            return {}
        elif "git" in tool_name.lower():
            return {"repo_path": "."}
        elif "fetch" in tool_name.lower():
            return {
                "url": "https://httpbin.org/json",
                "max_length": 1000
            }
        elif "list" in tool_name.lower() or "directory" in tool_name.lower():
            return {"path": "."}
        elif "resolve" in tool_name.lower() or "library" in tool_name.lower():
            return {"libraryName": "python"}
        elif "read" in tool_name.lower() and "graph" in tool_name.lower():
            return {}
        else:
            # Generic fallback
            return {"query": message[:100]}
    
    def _estimate_thought_complexity(self, message: str) -> int:
        """Estimate how many thoughts are needed based on message complexity."""
        message_lower = message.lower()
        
        # Simple heuristics for thought count
        complexity_indicators = [
            ("research", 3),
            ("analyze", 3), 
            ("think about", 3),
            ("step by step", 4),
            ("comprehensive", 4),
            ("compare", 3),
            ("pros and cons", 4),
            ("optimal", 4),
            ("best practices", 3),
            ("architecture", 4),
            ("design", 3),
            ("plan", 3)
        ]
        
        max_thoughts = 1
        for indicator, thoughts in complexity_indicators:
            if indicator in message_lower:
                max_thoughts = max(max_thoughts, thoughts)
        
        # Factor in message length
        if len(message) > 200:
            max_thoughts += 1
        if len(message) > 500:
            max_thoughts += 1
            
        return min(max_thoughts, 5)  # Cap at 5 thoughts
    

    
    def _get_tool_action_description(self, tool_id: str, message: str) -> str:
        """Get clean action description for Cursor-style tool usage display."""
        # Generic descriptions based on tool_id patterns
        descriptions = {
            "sequential-thinking": "analyze this request step by step",
            "fetch": "research information online",
            "context7": "look up documentation",
            "memory": "store conversation context", 
            "git": "analyze repository",
            "time": "get current time",
            "filesystem": "read filesystem"
        }
        
        return descriptions.get(tool_id, f"use {tool_id} tool")
    
    def _get_tool_status_info(self, tool_id: str, message: str) -> str:
        """Get contextual status information for a tool."""
        # Generic status descriptions
        status_info = {
            "sequential-thinking": "analyzing request step by step",
            "fetch": "researching online information", 
            "context7": "looking up documentation",
            "memory": "storing conversation context",
            "git": "analyzing repository",
            "time": "getting current time",
            "filesystem": "reading filesystem"
        }
        
        return status_info.get(tool_id, f"processing with {tool_id}")
    
    def _get_success_info(self, tool_id: str, result: Dict) -> str:
        """Get success information from tool results."""
        try:
            if tool_id == "sequential-thinking":
                # Look for thought information in the result
                if "result" in result:
                    thought_data = result["result"]
                    if isinstance(thought_data, dict):
                        thought_num = thought_data.get("thoughtNumber", 1)
                        total_thoughts = thought_data.get("totalThoughts", 1)
                        return f"thought {thought_num} of {total_thoughts} completed"
                return "analysis completed"
            
            elif tool_id == "fetch":
                # Look for URL or data size
                if "result" in result:
                    fetch_result = result["result"]
                    if isinstance(fetch_result, dict):
                        url = fetch_result.get("url", "")
                        if url:
                            return f"fetched data from {url[:30]}..."
                return "web request completed"
            
            elif tool_id == "context7":
                # Look for library information
                if "result" in result:
                    ctx_result = result["result"]
                    if isinstance(ctx_result, dict):
                        lib_id = ctx_result.get("libraryId", "")
                        if lib_id:
                            return f"found docs for {lib_id}"
                return "documentation retrieved"
            
            elif tool_id == "memory":
                # Look for entity creation information
                if "result" in result:
                    memory_result = result["result"]
                    if isinstance(memory_result, dict) and "entities" in memory_result:
                        return f"conversation context saved to memory"
                    elif isinstance(memory_result, list) and len(memory_result) > 0:
                        return f"created {len(memory_result)} memory entities"
                return "context saved"
            
            elif tool_id == "git":
                # Look for git status information
                if "result" in result:
                    git_result = result["result"]
                    if "status" in str(git_result).lower():
                        return "repository status analyzed"
                return "repository analyzed"
            
            elif tool_id == "filesystem":
                # Look for file listing information
                if "result" in result:
                    fs_result = result["result"]
                    if isinstance(fs_result, dict) and "files" in fs_result:
                        file_count = len(fs_result.get("files", []))
                        return f"listed {file_count} files"
                    elif isinstance(fs_result, list):
                        return f"listed {len(fs_result)} items"
                return "filesystem analyzed"
            
            elif tool_id == "time":
                return "timestamp retrieved"
            
            else:
                return "completed successfully"
                
        except Exception:
            return "completed"
    
    def _synthesize_tool_results(self, message: str, results: Dict) -> str:
        """Synthesize tool results into a natural response."""
        if not self.llm_provider:
            return "I used some tools to gather information, but I need an LLM to synthesize the results properly."
        
        # Show progress for synthesis step
        print(f"  → Analyzing {len(results)} tool results...", end=" ", flush=True)
        
        # Extract actual content from MCP tool results
        processed_results = {}
        for tool_id, result in results.items():
            if isinstance(result, dict):
                if "error" in result:
                    processed_results[tool_id] = f"Error: {result['error']}"
                elif "result" in result:
                    # Try to extract meaningful content from the result
                    tool_result = result["result"]
                    if isinstance(tool_result, dict):
                        # For sequential thinking, look for the actual analysis
                        if tool_id == "sequential-thinking":
                            if "reasoning" in tool_result:
                                processed_results[tool_id] = f"Analysis: {tool_result['reasoning']}"
                            elif "guidance" in tool_result:
                                processed_results[tool_id] = f"Guidance: {tool_result['guidance']}"
                            else:
                                processed_results[tool_id] = f"Thinking completed: {str(tool_result)}"
                        else:
                            processed_results[tool_id] = str(tool_result)
                    else:
                        processed_results[tool_id] = str(tool_result)
                else:
                    processed_results[tool_id] = str(result)
            else:
                processed_results[tool_id] = str(result)
        
        # Log what we're synthesizing
        self.logger.info(f"COLLABORATIVE: Synthesizing results from {list(processed_results.keys())}")
        for tool_id, content in processed_results.items():
            self.logger.info(f"COLLABORATIVE: {tool_id} content preview: {content[:100]}...")
        
        synthesis_prompt = f"""
        The user asked: {message}
        
        I used these tools and got these results:
        
        {chr(10).join([f"{tool_id}: {content}" for tool_id, content in processed_results.items()])}
        
        Based on these tool results, provide a helpful, comprehensive response to the user's question. 
        Don't mention the technical details of how the tools work - just synthesize the information naturally.
        If the tools provided analysis or research, incorporate that into your response.
        If any tools failed, don't mention the failures - just work with what succeeded.
        """
        
        try:
            import time  # Import here for timing
            start_time = time.time()
            response = self.llm_provider.generate_text(synthesis_prompt, temperature=0.3)
            elapsed = time.time() - start_time
            if elapsed > 0.5:
                print(f"({elapsed:.1f}s)", end=" ", flush=True)
            return response.strip()
        except Exception as e:
            self.logger.error(f"COLLABORATIVE: Synthesis failed: {e}")
            # Fallback: provide a basic response with the tool results
            if processed_results:
                return f"I gathered some information for you:\n\n" + "\n".join([f"• {content}" for content in processed_results.values()])
            else:
                return "I tried to gather information using my tools, but I'm having trouble right now. Could you rephrase your question?"
    
    def _generate_response_with_llm_tool_selection(self, message: str, strategy: Dict) -> str:
        """Let the LLM decide which tools to use and generate the response."""
        if not self.llm_provider:
            return "I need an LLM provider to help decide which tools to use."
        
        # Additional recursion check for LLM tool selection
        if self._recursion_depth > 2:
            if self.verbose:
                print(f"[DEBUG] LLM tool selection recursion limit, falling back to simple response", flush=True)
            return "I understand your request and will help based on what I know."
        
        # Get all available tools (excluding those in cooldown)
        available_tools = self._get_available_tools_with_fallbacks()
        if not available_tools:
            # Check if tools are in cooldown vs unavailable
            all_tools = self.mcp_manager.get_available_tools() if self.mcp_manager else []
            cooldown_count = sum(1 for tool in all_tools if self._is_tool_in_cooldown(tool))
            if cooldown_count > 0:
                return f"My tools are temporarily cooling down after connection issues. Let me answer based on what I know for now..."
            else:
                return "No tools are available right now. Let me answer based on what I know..."
        
        # Create tool selection prompt with dynamic descriptions
        tool_descriptions = self._get_dynamic_tool_descriptions(available_tools)
        
        tool_info = []
        for tool in available_tools:
            desc = tool_descriptions.get(tool, "General utility tool")
            tool_info.append(f"• {tool}: {desc}")
        
        tool_selection_prompt = f"""
        User request: {message}
        
        Available tools that can enhance your response:
        {chr(10).join(tool_info)}
        
        PROACTIVE TOOL SELECTION STRATEGY:
        You should actively consider using tools to provide better, more comprehensive responses. Think about:
        
        🎯 WHEN TO USE TOOLS:
        - Technical questions → context7 (for docs) + sequential-thinking (for analysis)
        - Research requests → fetch (for current info) + sequential-thinking (for synthesis)
        - Complex analysis → sequential-thinking (for step-by-step reasoning)
        - Programming/coding questions → context7 (for documentation)
        - Questions about "best practices" or "how to" → context7 + sequential-thinking
        - Any question that would benefit from current information → fetch
        - Important conversations → memory (to store context)
        
        🎯 TOOL COMBINATIONS THAT WORK WELL:
        - sequential-thinking + context7: For technical analysis with documentation
        - sequential-thinking + fetch: For research with analysis
        - context7 alone: For straightforward documentation lookups
        - sequential-thinking alone: For complex reasoning without external data
        
        INSTRUCTIONS:
        1. Default to using tools unless it's a very simple greeting or acknowledgment
        2. Choose 1-2 tools that would genuinely improve your response quality
        3. Only respond "NO_TOOLS" for simple chat like greetings, thanks, or yes/no responses
        4. When in doubt, use tools - they almost always improve the response
        
        Response format: Tool names separated by commas (e.g., "sequential-thinking", "context7,sequential-thinking", or "NO_TOOLS")
        
        Decision:
        """
        
        try:
            # Get LLM's tool selection decision
            decision = self.llm_provider.generate_text(tool_selection_prompt, temperature=0.1).strip()
            
            if self.verbose:
                print(f"[DEBUG] LLM tool selection decision: {decision}")
            
            if decision.upper() == "NO_TOOLS":
                # LLM decided no tools needed
                return self._generate_intelligent_response(message, strategy)
            
            # Parse tool selection
            selected_tools = [tool.strip() for tool in decision.split(",")]
            # Validate tools exist
            valid_tools = [tool for tool in selected_tools if tool in available_tools]
            
            if not valid_tools:
                if self.verbose:
                    print(f"[DEBUG] LLM selected invalid tools: {selected_tools}")
                return self._generate_intelligent_response(message, strategy)
            
            if self.verbose:
                print(f"[DEBUG] LLM selected valid tools: {valid_tools}")
            
            # Filter tools to only those actually available
            available_tools = self.mcp_manager.get_available_tools() if self.mcp_manager else []
            working_tools = [tool for tool in valid_tools[:2] if tool in available_tools]
            
            if not working_tools:
                unavailable_tools = [tool for tool in valid_tools[:2] if tool not in available_tools]
                if unavailable_tools:
                    return f"The tools I wanted to use ({', '.join(unavailable_tools)}) are currently unavailable. Let me answer based on what I know..."
                else:
                    return "No tools are currently available. Let me answer based on what I know..."
            
            # Use the available tools
            results = {}
            for tool_id in working_tools:
                action_description = self._get_tool_action_description(tool_id, message)
                print(f"Using {tool_id} to {action_description}", flush=True)
                
                # Show connection status for better UX
                print(f"  → Connecting to {tool_id}...", end=" ", flush=True)
                
                # Suppress MCP console spam during call
                if self.mcp_manager:
                    import logging
                    mcp_logger = logging.getLogger("swarmdev.mcp")
                    original_level = None
                    for handler in mcp_logger.handlers:
                        if isinstance(handler, logging.StreamHandler):
                            original_level = handler.level
                            handler.setLevel(logging.CRITICAL)
                            break
                
                result = self._call_tool_safely(tool_id, message)
                
                # Restore console logging
                if self.mcp_manager and original_level is not None:
                    for handler in mcp_logger.handlers:
                        if isinstance(handler, logging.StreamHandler):
                            handler.setLevel(original_level)
                            break
                
                # Immediate feedback on connection result  
                if result and not result.get("error"):
                    print("✓", flush=True)
                else:
                    print("✗", flush=True)
                
                if result and not result.get("error"):
                    results[tool_id] = result
                    if self.verbose:
                        print(f"[DEBUG] Tool completed successfully")
                else:
                    error_msg = result.get("error", "unknown error") if result else "no response"
                    if "timeout" in error_msg.lower():
                        print(f"   Warning: Connection timeout - will retry next time")
                    elif "retry" in error_msg.lower():
                        print(f"   Warning: Initialization in progress")
                    else:
                        print(f"   Error: {error_msg[:50]}...")
            
            # Generate response with results
            if results:
                print(f"  → Synthesizing results into response...", end=" ", flush=True)
                response = self._synthesize_tool_results(message, results)
                print("✓", flush=True)
                return response
            else:
                return "The tools I tried to use had issues. Let me answer based on what I know..."
                
        except Exception as e:
            if self.verbose:
                print(f"[DEBUG] Exception in LLM tool selection: {e}")
            return self._generate_intelligent_response(message, strategy) 
    
    def _get_dynamic_tool_descriptions(self, available_tools: List[str]) -> Dict[str, str]:
        """Generate tool descriptions dynamically based on available tools."""
        # Basic descriptions that can be enhanced
        base_descriptions = {
            "sequential-thinking": "Advanced step-by-step reasoning and analysis",
            "context7": "Documentation and code examples lookup", 
            "fetch": "Web research and information retrieval",
            "memory": "Conversation context and preferences storage",
            "time": "Current time and date information",
            "git": "Repository analysis and version control",
            "filesystem": "File and directory operations"
        }
        
        # Only return descriptions for available tools
        return {tool: base_descriptions.get(tool, f"{tool} operations") 
                for tool in available_tools}