# SwarmDev CLI Reference

Complete command-line interface reference for the SwarmDev platform with model-aware configuration.

## Overview

SwarmDev provides a command-line interface with multiple commands for different workflows:

- `swarmdev assistant` - Interactive assistant for complete project setup
- `swarmdev refine` - Goal refinement through conversation  
- `swarmdev build` - Build a project from a goal file
- `swarmdev status` - Check project status and monitor progress
- `swarmdev workflows` - List available workflows
- `swarmdev analyze-logs` - Analyze agent logs and generate reports

## Model-Aware Configuration Benefits

SwarmDev automatically optimizes parameters for your chosen LLM model:

- **Simple Configuration**: Same settings work across all providers and models
- **Automatic Parameter Translation**: `max_tokens` becomes `max_completion_tokens` for o1, `max_output_tokens` for Gemini
- **Constraint Handling**: Temperature restrictions for reasoning models (o1, o3, o4 series) handled automatically

## Global Options

These options can be used with any command:

| Option | Default | Description |
|--------|---------|-------------|
| `--verbose`, `-v` | False | Enable verbose output |
| `--quiet`, `-q` | False | Suppress all output except errors |
| `--log-level` | `info` | Set logging level (debug, info, warning, error) |
| `--config` | None | Path to configuration file |
| `--help`, `-h` | - | Show help message and exit |

## Commands

### `swarmdev assistant`

Interactive assistant for complete project setup with guided conversation.

**Usage:**
```bash
swarmdev assistant [options]
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--llm-provider` | `auto` | LLM provider to use (openai, anthropic, google, auto) |
| `--llm-model` | Provider default | LLM model to use |

**Model-Aware Examples:**
```bash
# Start assistant with auto-detected LLM provider (model-aware optimization)
swarmdev assistant

# Use OpenAI o1 model (temperature automatically set to 1.0)
swarmdev assistant --llm-provider openai --llm-model o1-mini

# Use Anthropic Claude (token limits automatically enforced)
swarmdev assistant --llm-provider anthropic --llm-model claude-3-5-sonnet-20241022

# Use Google Gemini (parameters automatically translated)
swarmdev assistant --llm-provider google --llm-model gemini-2.0-flash-001
```

### `swarmdev refine`

Refine a project goal through conversation.

**Usage:**
```bash
swarmdev refine [options]
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--output`, `-o` | None | Output file for the refined goal |

**Examples:**
```bash
# Refine goal and save to goal.txt
swarmdev refine --output goal.txt

# Refine goal interactively (no file output)
swarmdev refine
```

### `swarmdev build`

Build a project from a goal file using the swarm of AI agents with model-aware optimization.

**Usage:**
```bash
swarmdev build --goal GOAL_FILE [options]
```

**Required Options:**
| Option | Description |
|--------|-------------|
| `--goal`, `-g` | Path to goal file (required) |

**Optional Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--project-dir`, `-d` | `./project` | Project directory where files will be created |
| `--max-runtime` | `3600` | Maximum runtime in seconds |
| `--llm-provider` | `auto` | LLM provider to use (openai, anthropic, google, auto) |
| `--llm-model` | Provider default | LLM model to use |
| `--background`, `-b` | False | Run build in background and return immediately |
| `--wait`, `-w` | True | Wait for build to complete (default behavior) |
| `--workflow` | `standard_project` | Workflow type to use |
| `--max-iterations` | `3` | Maximum iterations for iteration workflow |

**Available Workflows:**
- `standard_project` - Research → Planning → Development → Documentation
- `research_only` - Conduct research only
- `development_only` - Development and documentation (assumes research done)
- `indefinite` - Continuous improvement until manually stopped
- `iteration` - Configurable number of improvement cycles

**Model-Aware Examples:**
```bash
# Basic build with auto-detected provider (model-aware optimization)
swarmdev build --goal my_goal.txt

# OpenAI o1 model (reasoning model constraints handled automatically)
swarmdev build --goal goal.txt --llm-provider openai --llm-model o1-mini --project-dir ./my_app

# Anthropic Claude (token limits automatically enforced to 8192)
swarmdev build --goal goal.txt --llm-provider anthropic --llm-model claude-3-5-sonnet-20241022

# Google Gemini (max_tokens → max_output_tokens automatically)
swarmdev build --goal goal.txt --llm-provider google --llm-model gemini-2.0-flash-001

# Background build with iteration workflow
swarmdev build --goal goal.txt --background --workflow iteration --max-iterations 5

# Research-only workflow with any provider
swarmdev build --goal goal.txt --workflow research_only

# Indefinite improvement workflow
swarmdev build --goal goal.txt --workflow indefinite
```

### `swarmdev status`

Check the status of a project and monitor progress.

**Usage:**
```bash
swarmdev status --project-id PROJECT_ID [options]
```

**Required Options:**
| Option | Description |
|--------|-------------|
| `--project-id`, `-p` | Project ID (required) |

**Optional Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--watch`, `-w` | False | Watch status in real-time (updates every 2 seconds) |
| `--logs`, `-l` | False | Show recent logs from agents |
| `--detailed` | False | Show detailed task information |
| `--refresh-rate` | `2` | Refresh rate in seconds for --watch mode |

**Examples:**
```bash
# Basic status check
swarmdev status --project-id project_20250530_223934

# Watch status in real-time
swarmdev status --project-id project_20250530_223934 --watch

# Detailed status with logs (shows MCP usage and LLM metrics)
swarmdev status --project-id project_20250530_223934 --detailed --logs

# Fast refresh monitoring
swarmdev status --project-id project_20250530_223934 --watch --refresh-rate 1
```

