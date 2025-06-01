# API Documentation

This directory contains API documentation for the SwarmDev platform.

## Overview

The SwarmDev platform provides several APIs for interacting with the system:

1. **Interactive Agent API** - For goal refinement through conversation
2. **Goal Storage API** - For storing and retrieving project goals
3. **Swarm Builder API** - For initiating and monitoring project builds
4. **Orchestration API** - For coordinating agent activities

## Model-Aware Configuration

SwarmDev automatically optimizes parameters for different LLM models and providers. The same API calls work across all providers with automatic parameter translation and constraint handling.

## API Reference

### Interactive Agent API

```python
from swarmdev.interactive_agent import LLMEnabledInteractiveAgent
from swarmdev.utils.llm_provider import OpenAIProvider, AnthropicProvider, GoogleProvider

# Model-aware initialization - works with any provider
# OpenAI (with automatic o1 model handling)
llm_provider = OpenAIProvider(api_key="your-api-key", model="o1-mini")
agent = LLMEnabledInteractiveAgent(llm_provider)

# Anthropic (with automatic token limit enforcement)
llm_provider = AnthropicProvider(api_key="your-api-key", model="claude-3-5-sonnet-20241022")
agent = LLMEnabledInteractiveAgent(llm_provider)

# Google (with automatic parameter translation)
llm_provider = GoogleProvider(api_key="your-api-key", model="gemini-2.0-flash-001")
agent = LLMEnabledInteractiveAgent(llm_provider)

# Start a conversation (same API regardless of provider)
greeting = agent.start_conversation()

# Process user messages
response = agent.process_message("I want to build a task management app")

# Store the refined goal
agent.store_goal("goal.txt")
```

### Goal Storage API

```python
from swarmdev.goal_processor import GoalStorage

# Initialize the storage (uses .swarmdev/goals by default)
storage = GoalStorage("./.swarmdev/goals")

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

# Model-aware configuration - automatically optimizes for chosen LLM
config = {
    "llm_provider": "openai",  # or "anthropic", "google", "auto"
    "llm_model": "gpt-4o",     # automatically optimized
    "max_runtime": 3600,
    "workflow": "standard_project"
}

# Initialize the builder
builder = SwarmBuilder(
    project_dir="./project",
    goal_file="goal.txt",
    config=config
)

# Start the build process (model-aware optimization applied automatically)
project_id = builder.build()

# Get build status (includes MCP and LLM metrics)
status = builder.get_status()

# Cancel a build
builder.cancel()
```

### Provider Registry API

```python
from swarmdev.utils.llm_provider import ProviderRegistry

# Auto-detect available providers
registry = ProviderRegistry()
registry.discover_providers()

# Get the best available provider
provider = registry.get_provider()

# Get provider by capability
provider = registry.get_provider_by_capability("reasoning")
```

### Orchestration API

```python
from swarmdev.swarm_builder.orchestration import Orchestrator
from swarmdev.swarm_builder.agents import ResearchAgent
from swarmdev.swarm_builder.workflows import StandardProjectWorkflow
from swarmdev.utils.llm_provider import ProviderRegistry

# Model-aware setup
registry = ProviderRegistry()
registry.discover_providers()
llm_provider = registry.get_provider()

# Initialize the orchestrator
orchestrator = Orchestrator()

# Register an agent (automatically gets model-aware optimization)
agent = ResearchAgent("research_agent", "research", llm_provider, mcp_manager=None)
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

# Get execution status (includes model-aware metrics)
status = orchestrator.get_execution_status(execution_id)

# Stop the orchestrator
orchestrator.stop()
```

## Model-Aware Examples

### Switching Providers with Same Configuration

```python
# Same configuration works with any provider
config = {
    "temperature": 0.7,
    "max_tokens": 4000,
    "workflow": "standard_project"
}

# OpenAI (o1 models get temperature=1.0, max_completion_tokens automatically)
openai_builder = SwarmBuilder(
    project_dir="./project",
    goal_file="goal.txt",
    config={**config, "llm_provider": "openai", "llm_model": "o1-mini"}
)

# Anthropic (token limits enforced automatically)
anthropic_builder = SwarmBuilder(
    project_dir="./project",
    goal_file="goal.txt", 
    config={**config, "llm_provider": "anthropic", "llm_model": "claude-3-5-sonnet-20241022"}
)

# Google (max_tokens becomes max_output_tokens automatically)
google_builder = SwarmBuilder(
    project_dir="./project",
    goal_file="goal.txt",
    config={**config, "llm_provider": "google", "llm_model": "gemini-2.0-flash-001"}
)
```

### Auto Provider Detection

```python
# Let the system choose the best available provider
config = {
    "llm_provider": "auto",  # Auto-detect available providers
    "temperature": 0.7,
    "max_tokens": 4000
}

builder = SwarmBuilder(
    project_dir="./project",
    goal_file="goal.txt",
    config=config
)

# The system will automatically:
# 1. Check for available API keys
# 2. Choose the best provider
# 3. Apply model-aware optimizations
project_id = builder.build()
```

## Error Handling

All APIs use Python exceptions for error handling. The model-aware system prevents most parameter conflicts:

```python
try:
    # Model-aware system prevents parameter conflicts automatically
    builder = SwarmBuilder(
        project_dir="./project",
        goal_file="goal.txt",
        config={"llm_provider": "openai", "llm_model": "o1-mini"}
    )
    project_id = builder.build()
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Build error: {e}")
```

## Authentication

API authentication is handled through environment variables for LLM provider credentials:

```bash
# At least one provider API key required
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"  # Alternative
export GOOGLE_API_KEY="your-google-key"        # Alternative

# Optional MCP tool configuration
export CONTEXT7_API_KEY="your-context7-key"
```

## Rate Limiting and Model-Aware Optimization

The SwarmDev platform respects rate limits of underlying LLM providers and automatically optimizes parameters:

```python
# Model-aware provider initialization
llm_provider = OpenAIProvider(
    api_key="your-api-key",
    model="gpt-4o",  # Automatically optimized
    # No need to specify model-specific parameters
    # System handles max_tokens vs max_completion_tokens automatically
)

# For reasoning models, temperature restrictions are handled automatically
reasoning_provider = OpenAIProvider(
    api_key="your-api-key", 
    model="o1-mini",
    temperature=0.7  # Automatically ignored and set to 1.0 for o1 models
)
```

## Configuration File Locations

The API respects the standard configuration file hierarchy:

1. `.swarmdev/swarmdev_config.json` in project directory (recommended)
2. `./swarmdev_config.json` in current directory (fallback)
3. Path specified in config parameter

```python
# Using project-specific configuration
builder = SwarmBuilder(
    project_dir="./my_project",  # Will look for .swarmdev/swarmdev_config.json here
    goal_file="goal.txt"
)

# Using custom configuration file
builder = SwarmBuilder(
    project_dir="./my_project",
    goal_file="goal.txt",
    config={"config_file": "./custom_config.json"}
)
```

```