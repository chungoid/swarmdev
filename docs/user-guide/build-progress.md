# Build Progress & Monitoring

SwarmDev provides comprehensive real-time monitoring of your project builds, including detailed metrics about agent activity, MCP tool usage, and LLM consumption.

## Progress Display Features

### Real-time Build Status
The CLI shows live progress including:
- **Current Workflow Phase**: Which stage of the workflow is active
- **Active Agents**: Which agents are currently working and their tasks
- **Completion Progress**: Percentage complete and estimated time remaining
- **Resource Usage**: MCP tool calls and LLM token consumption

### Enhanced Metrics

#### MCP Tool Usage
The build progress now shows detailed MCP (Model Context Protocol) tool usage:
- **Total MCP Calls**: Total number of MCP tool calls across all agents
- **Success Rate**: Percentage of successful MCP calls vs failed calls
- **Server Usage**: Breakdown of calls per MCP server name
- **Response Times**: Average response times per server

Example display:
```
MCP Tool Usage:
  Total MCP Calls: 15
  Success Rate: 93.3% (14 successful, 1 failed)
  Server Usage:
    sequentialthinking: 8 calls
    swarmdev: 4 calls
    context7: 3 calls
  Average Response Time: 1.2s
```

#### LLM Usage Tracking
Comprehensive LLM (Large Language Model) usage metrics:
- **Model(s)**: Which LLM model(s) are being used
- **Provider(s)**: Which LLM provider(s) are being used  
- **Total LLM Calls**: Number of LLM API calls made
- **Input Tokens**: Total tokens sent to the LLM
- **Output Tokens**: Total tokens received from the LLM
- **Total Tokens**: Combined input and output tokens
- **Estimated Cost**: Approximate API cost (when available)

Example display:
```
LLM Usage:
  Model(s): gpt-4o, claude-3-opus-20240229
  Provider(s): OpenAI, Anthropic
  Total LLM Calls: 23
  Input Tokens: 45,230
  Output Tokens: 12,840
  Total Tokens: 58,070
  Estimated Cost: $2.34
```

## Monitoring Commands

### Basic Status Checking
```bash
# Check current status
swarmdev status

# Get detailed status with metrics
swarmdev status --detailed

# Check specific project
swarmdev status --project-id PROJECT_ID
```

### Real-time Monitoring
```bash
# Watch real-time updates (refreshes every 2 seconds)
swarmdev status --watch

# Watch specific project
swarmdev status --project-id PROJECT_ID --watch

# Watch with verbose agent details
swarmdev status --watch --agents --verbose
```

### Specialized Status Views
```bash
# Check only MCP tool status
swarmdev status --mcp-only

# View agent activity details
swarmdev status --agents

# Show resource usage summary
swarmdev status --usage

# Check system health
swarmdev status --health
```

## Background Processing

For long-running projects, SwarmDev supports background processing:

### Starting Background Builds
```bash
# Run build in background
swarmdev build \
  --goal "Complex full-stack application" \
  --workflow iteration \
  --background \
  --project-id my-large-project \
  --project-dir ./large-project
```

### Monitoring Background Jobs
```bash
# List all background jobs
swarmdev jobs

# Monitor specific background job
swarmdev status --project-id my-large-project --watch

# Get background job logs
swarmdev logs --project-id my-large-project --follow
```

### Managing Background Jobs
```bash
# Pause a background job
swarmdev pause --project-id my-large-project

# Resume a paused job
swarmdev resume --project-id my-large-project

# Stop a background job
swarmdev stop --project-id my-large-project
```

## Progress Interpretation

### Workflow Phases
SwarmDev shows progress through different phases:

1. **Initialization**: Setting up agents and workspace
2. **Research**: Information gathering and analysis
3. **Planning**: Project planning and task breakdown
4. **Development**: Code implementation and file generation
5. **Analysis**: Project state analysis (for iteration workflows)
6. **Documentation**: Documentation generation and organization
7. **Completion**: Final validation and cleanup

### Agent Status Indicators
- **Active**: Agent is currently processing
- **Waiting**: Agent is waiting for dependencies
- **Completed**: Agent has finished its tasks
- **Error**: Agent encountered an error
- **Paused**: Agent is temporarily paused

### Progress Percentages
- **0-20%**: Initialization and setup
- **20-40%**: Research and analysis phase
- **40-60%**: Planning and design phase
- **60-85%**: Development and implementation
- **85-95%**: Documentation and testing
- **95-100%**: Final validation and completion

## Troubleshooting Monitoring

### Metrics Not Appearing

If you don't see MCP and LLM metrics:

1. **Check SwarmDev Version**: Ensure you're running the latest version
2. **Verify MCP Tools**: Check if MCP tools are configured:
   ```bash
   ls -la ~/.swarmdev/mcp_config.json
   ```
3. **Check Project Context**: Verify you're in the correct project directory
4. **Wait for Agent Activity**: Metrics appear after agents start working

### Empty or Zero Metrics

Common causes and solutions:

- **Early Build Stage**: Metrics accumulate as agents work
- **MCP Tools Not Available**: Ensure Docker is running and MCP servers are started
- **Build Completed**: Check final status for complete metrics
- **Configuration Issues**: Verify API keys and configuration

### Debug Information

Access detailed monitoring information:

```bash
# View detailed logs
swarmdev logs --verbose

# Check agent-specific logs
swarmdev logs --agent research --project-id PROJECT_ID

# Monitor MCP tool activity
tail -f ~/.swarmdev/logs/mcp.log

# Check LLM provider usage
tail -f ~/.swarmdev/logs/llm.log
```

## Advanced Monitoring

### Custom Monitoring Scripts

Create custom monitoring dashboards:

```bash
# Export status to JSON for custom processing
swarmdev status --json > status.json

# Monitor multiple projects
for project in project1 project2 project3; do
  echo "=== $project ==="
  swarmdev status --project-id $project --brief
done
```

### Integration with External Tools

Monitor SwarmDev builds in external systems:

```bash
# Send status to webhook
swarmdev status --json | curl -X POST -H "Content-Type: application/json" \
  -d @- https://your-webhook.com/swarmdev-status

# Log to external monitoring
swarmdev status --usage | logger -t swarmdev-monitor
```

### Performance Optimization

Monitor and optimize build performance:

```bash
# Check resource usage patterns
swarmdev status --usage --history

# Analyze agent efficiency
swarmdev status --agents --performance

# Monitor token consumption trends
swarmdev status --llm-usage --trending
```

## Log Files Location

SwarmDev creates comprehensive logs in `~/.swarmdev/logs/`:

- `swarmdev.log`: Main application log
- `agents.log`: Agent-specific activity
- `mcp.log`: MCP tool usage and errors
- `llm.log`: LLM provider interactions
- `builds/PROJECT_ID/`: Project-specific build logs

## Best Practices

### Monitoring Recommendations

1. **Use `--watch` for Active Builds**: Real-time monitoring for builds in progress
2. **Check `--usage` Regularly**: Monitor token consumption to control costs
3. **Review Logs After Completion**: Understand what happened during the build
4. **Monitor Background Jobs**: Regularly check on long-running background processes
5. **Set Up Alerts**: Use external monitoring for critical production builds

### Performance Tips

- Use `--brief` for quick status checks
- Monitor MCP tool performance to identify bottlenecks
- Track token usage to optimize prompt efficiency
- Review agent logs to understand workflow bottlenecks

---

The enhanced monitoring system provides complete visibility into your SwarmDev builds, helping you understand performance, track resource usage, and troubleshoot issues effectively. 