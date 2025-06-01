# MCP (Model Context Protocol) Setup Guide

This guide shows you how to configure external MCP servers to extend your SwarmDev agents' capabilities with the model-aware configuration system.

## What are MCP Servers?

MCP servers provide additional tools and capabilities that your SwarmDev agents can use during project development. They can offer specialized reasoning, context management, documentation lookup, and more.

## Quick Setup

### 1. Prepare Docker Images

First, ensure you have the MCP server Docker images available:

```bash
# Pull the sequential thinking MCP server
docker pull sequential-thinking:latest

# Pull the Context7 MCP server  
docker pull context7-mcp:latest
```

### 2. Copy Configuration Files to Project

Create your project directory and copy configuration files:

```bash
# Create project directory
mkdir my_project && cd my_project

# Create .swarmdev directory
mkdir -p .swarmdev

# Copy the main SwarmDev config
cp examples/swarmdev_config.json .swarmdev/swarmdev_config.json

# Copy the MCP configuration
cp examples/mcp_config.json .swarmdev/mcp_config.json
```

### 3. Update Your Environment

Set any required environment variables:

```bash
# For Context7 (if API key required)
export CONTEXT7_API_KEY="your-api-key-if-needed"

# Set your LLM provider API key
export OPENAI_API_KEY="your-openai-key"  # or ANTHROPIC_API_KEY, GOOGLE_API_KEY
```

## Configuration Files Explained

### Main Configuration (`.swarmdev/swarmdev_config.json`)

The model-aware configuration automatically enables MCP tools:

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4o", 
    "temperature": 0.7,
    "max_tokens": 4000
  },
  "mcp": {
    "enabled": true,
    "config_file": "./.swarmdev/mcp_config.json",
    "docker_enabled": true,
    "docker_network": null
  }
}
```

**Works with any LLM provider** - the same MCP configuration works whether you use OpenAI, Anthropic, or Google models.

### MCP Configuration (`.swarmdev/mcp_config.json`)

This file defines how to connect to each MCP server:

```json
{
  "servers": {
    "sequential_thinking": {
      "command": "docker",
      "args": ["run", "--rm", "-p", "8000:8000", "sequential-thinking:latest"],
      "capabilities": ["reasoning", "planning"]
    },
    "context7": {
      "command": "mcp-context7",
      "args": ["--api-key", "${CONTEXT7_API_KEY}"],
      "capabilities": ["documentation", "reasoning"]
    }
  }
}
```

## Using MCP Tools with Model-Aware System

### Sequential Thinking Server

Works automatically with any LLM model for complex reasoning:

```bash
# With OpenAI o1 models (reasoning model aware)
swarmdev build --goal complex_project.txt --llm-provider openai --llm-model o1-mini

# With Anthropic Claude (standard chat model)  
swarmdev build --goal complex_project.txt --llm-provider anthropic --llm-model claude-3-5-sonnet-20241022

# With Google Gemini (multimodal support)
swarmdev build --goal complex_project.txt --llm-provider google --llm-model gemini-2.0-flash-001
```

Your agents will automatically use sequential thinking for:
- Breaking down complex problems
- Planning implementation strategies  
- Analyzing trade-offs and alternatives
- Multi-step reasoning processes

### Context7 Server

Provides advanced documentation and context management regardless of LLM provider:

```bash
# For projects requiring extensive research (any provider)
swarmdev build --goal research_project.txt --workflow research_only
```

Your agents will use Context7 for:
- Looking up library documentation
- Managing project context across tasks
- Generating comprehensive documentation
- Reasoning about code relationships

## Model-Aware MCP Integration

The model-aware system automatically optimizes MCP tool usage based on your chosen LLM:

### With Reasoning Models (o1, o3, o4 series)
- Temperature restrictions handled automatically
- Higher token limits for complex reasoning
- MCP tools complement built-in reasoning capabilities

### With Standard Chat Models (GPT-4, Claude, Gemini)
- Full parameter support
- MCP tools provide enhanced reasoning capabilities
- Optimal balance between local and external reasoning

### With Multimodal Models
- Vision capabilities detected automatically
- MCP tools provide text-based reasoning support
- Extended context windows utilized appropriately

## Advanced Configuration

### Custom Docker Networks

Create isolated networks for different projects:

```bash
# Create project-specific network
docker network create my-project-swarmdev

