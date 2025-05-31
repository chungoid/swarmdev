"""
Integration of the Interactive Agent with LLM capabilities.
This module provides an LLM-enabled version of the Interactive Agent.
"""

from typing import Dict, List, Optional, Tuple

from ..utils.llm_provider import LLMProviderInterface
from .agent import InteractiveAgent


class LLMEnabledInteractiveAgent(InteractiveAgent):
    """
    LLM-enabled Interactive Agent for goal refinement through guided conversation.
    
    This agent uses a Large Language Model to generate responses, analyze user input,
    and refine project goals through natural conversation.
    """
    
    def __init__(self, llm_provider: LLMProviderInterface, config: Optional[Dict] = None):
        """
        Initialize the LLM-enabled Interactive Agent.
        
        Args:
            llm_provider: LLM provider instance
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.llm_provider = llm_provider
    
    def process_message(self, message: str) -> str:
        """
        Process a user message and generate a response using the LLM.
        
        Args:
            message: User message content
            
        Returns:
            str: Agent response
        """
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": message})
        
        # If this is the first user message, treat it as the initial goal
        if self.current_goal is None:
            self.current_goal = message
        
        # Generate response using LLM
        prompt = self._create_prompt()
        response = self._generate_response(prompt)
        
        # Extract refined goal if present in the response
        refined_goal = self._extract_refined_goal(response)
        if refined_goal:
            self.current_goal = refined_goal
        
        # Add agent response to history
        self.conversation_history.append({"role": "agent", "content": response})
        return response
    
    def _create_prompt(self) -> str:
        """
        Create a prompt for the LLM based on the conversation history.
        
        Returns:
            str: Formatted prompt
        """
        # Convert conversation history to a format suitable for the LLM
        formatted_history = "\n\n".join([
            f"{'User' if msg['role'] == 'user' else 'Agent'}: {msg['content']}"
            for msg in self.conversation_history
        ])
        
        # Create the prompt
        prompt = (
            "You are an AI assistant helping a user refine their project idea into an actionable goal "
            "for an autonomous swarm of AI agents to work on. Your job is to ask clarifying questions, "
            "identify ambiguities, and help structure the goal clearly.\n\n"
            f"Current conversation:\n{formatted_history}\n\n"
            "Based on this conversation, please provide a helpful response that either:\n"
            "1. Asks clarifying questions about aspects of the project that are unclear\n"
            "2. Summarizes the refined goal if you have enough information\n\n"
            "If you have enough information to define a clear goal, include a section with the heading "
            "'REFINED GOAL:' followed by the complete, refined goal statement."
        )
        
        return prompt
    
    def _generate_response(self, prompt: str) -> str:
        """
        Generate a response using the LLM.
        
        Args:
            prompt: Formatted prompt
            
        Returns:
            str: LLM-generated response
        """
        try:
            response = self.llm_provider.generate_text(prompt, temperature=0.7)
            return response
        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return "I'm having trouble processing your request. Could you please provide more details about your project?"
    
    def _extract_refined_goal(self, response: str) -> Optional[str]:
        """
        Extract the refined goal from the LLM response if present.
        
        Args:
            response: LLM-generated response
            
        Returns:
            Optional[str]: Refined goal if present, None otherwise
        """
        if "REFINED GOAL:" in response:
            parts = response.split("REFINED GOAL:")
            if len(parts) > 1:
                goal_part = parts[1].strip()
                # Extract until the next section or the end
                end_markers = ["NEXT STEPS:", "QUESTIONS:", "CLARIFICATION:"]
                for marker in end_markers:
                    if marker in goal_part:
                        goal_part = goal_part.split(marker)[0].strip()
                return goal_part
        return None
    
    def _is_goal_complete(self, goal: str) -> bool:
        """
        Check if the current goal has enough information to proceed.
        
        Args:
            goal: Current goal description
            
        Returns:
            bool: True if the goal is complete, False otherwise
        """
        # Use the LLM to determine if the goal is complete
        prompt = (
            f"Below is a project goal description. Evaluate whether it contains enough information "
            f"for an autonomous AI system to begin working on it. The description should include "
            f"the problem being solved, target users, key features, and success criteria.\n\n"
            f"Goal description:\n{goal}\n\n"
            f"Is this goal description complete enough to begin work? Answer YES or NO."
        )
        
        try:
            response = self.llm_provider.generate_text(prompt, temperature=0.2)
            return "YES" in response.upper()
        except Exception:
            # Fall back to the basic implementation if LLM fails
            return super()._is_goal_complete(goal)
