# Installation Guide

This guide will help you install and set up SwarmDev on your system.

## Prerequisites

Before installing SwarmDev, ensure you have:

- **Python 3.9 or higher** - Required for the core SwarmDev platform
- **Docker** - Required for enhanced MCP servers (7 built-in servers)
- **Git** - For cloning the repository and version control operations
- **API Key** - At least one of: OpenAI, Anthropic (Claude), or Google

### System Requirements

- **Operating System**: Linux, macOS, or Windows (with WSL2 recommended)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Disk Space**: 2GB for installation and Docker images
- **Internet Connection**: Required for API calls and Docker image downloads

## Installation Methods

### Method 1: Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/chungoid/swarmdev.git
cd swarmdev

# Install using pipx (recommended for isolation)
pipx install .
pipx ensurepath && exec $SHELL

# Pull Docker images for MCP servers
swarmdev pull-images
```

### Method 2: Development Install

If you plan to contribute or modify SwarmDev:

```bash
# Clone the repository
git clone https://github.com/chungoid/swarmdev.git
cd swarmdev

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

# Pull Docker images
swarmdev pull-images
```

### Method 3: Traditional pip Install

```bash
# Clone and install
git clone https://github.com/chungoid/swarmdev.git
cd swarmdev
pip install .

# Pull Docker images
swarmdev pull-images
```

## Docker Setup

SwarmDev uses 7 built-in Docker-based MCP servers. After installation, ensure Docker is properly configured:

### Fix Docker Permissions (Linux/macOS)

If you encounter "permission denied" or "broken pipe" errors:

```bash
# Automatic fix (recommended)
swarmdev fix-docker-group

# Manual fix
sudo usermod -aG docker $USER
newgrp docker  # Activate in current session
```

**Note**: Group membership changes require a new login session to fully take effect.

### Docker on Windows

For Windows users, ensure:
- Docker Desktop is installed and running
- WSL2 backend is enabled (recommended)
- Your user account has Docker access

## API Configuration

SwarmDev supports multiple LLM providers. You need at least one API key.

### Method 1: Environment Variables

```bash
# OpenAI (GPT models)
export OPENAI_API_KEY="your-openai-key-here"

# Anthropic (Claude models)
export ANTHROPIC_API_KEY="your-anthropic-key-here"

# Google (Gemini models)
export GOOGLE_API_KEY="your-google-key-here"
```

### Method 2: .env File

Create a `.env` file in your project directory or home directory:

```
# .env file
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
GOOGLE_API_KEY=your-google-key-here

# Optional: Set default provider
SWARMDEV_LLM_PROVIDER=openai
SWARMDEV_LLM_MODEL=gpt-4o
```

### Method 3: Configuration File

Create a configuration file at `~/.swarmdev/config.json`:

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4o",
    "api_key": "your-api-key-here"
  }
}
```

## Verification

### Test Installation

```bash
# Check SwarmDev is installed
swarmdev --version

# Check help
swarmdev --help
```

### Test MCP Integration

Run the comprehensive MCP test suite:

```bash
cd scripts
python3 test_mcp_installation.py
```

Expected output:
```
============================================================
FINAL TEST REPORT
============================================================

Overall Score: 100.0% (6/6 tests passed)

Configuration Loading: PASSED
   Servers found: 7

Server Initialization: PASSED

Functionality Tests:
   memory: PASSED (0.48s)
   time: PASSED (0.79s)
   git: PASSED (0.88s)

Performance Test: PASSED

EXCELLENT! Your MCP installation is working great!
```

### Test Agent Integration

```bash
python3 test_collaborative_agent.py
```

Expected output:
```
============================================================
COLLABORATIVE AGENT TEST REPORT
============================================================

Docker Infrastructure Status:
  memory: Container running
  sequential-thinking: Container running
  context7: Container running
  git: Container running
  time: Container running
  fetch: Container running
  filesystem: Container running

Infrastructure Score: 7/7 containers working

Agent Integration Score: 7/7 tools working
Success Rate: 100.0%

Overall Assessment:
PASS: All MCP tools and agent integration working perfectly!

TEST SUITE: PASS - All systems operational
```

## Troubleshooting

### Common Issues

#### "Command not found: swarmdev"

**Solution**: Ensure your PATH includes pipx binaries:
```bash
pipx ensurepath
exec $SHELL
```

#### Docker Permission Errors

**Solution**: Fix Docker group membership:
```bash
swarmdev fix-docker-group
# Then log out and back in, or run: newgrp docker
```

#### API Key Not Found

**Solution**: Verify your API key configuration:
```bash
# Check environment variables
echo $OPENAI_API_KEY

# Test with explicit key
swarmdev build --goal "test" --openai-api-key "your-key"
```

#### MCP Servers Not Starting

**Solution**: 
1. Ensure Docker is running: `docker ps`
2. Pull images manually: `swarmdev pull-images`
3. Check Docker permissions (see above)

### Getting Help

If you encounter issues:

1. **Check the logs**: SwarmDev creates logs in `~/.swarmdev/logs/`
2. **Run diagnostics**: `swarmdev status --verbose`
3. **GitHub Issues**: [Report issues](https://github.com/chungoid/swarmdev/issues)
4. **CLI Help**: `swarmdev --help` or `swarmdev <command> --help`

## Next Steps

Once installation is complete:

1. **Quick Start**: Follow the [Quick Start Tutorial](quick-start.md)
2. **Examples**: Explore [Examples & Use Cases](examples.md)
3. **Configuration**: Review [Configuration Guide](../configuration/README.md)

---

**Installation complete!** You're ready to start building with SwarmDev. 