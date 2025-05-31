# Environment Variables Reference

Complete reference for all environment variables used by the SwarmDev platform.

## Overview

SwarmDev uses environment variables for configuration, particularly for API keys and sensitive settings that should not be stored in configuration files or command-line arguments.

## Required Environment Variables

### LLM Provider API Keys

These are required based on which LLM provider you want to use:

| Variable | Required For | Description | Example |
|----------|--------------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI provider | OpenAI API key for GPT models | `sk-proj-...` |
| `ANTHROPIC_API_KEY` | Anthropic provider | Anthropic API key for Claude models | `sk-ant-...` |
| `GOOGLE_API_KEY` | Google provider | Google API key for Gemini models | `AIza...` |

**Note:** At least one API key is required for SwarmDev to function. The `auto` provider selection will use the first available provider based on these environment variables.

## Optional Environment Variables

### Configuration Override Variables

These variables can override configuration file settings and command-line defaults:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SWARMDEV_CONFIG_FILE` | string | None | Path to configuration file |
| `SWARMDEV_PROJECT_DIR` | string | `./project` | Default project directory |
| `SWARMDEV_GOAL_FILE` | string | None | Default goal file path |
| `SWARMDEV_LOG_LEVEL` | string | `info` | Default logging level |

### LLM Configuration Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SWARMDEV_LLM_PROVIDER` | string | `auto` | Default LLM provider |
| `SWARMDEV_LLM_MODEL` | string | Provider default | Default LLM model |
| `SWARMDEV_LLM_TEMPERATURE` | float | `0.7` | Default temperature for text generation |
| `SWARMDEV_LLM_MAX_TOKENS` | integer | `1000` | Default max tokens for responses |

### Workflow Configuration Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SWARMDEV_WORKFLOW` | string | `standard_project` | Default workflow type |
| `SWARMDEV_MAX_ITERATIONS` | integer | `3` | Default max iterations for iteration workflow |
| `SWARMDEV_MAX_RUNTIME` | integer | `3600` | Default max runtime in seconds |

### Agent Configuration Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SWARMDEV_AGENT_RESEARCH_COUNT` | integer | `1` | Number of research agents |
| `SWARMDEV_AGENT_PLANNING_COUNT` | integer | `1` | Number of planning agents |
| `SWARMDEV_AGENT_DEVELOPMENT_COUNT` | integer | `2` | Number of development agents |
| `SWARMDEV_AGENT_DOCUMENTATION_COUNT` | integer | `1` | Number of documentation agents |
| `SWARMDEV_AGENT_ANALYSIS_COUNT` | integer | `1` | Number of analysis agents |

### Memory and Storage Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SWARMDEV_MEMORY_VECTOR_STORE` | string | `chroma` | Vector store type |
| `SWARMDEV_MEMORY_VECTOR_STORE_PATH` | string | `./vector_store` | Vector store directory |
| `SWARMDEV_MEMORY_EMBEDDING_MODEL` | string | Provider default | Embedding model to use |
| `SWARMDEV_MEMORY_CACHE_SIZE` | integer | `10000` | Number of cached embeddings |

### Orchestrator Configuration Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SWARMDEV_WORKFLOW_PARALLELISM` | integer | `4` | Number of parallel workflow tasks |
| `SWARMDEV_WORKFLOW_TIMEOUT` | integer | `3600` | Workflow timeout in seconds |
| `SWARMDEV_WORKFLOW_RETRY_ATTEMPTS` | integer | `3` | Number of retry attempts |

### Performance and Optimization Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SWARMDEV_OPTIMIZATION_ENABLED` | boolean | `true` | Enable self-optimization |
| `SWARMDEV_OPTIMIZATION_OBJECTIVE` | string | `balanced` | Optimization objective |
| `SWARMDEV_OPTIMIZATION_MONITOR_INTERVAL` | integer | `60` | Monitoring interval in seconds |
| `SWARMDEV_OPTIMIZATION_ADAPTATION_INTERVAL` | integer | `3600` | Adaptation interval in seconds |

### MCP Tools Configuration Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SWARMDEV_MCP_TOOLS_ENABLED` | boolean | `true` | Enable MCP tools |
| `SWARMDEV_MCP_DOCKER_ENABLED` | boolean | `true` | Enable Docker-based MCP tools |
| `SWARMDEV_MCP_DOCKER_NETWORK` | string | `swarmdev` | Docker network name |
| `SWARMDEV_MCP_DOCKER_MEMORY_LIMIT` | string | `2g` | Docker memory limit |
| `SWARMDEV_MCP_DOCKER_CPU_LIMIT` | integer | `1` | Docker CPU limit |

### Third-Party Integration Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CONTEXT7_API_KEY` | string | None | Context7 API key (if using Context7 MCP tool) |
| `SEQUENTIAL_THINKING_ENDPOINT` | string | None | Sequential thinking service endpoint |

## Environment Variable Formats

### Boolean Values

Boolean environment variables accept these values:

- **True values:** `true`, `True`, `TRUE`, `1`, `yes`, `Yes`, `YES`, `on`, `On`, `ON`
- **False values:** `false`, `False`, `FALSE`, `0`, `no`, `No`, `NO`, `off`, `Off`, `OFF`

### Numeric Values

- **Integers:** Plain numbers (e.g., `3`, `1000`, `3600`)
- **Floats:** Decimal numbers (e.g., `0.7`, `1.0`, `0.3`)

### String Values

String values are used as-is. No special quoting is required unless the value contains spaces or special characters.

## Setting Environment Variables

### Linux/macOS (Bash)

```bash
# Set for current session
export OPENAI_API_KEY="your-api-key-here"
export SWARMDEV_LLM_PROVIDER="openai"
export SWARMDEV_WORKFLOW="iteration"

# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc
echo 'export SWARMDEV_LLM_PROVIDER="openai"' >> ~/.bashrc
```

