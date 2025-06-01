# SwarmDev Configuration Defaults

Complete reference for all configurable options and their default values in the SwarmDev platform.

## Overview

SwarmDev can be configured through multiple methods (in order of precedence):

1. **Command-line Arguments** (highest priority)
2. **Environment Variables**
3. **Configuration Files** (JSON)
4. **Built-in Defaults** (lowest priority)

## Model-Aware Configuration Defaults

SwarmDev uses a **model-aware configuration system** that automatically sets optimal defaults based on the LLM model selected.

### Provider Defaults

| Provider | Default Model | Default Max Tokens | Temperature |
|----------|---------------|-------------------|-------------|
| `openai` | `o4-mini-2025-04-16` | `4000` | `0.7` |
| `anthropic` | `claude-3-opus-20240229` | `4000` (capped at model limit) | `0.7` |
| `google` | `gemini-2.0-flash-001` | `4000` | `0.7` |

### Reasoning Model Defaults (o1, o3, o4 series)

| Setting | Default Value | Description |
|---------|---------------|-------------|
| Max Tokens | `25000` | Much higher for reasoning tasks |
| Temperature | `1.0` (forced) | Only supported value (user setting ignored) |
| Parameters | Minimal set | Many standard parameters excluded automatically |

## Command-Line Argument Defaults

### Global Options

| Option | Default Value | Type | Description |
|--------|---------------|------|-------------|
| `--verbose` | `False` | boolean | Enable verbose output |
| `--quiet` | `False` | boolean | Suppress all output except errors |
| `--log-level` | `"info"` | string | Logging level (debug, info, warning, error) |
| `--config` | `None` | string | Path to configuration file |

### Build Command Defaults

| Option | Default Value | Type | Description |
|--------|---------------|------|-------------|
| `--project-dir` | `"./project"` | string | Project directory where files will be created |
| `--max-runtime` | `3600` | integer | Maximum runtime in seconds (1 hour) |
| `--llm-provider` | `"auto"` | string | LLM provider (openai, anthropic, google, auto) |
| `--llm-model` | Provider default | string | LLM model to use |
| `--background` | `False` | boolean | Run build in background |
| `--workflow` | `"standard_project"` | string | Workflow type to use |
| `--max-iterations` | `3` | integer | Maximum iterations for iteration workflow |

### Status Command Defaults

| Option | Default Value | Type | Description |
|--------|---------------|------|-------------|
| `--watch` | `False` | boolean | Watch status in real-time |
| `--logs` | `False` | boolean | Show recent logs from agents |
| `--detailed` | `False` | boolean | Show detailed task information |
| `--refresh-rate` | `2` | integer | Refresh rate in seconds for watch mode |

### Analyze-Logs Command Defaults

| Option | Default Value | Type | Description |
|--------|---------------|------|-------------|
| `--logs-dir` | `".swarmdev/logs"` | string | Directory containing log files |
| `--output` | `"workflow_analysis.md"` | string | Output file for analysis report |
| `--show-report` | `False` | boolean | Display report summary in terminal |

## Configuration File Defaults

### File Locations (in order of precedence)

1. Path specified by `--config` command-line argument
2. `.swarmdev/swarmdev_config.json` in project directory
3. `./swarmdev_config.json` in current directory

### LLM Configuration Defaults

```json
{
  "llm": {
    "provider": "auto",
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 4000,
    "timeout": 60
  }
}
```

**Model-Aware Behavior:**
- Parameters automatically optimized per model family
- Token limits enforced based on model capabilities
- Temperature restrictions handled for reasoning models

### Project Configuration Defaults

```json
{
  "project": {
    "project_dir": "./project",
    "max_runtime": 3600
  }
}
```

### Agent Configuration Defaults

With the model-aware system, agents inherit LLM settings automatically:

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

**Note:** Agent-specific model and temperature configurations are no longer needed or supported.

### Memory Configuration Defaults

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

### Workflow Configuration Defaults

```json
{
  "workflow": {
    "parallelism": 4,
    "timeout": 3600,
    "retry_attempts": 3,
    "checkpoint_interval": 300
  }
}
```

### MCP Configuration Defaults

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

## Workflow Defaults

### Available Workflows

| Workflow ID | Name | Description | Default Max Iterations |
|-------------|------|-------------|----------------------|
| `standard_project` | Standard Project Workflow | Research → Planning → Development → Documentation | N/A |
| `research_only` | Research Only Workflow | Conduct research without implementation | N/A |
| `development_only` | Development Only Workflow | Development and documentation (assumes research done) | N/A |
| `indefinite` | Indefinite Improvement Workflow | Continuous improvement until manually stopped | Unlimited |
| `iteration` | Iteration Improvement Workflow | Configurable number of improvement cycles | 3 |

