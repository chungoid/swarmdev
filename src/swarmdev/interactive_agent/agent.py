"""
Interactive Agent implementation for the SwarmDev platform.
This module provides the base interactive agent class.
"""

from typing import Dict, List, Optional, Tuple


class InteractiveAgent:
    """
    Interactive Agent for goal refinement through guided conversation.
    
    This agent helps users refine their project ideas into actionable goals
    through a series of targeted questions and clarifications.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the Interactive Agent.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.conversation_history = []
        self.current_goal = None
    
    def start_conversation(self) -> str:
        """
        Start a new conversation with the user.
        
        Returns:
            str: Initial greeting message
        """
        self.conversation_history = []
        self.current_goal = None
        
        greeting = (
            "Hello! I'm here to help you refine your project idea into an actionable goal. "
            "Please describe the project you'd like the swarm to build for you."
        )
        
        self.conversation_history.append({"role": "agent", "content": greeting})
        return greeting
    
    def process_message(self, message: str) -> str:
        """
        Process a user message and generate a response.
        
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
            
            # Generate clarifying questions based on the initial goal
            response = self._generate_questions(self.current_goal)
        else:
            # Refine the goal based on the user's response
            self.current_goal = self._refine_goal(self.current_goal, message)
            
            # Check if we have enough information
            if self._is_goal_complete(self.current_goal):
                response = (
                    f"Thank you for providing that information. Based on our conversation, "
                    f"I've refined your goal to:\n\n{self.current_goal}\n\n"
                    f"Is this accurate? If so, I can store this goal for the swarm to begin working on."
                )
            else:
                # Ask for more information
                response = self._generate_questions(self.current_goal)
        
        # Add agent response to history
        self.conversation_history.append({"role": "agent", "content": response})
        return response
    
    def store_goal(self, file_path: str) -> bool:
        """
        Store the refined goal to a file.
        
        Args:
            file_path: Path to the goal file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.current_goal or not self._is_goal_complete(self.current_goal):
            return False
        
        try:
            with open(file_path, 'w') as f:
                f.write(self.current_goal)
            return True
        except Exception as e:
            print(f"Error storing goal: {e}")
            return False
    
    def _generate_questions(self, goal: str) -> str:
        """
        Generate clarifying questions based on the current goal.
        
        Args:
            goal: Current goal description
            
        Returns:
            str: Questions to ask the user
        """
        # This is a placeholder implementation
        # In a real implementation, this would analyze the goal and identify ambiguities
        return (
            "To better understand your project requirements, could you please provide more details about:\n\n"
            "1. What problem is this project trying to solve?\n"
            "2. Who are the intended users?\n"
            "3. What are the most important features or capabilities?\n"
            "4. Are there any specific technologies or approaches you'd like to use?\n"
            "5. What would a successful outcome look like?"
        )
    
    def _refine_goal(self, current_goal: str, user_response: str) -> str:
        """
        Refine the current goal based on user response.
        
        Args:
            current_goal: Current goal description
            user_response: User's response to questions
            
        Returns:
            str: Refined goal
        """
        # This is a placeholder implementation
        # In a real implementation, this would use NLP to integrate the user's response
        return f"{current_goal}\n\nAdditional information:\n{user_response}"
    
    def _is_goal_complete(self, goal: str) -> bool:
        """
        Check if the current goal has enough information to proceed.
        
        Args:
            goal: Current goal description
            
        Returns:
            bool: True if the goal is complete, False otherwise
        """
        # This is a placeholder implementation
        # In a real implementation, this would check for completeness based on required information
        return len(self.conversation_history) >= 6  # At least 3 exchanges
