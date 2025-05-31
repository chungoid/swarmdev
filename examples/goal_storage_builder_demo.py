"""
Example script demonstrating goal storage and builder functionality.
This script shows how to use the goal storage and builder to start a project.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from swarmdev.goal_processor import GoalStorage, SwarmBuilder


def main():
    """Run the goal storage and builder demo."""
    # Initialize the goal storage
    goal_storage = GoalStorage("./goals")
    
    # Check if a goal file is provided
    if len(sys.argv) > 1:
        goal_file = sys.argv[1]
        
        # Check if the file exists
        if not os.path.exists(goal_file):
            print(f"Error: Goal file {goal_file} not found.")
            return
        
        # Read the goal file
        with open(goal_file, 'r') as f:
            goal_text = f.read()
        
        # Store the goal
        goal_id = goal_storage.store_goal(goal_text)
        print(f"Goal stored with ID: {goal_id}")
    else:
        # List available goals
        goals = goal_storage.list_goals()
        
        if not goals:
            print("No goals found. Please provide a goal file.")
            return
        
        print("Available goals:")
        for i, goal_id in enumerate(goals):
            print(f"{i+1}. {goal_id}")
        
        # Select a goal
        selection = input("Select a goal (number): ")
        try:
            index = int(selection) - 1
            if index < 0 or index >= len(goals):
                print("Invalid selection.")
                return
            
            goal_id = goals[index]
        except ValueError:
            print("Invalid selection.")
            return
    
    # Create a project directory
    project_dir = "./project"
    os.makedirs(project_dir, exist_ok=True)
    
    # Initialize the builder
    builder = SwarmBuilder(
        project_dir=project_dir,
        goal_id=goal_id,
        config={
            "max_runtime": 3600,  # 1 hour
            "verbose": True
        }
    )
    
    # Start the build process
    project_id = builder.build()
    print(f"Build process started with project ID: {project_id}")
    print(f"Project files will be created in: {project_dir}")
    print("You can check the status with:")
    print(f"  swarmdev status --project-id {project_id}")


if __name__ == "__main__":
    main()