# Update .swarmdev/mcp_config.json
{
  "servers": {
    "sequential_thinking": {
      "command": "docker",
      "args": ["run", "--rm", "--network", "my-project-swarmdev", "-p", "8000:8000", "sequential-thinking:latest"],
      "capabilities": ["reasoning", "planning"]
    }
  }
}
```

### Resource Limits

Control Docker resource usage:

```json
{
  "servers": {
    "sequential_thinking": {
      "command": "docker",
      "args": [
        "run", "--rm", 
        "--memory", "2g",
        "--cpus", "1.0",
        "-p", "8000:8000", 
        "sequential-thinking:latest"
      ],
      "capabilities": ["reasoning", "planning"]
    }
  }
}
```

### Provider-Specific Optimizations

Configure different MCP tool usage based on LLM provider:

```json
{
  "llm": {
    "provider": "openai",
    "model": "o1-mini"
  },
  "mcp": {
    "enabled": true,
    "config_file": "./.swarmdev/mcp_config.json",
    "provider_optimizations": {
      "reasoning_models": {
        "prefer_external_reasoning": false,
        "use_for_planning": true
      },
      "chat_models": {
        "prefer_external_reasoning": true,
        "use_for_planning": true
      }
    }
  }
}
```

### Disabling Specific Tools

You can disable specific tools while keeping others enabled:

```json
{
  "servers": {
    "sequential_thinking": {
      "command": "docker",
      "args": ["run", "--rm", "-p", "8000:8000", "sequential-thinking:latest"],
      "capabilities": ["reasoning", "planning"],
      "enabled": false
    },
    "context7": {
      "command": "mcp-context7",
      "args": ["--api-key", "${CONTEXT7_API_KEY}"],
      "capabilities": ["documentation", "reasoning"],
      "enabled": true
    }
  }
}
```

## Troubleshooting

### Docker Issues

```bash
# Check if Docker is running
docker info

# Verify images are available
docker images | grep -E "(sequential-thinking|context7-mcp)"

# Test MCP server manually
docker run --rm sequential-thinking:latest --version
```

### Configuration Issues

```bash
# Check config file locations
ls .swarmdev/swarmdev_config.json
ls .swarmdev/mcp_config.json

# Validate JSON syntax
jq . .swarmdev/swarmdev_config.json
jq . .swarmdev/mcp_config.json
```

### Network Issues

```bash
# Check network exists
docker network ls | grep swarmdev

# Create network if needed
docker network create swarmdev

# Test container network connectivity
docker run --rm --network swarmdev alpine ping -c 1 google.com
```

### Model-Aware System Issues

```bash
# Verify model-aware parameter handling
swarmdev build --goal test.txt --llm-provider openai --llm-model o1-mini --project-dir test_project

# Check if MCP tools are being called appropriately
tail -f test_project/.swarmdev/logs/swarmdev.log | grep -i mcp
```

## Monitoring MCP Tools

### Enable Detailed Logging

Set up comprehensive logging in your project:

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4o"
  },
  "mcp": {
    "enabled": true,
    "config_file": "./.swarmdev/mcp_config.json",
    "logging": {
      "level": "debug",
      "enable_metrics": true,
      "log_tool_usage": true
    }
  }
}
```

### Check Tool Usage

Monitor which tools your agents are using:

```bash
# Watch MCP usage in real-time
tail -f .swarmdev/logs/swarmdev.log | grep -i mcp

# Check agent-specific MCP usage
tail -f .swarmdev/logs/*_agent.log | grep -i "sequential_thinking\|context7"

# Monitor with status command
swarmdev status --project-id <project-id> --detailed --logs
```

## Example Workflow with MCP Tools

Here's a complete example using the model-aware system with MCP tools:

```bash
# 1. Set up project with configuration
mkdir dashboard_project && cd dashboard_project
mkdir -p .swarmdev
cp examples/swarmdev_config.json .swarmdev/
cp examples/mcp_config.json .swarmdev/

# 2. Create goal file
echo "Create a React dashboard with user authentication, data visualization charts, and real-time updates. Include comprehensive documentation and testing." > goal.txt

# 3. Build with model-aware optimization and MCP tools
swarmdev build --goal goal.txt --workflow standard_project --project-dir ./dashboard_project

# 4. Monitor progress (agents use MCP tools automatically with any LLM)
swarmdev status --project-id <project-id> --watch --detailed
```

Your agents will automatically leverage:
- **Model-aware parameter optimization** for your chosen LLM
- **Sequential thinking** for complex architecture planning
- **Context7** for React library documentation and best practices
- **Enhanced reasoning capabilities** throughout the development process

## Provider-Specific Examples

### OpenAI with o1 (Reasoning Model)
```bash
swarmdev build --goal goal.txt --llm-provider openai --llm-model o1-mini
# MCP tools complement built-in reasoning, temperature automatically set to 1.0
```

### Anthropic Claude
```bash  
swarmdev build --goal goal.txt --llm-provider anthropic --llm-model claude-3-5-sonnet-20241022
# MCP tools provide enhanced reasoning, token limits automatically enforced
```

### Google Gemini
```bash
swarmdev build --goal goal.txt --llm-provider google --llm-model gemini-2.0-flash-001
# MCP tools work with multimodal capabilities, parameters automatically translated
```

## Next Steps

- **Experiment with different LLM providers** using the same MCP configuration
- **Monitor MCP tool efficiency** with different model families
- **Configure provider-specific optimizations** for your workflow needs
- **Explore creating custom MCP servers** for domain-specific tools
- **Set up monitoring and metrics** for MCP tool performance across different models 