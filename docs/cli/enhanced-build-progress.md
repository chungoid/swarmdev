# Enhanced Build Progress Page

The SwarmDev build progress page now includes detailed metrics about MCP tool usage and LLM token consumption to give you better visibility into your project builds.

## New Metrics Display

### MCP Tool Usage
The build progress now shows:
- **Total MCP Calls**: Total number of MCP tool calls across all agents
- **Success Rate**: Percentage of successful MCP calls vs failed calls
- **Server Usage**: Breakdown of calls per MCP server name

Example display:
```
MCP Tool Usage:
  Total MCP Calls: 15
  Success Rate: 93.3% (14 successful, 1 failed)
  Server Usage:
    sequentialthinking: 8 calls
    swarmdev: 4 calls
    context7: 3 calls
```

### LLM Usage
The build progress now shows:
- **Model(s)**: Which LLM model(s) are being used
- **Provider(s)**: Which LLM provider(s) are being used  
- **Total LLM Calls**: Number of LLM API calls made
- **Input Tokens**: Total tokens sent to the LLM
- **Output Tokens**: Total tokens received from the LLM
- **Total Tokens**: Combined input and output tokens

Example display:
```
LLM Usage:
  Model(s): gpt-4o, claude-3-opus-20240229
  Provider(s): OpenAI, Anthropic
  Total LLM Calls: 23
  Input Tokens: 45,230
  Output Tokens: 12,840
  Total Tokens: 58,070
```

## Viewing Enhanced Metrics

The enhanced metrics automatically appear in:

1. **Live Status Monitoring**:
   ```bash
   swarmdev status --project-id PROJECT_ID --watch
   ```

2. **One-time Status Check**:
   ```bash
   swarmdev status --project-id PROJECT_ID --detailed
   ```

3. **During Build Monitoring**:
   The metrics appear automatically when monitoring a build in progress.

## Troubleshooting

### Metrics Not Appearing

If you don't see the MCP and LLM metrics in your build progress:

1. **Check SwarmDev Version**: Make sure you're running the latest version with the enhanced metrics support.

2. **Verify MCP Tools**: Metrics only appear if MCP tools are enabled and being used:
   ```bash
   # Check if MCP tools are configured
   ls -la ~/.swarmdev/mcp_config.json
   ```

3. **Check Project Structure**: Make sure you're checking status from the correct project directory or using the correct project ID.

4. **Agent Activity**: Metrics only appear after agents have started working. Very early in the build process, metrics may be zero.

### Empty Metrics

If metrics show zero values:

- **MCP Tools Not Available**: If no MCP servers are configured, MCP metrics will be empty
- **Early Build Stage**: In the very beginning of a build, agents may not have made calls yet
- **Build Completed**: After a build completes, check the final status for complete metrics

### Debug Information

To see detailed metrics information in the logs:

```bash
# Check agent logs for detailed MCP usage
tail -f .swarmdev/logs/swarmdev.log | grep MCP

# Check for LLM provider usage
tail -f .swarmdev/logs/swarmdev.log | grep -i "llm\|token"
```

## Implementation Details

The metrics are collected from:
- **Base Agent**: Each agent tracks its own MCP and LLM usage
- **Orchestrator**: Aggregates metrics from all agents
- **SwarmBuilder**: Includes metrics in status reports  
- **CLI**: Displays formatted metrics in the progress page

This ensures accurate, real-time reporting of tool usage across your entire SwarmDev build process. 