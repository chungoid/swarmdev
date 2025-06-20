"""
SwarmDev Collaborative Agent - Simple Human-in-the-Loop Experience

A clean, simple conversational agent that:
- Maintains natural conversation with humans
- Uses MCP tools dynamically when helpful (decided by LLM)
- Can start workflows in the background
- No hardcoded tool logic - everything dynamic
"""

import json
import asyncio
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import uuid
import os

from ..goal_processor.builder import SwarmBuilder
from ..utils.llm_provider import LLMProviderInterface
from ..utils.mcp_manager import MCPManager


@dataclass
class ConversationMessage:
    """Simple conversation message."""
    id: str
    timestamp: str
    sender: str  # 'human' or 'agent'
    content: str
    message_type: str = 'chat'


@dataclass
class WorkflowState:
    """Basic workflow tracking."""
    workflow_id: str
    execution_id: str
    status: str  # 'running', 'paused', 'completed', 'failed'
    started_at: str
    goal: str


class CollaborativeAgent:
    """
    Simple collaborative agent for SwarmDev.
    
    Features:
    - Natural conversation interface
    - Dynamic MCP tool usage (LLM decides when/how)
    - Background workflow execution
    - No hardcoded tool logic
    """
    
    def __init__(self, 
                 llm_provider: LLMProviderInterface,
                 mcp_manager: Optional[MCPManager] = None,
                 project_dir: str = None,
                 config: Optional[Dict] = None):
        
        self.llm_provider = llm_provider
        self.mcp_manager = mcp_manager
        self.project_dir = project_dir or os.getcwd()
        self.config = config or {}
        self.verbose = self.config.get("verbose", False)
        
        # Basic state
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.is_active = False
        self.conversation_history: List[ConversationMessage] = []
        self.current_workflow: Optional[WorkflowState] = None
        self.workflow_thread: Optional[threading.Thread] = None
        
        # Setup logging
        self._setup_logging()
        
        self.logger.info(f"Collaborative Agent initialized - Session: {self.session_id}")
    
    def _setup_logging(self):
        """Simple logging setup."""
        logs_dir = os.path.join(self.project_dir, '.swarmdev', 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        self.logger = logging.getLogger(f"swarmdev.collaborative.{self.session_id}")
        
        if not self.logger.handlers:
            handler = logging.FileHandler(os.path.join(logs_dir, 'collaborative.log'))
            formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def start_session(self) -> str:
        """Start a collaborative session."""
        self.is_active = True
        
        welcome = """Hello! I'm your SwarmDev Collaborative Agent.

I can help you with:
• **Planning & Research** - Using my tools to gather information and analyze problems
• **Development Workflows** - Running background processes while we chat
• **Real-time Collaboration** - Ask questions, give feedback, adjust course anytime

"""
        
        if self.mcp_manager:
            available_tools = self.mcp_manager.get_available_tools()
            welcome += f"I have {len(available_tools)} tools ready to enhance our conversation when helpful."
        
        welcome += "\n\nWhat would you like to work on together?"
        
        self._add_message("agent", welcome)
        return welcome
    
    def send_message(self, human_message: str) -> str:
        """Send a message and get response."""
        if not self.is_active:
            return "Please start a session first by calling start_session()"
        
        self._add_message("human", human_message)
        
        # Let LLM decide action (chat, or use tool)
        llm_decision_json_str = self._get_llm_decision(human_message)
        
        try:
            llm_decision = json.loads(llm_decision_json_str)
            agent_action = llm_decision.get("action", {})
            thought = agent_action.get("thought", "Thinking...")
            self.logger.info(f"LLM thought: {thought}")

            initial_response_to_user = agent_action.get("initial_response_to_user", "Let me check on that.")

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM decision JSON: {e}. Raw: {llm_decision_json_str}")
            final_response = "I'm having a little trouble understanding how to proceed. Could you rephrase?"
            self._add_message("agent", final_response)
            return final_response

        if agent_action.get("use_tool"):
            tool_id = agent_action.get("tool_id")
            method_name = agent_action.get("method_name")
            parameters = agent_action.get("parameters", {})
            
            # Normalize keys (convert snake_case to camelCase) for better MCP compatibility
            parameters = self._normalize_param_keys(parameters)
            
            # Show brief initial response
            print(f"Agent: {initial_response_to_user}", flush=True)
            
            if not tool_id or not method_name:
                self.logger.error(f"LLM decided to use a tool but didn't specify tool_id or method_name. Decision: {agent_action}")
                final_response = "I wanted to use one of my tools, but I'm not sure which one or how. Can you clarify?"
            else:
                # Suppress noisy call notice for sequential-thinking to keep chat clean
                if not (tool_id == "sequential-thinking" and method_name == "sequentialthinking"):
                    print(f"{tool_id} call", flush=True)
                
                try:
                    # If sequential-thinking is requested, run a dedicated reasoning chain
                    if tool_id == "sequential-thinking" and method_name == "sequentialthinking":
                        final_response = self._run_sequential_thinking_chain(parameters, human_message)
                    else:
                        # Generic single-call invocation for all other tools
                        self.logger.info(f"DEBUG: Calling {tool_id} with method {method_name} and parameters: {parameters}")
                        tool_result = self.mcp_manager.call_tool(
                            tool_id,
                            "tools/call",
                            {"name": method_name, "arguments": parameters},
                            timeout=60 
                        )
                        # Process tool result
                        if tool_result and not tool_result.get("error"):
                            content = tool_result.get("content", tool_result.get("result", str(tool_result)))
                            if isinstance(content, list) and content:
                                final_response = content[0].get("text", str(content[0])) if isinstance(content[0], dict) else str(content[0])
                            elif isinstance(content, dict):
                                final_response = content.get("text", str(content))
                            else:
                                final_response = str(content)
                        else:
                            self.logger.warning(f"Tool {tool_id} failed with result: {tool_result}, falling back to direct LLM response")
                            fallback_prompt = f"Answer this question directly: {human_message}"
                            try:
                                final_response = self.llm_provider.generate_text(fallback_prompt, temperature=0.3, max_tokens=500)
                                self.logger.info(f"Fallback response generated: {final_response[:100]}...")
                            except Exception:
                                final_response = "I had trouble using my tools and generating a response. Could you try rephrasing your question?"
                        
                except Exception as e:
                    self.logger.error(f"Error calling tool {tool_id}->{method_name}: {e}", exc_info=True)
                    final_response = f"I tried to use the {tool_id} tool, but encountered an error: {e}. I can still try to answer based on what I know."
            
            # Add the substantive final response to conversation
            self._add_message("agent", final_response)
        else:
            # No tool needed, the initial_response_to_user is the final response
            final_response = initial_response_to_user
            self._add_message("agent", final_response)
        
        return final_response
    
    def start_workflow(self, goal: str, workflow_type: str = "standard_project") -> str:
        """Start a workflow in the background."""
        if self.current_workflow and self.current_workflow.status == "running":
            return "I'm already working on a project. Would you like me to pause it and start something new?"
        
        try:
            # Create workflow builder
            self.workflow_builder = SwarmBuilder(
                project_dir=self.project_dir,
                goal_file=None,
                config={"workflow": workflow_type}
            )
            
            # Track workflow
            execution_id = str(uuid.uuid4())
            self.current_workflow = WorkflowState(
                workflow_id=workflow_type,
                execution_id=execution_id,
                status="running",
                started_at=datetime.now().isoformat(),
                goal=goal
            )
            
            # Start in background
            self.workflow_thread = threading.Thread(
                target=self._run_workflow_background,
                args=(goal,),
                daemon=True
            )
            self.workflow_thread.start()
            
            return f"✓ Started working on: '{goal[:50]}...'\n\nI'm running this in the background. Feel free to chat with me anytime!"
            
        except Exception as e:
            return f"Failed to start workflow: {e}"
    
    def get_status(self) -> Dict:
        """Get current status."""
        status = {
            "session_id": self.session_id,
            "is_active": self.is_active,
            "conversation_length": len(self.conversation_history),
            "current_workflow": self.current_workflow.__dict__ if self.current_workflow else None
        }
        
        if self.mcp_manager:
            status["available_tools"] = self.mcp_manager.get_available_tools()
        
        return status
    
    def stop_session(self) -> str:
        """Stop the session."""
        self.is_active = False
        if self.current_workflow and self.current_workflow.status == "running":
            self.current_workflow.status = "paused"
        return "Session ended. See you next time!"
    
    # Private methods
    
    def _add_message(self, sender: str, content: str):
        """Add message to conversation history."""
        message = ConversationMessage(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            sender=sender,
            content=content
        )
        self.conversation_history.append(message)
    
    def _get_llm_decision(self, human_message: str) -> str:
        """
        Generate response, prompting LLM to decide if tools are needed and to specify them in JSON.
        Returns a JSON string.
        """
        recent_context = self._get_recent_context()
        
        tool_catalog_str = "No tools available."
        if self.mcp_manager:
            available_tools = self.mcp_manager.get_available_tools()
            if available_tools:
                detailed_tools = []
                for tool_id in available_tools:
                    try:
                        # Fetch capabilities which include methods and their schemas
                        capabilities = self.mcp_manager.get_server_capabilities(tool_id)
                        tool_info = self.mcp_manager.get_tool_info(tool_id) # For general description
                        
                        tool_description = tool_info.get('description', f'{tool_id} tool')
                        methods_info = []
                        if capabilities and "tools" in capabilities:
                            for method_spec in capabilities["tools"]:
                                methods_info.append({
                                    "name": method_spec.get("name"),
                                    "description": method_spec.get("description"),
                                    "input_schema": method_spec.get("input_schema")
                                })
                        detailed_tools.append({
                            "tool_id": tool_id,
                            "description": tool_description,
                            "methods": methods_info
                        })
                    except Exception as e:
                        self.logger.warning(f"Could not get capabilities for tool {tool_id}: {e}")
                        detailed_tools.append({"tool_id": tool_id, "description": f"{tool_id} (capabilities unavailable)", "methods": []})

                tool_catalog_str = json.dumps(detailed_tools, indent=2)

        prompt = f"""You are SwarmDev's Collaborative Agent. Your task is to analyze the user's message in the context of the ongoing conversation and decide on the best course of action. This might involve a direct textual response or utilizing one of your available tools.

CONVERSATION CONTEXT:
{recent_context}

USER MESSAGE: {human_message}

AVAILABLE TOOLS (with methods and input schemas):
{tool_catalog_str}

TOOL USAGE EXAMPLES:
- sequential-thinking: Use method "sequentialthinking". Provide parameters according to its input_schema (e.g., {{"thought": "step 1", "nextThoughtNeeded": true, "thoughtNumber": 1, "totalThoughts": 10}}).
- filesystem: Use for file operations
- memory: Use for knowledge storage
- fetch: Use for web content

YOUR TASK:
IMPORTANT: Your entire response MUST be a single, valid JSON object. No other text, greetings, or explanations are allowed.

Respond with a single, valid JSON object and NOTHING ELSE. The JSON object must have one top-level key: "action".
The value of "action" should be an object with the following fields:
- "thought": (String) Your brief reasoning for the chosen action.
- "use_tool": (Boolean) true if you decide to use a tool, false otherwise.
- "initial_response_to_user": (String) A message to show to the user immediately. If using a tool, keep this brief like "Analyzing..." or "Working on this..." If not using a tool, this will be your direct answer to the user.
- "tool_id": (String, Optional) If use_tool is true, the ID of the tool to use (e.g., "filesystem").
- "method_name": (String, Optional) If use_tool is true, the specific method of the tool to call (e.g., "list_directory"). Choose from the methods listed in AVAILABLE TOOLS.
- "parameters": (Object, Optional) If use_tool is true, a JSON object of parameters for the chosen method, conforming to its input_schema. Use the TOOL USAGE EXAMPLES above for proper parameter formats.

Ensure your entire output is ONLY the JSON object described. Do not include any other text, greeting, or explanation before or after the JSON.
Response (JSON only):
"""
        try:
            # Get LLM response (which should be a JSON string)
            json_response_str = self.llm_provider.generate_text(prompt, temperature=0.1, max_tokens=1000) # Increased max_tokens
            
            # Attempt to parse and then immediately return if successful
            try:
                json.loads(json_response_str) # Test parsing
                return json_response_str.strip()
            except json.JSONDecodeError as e:
                self.logger.error(f"LLM decision generation failed - JSONDecodeError: {e}. Raw response from LLM: \n---START LLM RAW RESPONSE---\n{json_response_str}\n---END LLM RAW RESPONSE---")
                # Fall through to the generic exception handler if specific logging isn't enough
                raise # Re-raise the exception to be caught by the outer try-except
            
        except Exception as e: # Catches JSONDecodeError if re-raised, or other errors from generate_text
            # Log the beginning of the prompt for context, as it might be very long
            prompt_snippet = prompt[:500] + "..." if len(prompt) > 500 else prompt
            self.logger.error(f"LLM decision generation failed: {e}. Prompt snippet was:\n{prompt_snippet}")
            # Fallback JSON indicating an error or inability to decide
            return json.dumps({
                "action": {
                    "thought": "Error in LLM decision making process.",
                    "use_tool": False,
                    "initial_response_to_user": "I'm having trouble deciding how to respond right now. Could you try rephrasing?"
                }
            })
    
    def _get_recent_context(self) -> str:
        """Get recent conversation context."""
        if not self.conversation_history:
            return "This is the start of our conversation."
        
        recent = self.conversation_history[-6:]  # Last 6 messages
        context_lines = []
        
        for msg in recent:
            context_lines.append(f"{msg.sender}: {msg.content[:200]}...")
        
        return "\n".join(context_lines)
    
    def _run_workflow_background(self, goal: str):
        """Run workflow in background thread."""
        try:
            # Save goal to file
            goal_file = os.path.join(self.project_dir, 'goal.txt')
            with open(goal_file, 'w') as f:
                f.write(goal)
            
            # Execute workflow
            self.workflow_builder.build()
            
            if self.current_workflow:
                self.current_workflow.status = "completed"
            
            # Notify user
            completion_msg = f"✓ Completed workflow for: {goal[:50]}...\n\nCheck your project directory for the results!"
            self._add_message("agent", completion_msg)
            
        except Exception as e:
            if self.current_workflow:
                self.current_workflow.status = "failed"
            
            error_msg = f"✗ Workflow failed: {e}\n\nI'm still here to help in other ways!"
            self._add_message("agent", error_msg)
            
            self.logger.error(f"Workflow execution failed: {e}")

    def _normalize_param_keys(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert snake_case keys to camelCase recursively for MCP tools that expect camelCase."""
        if not isinstance(params, dict):
            return params

        def to_camel(key: str) -> str:
            if '_' not in key:
                return key
            parts = key.split('_')
            return parts[0] + ''.join(p.capitalize() for p in parts[1:])

        normalized = {}
        for k, v in params.items():
            new_key = to_camel(k)
            if isinstance(v, dict):
                v = self._normalize_param_keys(v)  # recurse
            # Convert numeric strings to int when safe
            if isinstance(v, str) and v.isdigit():
                v_converted = int(v)
                v = v_converted
            normalized[new_key] = v
        return normalized

    # ---------------------------------------------------------------------
    # Sequential Thinking helper (LLM-driven loop, no user-visible thoughts)
    # ---------------------------------------------------------------------

    def _run_sequential_thinking_chain(self, initial_params: Dict[str, Any], human_message: str) -> str:
        """Execute a full sequential-thinking loop until nextThoughtNeeded == False.

        The LLM provides the *content* of each next thought; the MCP server merely
        stores bookkeeping. Intermediate thoughts are not shown to the user; only
        the final answer is returned.
        """
        try:
            # Extract initial values
            current_thought = initial_params.get("thought", "Let's think step by step.")
            thought_number = int(initial_params.get("thoughtNumber", 1))
            total_thoughts = int(initial_params.get("totalThoughts", 20))
            next_needed = bool(initial_params.get("nextThoughtNeeded", True))

            history: List[str] = []
            max_steps = 50  # safety cap

            while True:
                # Send current thought to the MCP server
                tool_args = {
                    "thought": current_thought,
                    "nextThoughtNeeded": next_needed,
                    "thoughtNumber": thought_number,
                    "totalThoughts": total_thoughts
                }
                self.logger.debug(f"Sequential-thinking call #{thought_number}: {current_thought[:80]}…")

                result = self.mcp_manager.call_tool(
                    "sequential-thinking",
                    "tools/call",
                    {"name": "sequentialthinking", "arguments": tool_args},
                    timeout=60
                )

                # If the tool itself errors, break and fallback
                if not result or result.get("error"):
                    self.logger.warning(f"Sequential-thinking server error: {result}")
                    break

                history.append(current_thought)

                # Parse bookkeeping response; we only care about flags / numbers
                payload = result.get("content", result.get("result", {}))
                if isinstance(payload, list) and payload:
                    payload = payload[0].get("text", payload[0]) if isinstance(payload[0], dict) else payload[0]
                if isinstance(payload, str):
                    try:
                        payload = json.loads(payload)
                    except json.JSONDecodeError:
                        payload = {}

                # Check if more thinking required
                next_needed = bool(payload.get("nextThoughtNeeded", False))
                if not next_needed or thought_number >= max_steps:
                    # Ask LLM to craft the final answer using the accumulated history
                    summary_prompt = (
                        f"We have finished a sequential reasoning chain for the user question below.\n"
                        f"Question: {human_message}\n\n"
                        f"Reasoning steps:\n" + "\n".join(f"Step {i+1}: {s}" for i, s in enumerate(history)) + "\n\n"
                        "Provide a concise, helpful answer to the user without exposing the internal steps."
                    )
                    try:
                        final_ans = self.llm_provider.generate_text(summary_prompt, temperature=0.3, max_tokens=400).strip()
                    except Exception as e:
                        self.logger.warning(f"LLM summarization failed: {e}. Falling back to direct answer.")
                        final_ans = ""

                    # Robust fallback: if LLM returned blank, answer directly without chain history
                    if not final_ans:
                        # Secondary attempt: ask LLM to answer directly without history.
                        try:
                            final_ans = self.llm_provider.generate_text(
                                f"Answer the question directly (sequential-thinking summary failed): {human_message}",
                                temperature=0.3,
                                max_tokens=2000
                            ).strip()
                        except Exception as e:
                            self.logger.error(f"Direct answer generation after sequential-thinking failed: {e}")
                            # Fail LOUD: return explicit error message so issue is visible to user.
                            raise RuntimeError("Sequential-thinking completed but summary generation failed. Check logs for details.")

                    return final_ans

                # Otherwise ask LLM for the next thought
                guidance_prompt = (
                    f"We are answering the user question: {human_message}\n\n"
                    f"Completed thoughts so far:\n" + "\n".join(f"Step {i+1}: {s}" for i, s in enumerate(history)) + "\n\n"
                    "Based on these, provide the *next* thought needed to continue the analysis, no more than two sentences.\n"
                    "Respond ONLY in JSON with keys: 'thought' (string), 'nextThoughtNeeded' (boolean)."
                )
                llm_json = self.llm_provider.generate_text(guidance_prompt, temperature=0.3, max_tokens=150)
                try:
                    parsed = json.loads(llm_json)
                    current_thought = parsed.get("thought", "Continue analysis…")
                    next_needed = bool(parsed.get("nextThoughtNeeded", False))
                except json.JSONDecodeError:
                    # If LLM didn't output valid JSON, fallback to simple continue or end
                    self.logger.warning(f"LLM returned invalid JSON for next thought: {llm_json}")
                    next_needed = False
                thought_number += 1

            # If loop breaks due to errors, fallback to direct answer
            fallback = self.llm_provider.generate_text(
                f"Answer the question directly: {human_message}", temperature=0.3, max_tokens=400)
            return fallback.strip()

        except Exception as e:
            self.logger.error(f"Unexpected error in sequential-thinking chain: {e}")
            return "I ran into an error while reasoning. Could you rephrase or try again?"