# Configuration Guide

This guide provides comprehensive information on configuring the SwarmDev platform.

## Configuration Methods

The SwarmDev platform can be configured using the following methods, listed in order of precedence (highest to lowest):

1. **Command-line Arguments**: Passed directly to the CLI commands
2. **Environment Variables**: Set in the shell or through a `.env` file
3. **Configuration Files**: JSON files with detailed settings
4. **Default Values**: Built-in defaults for all settings

## Configuration Files

SwarmDev supports configuration through JSON files. The platform looks for configuration in the following locations:

1. Path specified by the `--config` command-line argument
2. `.swarmdev/swarmdev_config.json` in the project directory (primary location)
3. `./swarmdev_config.json` in the current directory (fallback)

## Model-Aware Configuration System

SwarmDev uses an intelligent **model-aware configuration system** that automatically translates parameters based on the specific LLM model being used. This eliminates the need to manage different parameter sets for different models.

### Key Benefits:
- **Unified Configuration**: The same config works across all LLM providers and models
- **Automatic Parameter Translation**: `max_tokens` becomes `max_completion_tokens` for o1 models, `max_output_tokens` for Gemini, etc.
- **Model-Specific Constraints**: Temperature restrictions for reasoning models (o1, o3, o4 series) are automatically handled
- **Optimal Defaults**: Each model gets appropriate token limits and parameter settings

Example configuration file (JSON):

```json
{
  "llm": {
    "provider": "openai",
    "model": "o4-mini-2025-04-16",
    "temperature": 0.7,
    "max_tokens": 4000
  },
  "project": {
    "project_dir": "./projects",
    "goal_dir": "./goals",
    "max_runtime": 7200
  },
  "agents": {
    "research": {
      "count": 1,
      "memory_enabled": true
    },
    "planning": {
      "count": 1,
      "memory_enabled": true
    },
    "development": {
      "count": 2,
      "memory_enabled": true
    },
    "documentation": {
      "count": 1,
      "memory_enabled": true
    }
  },
  "memory": {
    "vector_store": "chroma",
    "vector_store_path": "./vector_store",
    "embedding_model": "text-embedding-3-small"
  },
  "workflow": {
    "parallelism": 4,
    "timeout": 3600,
    "retry_attempts": 3
  },
  "mcp": {
    "enabled": true,
    "config_file": "./mcp_config.json",
    "docker_enabled": true,
    "docker_network": null
  },
  "optimization": {
    "enabled": true,
    "objective": "balanced",
    "monitor_interval": 60,
    "adaptation_interval": 3600
  }
}
```

## Provider-Specific Examples

### OpenAI o1 (Reasoning Models)
```json
{
  "llm": {
    "provider": "openai",
    "model": "o1-mini",
    "temperature": 0.7,
    "max_tokens": 25000
  }
}
```
**Automatic Translation:**
- `temperature` is ignored (o1 models only support 1.0)
- `max_tokens` becomes `max_completion_tokens`
- Default raised to 25,000 for reasoning tasks

### Anthropic Claude
```json
{
  "llm": {
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "temperature": 0.7,
    "max_tokens": 6000
  }
}
```
**Automatic Translation:**
- Automatically capped at model limits (8192 for Claude 3.5)
- Standard parameter set maintained

### Google Gemini
```json
{
  "llm": {
    "provider": "google",
    "model": "gemini-2.0-flash-001",
    "temperature": 0.7,
    "max_tokens": 5000
  }
}
```
**Automatic Translation:**
- `max_tokens` becomes `max_output_tokens`
- Google-specific parameters (`top_k`) added automatically

## Environment Variables

Key environment variables for LLM providers:

```bash
# API Keys (required)
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"

# Default LLM settings
export SWARMDEV_LLM_PROVIDER="auto"
export SWARMDEV_LLM_MODEL="o4-mini-2025-04-16"

# Core settings
export SWARMDEV_PROJECT_DIR="./projects"
export SWARMDEV_LOG_LEVEL="info"

# Workflow settings
export SWARMDEV_WORKFLOW_PARALLELISM="4"
export SWARMDEV_WORKFLOW_TIMEOUT="3600"
```

## Command-line Arguments

The SwarmDev CLI supports various command-line arguments for different commands:

```bash
# Build a project from a goal
swarmdev build --goal goal.txt --project-dir ./project

# Use specific provider and model
swarmdev build --goal goal.txt --llm-provider openai --llm-model o1-mini

# Check the status of a project
swarmdev status --project-id project_123456

# List available workflows
swarmdev workflows --verbose
```

Common arguments across all commands:

