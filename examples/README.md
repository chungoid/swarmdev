# SwarmDev Examples

This directory contains example scripts demonstrating how to use the SwarmDev platform.

## Interactive Agent Demo

The `interactive_agent_demo.py` script demonstrates how to use the interactive agent for goal refinement through a conversational interface.

```bash
python examples/interactive_agent_demo.py
```

## Goal Storage and Builder Demo

The `goal_storage_builder_demo.py` script demonstrates how to use the goal storage system and the swarm builder to initiate a project build.

```bash
# With a specific goal file
python examples/goal_storage_builder_demo.py path/to/goal.txt

# Or select from existing goals
python examples/goal_storage_builder_demo.py
```

## Full Platform Demo

The `full_platform_demo.py` script demonstrates the complete SwarmDev platform workflow, from goal refinement to project building.

```bash
python examples/full_platform_demo.py
```

This demo shows how all components of the platform work together to create a complete project development pipeline.

## Requirements

All examples require the SwarmDev package to be installed or available in the Python path. They also require appropriate environment variables to be set for LLM provider access (e.g., `OPENAI_API_KEY`).

See the main documentation for more details on configuration and setup.
