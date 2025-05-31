# SwarmDev CLI Reference

Complete command-line interface reference for the SwarmDev platform.

## Overview

SwarmDev provides a command-line interface with multiple commands for different workflows:

- `swarmdev assistant` - Interactive assistant for complete project setup
- `swarmdev refine` - Goal refinement through conversation  
- `swarmdev build` - Build a project from a goal file
- `swarmdev status` - Check project status and monitor progress
- `swarmdev workflows` - List available workflows
- `swarmdev analyze-logs` - Analyze agent logs and generate reports

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

**Examples:**
```bash
# Start assistant with auto-detected LLM provider
swarmdev assistant

# Use specific provider and model
swarmdev assistant --llm-provider openai --llm-model gpt-4o

# Use Google Gemini
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

Build a project from a goal file using the swarm of AI agents.

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

**Examples:**
```bash
# Basic build with default settings
swarmdev build --goal my_goal.txt

# Custom project directory and workflow
swarmdev build --goal goal.txt --project-dir ./my_app --workflow iteration --max-iterations 5

# Background build with specific LLM
swarmdev build --goal goal.txt --background --llm-provider openai --llm-model gpt-4o

# Research-only workflow
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

# Detailed status with logs
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
| `--logs-dir` | `logs` | Directory containing log files |
| `--output`, `-o` | `workflow_analysis.md` | Output file for analysis report |
| `--workflow-id` | None | Filter analysis by specific workflow ID |
| `--show-report` | False | Display report summary in terminal |

**Examples:**
```bash
# Analyze logs with default settings
swarmdev analyze-logs

# Custom logs directory and output
swarmdev analyze-logs --logs-dir ./project/logs --output analysis.md

# Show summary in terminal
swarmdev analyze-logs --show-report

# Filter by workflow ID
swarmdev analyze-logs --workflow-id standard_project --show-report
```

## LLM Provider Configuration

### Default Models

When using `--llm-provider` without specifying a model, these defaults are used:

| Provider | Default Model |
|----------|---------------|
| `openai` | `gpt-4o` |
| `anthropic` | `claude-3-opus-20240229` |
| `google` | `gemini-2.0-flash-001` |

### Auto Provider Selection

When using `--llm-provider auto` (default), the system will:

1. Check for available API keys in environment variables
2. Register providers with available API keys
3. Use the first available provider as default
4. Prefer OpenAI if multiple providers are available

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

### Complete Workflow
```bash
# 1. Refine your goal
swarmdev refine --output goal.txt

# 2. Build the project
swarmdev build --goal goal.txt --project-dir ./my_project

# 3. Monitor progress
swarmdev status --project-id project_20250530_223934 --watch
```

### Interactive Development
```bash
# Use assistant for guided setup
swarmdev assistant

# The assistant will help you refine goals, configure settings, and start builds
```

### Background Processing
```bash
# Start build in background
swarmdev build --goal goal.txt --background

# Check status periodically
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
   Solution: Set the appropriate API key environment variable

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

### Debug Mode

Use `--verbose` and `--log-level debug` for detailed debugging:

```bash
swarmdev build --goal goal.txt --verbose --log-level debug
```

### Log Files

SwarmDev creates log files in the current directory:
- `swarmdev.log` - Main application log
- Additional agent logs in the `logs/` directory (when using analyze-logs) 