### `swarmdev workflows`

List available workflows and their descriptions.

**Usage:**
```bash
swarmdev workflows [options]
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--verbose` | False | Show detailed workflow descriptions and usage examples |

**Examples:**
```bash
# List workflows
swarmdev workflows

# Show detailed descriptions
swarmdev workflows --verbose
```

### `swarmdev analyze-logs`

Analyze agent logs and generate workflow performance reports.

**Usage:**
```bash
swarmdev analyze-logs [options]
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--logs-dir` | `.swarmdev/logs` | Directory containing log files |
| `--output`, `-o` | `workflow_analysis.md` | Output file for analysis report |
| `--workflow-id` | None | Filter analysis by specific workflow ID |
| `--show-report` | False | Display report summary in terminal |

**Examples:**
```bash
# Analyze logs with default settings
swarmdev analyze-logs

# Custom logs directory and output
swarmdev analyze-logs --logs-dir ./project/.swarmdev/logs --output analysis.md

# Show summary in terminal
swarmdev analyze-logs --show-report

# Filter by workflow ID
swarmdev analyze-logs --workflow-id standard_project --show-report
```

## LLM Provider Configuration

### Model-Aware Default Models

When using `--llm-provider` without specifying a model, these defaults are used with automatic optimization:

| Provider | Default Model | Automatic Optimizations |
|----------|---------------|-------------------------|
| `openai` | `o4-mini-2025-04-16` | Parameter translation for reasoning models, temperature constraints |
| `anthropic` | `claude-3-opus-20240229` | Token limit enforcement (8192 for Claude 3.5) |
| `google` | `gemini-2.0-flash-001` | Parameter translation (max_tokens → max_output_tokens) |

### Auto Provider Selection

When using `--llm-provider auto` (default), the system will:

1. Check for available API keys in environment variables
2. Register providers with available API keys
3. Use the first available provider as default
4. Prefer OpenAI if multiple providers are available
5. Apply model-aware optimizations automatically

### Model-Specific Behavior

#### Reasoning Models (o1, o3, o4 series)
- Temperature automatically forced to 1.0 (user setting ignored)
- `max_tokens` becomes `max_completion_tokens` automatically
- Higher default token limits (25,000)
- Limited parameter set (some parameters excluded automatically)

#### Standard Chat Models (GPT-4, Claude, etc.)
- Full parameter support
- Model-specific token limit enforcement
- Standard parameter translation

#### Multimodal Models
- Vision capabilities detected automatically
- Extended context windows utilized appropriately

## Configuration Files

SwarmDev looks for configuration files in this order:

1. Path specified by `--config` argument
2. `.swarmdev/swarmdev_config.json` in project directory (recommended)
3. `./swarmdev_config.json` in current directory (fallback)

## Environment Variables

Required environment variables for LLM providers:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `GOOGLE_API_KEY` | Google API key |

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error (missing files, configuration errors, etc.) |

## Common Usage Patterns

### Complete Workflow with Model-Aware System
```bash
# 1. Refine your goal
swarmdev refine --output goal.txt

# 2. Build with auto-detected provider (model-aware optimization)
swarmdev build --goal goal.txt --project-dir ./my_project

# 3. Monitor progress with detailed metrics
swarmdev status --project-id project_20250530_223934 --watch --detailed
```

### Interactive Development
```bash
# Use assistant for guided setup (automatically optimized for your available models)
swarmdev assistant

# The assistant will help you refine goals, recommend optimal configurations, and start builds
```

### Provider Switching with Same Configuration
```bash
# Same project with different providers (no config changes needed)
swarmdev build --goal goal.txt --llm-provider openai --llm-model o4-mini-2025-04-16
swarmdev build --goal goal.txt --llm-provider anthropic --llm-model claude-3-5-sonnet-20241022
swarmdev build --goal goal.txt --llm-provider google --llm-model gemini-2.0-flash-001
```

### Background Processing
```bash
# Start build in background
swarmdev build --goal goal.txt --background

# Check status periodically (includes MCP and LLM usage metrics)
swarmdev status --project-id project_20250530_223934

# Analyze results when complete
swarmdev analyze-logs --show-report
```

### Continuous Improvement
```bash
# Run indefinite improvement workflow
swarmdev build --goal goal.txt --workflow indefinite

# Monitor in another terminal
swarmdev status --project-id project_20250530_223934 --watch --detailed
```

## Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   OPENAI_API_KEY environment variable not set
   ```
   Solution: Set the appropriate API key environment variable or use `--llm-provider auto` to auto-detect available providers

2. **Goal File Not Found**
   ```
   Goal file not found: goal.txt
   ```
   Solution: Ensure the goal file exists and path is correct

3. **Project Not Found**
   ```
   Project not found: project_12345
   ```
   Solution: Check project ID and ensure project directory exists

4. **Model Parameter Conflicts (Rare with Model-Aware System)**
   ```
   Model parameter error
   ```
   Solution: The model-aware system prevents most conflicts automatically. If issues persist, check model availability.

### Debug Mode

Use `--verbose` and `--log-level debug` for detailed debugging:

```bash
swarmdev build --goal goal.txt --verbose --log-level debug
```

### Log Files

SwarmDev creates log files in the project's `.swarmdev/logs/` directory:
- `swarmdev.log` - Main application log
- Agent-specific logs for detailed execution tracking
- MCP usage and LLM metrics included in status reports 