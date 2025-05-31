"""
Example script demonstrating the interactive agent for goal refinement.
This script shows how to use the interactive agent to refine a project goal.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from swarmdev.utils.llm_provider import OpenAIProvider, ProviderRegistry
from swarmdev.interactive_agent import LLMEnabledInteractiveAgent


def main():
    """Run the interactive agent demo."""
    # Initialize the LLM provider
    provider_registry = ProviderRegistry()
    provider_registry.discover_providers()
    
    # Get the default provider
    llm_provider = provider_registry.get_provider()
    
    # Create the interactive agent
    agent = LLMEnabledInteractiveAgent(llm_provider)
    
    # Start the conversation
    greeting = agent.start_conversation()
    print(f"Agent: {greeting}")
    
    # Main conversation loop
    while True:
        # Get user input
        user_input = input("You: ")
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Agent: Goodbye! Thank you for using the SwarmDev platform.")
            break
        
        # Process the message
        response = agent.process_message(user_input)
        print(f"Agent: {response}")
        
        # Check if the goal is complete
        if "Is this accurate?" in response and "I can store this goal" in response:
            # Ask if the user wants to store the goal
            store_input = input("Do you want to store this goal? (yes/no): ")
            
            if store_input.lower() in ["yes", "y"]:
                # Store the goal
                goal_file = "goal.txt"
                if agent.store_goal(goal_file):
                    print(f"Agent: Goal stored successfully in {goal_file}.")
                    print("You can now run the builder with:")
                    print(f"  swarmdev build --goal-file {goal_file} --project-dir ./project")
                else:
                    print("Agent: Failed to store the goal.")
                
                break


if __name__ == "__main__":
    main()
