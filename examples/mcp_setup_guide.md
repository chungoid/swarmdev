# MCP (Model Context Protocol) Setup Guide

This guide shows you how to configure external MCP servers to extend your SwarmDev agents' capabilities.

## What are MCP Servers?

MCP servers provide additional tools and capabilities that your SwarmDev agents can use during project development. They can offer specialized reasoning, context management, documentation lookup, and more.

## Quick Setup

### 1. Prepare Docker Images

First, ensure you have the MCP server Docker images available:

```bash
# Pull the sequential thinking MCP server
docker pull mcp/sequentialthinking

# Pull the Context7 MCP server  
docker pull context7-mcp
```

### 2. Copy Example Configuration Files

Copy the example configuration files to your project:

```bash
# Copy the main SwarmDev config
cp examples/swarmdev_config.json ./swarmdev.json

# Copy the MCP configuration
cp examples/mcp_config.json ./mcp_config.json
```

### 3. Update Your Environment

Set any required environment variables:

```bash
# For Context7 (if API key required)
export CONTEXT7_API_KEY="your-api-key-if-needed"

# Ensure Docker network exists
docker network create swarmdev
```

## Configuration Files Explained

### Main Configuration (`swarmdev.json`)

The main configuration enables MCP tools and points to the MCP config file:

```json
{
  "mcp_tools": {
    "enabled": true,
    "config_file": "./mcp_config.json",
    "docker_enabled": true,
    "docker_network": "swarmdev",
    "tools": [
      {
        "id": "sequentialthinking",
        "enabled": true,
        "capabilities": ["reasoning", "planning", "analysis"]
      },
      {
        "id": "context7", 
        "enabled": true,
        "capabilities": ["context_management", "reasoning", "documentation"]
      }
    ]
  }
}
```

### MCP Configuration (`mcp_config.json`)

This file defines how to connect to each MCP server:

```json
{
  "mcpServers": {
    "sequentialthinking": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "mcp/sequentialthinking"],
      "timeout": 30,
      "capabilities": ["reasoning", "planning", "analysis", "problem_solving"]
    },
    "context7": {
      "command": "docker", 
      "args": ["run", "-i", "--rm", "context7-mcp"],
      "timeout": 60,
      "capabilities": ["context_management", "reasoning", "documentation"]
    }
  }
}
```

## Using MCP Tools in Your Workflow

### Sequential Thinking Server

The sequential thinking server helps agents with complex reasoning tasks:

```bash
# When building projects that require complex planning
swarmdev build --goal complex_project.txt --workflow standard_project
```

Your agents will automatically use sequential thinking for:
- Breaking down complex problems
- Planning implementation strategies  
- Analyzing trade-offs and alternatives
- Multi-step reasoning processes

### Context7 Server

The Context7 server provides advanced context management:

```bash
# For projects requiring extensive documentation or library research
swarmdev build --goal research_project.txt --workflow research_only
```

Your agents will use Context7 for:
- Looking up library documentation
- Managing project context across tasks
- Generating comprehensive documentation
- Reasoning about code relationships

## Advanced Configuration

### Custom Docker Networks

Create isolated networks for different projects:

```bash
# Create project-specific network
docker network create my-project-swarmdev

# Update mcp_config.json
{
  "mcpSettings": {
    "dockerNetwork": "my-project-swarmdev"
  }
}
```

### Resource Limits

Control Docker resource usage:

```json
{
  "mcpSettings": {
    "dockerMemoryLimit": "1g",
    "dockerCpuLimit": 0.5,
    "globalTimeout": 180
  }
}
```

### Selective Tool Usage

Enable tools only for specific workflows:

```json
{
  "mcp_tools": {
    "tools": [
      {
        "id": "sequentialthinking",
        "enabled": true,
        "workflows": ["standard_project", "iteration"]
      },
      {
        "id": "context7",
        "enabled": true, 
        "workflows": ["research_only", "standard_project"]
      }
    ]
  }
}
```

## Troubleshooting

### Docker Issues

```bash
# Check if Docker is running
docker info

# Verify images are available
docker images | grep -E "(mcp/sequentialthinking|context7-mcp)"

# Test MCP server manually
docker run --rm -i mcp/sequentialthinking
```

### Network Issues

```bash
# Check network exists
docker network ls | grep swarmdev

# Recreate network if needed
docker network rm swarmdev
docker network create swarmdev
```

### Permission Issues

```bash
# Ensure user can run Docker
sudo usermod -aG docker $USER
# Then logout and login again
```

## Monitoring MCP Tools

### Enable Logging

Set detailed logging in your configuration:

```json
{
  "mcpSettings": {
    "logLevel": "debug",
    "enableMetrics": true
  }
}
```

### Check Tool Usage

Monitor which tools your agents are using:

```bash
# Watch SwarmDev logs
tail -f swarmdev.log | grep -i mcp

# Check specific agent logs
tail -f logs/development_agent.log | grep -i "sequential\|context7"
```

## Example Workflow with MCP Tools

Here's a complete example of using SwarmDev with MCP tools:

```bash
# 1. Set up configuration
cp examples/swarmdev_config.json ./swarmdev.json
cp examples/mcp_config.json ./mcp_config.json

# 2. Create goal file
echo "Create a React dashboard with user authentication, data visualization charts, and real-time updates. Include comprehensive documentation and testing." > goal.txt

# 3. Start build with MCP tools enabled
swarmdev build --goal goal.txt --workflow standard_project --project-dir ./dashboard

# 4. Monitor progress (agents will use MCP tools automatically)
swarmdev status --project-id <project-id> --watch --detailed
```

Your agents will automatically leverage:
- **Sequential thinking** for complex architecture planning
- **Context7** for React library documentation and best practices
- Enhanced reasoning capabilities throughout the development process

## Next Steps

- Explore creating custom MCP servers for domain-specific tools
- Configure additional MCP servers from the community
- Set up monitoring and metrics for MCP tool performance
- Experiment with different tool combinations for various project types 