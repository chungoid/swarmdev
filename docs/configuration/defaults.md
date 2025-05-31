# SwarmDev Configuration Defaults

Complete reference for all configurable options and their default values in the SwarmDev platform.

## Overview

SwarmDev can be configured through multiple methods (in order of precedence):

1. **Command-line Arguments** (highest priority)
2. **Environment Variables**
3. **Configuration Files** (JSON/YAML)
4. **Built-in Defaults** (lowest priority)

## Command-Line Argument Defaults

### Global Options

| Option | Default Value | Type | Description |
|--------|---------------|------|-------------|
| `--verbose` | `False` | boolean | Enable verbose output |
| `--quiet` | `False` | boolean | Suppress all output except errors |
| `--log-level` | `"info"` | string | Logging level (debug, info, warning, error) |
| `--config` | `None` | string | Path to configuration file |

### Build Command Defaults

| Option | Default Value | Type | Description |
|--------|---------------|------|-------------|
| `--project-dir` | `"./project"` | string | Project directory where files will be created |
| `--max-runtime` | `3600` | integer | Maximum runtime in seconds (1 hour) |
| `--llm-provider` | `"auto"` | string | LLM provider (openai, anthropic, google, auto) |
| `--llm-model` | Provider default | string | LLM model to use |
| `--background` | `False` | boolean | Run build in background |
| `--wait` | `True` | boolean | Wait for build to complete |
| `--workflow` | `"standard_project"` | string | Workflow type to use |
| `--max-iterations` | `3` | integer | Maximum iterations for iteration workflow |

### Status Command Defaults

| Option | Default Value | Type | Description |
|--------|---------------|------|-------------|
| `--watch` | `False` | boolean | Watch status in real-time |
| `--logs` | `False` | boolean | Show recent logs from agents |
| `--detailed` | `False` | boolean | Show detailed task information |
| `--refresh-rate` | `2` | integer | Refresh rate in seconds for watch mode |

### Analyze-Logs Command Defaults

| Option | Default Value | Type | Description |
|--------|---------------|------|-------------|
| `--logs-dir` | `"logs"` | string | Directory containing log files |
| `--output` | `"workflow_analysis.md"` | string | Output file for analysis report |
| `--workflow-id` | `None` | string | Filter analysis by specific workflow ID |
| `--show-report` | `False` | boolean | Display report summary in terminal |

## LLM Provider Defaults

### Default Models by Provider

| Provider | Default Model | Context Length | Capabilities |
|----------|---------------|----------------|--------------|
| `openai` | `"gpt-4o"` | 128k tokens | Text, chat, embeddings, function calling, vision |
| `anthropic` | `"claude-3-opus-20240229"` | 200k tokens | Text, chat, function calling, vision |
| `google` | `"gemini-2.0-flash-001"` | 1M-2M tokens | Text, chat, embeddings, function calling, vision, code execution |

### LLM Generation Parameters

#### OpenAI Provider Defaults

| Parameter | Default Value | Type | Description |
|-----------|---------------|------|-------------|
| `temperature` | `0.7` | float | Creativity/randomness (0.0-2.0) |
| `max_tokens` | `1000` | integer | Maximum tokens in response |
| `top_p` | `1.0` | float | Nucleus sampling (0.0-1.0) |
| `frequency_penalty` | `0.0` | float | Frequency penalty (-2.0 to 2.0) |
| `presence_penalty` | `0.0` | float | Presence penalty (-2.0 to 2.0) |

#### Anthropic Provider Defaults

| Parameter | Default Value | Type | Description |
|-----------|---------------|------|-------------|
| `temperature` | `0.7` | float | Creativity/randomness (0.0-1.0) |
| `max_tokens` | `1000` | integer | Maximum tokens in response |
| `top_p` | `1.0` | float | Nucleus sampling (0.0-1.0) |

#### Google Provider Defaults

| Parameter | Default Value | Type | Description |
|-----------|---------------|------|-------------|
| `temperature` | `0.7` | float | Creativity/randomness (0.0-1.0) |
| `max_output_tokens` | `1000` | integer | Maximum tokens in response |
| `top_p` | `1.0` | float | Nucleus sampling (0.0-1.0) |
| `top_k` | `32` | integer | Top-k sampling |

