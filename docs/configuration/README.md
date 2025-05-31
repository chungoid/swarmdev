# Configuration Guide

This guide provides comprehensive information on configuring the SwarmDev platform.

## Configuration Methods

The SwarmDev platform can be configured using the following methods, listed in order of precedence (highest to lowest):

1. **Command-line Arguments**: Passed directly to the CLI commands
2. **Environment Variables**: Set in the shell or through a `.env` file
3. **Configuration Files**: JSON or YAML files with detailed settings
4. **Default Values**: Built-in defaults for all settings

## Configuration Files

SwarmDev supports configuration through JSON or YAML files. By default, the platform looks for configuration in the following locations:

1. Path specified by the `--config` command-line argument
2. Path specified by the `SWARMDEV_CONFIG_FILE` environment variable
3. `./swarmdev.json` or `./swarmdev.yaml` in the current directory
4. `~/.swarmdev/config.json` or `~/.swarmdev/config.yaml` in the user's home directory

Example configuration file (JSON):

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 1000000
  },
  "project": {
    "project_dir": "./projects",
    "goal_dir": "./goals",
    "max_runtime": 86400
  },
  "agents": {
    "research": {
      "count": 1,
      "model": "gpt-4o",
      "temperature": 0.5
    },
    "planning": {
      "count": 1,
      "model": "gpt-4o",
      "temperature": 0.3
    },
    "development": {
      "count": 2,
      "model": "gpt-4o",
      "temperature": 0.2
    },
    "documentation": {
      "count": 1,
      "model": "gpt-4o",
      "temperature": 0.7
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
  "optimization": {
    "enabled": true,
    "objective": "balanced",
    "monitor_interval": 60,
    "adaptation_interval": 3600
  },
  "mcp_tools": {
    "enabled": true,
    "docker_enabled": true,
    "tools": [
      {
        "id": "sequential_thinking",
        "type": "docker",
        "image": "sequential-thinking:latest",
        "port": 8000,
        "capabilities": ["reasoning", "planning"]
      },
      {
        "id": "context7",
        "type": "api",
        "url": "https://api.context7.com",
        "capabilities": ["context_management", "reasoning"]
      }
    ]
  }
}
```

Example configuration file (YAML):

```yaml
llm:
  provider: openai
  model: gpt-4o
  temperature: 0.7
  max_tokens: 1000000

project:
  project_dir: ./projects
  goal_dir: ./goals
  max_runtime: 86400

agents:
  research:
    count: 1
    model: gpt-4o
    temperature: 0.5
  planning:
    count: 1
    model: gpt-4o
    temperature: 0.3
  development:
    count: 2
    model: gpt-4o
    temperature: 0.2
  documentation:
    count: 1
    model: gpt-4o
    temperature: 0.7

memory:
  vector_store: chroma
  vector_store_path: ./vector_store
  embedding_model: text-embedding-3-small

workflow:
  parallelism: 4
  timeout: 3600
  retry_attempts: 3

optimization:
  enabled: true
  objective: balanced
  monitor_interval: 60
  adaptation_interval: 3600

mcp_tools:
  enabled: true
  docker_enabled: true
  tools:
    - id: sequential_thinking
      type: docker
      image: sequential-thinking:latest
      port: 8000
      capabilities: [reasoning, planning]
    - id: context7
      type: api
      url: https://api.context7.com
      capabilities: [context_management, reasoning]
```

## Environment Variables

For a complete list of supported environment variables, see the [Environment Variables Reference](./environment_variables.md).

Key environment variables include:

```bash
# Core settings
export SWARMDEV_PROJECT_DIR="./projects"
export SWARMDEV_GOAL_FILE="./goal.txt"
export SWARMDEV_LOG_LEVEL="info"

# LLM provider settings
export OPENAI_API_KEY="your-api-key"
export SWARMDEV_LLM_PROVIDER="openai"
export SWARMDEV_LLM_MODEL="gpt-4o"
export SWARMDEV_LLM_TEMPERATURE="0.7"

# Agent settings
export SWARMDEV_AGENT_RESEARCH_COUNT="1"
export SWARMDEV_AGENT_PLANNING_COUNT="1"
export SWARMDEV_AGENT_DEVELOPMENT_COUNT="2"
export SWARMDEV_AGENT_DOCUMENTATION_COUNT="1"

# Memory settings
export SWARMDEV_MEMORY_VECTOR_STORE="chroma"
export SWARMDEV_MEMORY_VECTOR_STORE_PATH="./vector_store"

# Workflow settings
export SWARMDEV_WORKFLOW_PARALLELISM="4"
export SWARMDEV_WORKFLOW_TIMEOUT="3600"

# Optimization settings
export SWARMDEV_OPTIMIZATION_ENABLED="true"
export SWARMDEV_OPTIMIZATION_OBJECTIVE="balanced"
```

## Command-line Arguments

The SwarmDev CLI supports various command-line arguments for different commands:

```bash
# Refine a goal through conversation
swarmdev refine --output goal.txt

# Build a project from a goal
swarmdev build --goal-file goal.txt --project-dir ./project

# Check the status of a project
swarmdev status --project-id project_123456

# List available workflows
swarmdev workflows list

# Execute a specific workflow
swarmdev workflows execute --workflow-id standard_project --goal-file goal.txt
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

Configure which LLM providers to use and their settings:

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 1000000,
    "top_p": 1.0,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
    "timeout": 60,
    "retry_attempts": 3,
    "plugins_dir": "./llm_plugins",
    "fallback_provider": "anthropic",
    "fallback_model": "claude-3-opus-20240229"
  }
}
```

### Agent Configuration

Configure the agents used in the swarm:

```json
{
  "agents": {
    "research": {
      "count": 1,
      "model": "gpt-4o",
      "temperature": 0.5,
      "memory_enabled": true
    },
    "planning": {
      "count": 1,
      "model": "gpt-4o",
      "temperature": 0.3,
      "memory_enabled": true
    },
    "development": {
      "count": 2,
      "model": "gpt-4o",
      "temperature": 0.2,
      "memory_enabled": true
    },
    "documentation": {
      "count": 1,
      "model": "gpt-4o",
      "temperature": 0.7,
      "memory_enabled": true
    }
  }
}
```

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
    "cache_size": 10000,
    "working_memory_limit": 100,
    "episodic_enabled": true,
    "semantic_enabled": true,
    "procedural_enabled": true,
    "consolidation_threshold": 0.8,
    "mmr_lambda": 0.7,
    "persistence_enabled": true,
    "backup_enabled": true,
    "backup_interval": 3600
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
    "checkpoint_interval": 300,
    "notification_enabled": true,
    "notification_interval": 600
  }
}
```

