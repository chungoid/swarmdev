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
                    if tool_id == "sequential-thinking" and method_name == "sequentialthinking":
                        accumulated_thought_content = []
                        current_params = parameters.copy()
                        
                        # LLM provides the initial thoughtNumber (e.g., 1)
                        # LLM provides initial totalThoughts and nextThoughtNeeded
                        
                        # Ensure thoughtNumber is an int for loop increment.
                        # Robustly get parameters, checking for different casings LLM might use.
                        def get_param_robustly(p_dict, keys, default_val, target_type=None):
                            for key in keys:
                                if key in p_dict:
                                    val = p_dict[key]
                                    if target_type:
                                        try:
                                            return target_type(val)
                                        except ValueError:
                                            self.logger.warning(f"Invalid type for param {key}, expected {target_type}, got {val}. Using default.")
                                            return default_val
                                    return val
                            return default_val

                        current_thought_number = get_param_robustly(current_params, ["thoughtNumber", "thought_number"], 1, int)
                        max_steps = get_param_robustly(current_params, ["totalThoughts", "total_thoughts"], 1, int)
                        loop_next_thought_needed = get_param_robustly(current_params, ["nextThoughtNeeded", "next_thought_needed"], True, bool)
                        
                        current_params["thoughtNumber"] = current_thought_number # Normalize for tool call
                        current_params["totalThoughts"] = max_steps           # Normalize for tool call
                        current_params["nextThoughtNeeded"] = loop_next_thought_needed # Normalize for tool call

                        self.logger.info(f"Starting sequential-thinking loop. Initial params (normalized): {current_params}, Max steps: {max_steps}, Initial next_needed: {loop_next_thought_needed}")

                        for step in range(max_steps):
                            if not loop_next_thought_needed and step > 0: # only break if not the first iteration and explicitly told to stop
                                self.logger.info(f"Sequential thinking loop breaking: nextThoughtNeeded is false after step {step}.")
                                break

                            current_params["thoughtNumber"] = current_thought_number # Update thoughtNumber for the current call
                            
                            self.logger.info(f"Calling sequential-thinking step {current_thought_number}/{max_steps}, params: {json.dumps(current_params)}")
                            tool_step_result = self.mcp_manager.call_tool(
                                tool_id,
                                "tools/call",
                                {"name": method_name, "arguments": current_params},
                                timeout=35 
                            )
                            self.logger.info(f"Sequential-thinking step {current_thought_number} result: {json.dumps(tool_step_result)}")

                            raw_text_from_tool = ""
                            if tool_step_result.get("result", {}).get("content"):
                                for item_content in tool_step_result["result"]["content"]:
                                    if item_content.get("type") == "text" and item_content.get("text"):
                                        raw_text_from_tool = item_content["text"]
                                        break
                            
                            if not raw_text_from_tool:
                                accumulated_thought_content.append(f"[Thought {current_thought_number}: No text content returned]")
                                self.logger.warning(f"No text content from sequential-thinking step {current_thought_number}")
                                # Decide if we should stop if no content
                                loop_next_thought_needed = False # Stop if tool returns nothing
                                continue

                            try:
                                # Try to parse as JSON to get control signals like nextThoughtNeeded
                                status_data = json.loads(raw_text_from_tool)
                                loop_next_thought_needed = status_data.get("nextThoughtNeeded", False)
                                # If it's JSON, it's status. The actual thought might be missing or elsewhere.
                                # For now, we'll log this status as part of the accumulated content.
                                accumulated_thought_content.append(f"[Thought {current_thought_number} Status: {raw_text_from_tool}]")
                                if "totalThoughts" in status_data and int(status_data["totalThoughts"]) != max_steps:
                                    self.logger.info(f"Tool updated totalThoughts from {max_steps} to {status_data['totalThoughts']}")
                                    max_steps = int(status_data["totalThoughts"]) # Allow tool to guide total length

                            except json.JSONDecodeError:
                                # Not JSON, assume it's the actual thought content for this step
                                accumulated_thought_content.append(raw_text_from_tool)
                                # If we get raw text, assume the tool might not be providing nextThoughtNeeded explicitly in this response,
                                # so we continue based on max_steps or if a previous JSON status set nextThoughtNeeded.
                                # If nextThoughtNeeded was not updated by a JSON status, it keeps its previous value.
                                # If it was never true (e.g. LLM said nextThoughtNeeded=false initially), loop wouldn't run past first step if step > 0.

                            current_thought_number += 1
                        
                        tool_result = {
                            "type": "sequential_thinking_output",
                            "steps_taken": current_thought_number - parameters.get("thoughtNumber", 1), # How many steps we actually ran
                            "initial_prompt": parameters.get("thought"),
                            "accumulated_thoughts": accumulated_thought_content
                        }
                        self.logger.info(f"Sequential-thinking loop completed. Result for synthesis: {json.dumps(tool_result, indent=2)}")

                    else:
                        # Standard single-call tool logic
                        tool_result = self.mcp_manager.call_tool(
                            tool_id,
                            "tools/call",
                            {"name": method_name, "arguments": parameters},
                            timeout=25 
                        )
                    print(f"Tool {tool_id} result (or final accumulated): {json.dumps(tool_result, indent=2)}", flush=True) # Ensure this prints the final result
                    final_response = self._synthesize_final_response(human_message, initial_response_to_user, tool_id, method_name, tool_result)
                except Exception as e:
                    self.logger.error(f"Error calling tool {tool_id}->{method_name} or in sequential_thinking loop: {e}", exc_info=True)
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

