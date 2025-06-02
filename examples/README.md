# SwarmDev Examples

This directory contains practical examples and configuration files to help you get started with SwarmDev quickly.

## Files Overview

### Getting Started
- **`basic_usage.md`** - Step-by-step guide for your first SwarmDev project
- **`swarmdev_config.json`** - Example main configuration file with model-aware settings

### MCP (Model Context Protocol) Setup
- **`mcp_config.json`** - **CORRECT** MCP server configuration for all 7 bundled servers
- **`mcp_setup_guide.md`** - Complete guide for setting up external MCP servers

## Model-Aware Configuration System

SwarmDev now uses an intelligent **model-aware configuration system** that automatically optimizes parameters for any LLM model:

### Key Benefits:
- **Same Config Everywhere**: Use identical settings across OpenAI, Anthropic, and Google models
- **Automatic Parameter Translation**: `max_tokens` becomes `max_completion_tokens` for o1, `max_output_tokens` for Gemini
- **Smart Constraints**: Temperature restrictions for reasoning models (o1, o3, o4 series) handled automatically
- **Optimal Defaults**: Each model family gets appropriate token limits and parameters

## Built-in MCP Servers

SwarmDev includes **7 bundled Docker-based MCP servers** that work out of the box:

1. **git** - Git operations and repository management
2. **time** - Time zone operations and conversions  
3. **fetch** - Web content fetching and processing
4. **filesystem** - File system operations with current directory access
5. **memory** - Persistent memory storage for context
6. **sequential-thinking** - Advanced reasoning through sequential thoughts
7. **context7** - Up-to-date documentation and code examples

**Important**: The `mcp_config.json` file shows the correct configuration format. SwarmDev works without any MCP configuration files (uses built-in defaults), but you can customize server settings using this format.

cp examples/swarmdev_config.json .swarmdev/swarmdev_config.json

# Start the interactive assistant
swarmdev assistant
```

### 2. Direct Build (Skip Assistant)

```bash
# Create a goal file
echo "Create a React todo app with CRUD operations" > goal.txt

# Build with default settings (uses built-in MCP servers automatically)
swarmdev build --goal goal.txt --project-dir ./my_project
```

### 3. Advanced Setup with Custom MCP Configuration

```bash
# Copy both configuration files to project
mkdir -p my_project/.swarmdev
cp examples/swarmdev_config.json my_project/.swarmdev/
cp examples/mcp_config.json my_project/.swarmdev/

# Start building with customized MCP settings
swarmdev build --goal goal.txt --project-dir ./my_project
```

## Configuration Files Explained

### Main Configuration (`.swarmdev/swarmdev_config.json`)

The model-aware configuration automatically handles differences between providers:

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 4000
  }
}
```

**Works identically with any provider:**
- **OpenAI**: `gpt-4o`, `o1-mini`, `gpt-3.5-turbo`
- **Anthropic**: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`
- **Google**: `gemini-2.0-flash-001`, `gemini-1.5-pro`

### MCP Configuration (`.swarmdev/mcp_config.json`)

Configure the 7 bundled MCP servers (all Docker-based):

```json
{
  "servers": {
    "git": {
      "command": ["docker", "run", "--rm", "-i", "mcp/git"],
      "timeout": 30,
      "enabled": true,
      "description": "Git operations and repository management"
    },
    "sequential-thinking": {
      "command": ["docker", "run", "--rm", "-i", "mcp/sequentialthinking"],
      "timeout": 60,
      "enabled": true,
      "description": "Advanced reasoning through sequential thoughts"
    },
    "context7": {
      "command": ["docker", "run", "--rm", "-i", "-e", "MCP_TRANSPORT=stdio", "context7-mcp"],
      "timeout": 30,
      "enabled": true,
      "description": "Up-to-date documentation and code examples"
    }
  },
  "settings": {
    "defaultTimeout": 30,
    "persistentConnections": true,
    "autoDiscovery": true,
    "retryCount": 3,
    "retryDelay": 1.0
  }
}
```

**Note**: This is just a partial example. The complete file includes all 7 servers (git, time, fetch, filesystem, memory, sequential-thinking, context7).

## Provider Examples

### OpenAI with o1 Reasoning Model
```bash
# Configuration automatically handles o1 constraints
swarmdev build --goal goal.txt --llm-provider openai --llm-model o1-mini
# Temperature ignored (forced to 1.0), max_tokens becomes max_completion_tokens
```

### Anthropic Claude
```bash
# Automatic token limit enforcement (8192 for Claude 3.5)
swarmdev build --goal goal.txt --llm-provider anthropic --llm-model claude-3-5-sonnet-20241022
```

### Google Gemini
```bash
# Automatic parameter translation (max_tokens → max_output_tokens)
swarmdev build --goal goal.txt --llm-provider google --llm-model gemini-2.0-flash-001
```

## Usage Examples

### Interactive Assistant (Recommended)
```bash
swarmdev assistant
# Guides you through goal refinement and configuration
# Automatically suggests optimal settings for your project
```

### Research Project with Documentation Lookup
```bash
echo "Research modern Python web frameworks and their performance characteristics" > research_goal.txt
swarmdev build --goal research_goal.txt --workflow research_only
```

### Complex Dashboard Project
```bash
echo "Create a React dashboard with authentication, charts, and real-time updates" > dashboard_goal.txt
swarmdev build --goal dashboard_goal.txt --workflow standard_project --project-dir ./dashboard
```

### Iterative Improvement
```bash
# Start with basic implementation
swarmdev build --goal goal.txt --workflow development_only --project-dir ./app

