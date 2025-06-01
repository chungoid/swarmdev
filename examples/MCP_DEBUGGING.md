# MCP Tools Debugging Guide

This guide helps you troubleshoot issues with MCP (Model Context Protocol) tools in SwarmDev.

## Quick Diagnosis

If your SwarmDev assistant says it has MCP tools available but they don't work, follow these steps:

### 1. Run the Debug Script

```bash
python test_mcp.py --verbose
```

This will show you detailed information about your MCP tool configuration and test each tool.

### 2. Check Your Configuration

MCP tools are configured through JSON files in a hierarchical system:

- **Global config**: `~/.swarmdev/mcp_config.json` (affects all projects)
- **Project config**: `./.swarmdev/mcp_config.json` (project-specific overrides)

Use the sample configuration:
```bash
cp sample_mcp_config.json ~/.swarmdev/mcp_config.json
```

### 3. Enable Verbose Mode in Assistant

Run the assistant with verbose logging to see detailed MCP tool debugging:

```bash
swarmdev assistant --verbose
```

This will show:
- MCP tool initialization details
- Real-time debugging when tools are used
- Detailed error messages
- Connection status information

### 4. Use Debug Commands

In verbose mode, the assistant has special debug commands:

- `mcp-status` - Show current MCP tool status
- `mcp-test` - Test MCP tool connectivity

## Common Issues

### Issue 1: "No tools available"
**Symptoms**: Assistant reports 0 MCP tools
**Solution**: 
- Check if MCP config files exist
- Verify paths in configuration are correct
- Ensure required dependencies are installed (Node.js, Python packages)

### Issue 2: "Tools timeout during initialization"
**Symptoms**: Tools show as available but fail with timeout errors
**Solution**:
- Increase timeout values in configuration
- Check if bundled MCP servers are built (run `npm run build` in each bundled_mcp directory)
- Verify Node.js and npm are properly installed

### Issue 3: "Connection failed after 3 attempts"
**Symptoms**: Persistent connection failures
**Solution**:
- Check command paths in configuration
- Verify executable permissions
- Test individual tools manually

### Issue 4: "Tool not implemented"
**Symptoms**: Some tools work, others return "not implemented"
**Solution**:
- Check the CollaborativeAgent's `_call_tool_safely` method supports your tool
- Verify tool name matches exactly
- Ensure tool provides expected interface

## Building Bundled Tools

The bundled MCP tools need to be built before use:

```bash
# Build sequential-thinking tool
cd src/swarmdev/bundled_mcp/sequential-thinking
npm install
npm run build

# Build context7 tool  
cd ../context7
npm install
npm run build

# Build memory tool
cd ../memory
npm install
npm run build
```

## Tool-Specific Debugging

### Sequential Thinking Tool
- Check if TypeScript is compiled: `dist/index.js` should exist
- Test directly: `node dist/index.js` (should start MCP server)

### Context7 Tool
- Verify network connectivity (needs internet access)
- Check if API endpoints are accessible

### Memory Tool
- Ensure write permissions in project directory
- Check if storage directory can be created

## Getting Help

1. Run `python test_mcp.py --verbose` and share the output
2. Check logs in `.swarmdev/logs/` for detailed error information
3. Enable verbose mode in the assistant for real-time debugging
4. Use the debug commands `mcp-status` and `mcp-test` in verbose mode

## Sample Working Configuration

See `sample_mcp_config.json` for a complete working configuration that includes:
- All bundled SwarmDev tools
- Common external tools (time, fetch, git)
- Proper timeout and capability settings

Copy this to `~/.swarmdev/mcp_config.json` to get started quickly. 