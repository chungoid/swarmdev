# SwarmDev Basic Usage Examples

This guide provides practical examples of how to use SwarmDev for common development scenarios.

## Prerequisites

Before using SwarmDev, ensure you have:

1. **Python 3.8+** installed
2. **SwarmDev package** installed (`pip install swarmdev`)
3. **At least one LLM provider API key** set up

### Set up your API key:

```bash
# For OpenAI (recommended for beginners)
export OPENAI_API_KEY="your-openai-api-key"

# Or for Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Or for Google
export GOOGLE_API_KEY="your-google-api-key"
```

## Model-Aware Configuration Benefits

SwarmDev automatically optimizes parameters for your chosen model:

- **Simple Configuration**: Same config works across all providers and models
- **Automatic Parameter Translation**: `max_tokens` becomes `max_completion_tokens` for o1, `max_output_tokens` for Gemini
- **Constraint Handling**: Temperature restrictions for reasoning models (o1, o3, o4 series) handled automatically

## Quick Start: Your First Project

### 1. Interactive Goal Refinement

Start with the interactive assistant to define your project:

```bash
swarmdev assistant
```

**Example conversation:**
```
Assistant: Welcome to SwarmDev! I'm here to help you build amazing projects with AI agents.

Let's start by understanding what you want to create. Could you describe your project idea?

You: I want to create a simple todo list web application