## Agent Configuration Defaults

### Agent Capabilities by Type

| Agent Type | Primary Function | Memory Enabled | Default Count |
|------------|------------------|----------------|---------------|
| Research | Information gathering and analysis | true | 1 |
| Planning | Blueprint creation and planning | true | 1 |
| Development | Code implementation | true | 2 |
| Documentation | Documentation creation | true | 1 |
| Analysis | Project analysis and improvement | true | 1 |

## Directory Structure Defaults

### Default Project Layout

```
./project/                 # Main project directory
├── .swarmdev/            # SwarmDev metadata and configuration
│   ├── swarmdev_config.json  # Project configuration
│   ├── mcp_config.json       # MCP tools configuration
│   ├── logs/                 # Agent execution logs
│   └── goals/                # Goal storage
├── src/                  # Source code (if applicable)
├── docs/                 # Documentation
├── tests/                # Tests (if applicable)
└── README.md            # Project README
```

### Log Configuration Defaults

| Setting | Default Value | Description |
|---------|---------------|-------------|
| Console Logging | Enabled | Log to console/stdout |
| File Logging | Enabled | Log to `.swarmdev/logs/swarmdev.log` |
| Agent Logging | Enabled | Separate logs per agent type |
| Log Level | INFO | Default logging level |

## Environment Variable Defaults

### Required Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | If using OpenAI | OpenAI API key |
| `ANTHROPIC_API_KEY` | If using Anthropic | Anthropic API key |
| `GOOGLE_API_KEY` | If using Google | Google API key |

### Optional Environment Variables

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `SWARMDEV_LLM_PROVIDER` | `"auto"` | Default LLM provider |
| `SWARMDEV_PROJECT_DIR` | `"./project"` | Default project directory |
| `SWARMDEV_LOG_LEVEL` | `"info"` | Default log level |

## Performance Defaults

### Resource Limits

| Setting | Default Value | Description |
|---------|---------------|-------------|
| API Timeout | 60 seconds | LLM API request timeout |
| Parallelism | 4 | Maximum parallel tasks |
| Memory Limit | System dependent | Maximum memory usage per agent |

### Error Handling Defaults

| Setting | Default Value | Description |
|---------|---------------|-------------|
| Max Retry Attempts | 3 | Maximum retry attempts for failed operations |
| Retry Backoff | Exponential | Backoff strategy for retries |
| Graceful Degradation | Enabled | Continue with partial failures |

## Model-Specific Configuration

### OpenAI Model Families

#### Standard Chat Models (GPT-4, GPT-3.5)
- Full parameter support
- Standard token limits (4000 default)
- Temperature 0.0-2.0 supported

#### Reasoning Models (o1, o3, o4 series)
- `max_tokens` → `max_completion_tokens` automatically
- Temperature fixed at 1.0 (user setting ignored)
- Higher token defaults (25,000)
- Limited parameter set

### Anthropic Model Families

#### Claude 3 Series
- Token limits enforced per model (4096 for Claude 3, 8192 for Claude 3.5)
- Standard parameter set
- Automatic limit capping

### Google Model Families

#### Gemini Series
- `max_tokens` → `max_output_tokens` automatically
- Google-specific parameters added (`top_k`)
- Model-appropriate defaults

## Override Priority

Configuration values are applied in this order (highest to lowest priority):

1. **Command-line arguments** (e.g., `--llm-provider openai`)
2. **Environment variables** (e.g., `SWARMDEV_LLM_PROVIDER=openai`)
3. **Configuration file values** (JSON files)
4. **Model-aware defaults** (based on selected model)
5. **Built-in system defaults** (documented above)

## Migration from Legacy Configuration

### Deprecated Settings

The following settings are no longer needed with the model-aware system:

- Agent-specific `model` settings (inherited from main LLM config)
- Agent-specific `temperature` settings (optimized automatically)
- Model-specific parameter configurations (handled automatically)
- YAML configuration files (JSON only now)

### Migration Example

**Old Configuration:**
```json
{
  "agents": {
    "research": {"count": 1, "model": "gpt-4o", "temperature": 0.5},
    "development": {"count": 2, "model": "gpt-4o", "temperature": 0.2}
  }
}
```

**New Configuration:**
```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7
  },
  "agents": {
    "research": {"count": 1},
    "development": {"count": 2}
  }
}
```

The system automatically handles agent optimization based on the main LLM configuration. 