### Embedding Models

| Provider | Default Embedding Model | Description |
|----------|-------------------------|-------------|
| `openai` | `"text-embedding-3-small"` | OpenAI's latest small embedding model |
| `anthropic` | `"all-MiniLM-L6-v2"` | SentenceTransformer fallback (no native embeddings) |
| `google` | `"models/text-embedding-004"` | Google's latest embedding model |

## Workflow Defaults

### Available Workflows

| Workflow ID | Name | Description | Default Max Iterations |
|-------------|------|-------------|----------------------|
| `standard_project` | Standard Project Workflow | Research → Planning → Development → Documentation | N/A |
| `research_only` | Research Only Workflow | Conduct research without implementation | N/A |
| `development_only` | Development Only Workflow | Development and documentation (assumes research done) | N/A |
| `indefinite` | Indefinite Improvement Workflow | Continuous improvement until manually stopped | Unlimited |
| `iteration` | Iteration Improvement Workflow | Configurable number of improvement cycles | 3 |

### Workflow Task Configuration

#### Research Agent Task Defaults

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `depth` | `"medium"` | Research depth (shallow, medium, deep) |
| `focus_areas` | `["technologies", "best_practices", "similar_projects"]` | Areas to focus research on |

#### Planning Agent Task Defaults

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `planning_depth` | `"detailed"` | Planning detail level |
| `include_architecture` | `true` | Include architecture planning |
| `include_timeline` | `true` | Include timeline estimation |

#### Development Agent Task Defaults

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `implementation_style` | `"modular"` | Implementation approach |
| `include_tests` | `true` | Include test implementation |
| `code_quality` | `"high"` | Code quality standard |

#### Documentation Agent Task Defaults

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `include_user_guide` | `true` | Include user guide |
| `include_api_docs` | `true` | Include API documentation |
| `include_examples` | `true` | Include examples |

#### Analysis Agent Task Defaults

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `analysis_depth` | `"comprehensive"` | Analysis detail level |
| `workflow_type` | Based on workflow | Type of workflow being analyzed |
| `check_continue` | `true` | Check if workflow should continue |

## Agent Configuration Defaults

### Agent Capabilities by Type

| Agent Type | Primary Function | Default Temperature | Memory Enabled |
|------------|------------------|-------------------|----------------|
| Research | Information gathering and analysis | 0.5 | true |
| Planning | Blueprint creation and planning | 0.3 | true |
| Development | Code implementation | 0.2 | true |
| Documentation | Documentation creation | 0.7 | true |
| Analysis | Project analysis and improvement suggestions | 0.3 | true |

### Agent Count Defaults

| Agent Type | Default Count | Configurable |
|------------|---------------|--------------|
| Research | 1 | Yes |
| Planning | 1 | Yes |
| Development | 2 | Yes |
| Documentation | 1 | Yes |
| Analysis | 1 | Yes |

## File and Directory Defaults

### Default Directory Structure

| Directory | Purpose | Default Location |
|-----------|---------|------------------|
| Project Directory | Main project files | `./project` |
| Goal Directory | Goal files | `./goals` |
| Logs Directory | Agent logs | `./logs` |
| Agent Work Directory | Agent artifacts and analysis | `./agent_work` |
| Vector Store | Memory embeddings | `./vector_store` |

### Default File Names

| File Type | Default Name | Purpose |
|-----------|--------------|---------|
| Goal File | `goal.txt` | Project goal description |
| Project Metadata | `project_metadata.json` | Project status and metadata |
| Main Log | `swarmdev.log` | Main application log |
| Analysis Report | `workflow_analysis.md` | Workflow analysis output |

## Orchestrator Defaults

### Task Management

| Setting | Default Value | Description |
|---------|---------------|-------------|
| Task Queue Processing Interval | 0.1 seconds | How often to check task queue |
| Task Timeout | 30 seconds | Default timeout for agent join operations |
| Max Concurrent Tasks | Based on agent count | Maximum parallel task execution |

### Execution Tracking

| Setting | Default Value | Description |
|---------|---------------|-------------|
| Status Check Interval | 2 seconds | Default refresh rate for status monitoring |
| Artifact Save | Enabled | Save task artifacts and results |
| Progress Tracking | Enabled | Track task completion progress |