GUIDANCE ON ASSISTING WITH GOAL REFINEMENT:
- If the user is asking for ways to expand, refine, brainstorm about a goal (like `goal.txt`), or asking for ideas for features/tools/libraries, this IS an actionable task.
- You SHOULD use your tools to help. For example:
    - Use `sequential-thinking` to structure brainstorming steps or explore pros/cons.
    - Use `fetch` to research new tools, libraries, or concepts the user mentions.
    - Use `context7` to look up details about specific technologies.
- Your `thought` should reflect this plan, and `initial_response_to_user` should tell the user how you intend to help them (e.g., "Okay, let me research some additional libraries for network scanning and I'll get back to you with ideas.").

CRITICAL INSTRUCTIONS FOR `goal.txt` and `filesystem` tool:
1.  If the user discusses a project goal, or asks to save/write a goal, you should consider using the `filesystem` tool with the `write_file` method.
2.  When using `filesystem.write_file` to create or update `goal.txt`, the `path` parameter MUST be exactly `/workspace/goal.txt`.
    Example: `"parameters": {{ "path": "/workspace/goal.txt", "content": "... synthesized content ..." }}`
3.  The `content` for `goal.txt` should be synthesized from the relevant parts of the current conversation. If `goal.txt` was previously discussed or shown, use that as a base and incorporate new refinements.

Example 1 (using `filesystem` to write `goal.txt`):
{{
  "action": {{
    "thought": "User has defined a goal for a new project. I will write this to /workspace/goal.txt using the filesystem.write_file method.",
    "use_tool": true,
    "initial_response_to_user": "Okay, I'll create the goal.txt file for your new project in your workspace.",
    "tool_id": "filesystem",
    "method_name": "write_file",
    "parameters": {{ "path": "/workspace/goal.txt", "content": "# New Project Idea\n## Core Objective\nDescribe the main aim of the project... (full content synthesized from conversation history)" }}
  }}
}}

Example 2 (not using a tool, direct answer):
{{
  "action": {{
    "thought": "User is asking a general question that I can answer directly.",
    "use_tool": false,
    "initial_response_to_user": "SwarmDev is a platform for building autonomous agent swarms."
  }}
}}

