# API Documentation

This directory contains API documentation for the SwarmDev platform.

## Overview

The SwarmDev platform provides several APIs for interacting with the system:

1. **Interactive Agent API** - For goal refinement through conversation
2. **Goal Storage API** - For storing and retrieving project goals
3. **Swarm Builder API** - For initiating and monitoring project builds
4. **Orchestration API** - For coordinating agent activities

## API Reference

### Interactive Agent API

```python
from swarmdev.interactive_agent import LLMEnabledInteractiveAgent
from swarmdev.utils.llm_provider import OpenAIProvider

# Initialize the agent
llm_provider = OpenAIProvider(api_key="your-api-key")
agent = LLMEnabledInteractiveAgent(llm_provider)

# Start a conversation
greeting = agent.start_conversation()

# Process user messages
response = agent.process_message("I want to build a task management app")

# Store the refined goal
agent.store_goal("goal.txt")
```

### Goal Storage API

```python
from swarmdev.goal_processor import GoalStorage

# Initialize the storage
storage = GoalStorage("./goals")

# Store a goal
goal_id = storage.store_goal("Build a task management app...")

# Retrieve a goal
goal_text = storage.get_goal(goal_id)

# List available goals
goals = storage.list_goals()

# Get versions of a goal
versions = storage.get_versions(goal_id)
```

### Swarm Builder API

```python
from swarmdev.goal_processor import SwarmBuilder

# Initialize the builder
builder = SwarmBuilder(
    project_dir="./project",
    goal_file="goal.txt",
    config={"max_runtime": 3600}
)

# Start the build process
project_id = builder.build()

# Get build status
status = builder.get_status()

# Cancel a build
builder.cancel()
```

### Orchestration API

```python
from swarmdev.swarm_builder.orchestration import Orchestrator
from swarmdev.swarm_builder.agents import ResearchAgent
from swarmdev.swarm_builder.workflows import StandardProjectWorkflow

# Initialize the orchestrator
orchestrator = Orchestrator()

# Register an agent
agent = ResearchAgent("research_agent", llm_provider)
orchestrator.register_agent(agent)

# Register a workflow
workflow = StandardProjectWorkflow()
orchestrator.register_workflow(workflow.workflow_id, workflow.to_dict())

# Start the orchestrator
orchestrator.start()

# Execute a workflow
execution_id = orchestrator.execute_workflow(
    workflow_id=workflow.workflow_id,
    context={"goal": "Build a task management app..."}
)

# Get execution status
status = orchestrator.get_execution_status(execution_id)

# Stop the orchestrator
orchestrator.stop()
```

## Error Handling

All APIs use Python exceptions for error handling. Catch exceptions to handle errors gracefully:

```python
try:
    goal_id = storage.store_goal("Build a task management app...")
except Exception as e:
    print(f"Error storing goal: {e}")
```

## Authentication

API authentication is handled through environment variables for LLM provider credentials:

```bash
export OPENAI_API_KEY="your-api-key"
export ANTHROPIC_API_KEY="your-api-key"
```

## Rate Limiting

The SwarmDev platform respects rate limits of underlying LLM providers. Configure retry behavior in the provider configuration:

```python
llm_provider = OpenAIProvider(
    api_key="your-api-key",
    max_retries=3,
    retry_delay=1.0
)
```