# Then improve with iterations
swarmdev build --goal goal.txt --workflow iteration --max-iterations 3 --project-dir ./app
```

## Customization Tips

### Simple Provider Switching
```json
{
  "llm": {
    "provider": "anthropic",           // Change provider
    "model": "claude-3-5-sonnet-20241022",  // Change model
    "temperature": 0.7                 // Same config works everywhere
  }
}
```

### Resource Optimization
```json
{
  "workflow": {
    "parallelism": 2,     // Reduce for slower machines
    "timeout": 7200       // Increase for complex projects
  },
  "agents": {
    "development": {
      "count": 1          // Reduce agent count to save resources
    }
  }
}
```

### Disable MCP Tools
```json
{
  "mcp": {
    "enabled": false
  }
}
```

## Environment Variables

Set these in your shell or `.env` file:

```bash
# Required: At least one LLM provider API key
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"  # Alternative
export GOOGLE_API_KEY="your-google-key"        # Alternative

# Optional: MCP tool configuration  
export CONTEXT7_API_KEY="your-context7-key"    # If using Context7

# Optional: Default settings
export SWARMDEV_LLM_PROVIDER="auto"            # Auto-detect available providers
export SWARMDEV_PROJECT_DIR="./projects"       # Default project directory
```

## Workflow Types

Choose the right workflow for your project:

### `standard_project` (Default)
Complete development: Research → Planning → Development → Documentation

### `research_only`
Focus on research and technology analysis only

### `development_only`
Skip research and planning, implement immediately

### `indefinite`
Continuous improvement cycles until manually stopped

### `iteration`
Fixed number of improvement cycles (use `--max-iterations`)

## File Locations

SwarmDev looks for configuration files in this order:

1. `.swarmdev/swarmdev_config.json` in project directory (recommended)
2. `./swarmdev_config.json` in current directory (fallback)
3. Path specified by `--config` argument

## Troubleshooting

### Common Issues

1. **No LLM Provider Available**
   ```bash
   # Check API keys are set
   echo $OPENAI_API_KEY
   # Use 'auto' provider to detect available keys
   swarmdev build --goal goal.txt --llm-provider auto
   ```

2. **Configuration Not Found**
   ```bash
   # Ensure config is in the right location
   ls .swarmdev/swarmdev_config.json
   # Or specify explicitly
   swarmdev build --goal goal.txt --config my_config.json
   ```

3. **Model Parameter Errors**
   ```bash
   # Model-aware system prevents most parameter conflicts
   # If issues persist, check model availability
   swarmdev build --goal goal.txt --llm-provider openai --llm-model gpt-4o
   ```

4. **Docker Issues with MCP**
   ```bash
   # Check Docker is running
   docker info
   # Ensure MCP config file exists
   ls .swarmdev/mcp_config.json
   ```

## Monitoring Your Projects

### Real-time Status
```bash
# Watch live progress
swarmdev status --project-id PROJECT_ID --watch

# Get detailed information
swarmdev status --project-id PROJECT_ID --detailed --logs
```

### Background Processing
```bash
# Start in background
swarmdev build --goal goal.txt --background

# Monitor anytime
swarmdev status --project-id PROJECT_ID --watch
```

## Next Steps

1. **Read the Guides**: Start with `basic_usage.md` for a walkthrough
2. **Try Different Providers**: Use the same config with different LLM providers
3. **Experiment with Workflows**: Try different workflow types for different project needs
4. **Set Up MCP**: Follow `mcp_setup_guide.md` for enhanced reasoning capabilities
5. **Monitor Progress**: Use `swarmdev status` to watch your projects develop

## Getting Help

- **Configuration**: See `docs/configuration/README.md` for detailed configuration options
- **Model-Aware System**: Read `MODEL_AWARE_CONFIG.md` for parameter translation details
- **CLI Help**: `swarmdev --help` or `swarmdev <command> --help`
- **Troubleshooting**: Check `docs/configuration/defaults.md` for all default values
- **Logs**: Monitor `.swarmdev/logs/` directory for detailed execution logs