Example 3 (tool use for goal refinement/brainstorming):
{{
  "action": {{
    "thought": "User wants to expand their project goal. I should use sequential-thinking to help brainstorm additional relevant areas like core features, advanced capabilities, and potential integrations.",
    "use_tool": true,
    "initial_response_to_user": "Great question! Let me think about how we can make your project more comprehensive. I'll consider core features, advanced capabilities, and potential integrations, then get back to you with some ideas.",
    "tool_id": "sequential-thinking", 
    "method_name": "sequentialthinking",
    "parameters": {{ "thought": "Brainstorm ways to expand a generic project goal. Consider: core features that must be included, advanced capabilities that would make it stand out, and potential integrations with other tools or services. What areas would provide the most value? Provide a comprehensive list of ideas.", "thoughtNumber": 1, "nextThoughtNeeded": false, "totalThoughts": 1 }}
  }}
}}

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
                if tool_result.get("type") == "sequential_thinking_output":
                    # Basic formatting for sequential thinking output
                    thoughts_str = "\n".join(tool_result.get("accumulated_thoughts", ["No thoughts recorded."]))
                    return f"{agent_initial_utterance}\nTool {tool_id} ({method_name}) completed.\nAccumulated thoughts:\n{thoughts_str[:1000]}..."
                return f"{agent_initial_utterance}\nTool {tool_id} ({method_name}) completed. Result: {str(tool_result)[:300]}..."
            else:
                return f"{agent_initial_utterance}\nTool {tool_id} ({method_name}) encountered an issue: {tool_result.get('error', 'Unknown error')}."

        tool_output_for_prompt = ""
        if tool_result.get("type") == "sequential_thinking_output":
            # More descriptive formatting for the LLM
            tool_output_for_prompt = f"The '{tool_id}' tool was used for a multi-step thinking process."
            tool_output_for_prompt += f"\nInitial prompt for the tool: {tool_result.get('initial_prompt', 'N/A')}"
            tool_output_for_prompt += f"\nNumber of thinking steps taken: {tool_result.get('steps_taken', 'N/A')}"
            tool_output_for_prompt += "\nAccumulated thoughts/outputs from each step:"
            for i, thought in enumerate(tool_result.get("accumulated_thoughts", [])):
                tool_output_for_prompt += f"\nStep {i+1}: {thought[:500]}" # Limit length of each step in prompt
                if len(thought) > 500:
                    tool_output_for_prompt += "..."
        else:
            # Standard handling for other tools
            tool_output_for_prompt = json.dumps(tool_result, indent=2)


        synthesis_prompt = f"""You are SwarmDev's Collaborative Agent.
The user originally said: "{original_human_message}"
You initially responded: "{agent_initial_utterance}" (indicating you might use a tool).
You then used the tool '{tool_id}' with method '{method_name}'.

The tool execution resulted in:
{tool_output_for_prompt}

Based on the original request, your initial response, and the tool's result, formulate a concise and helpful final response to the user.
- If the tool was successful, integrate its findings naturally. For multi-step tools like sequential-thinking, summarize the key outcomes or the final developed thought. 
    - If the 'accumulated_thoughts' for sequential-thinking seems to contain ONLY status updates (e.g., JSON objects with 'thoughtNumber', 'nextThoughtNeeded') and no actual textual thought content for each step, explicitly state that the tool provided progress updates but not the detailed thoughts, and ask if the user wants to try a different approach.
- If the tool was successful and the output is data (like file content from `read_file` or information from `fetch`) that is meant to be used in a subsequent step for the user's original request (e.g., user asked to "refine X after reading X"), your response should acknowledge receipt/summary of the data and clearly state your plan for the NEXT step (e.g., "Okay, I have the content of goal.txt. Now, I will use sequential-thinking to brainstorm refinements."). This sets up the user for your next action.
- If the tool failed (e.g., an error message in 'tool_output_for_prompt'), acknowledge the specific error transparently. Do NOT attempt to generate a response as if the tool succeeded. Instead, state the problem and ask the user how they'd like to proceed (e.g., try again, try a different tool, or abandon the attempt).
- Do not explicitly say "The tool returned...". Instead, incorporate the information. For example, if the tool listed files, say "Here are the files I found: ...".
- Be conversational.

Final response to user:
            """
        
        try:
            final_response = self.llm_provider.generate_text(synthesis_prompt, temperature=0.3, max_tokens=700) # Increased max_tokens
            return final_response.strip()
        except Exception as e:
            self.logger.error(f"Final response synthesis failed: {e}")
            # Fallback if synthesis fails, providing at least some of the raw accumulated data for sequential_thinking
            if tool_result.get("type") == "sequential_thinking_output":
                thoughts_str = "\n".join(tool_result.get("accumulated_thoughts", ["No thoughts recorded."]))
                return f"{agent_initial_utterance}\nI used the {tool_id} tool. Here's a summary of the thinking process:\n{thoughts_str[:1000]}..."
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