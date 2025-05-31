"""
Example script demonstrating the full platform functionality.
This script shows how to use all components of the SwarmDev platform together.
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from swarmdev.utils.llm_provider import OpenAIProvider, ProviderRegistry
from swarmdev.interactive_agent import LLMEnabledInteractiveAgent
from swarmdev.goal_processor import GoalStorage, SwarmBuilder
from swarmdev.swarm_builder.agents import ResearchAgent, PlanningAgent, DevelopmentAgent, DocumentationAgent
from swarmdev.swarm_builder.orchestration import Orchestrator
from swarmdev.swarm_builder.workflows import StandardProjectWorkflow


def main():
    """Run the full platform demo."""
    print("SwarmDev Platform Demo")
    print("======================")
    
    # Initialize the LLM provider
    print("\nInitializing LLM provider...")
    provider_registry = ProviderRegistry()
    provider_registry.discover_providers()
    
    # Get the default provider
    llm_provider = provider_registry.get_provider()
    
    # Step 1: Interactive Goal Refinement
    print("\nStep 1: Interactive Goal Refinement")
    print("----------------------------------")
    
    # Create the interactive agent
    agent = LLMEnabledInteractiveAgent(llm_provider)
    
    # Start the conversation
    greeting = agent.start_conversation()
    print(f"Agent: {greeting}")
    
    # For demo purposes, we'll use a predefined goal
    predefined_goal = """
    Build a web application for task management with the following features:
    - User authentication (signup, login, logout)
    - Task creation, editing, and deletion
    - Task categorization and priority levels
    - Due dates and reminders
    - Simple dashboard with task statistics
    - Responsive design for mobile and desktop
    
    The application should be built using Python with Flask for the backend,
    SQLite for the database, and HTML/CSS/JavaScript for the frontend.
    """
    
    print("\nFor this demo, we'll use a predefined goal:")
    print(predefined_goal)
    
    # Process the predefined goal
    response = agent.process_message(predefined_goal)
    print(f"\nAgent: {response}")
    
    # Store the goal
    goal_file = "demo_goal.txt"
    if agent.store_goal(goal_file):
        print(f"\nGoal stored successfully in {goal_file}.")
    else:
        print("\nFailed to store the goal.")
        return
    
    # Step 2: Goal Storage
    print("\nStep 2: Goal Storage")
    print("------------------")
    
    # Initialize the goal storage
    goal_storage = GoalStorage("./goals")
    
    # Read the goal file
    with open(goal_file, 'r') as f:
        goal_text = f.read()
    
    # Store the goal
    goal_id = goal_storage.store_goal(goal_text)
    print(f"Goal stored with ID: {goal_id}")
    
    # Step 3: Swarm Builder Setup
    print("\nStep 3: Swarm Builder Setup")
    print("-------------------------")
    
    # Create a project directory
    project_dir = "./demo_project"
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
    
    # Step 4: Orchestration Setup
    print("\nStep 4: Orchestration Setup")
    print("-------------------------")
    
    # Initialize the orchestrator
    orchestrator = Orchestrator()
    
    # Register agents
    research_agent = ResearchAgent("research_agent_1", llm_provider)
    planning_agent = PlanningAgent("planning_agent_1", llm_provider)
    development_agent = DevelopmentAgent("development_agent_1", llm_provider)
    documentation_agent = DocumentationAgent("documentation_agent_1", llm_provider)
    
    orchestrator.register_agent(research_agent)
    orchestrator.register_agent(planning_agent)
    orchestrator.register_agent(development_agent)
    orchestrator.register_agent(documentation_agent)
    
    print("Registered agents:")
    print("- Research Agent")
    print("- Planning Agent")
    print("- Development Agent")
    print("- Documentation Agent")
    
    # Register workflow
    workflow = StandardProjectWorkflow()
    orchestrator.register_workflow(workflow.workflow_id, workflow.to_dict())
    print(f"Registered workflow: {workflow.name}")
    
    # Start the orchestrator
    orchestrator.start()
    print("Orchestrator started")
    
    # Step 5: Execute Workflow
    print("\nStep 5: Execute Workflow")
    print("---------------------")
    
    # Execute the workflow
    execution_id = orchestrator.execute_workflow(
        workflow_id=workflow.workflow_id,
        context={
            "goal": goal_text,
            "project_id": project_id,
            "project_dir": project_dir
        }
    )
    print(f"Workflow execution started with ID: {execution_id}")
    
    # Monitor execution status
    print("\nMonitoring execution status...")
    for _ in range(5):  # In a real scenario, this would run until completion
        status = orchestrator.get_execution_status(execution_id)
        print(f"Status: {status['status']}")
        print(f"Completed tasks: {status['completed_tasks']}/{status['total_tasks']}")
        time.sleep(1)  # Wait for 1 second between status checks
    
    # In a real scenario, we would wait for completion
    print("\nNote: In a real scenario, this would run until all tasks are completed.")
    print("For demo purposes, we're stopping after a few status checks.")
    
    # Stop the orchestrator
    orchestrator.stop()
    print("Orchestrator stopped")
    
    # Step 6: Check Results
    print("\nStep 6: Check Results")
    print("------------------")
    
    # Check the project status
    status = builder.get_status()
    print(f"Project status: {status['status']}")
    
    print("\nDemo completed successfully!")
    print("In a real scenario, the swarm would continue working until the project is complete.")
    print("You would then find all project files in the specified project directory.")


if __name__ == "__main__":
    main()
