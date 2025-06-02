# SwarmDev MCP Setup Scripts

This directory contains scripts to set up and test SwarmDev's MCP (Model Context Protocol) integration.

## Quick Start

### 1. One-Command Setup

Run the complete setup and verification process:

```bash
python scripts/setup_mcp_servers.py
```

This script will:
- Build all MCP server Docker images
- Create default MCP configuration
- Run comprehensive installation tests
- Show you a detailed report with scoring

### 2. Manual Testing Only

If you already have everything set up and just want to test:

```bash
python scripts/test_mcp_installation.py
```

## What Gets Tested

The test suite verifies:

1. **Configuration Loading** - Can SwarmDev find and load MCP servers?
2. **Server Initialization** - Are all Docker images ready for lazy initialization?
3. **Functionality Tests** - Do the servers actually work with real calls?
   - Memory server (knowledge graph operations)
   - Time server (timezone operations)  
   - Git server (repository operations)
4. **Performance & Metrics** - Overall system health and response times

## Understanding Results

### Scoring
- **80%+** = Excellent! Everything working perfectly
- **60-79%** = Good! Minor issues that don't prevent usage
- **40-59%** = Partial! Some servers need attention
- **<40%** = Poor! Significant setup problems

### Next Steps After Setup
- Use `swarmdev status` to monitor MCP health
- Use `swarmdev build <goal>` to start building projects with MCP tools
- Check `~/.swarmdev/mcp_config.json` for configuration
- View logs in `.swarmdev/logs/mcp.log`

## Troubleshooting

### Common Issues

**Docker BuildKit Errors**
```bash
export DOCKER_BUILDKIT=1
# Then re-run setup
```

**Memory Server Connection Issues**
The memory server sometimes needs a moment to start up. This is usually not a problem in real usage.

**No Servers Found**
Check that Docker is running and you have the required dependencies installed.

### Manual Server Testing

Test individual servers manually:
```bash
# Test memory server
docker run --rm -i mcp/memory

# Test time server  
docker run --rm -i mcp/time

# Test git server
docker run --rm -i mcp/git
```

## Configuration Files

### Build Configuration
The setup uses `scripts/mcp_build_config.json` if it exists, otherwise uses sensible defaults.

### Runtime Configuration
MCP servers are configured in `~/.swarmdev/mcp_config.json` with Docker commands that work out of the box.

## Advanced Usage

### Custom Build Configuration
Create `scripts/mcp_build_config.json`:
```json
{
  "servers": [
    {
      "name": "custom-server",
      "directory": "path/to/server",
      "build_commands": [["npm", "install"]],
      "docker_tag": "mcp/custom"
    }
  ]
}
```

### Test Results Analysis
Detailed test results are saved to `.swarmdev/mcp_test_results.json` for programmatic analysis.

## Scripts Overview

- `setup_mcp_servers.py` - Main setup script (builds + tests)
- `test_mcp_installation.py` - Comprehensive test suite
- `mcp_build_config.json` - Optional build configuration

The setup is designed to be idempotent - you can run it multiple times safely to rebuild or update your MCP installation. 