## Memory System Defaults

### Vector Store Configuration

| Setting | Default Value | Description |
|---------|---------------|-------------|
| Vector Store Type | `"chroma"` | Vector database type |
| Embedding Dimension | Model dependent | Embedding vector size |
| Cache Size | 10000 | Number of cached embeddings |
| Persistence | Enabled | Save embeddings to disk |

### Memory Types

| Memory Type | Default State | Description |
|-------------|---------------|-------------|
| Working Memory | Enabled | Short-term context |
| Episodic Memory | Enabled | Task and interaction history |
| Semantic Memory | Enabled | Knowledge and concepts |
| Procedural Memory | Enabled | Skills and procedures |

## Logging Defaults

### Log Levels

| Level | Default For | Description |
|-------|-------------|-------------|
| DEBUG | Development | Detailed debugging information |
| INFO | Production | General information messages |
| WARNING | All | Warning messages |
| ERROR | All | Error messages |

### Log Configuration

| Setting | Default Value | Description |
|---------|---------------|-------------|
| Console Logging | Enabled | Log to console/stdout |
| File Logging | Enabled | Log to `swarmdev.log` |
| Agent Logging | Enabled | Separate logs for each agent |
| Rotation | Daily | Log file rotation policy |

## Performance Defaults

### Resource Limits

| Setting | Default Value | Description |
|---------|---------------|-------------|
| Memory Limit | System dependent | Maximum memory usage |
| CPU Cores | All available | Number of cores to use |
| Network Timeout | 60 seconds | Network request timeout |
| API Rate Limits | Provider dependent | API call rate limiting |

### Optimization

| Setting | Default Value | Description |
|---------|---------------|-------------|
| Parallel Processing | Enabled | Process tasks in parallel |
| Caching | Enabled | Cache LLM responses and embeddings |
| Batch Processing | Enabled | Batch similar operations |
| Resource Monitoring | Enabled | Monitor resource usage |

## Security Defaults

### API Key Management

| Setting | Default Value | Description |
|---------|---------------|-------------|
| Environment Variables | Required | API keys from environment only |
| Key Validation | Enabled | Validate API keys on startup |
| Key Rotation | Manual | No automatic key rotation |

### File Permissions

| Setting | Default Value | Description |
|---------|---------------|-------------|
| Project Files | User read/write | Created files permissions |
| Log Files | User read/write | Log file permissions |
| Config Files | User read/write | Configuration file permissions |

## Error Handling Defaults

### Retry Configuration

| Setting | Default Value | Description |
|---------|---------------|-------------|
| Max Retry Attempts | 3 | Maximum retry attempts for failed operations |
| Retry Backoff | Exponential | Backoff strategy for retries |
| Timeout Handling | Graceful | How to handle timeouts |

### Error Recovery

| Setting | Default Value | Description |
|---------|---------------|-------------|
| Graceful Degradation | Enabled | Continue with partial failures |
| Error Reporting | Enabled | Report errors to logs |
| Crash Recovery | Enabled | Attempt to recover from crashes |

## Configuration File Format

### JSON Configuration Example

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 1000
  },
  "workflow": {
    "type": "standard_project",
    "max_iterations": 3,
    "parallelism": 4
  },
  "agents": {
    "research": {"count": 1, "temperature": 0.5},
    "planning": {"count": 1, "temperature": 0.3},
    "development": {"count": 2, "temperature": 0.2},
    "documentation": {"count": 1, "temperature": 0.7}
  }
}
```

### YAML Configuration Example

```yaml
llm:
  provider: openai
  model: gpt-4o
  temperature: 0.7
  max_tokens: 1000

workflow:
  type: standard_project
  max_iterations: 3
  parallelism: 4

agents:
  research:
    count: 1
    temperature: 0.5
  planning:
    count: 1
    temperature: 0.3
  development:
    count: 2
    temperature: 0.2
  documentation:
    count: 1
    temperature: 0.7
```

## Override Priority

Configuration values are applied in this order (highest to lowest priority):

1. **Command-line arguments** (e.g., `--llm-provider openai`)
2. **Environment variables** (e.g., `SWARMDEV_LLM_PROVIDER=openai`)
3. **Configuration file values** (JSON/YAML files)
4. **Built-in defaults** (documented above) 