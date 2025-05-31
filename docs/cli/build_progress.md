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
- **Provider(s)**: Which LLM provider(s) are active
- **Total LLM Calls**: Number of LLM API calls made
- **Input Tokens**: Total input tokens consumed
- **Output Tokens**: Total output tokens generated
- **Total Tokens**: Combined input and output token count

Example display:
```
LLM Usage:
  Model(s): gpt-4o
  Provider(s): OpenAI
  Total LLM Calls: 12
  Input Tokens: 45,230
  Output Tokens: 12,890
  Total Tokens: 58,120
```

## How It Works

The metrics are collected from:

1. **MCP Manager**: Tracks tool calls, success rates, and per-server usage
2. **Base Agent**: Aggregates MCP usage across all agent types
3. **LLM Providers**: Track token consumption and model information
4. **Orchestrator**: Collects metrics from all agents and includes them in status updates

## Benefits

- **Cost Monitoring**: Track token usage to monitor LLM API costs
- **Performance Insights**: See which MCP tools are being used most
- **Debugging**: Identify failed MCP calls or high token usage
- **Optimization**: Understand which agents and tools are most active

## Viewing Enhanced Metrics

The enhanced metrics are automatically displayed when using:

```bash
# Real-time build monitoring
swarmdev build --goal goal.txt

# Status checking
swarmdev status PROJECT_ID

# Status with details
swarmdev status PROJECT_ID --detailed
```

## Configuration

No additional configuration is needed. The metrics tracking is:
- **Automatic**: Enabled by default for all builds
- **Lightweight**: Minimal overhead on build performance  
- **Comprehensive**: Covers all agent types and tool usage

## Troubleshooting

If metrics show zeros or "No ... usage recorded":
- Check that MCP tools are properly configured in `mcp_config.json`
- Verify LLM provider is properly initialized
- Ensure agents have required API keys configured

The enhanced metrics help you optimize your SwarmDev workflows and monitor resource usage effectively! 