### MCP Tool Configuration

Configure Multi-Context Processing tools:

```json
{
  "mcp_tools": {
    "enabled": true,
    "config_dirs": ["./mcp_tools"],
    "docker_enabled": true,
    "docker_network": "swarmdev",
    "docker_memory_limit": "2g",
    "docker_cpu_limit": 1,
    "tools": [
      {
        "id": "sequential_thinking",
        "type": "docker",
        "image": "sequential-thinking:latest",
        "port": 8000,
        "capabilities": ["reasoning", "planning"],
        "enabled": true
      },
      {
        "id": "context7",
        "type": "api",
        "url": "https://api.context7.com",
        "api_key": "${CONTEXT7_API_KEY}",
        "capabilities": ["context_management", "reasoning"],
        "enabled": true
      }
    ]
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
    "adaptation_interval": 3600,
    "human_approval_required": true,
    "metrics_retention": 604800,
    "policies": [
      "llm_parameter_tuning",
      "agent_allocation",
      "workflow_optimization",
      "resource_scaling"
    ]
  }
}
```

## Configuration Best Practices

1. **Use Environment Variables for Secrets**: Never store API keys or other secrets in configuration files. Use environment variables instead.

2. **Start with Defaults**: The platform comes with sensible defaults. Only override settings that you need to change.

3. **Use Configuration Files for Complex Settings**: For complex configurations, use a configuration file rather than environment variables.

4. **Version Control Configuration**: Keep your configuration files in version control, but exclude files with secrets.

5. **Use Environment-Specific Configurations**: Create different configuration files for development, testing, and production environments.

6. **Validate Configuration**: Always validate your configuration before deploying to production.

7. **Monitor Resource Usage**: Pay attention to resource usage, especially when configuring parallelism and agent counts.

8. **Start Small**: Begin with a minimal configuration and add complexity as needed.

## Troubleshooting

Common configuration issues and solutions:

1. **API Key Issues**: Ensure that API keys are correctly set in environment variables.

2. **Path Issues**: Ensure that all paths in the configuration are absolute or relative to the current working directory.

3. **Permission Issues**: Ensure that the user running the platform has permission to access all specified directories.

4. **Resource Constraints**: If the platform is running slowly, check resource usage and consider reducing parallelism or agent counts.

5. **Docker Issues**: If using Docker-based MCP tools, ensure that Docker is installed and running, and that the user has permission to use Docker.

6. **Network Issues**: If using API-based MCP tools, ensure that the network allows connections to the specified URLs.

7. **Configuration Precedence**: Remember that command-line arguments override environment variables, which override configuration files.

## Further Reading

- [Environment Variables Reference](./environment_variables.md)
- [API Documentation](../api/README.md)
- [Architecture Documentation](../architecture/README.md)
