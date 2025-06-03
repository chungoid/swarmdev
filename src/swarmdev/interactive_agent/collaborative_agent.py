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

        # Add agent's initial response (or action intent) to history
        # This makes the conversation flow more naturally
        self._add_message("agent", initial_response_to_user) 
        print(f"Agent: {initial_response_to_user}") # Also print to console for immediate feedback

        if agent_action.get("use_tool"):
            tool_id = agent_action.get("tool_id")
            method_name = agent_action.get("method_name")
            parameters = agent_action.get("parameters", {})
            
            if not tool_id or not method_name:
                self.logger.error(f"LLM decided to use a tool but didn't specify tool_id or method_name. Decision: {agent_action}")
                final_response = "I wanted to use one of my tools, but I'm not sure which one or how. Can you clarify?"
            else:
                print(f"Using {tool_id}->{method_name} with params: {json.dumps(parameters, indent=2)}", flush=True)
                try:
                    # Standard tool calling - no special cases
                    tool_result = self.mcp_manager.call_tool(
                        tool_id,
                        "tools/call",
                        {"name": method_name, "arguments": parameters},
                        timeout=25 
                    )
                    print(f"Tool {tool_id} result (or final accumulated): {json.dumps(tool_result, indent=2)}", flush=True) # Ensure this prints the final result
                    final_response = self._synthesize_final_response(human_message, initial_response_to_user, tool_id, method_name, tool_result)
                except Exception as e:
                    self.logger.error(f"Error calling tool {tool_id}->{method_name}: {e}", exc_info=True)
                    final_response = f"I tried to use the {tool_id} tool, but encountered an error: {e}. I can still try to answer based on what I know."
        else:
            # No tool needed, the initial_response_to_user is the final response
            final_response = initial_response_to_user
            
        # If the final response differs from the initial one (e.g., after tool use),
        # it might be good to add it as a new message or update the last one.
        # For simplicity now, we'll assume the initial response was a placeholder if a tool was used.
        # If no tool was used, initial_response_to_user IS the final_response.
        # If a tool was used, the last message added was the "I'm using tool X" type message.
        # So, we add the actual final response now.
        if agent_action.get("use_tool"):
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

YOUR TASK:
IMPORTANT: Your entire response MUST be a single, valid JSON object. No other text, greetings, or explanations are allowed.

Respond with a single, valid JSON object and NOTHING ELSE. The JSON object must have one top-level key: "action".
The value of "action" should be an object with the following fields:
- "thought": (String) Your brief reasoning for the chosen action.
- "use_tool": (Boolean) true if you decide to use a tool, false otherwise.
- "initial_response_to_user": (String) A message to show to the user immediately. If using a tool, this could be "Okay, I'll use [tool_name] to [action_description]." If not using a tool, this will be your direct answer to the user.
- "tool_id": (String, Optional) If use_tool is true, the ID of the tool to use (e.g., "filesystem").
- "method_name": (String, Optional) If use_tool is true, the specific method of the tool to call (e.g., "list_directory"). Choose from the methods listed in AVAILABLE TOOLS.
- "parameters": (Object, Optional) If use_tool is true, a JSON object of parameters for the chosen method, conforming to its input_schema.

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
    
    def _synthesize_final_response(self, original_human_message: str, agent_initial_utterance: str, tool_id: str, method_name: str, tool_result: Dict) -> str:
        """Create final response incorporating tool results."""
        if not self.llm_provider:
            # Simple fallback if no LLM
            if tool_result and not tool_result.get("error"):
                return f"{agent_initial_utterance}\nTool {tool_id} ({method_name}) completed. Result: {str(tool_result)[:300]}..."
            else:
                return f"{agent_initial_utterance}\nTool {tool_id} ({method_name}) encountered an issue: {tool_result.get('error', 'Unknown error')}."

        tool_output_for_prompt = json.dumps(tool_result, indent=2)

        synthesis_prompt = f"""You are SwarmDev's Collaborative Agent.
The user originally said: "{original_human_message}"
You initially responded: "{agent_initial_utterance}" (indicating you might use a tool).
You then used the tool '{tool_id}' with method '{method_name}'.

The tool execution resulted in:
{tool_output_for_prompt}

Based on the original request, your initial response, and the tool's result, formulate a concise and helpful final response to the user.
- If the tool was successful, integrate its findings naturally.
- If the tool failed, acknowledge the specific error transparently and suggest alternatives.
- Do not explicitly say "The tool returned...". Instead, incorporate the information naturally.
- Be conversational and helpful.

Final response to user:
"""
        
        try:
            final_response = self.llm_provider.generate_text(synthesis_prompt, temperature=0.3, max_tokens=700)
            return final_response.strip()
        except Exception as e:
            self.logger.error(f"Final response synthesis failed: {e}")
            # Standard fallback for all tools
            return f"{agent_initial_utterance}\nI've processed the information from the {tool_id} tool. {str(tool_result)[:200]}..."
    
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