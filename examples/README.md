# SwarmDev Examples

This directory contains practical examples and configuration files to help you get started with SwarmDev quickly.

## Files Overview

### Getting Started
- **`basic_usage.md`** - Step-by-step guide for your first SwarmDev project
- **`swarmdev_config.json`** - Example main configuration file with optimal settings

### MCP (Model Context Protocol) Setup
- **`mcp_config.json`** - Example MCP server configuration
- **`mcp_setup_guide.md`** - Complete guide for setting up external MCP servers

## Quick Start

### 1. Basic Project Setup

```bash
# Copy the example configuration
cp examples/swarmdev_config.json ./swarmdev.json

# Start the interactive assistant
swarmdev assistant
```

### 2. Advanced Setup with MCP Tools

```bash
# Copy both configuration files
cp examples/swarmdev_config.json ./swarmdev.json
cp examples/mcp_config.json ./mcp_config.json

# Docker network is optional (set to null in config for default)

# Pull MCP server images
docker pull mcp/sequentialthinking
docker pull context7-mcp

# Start building with enhanced capabilities
swarmdev build --goal your_goal.txt --config ./swarmdev.json
```

## Configuration Files Explained

### Main Configuration (`swarmdev_config.json`)

This file contains optimal settings for most projects:

- **LLM Settings**: Configured for OpenAI GPT-4o with balanced temperature
- **Agent Configuration**: Multiple agents with specialized roles
- **Memory System**: Enabled with vector storage for context retention  
- **Workflow Settings**: Balanced parallelism and timeout settings
- **MCP Integration**: Enabled with external reasoning and context management servers

### MCP Configuration (`mcp_config.json`)

Defines two powerful external MCP servers:

- **Sequential Thinking**: Advanced reasoning and planning capabilities
- **Context7**: Enhanced context management and documentation lookup

## Usage Examples

### Simple Todo App
```bash
# Using the assistant (recommended for beginners)
swarmdev assistant
# Then describe: "Create a React todo app with CRUD operations"
```

### Complex Dashboard Project
```bash
# Direct build with MCP tools for complex projects
echo "Create a React dashboard with authentication, charts, and real-time updates" > goal.txt
swarmdev build --goal goal.txt --config examples/swarmdev_config.json --workflow standard_project
```

### Research-Only Project
```bash
# Use Context7 for comprehensive research
echo "Research modern Python web frameworks and their performance characteristics" > research_goal.txt
swarmdev build --goal research_goal.txt --workflow research_only --config examples/swarmdev_config.json
```

## Customization Tips

### Adjust for Your Hardware
```json
{
  "workflow": {
    "parallelism": 2,  // Reduce for slower machines
    "timeout": 7200    // Increase for complex projects
  },
  "agents": {
    "development": {
      "count": 1       // Reduce agent count to save resources
    }
  }
}
```

### Use Different LLM Providers
```json
{
  "llm": {
    "provider": "anthropic",              // or "google"
    "model": "claude-3-opus-20240229",    // or "gemini-2.0-flash-001"
    "temperature": 0.7
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
# Required: At least one LLM provider
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"  # Alternative
export GOOGLE_API_KEY="your-google-key"        # Alternative

# Optional: MCP tool configuration
export CONTEXT7_API_KEY="your-context7-key"    # If required by Context7
export SWARMDEV_CONFIG_FILE="./swarmdev.json"  # Custom config location
```

## Troubleshooting

### Common Issues

1. **No LLM Provider Available**
   ```bash
   # Ensure API key is set
   echo $OPENAI_API_KEY
   # Should show your API key
   ```

2. **Docker Issues with MCP**
   ```bash
   # Check Docker is running
   docker info
   
   # Verify MCP images
   docker images | grep -E "(mcp/sequentialthinking|context7-mcp)"
   ```

3. **Permission Issues**
   ```bash
   # Ensure SwarmDev directories are writable
   mkdir -p projects goals logs vector_store
   chmod 755 projects goals logs vector_store
   ```

## Next Steps

1. **Read the Guides**: Start with `basic_usage.md` for a walkthrough
2. **Set Up MCP**: Follow `mcp_setup_guide.md` for enhanced capabilities  
3. **Experiment**: Try different workflows and configurations
4. **Monitor**: Use `swarmdev status` to watch your projects develop
5. **Iterate**: Use the iteration workflow to continuously improve projects

## Getting Help

- Check the main documentation in `docs/`
- Review configuration defaults in `docs/configuration/defaults.md`
- For CLI help: `swarmdev --help` or `swarmdev <command> --help`
- Monitor logs in the `logs/` directory for debugging