### Windows (PowerShell)

```powershell
# Set for current session
$env:OPENAI_API_KEY = "your-api-key-here"
$env:SWARMDEV_LLM_PROVIDER = "openai"
$env:SWARMDEV_WORKFLOW = "iteration"

# Set permanently (requires restart)
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your-api-key-here", "User")
[Environment]::SetEnvironmentVariable("SWARMDEV_LLM_PROVIDER", "openai", "User")
```

### Windows (Command Prompt)

```cmd
# Set for current session
set OPENAI_API_KEY=your-api-key-here
set SWARMDEV_LLM_PROVIDER=openai
set SWARMDEV_WORKFLOW=iteration

# Set permanently
setx OPENAI_API_KEY "your-api-key-here"
setx SWARMDEV_LLM_PROVIDER "openai"
```

## .env File Support

SwarmDev supports `.env` files for environment variables. Create a `.env` file in your project directory:

```bash
# .env file
OPENAI_API_KEY=your-api-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
GOOGLE_API_KEY=your-google-key-here

# SwarmDev configuration
SWARMDEV_LLM_PROVIDER=openai
SWARMDEV_LLM_MODEL=gpt-4o
SWARMDEV_WORKFLOW=standard_project
SWARMDEV_PROJECT_DIR=./my_project
SWARMDEV_LOG_LEVEL=info

# Agent configuration
SWARMDEV_AGENT_DEVELOPMENT_COUNT=3
SWARMDEV_MAX_ITERATIONS=5

# Performance tuning
SWARMDEV_WORKFLOW_PARALLELISM=6
SWARMDEV_LLM_TEMPERATURE=0.5
```

**Important:** Never commit `.env` files to version control. Add `.env` to your `.gitignore` file.

## Provider-Specific Configuration

### OpenAI Configuration

```bash
export OPENAI_API_KEY="sk-proj-..."
export SWARMDEV_LLM_PROVIDER="openai"
export SWARMDEV_LLM_MODEL="gpt-4o"  # or gpt-3.5-turbo, gpt-4-turbo, etc.
```

### Anthropic Configuration

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export SWARMDEV_LLM_PROVIDER="anthropic"
export SWARMDEV_LLM_MODEL="claude-3-opus-20240229"  # or claude-3-sonnet-20240229, claude-3-haiku-20240307
```

### Google Configuration

```bash
export GOOGLE_API_KEY="AIza..."
export SWARMDEV_LLM_PROVIDER="google"
export SWARMDEV_LLM_MODEL="gemini-2.0-flash-001"  # or gemini-1.5-pro-001, gemini-1.5-flash-001
```

### Multiple Providers

You can set up multiple providers and let SwarmDev auto-select:

```bash
export OPENAI_API_KEY="sk-proj-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AIza..."
export SWARMDEV_LLM_PROVIDER="auto"  # Will prefer OpenAI if available
```

## Common Configuration Examples

### Development Environment

```bash
# Development settings
export SWARMDEV_LOG_LEVEL="debug"
export SWARMDEV_LLM_TEMPERATURE="0.3"  # Lower for more consistent results
export SWARMDEV_WORKFLOW="development_only"
export SWARMDEV_MAX_RUNTIME="7200"  # 2 hours
```

### Production Environment

```bash
# Production settings
export SWARMDEV_LOG_LEVEL="info"
export SWARMDEV_LLM_TEMPERATURE="0.7"
export SWARMDEV_WORKFLOW="standard_project"
export SWARMDEV_OPTIMIZATION_ENABLED="true"
```

### High-Performance Setup

```bash
# High-performance settings
export SWARMDEV_AGENT_DEVELOPMENT_COUNT="4"
export SWARMDEV_WORKFLOW_PARALLELISM="8"
export SWARMDEV_MEMORY_CACHE_SIZE="50000"
export SWARMDEV_LLM_MAX_TOKENS="2000"
```

### Research-Focused Setup

```bash
# Research-focused settings
export SWARMDEV_WORKFLOW="research_only"
export SWARMDEV_AGENT_RESEARCH_COUNT="3"
export SWARMDEV_LLM_TEMPERATURE="0.8"  # Higher for more creative research
```

## Security Best Practices

### API Key Security

1. **Never commit API keys to version control**
2. **Use environment variables or .env files**
3. **Rotate API keys regularly**
4. **Use different keys for development and production**
5. **Monitor API key usage**

### Access Control

```bash
# Set restrictive permissions on .env files
chmod 600 .env

# Verify environment variables are not logged
export SWARMDEV_LOG_LEVEL="info"  # Avoid debug in production
```

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```
   Error: OPENAI_API_KEY environment variable not set
   ```
   Solution: Set the appropriate API key environment variable

2. **Invalid Boolean Value**
   ```
   Error: Invalid boolean value for SWARMDEV_OPTIMIZATION_ENABLED
   ```
   Solution: Use valid boolean values (true/false, 1/0, yes/no)

3. **Invalid Numeric Value**
   ```
   Error: Invalid integer value for SWARMDEV_MAX_ITERATIONS
   ```
   Solution: Ensure numeric environment variables contain valid numbers

### Debugging Environment Variables

```bash
# Check if environment variables are set
echo $OPENAI_API_KEY
echo $SWARMDEV_LLM_PROVIDER

# List all SwarmDev environment variables
env | grep SWARMDEV

# Verify .env file loading
swarmdev build --goal goal.txt --verbose
```

### Environment Variable Precedence

Remember the precedence order:

1. **Command-line arguments** (highest priority)
2. **Environment variables**
3. **Configuration files**
4. **Built-in defaults** (lowest priority)

This means command-line arguments will override environment variables if both are set. 