```bash
--config PATH           Path to configuration file
--log-level LEVEL       Logging level (debug, info, warning, error)
--verbose               Enable verbose output
--quiet                 Suppress all output except errors
--help                  Show help message and exit
```

## Configuration Categories

### LLM Provider Configuration

Configure which LLM providers to use with model-aware parameter handling:

```json
{
  "llm": {
    "provider": "openai",
    "model": "o4-mini-2025-04-16",
    "temperature": 0.7,
    "max_tokens": 4000,
    "timeout": 60
  }
}
```

**Model-Aware Features:**
- Automatic parameter translation for each model family
- Reasoning model constraint handling (o1, o3, o4 series)
- Provider-specific optimization (Gemini `top_k`, Claude limits)
- Fallback to compatible parameters when needed

### Agent Configuration

Agents now inherit LLM settings from the main configuration with automatic optimization:

```json
{
  "agents": {
    "research": {
      "count": 1,
      "memory_enabled": true
    },
    "planning": {
      "count": 1,
      "memory_enabled": true
    },
    "development": {
      "count": 2,
      "memory_enabled": true
    },
    "documentation": {
      "count": 1,
      "memory_enabled": true
    }
  }
}
```

**Note:** Agent-specific model and temperature configurations are no longer needed. All agents use the main LLM configuration with model-aware parameter optimization.

### Memory Configuration

Configure the vector memory system:

```json
{
  "memory": {
    "enabled": true,
    "vector_store": "chroma",
    "vector_store_path": "./vector_store",
    "embedding_model": "text-embedding-3-small",
    "cache_enabled": true,
    "working_memory_limit": 100
  }
}
```

### Workflow Configuration

Configure workflow execution:

```json
{
  "workflow": {
    "parallelism": 4,
    "timeout": 3600,
    "retry_attempts": 3,
    "retry_backoff": 2.0,
    "checkpoint_interval": 300
  }
}
```

### MCP Configuration

Configure Multi-Context Processing tools:

```json
{
  "mcp": {
    "enabled": true,
    "config_file": "./mcp_config.json",
    "docker_enabled": true,
    "docker_network": null
  }
}
```

The MCP tools are configured in a separate `mcp_config.json` file:

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

### Optimization Configuration

Configure self-optimization:

```json
{
  "optimization": {
    "enabled": true,
    "objective": "balanced",
    "monitor_interval": 60,
    "adaptation_interval": 3600
  }
}
```

## Configuration Best Practices

1. **Use Environment Variables for Secrets**: Never store API keys in configuration files. Use environment variables instead.

2. **Leverage Model-Aware System**: Don't specify model-specific parameters manually. Let the system handle parameter translation automatically.

3. **Start with Defaults**: The platform comes with sensible defaults. Only override settings you need to change.

4. **Use Simple Configurations**: With the model-aware system, you can use the same configuration across all providers and models.

5. **Configure by Provider**: When switching providers, only change the `provider` and `model` fields. All other parameters work automatically.

6. **Monitor Resource Usage**: Pay attention to resource usage, especially when configuring parallelism and agent counts.

## Model-Specific Constraints

### Reasoning Models (o1, o3, o4 series)
- **Temperature**: Only supports 1.0 (user setting ignored to prevent errors)
- **Parameters**: Many standard parameters not supported (automatically excluded)
- **Token Limits**: Much higher defaults (25,000+) for reasoning tasks

### Standard Chat Models (GPT-4, Claude, etc.)
- **Full Parameter Support**: All standard parameters available
- **Model-Specific Limits**: Automatically enforced (Claude 3.5: 8192 tokens, etc.)

### Multimodal Models
- **Vision Capabilities**: Automatically detected and enabled
- **Extended Context**: Large context windows utilized appropriately

## Troubleshooting

Common configuration issues and solutions:

1. **API Key Issues**: Ensure API keys are set as environment variables, not in config files.

2. **Model Parameter Errors**: With model-aware system, parameter conflicts are automatically resolved. If issues persist, check model availability.

3. **Configuration File Location**: Ensure config is in `.swarmdev/swarmdev_config.json` within your project directory.

4. **MCP Configuration**: MCP tools require a separate `mcp_config.json` file. Check that Docker is available for Docker-based tools.

5. **Provider-Specific Issues**: Use `--llm-provider auto` to let the system auto-detect available providers.

## Further Reading

- [Model-Aware Configuration Details](../MODEL_AWARE_CONFIG.md)
- [Environment Variables Reference](./environment_variables.md)
- [CLI Reference](../cli/README.md)
- [Architecture Documentation](../architecture/README.md)
