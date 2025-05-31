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

You: I want to create a simple todo list web applicationAssistant: That sounds like a great project! Let me help you refine this idea. A few questions:

1. Who are your target users?
2. What core features do you want?
3. What technology stack do you prefer?

You: I want a simple React app with basic CRUD operations.

