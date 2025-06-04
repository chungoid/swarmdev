# SwarmDev: Multi-Agent Swarm Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Built with Swarms](https://img.shields.io/badge/built%20with-swarms-orange.svg)](https://github.com/kyegomez/swarms)

SwarmDev is a comprehensive multi-agent swarm platform that enables autonomous project development through collaborative AI agents. The platform transforms high-level ideas into fully implemented projects through guided conversation, autonomous swarm intelligence, and continuous iterative improvement.

## Features

- **Interactive Goal Refinement**: LLM-powered conversation partner for transforming ideas into actionable goals
- **Multiple Workflow Types**: 7 specialized workflows for different development scenarios  
- **Autonomous Swarm Intelligence**: Specialized agents collaborate on research, planning, development, and documentation
- **Real-time Monitoring**: Live progress tracking with detailed status information
- **Enhanced MCP Integration**: 7 built-in Docker-based MCP servers for git operations, web research, advanced reasoning, and persistent memory
- **Flexible LLM Support**: Auto-detection and support for OpenAI, Anthropic, and Google providers
- **Background Processing**: Run long projects in the background with monitoring capabilities

## Installation

### Prerequisites
- Python 3.9+
- Docker (for enhanced MCP servers)
- API key for OpenAI, Anthropic, or Google

### Quick Install
```bash
git clone https://github.com/chungoid/swarmdev.git
cd swarmdev
pipx install .
pipx ensurepath && exec $SHELL
swarmdev pull-images

# Test MCP Install & Connections

## Common Docker Issues

If you encounter "permission denied" or "broken pipe" errors when using MCP tools, this is usually a Docker group membership issue:

```bash
# Fix Docker group membership automatically
swarmdev fix-docker-group

# Or manually add user to docker group
sudo usermod -aG docker $USER
newgrp docker  # Activate in current session
```

**Note**: Group membership changes require a new login session to fully take effect.
cd scripts
python3 test_mcp_installation.py
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

# Test Agent MCP tool usage
python3 test_collaborative_agent.py
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

Agent Integration Status:
  memory: PASS
  sequential-thinking: PASS
  context7: PASS
  git: PASS
  time: PASS
  fetch: PASS
  filesystem: PASS

Agent Integration Score: 7/7 tools working
Success Rate: 100.0%

Overall Assessment:
PASS: All MCP tools and agent integration working perfectly!

Critical Issues to Fix:
  • No issues found - system ready for production use!

TEST SUITE: PASS - All systems operational

# Set up API keys
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
# or create a .env file
```

## Built-in MCP Integration

SwarmDev automatically sets up 7 Docker-based MCP servers during installation:

| Server | Type | Capabilities | Description |
|--------|------|-------------|-------------|
| **git** | Docker (Python) | Repository operations | Git analysis, file operations, version control |
| **time** | Docker (Python) | Temporal operations | System time, scheduling, time-aware reasoning |
| **fetch** | Docker (Python) | Web requests | Online research, documentation lookup |
| **filesystem** | Docker (Node.js) | Filesystem commands | Agentic usage of filesystem operations |
| **sequential-thinking** | Docker (Node.js) | Advanced reasoning | Sequential thoughts, branching logic, problem solving |
| **memory** | Docker (Node.js) | Persistent storage | Agent memory, context persistence across sessions |
| **context7** | Docker (Node.js) | Documentation access | Up-to-date library and framework documentation |

### Adding Additional MCP Servers

To add more MCP servers beyond the built-in 7, edit your configuration:

**Global config** (affects all projects): `~/.swarmdev/mcp_config.json`
**Project config** (project-specific): `./project/.swarmdev/mcp_config.json`

```json
{
  "mcpServers": {
    "your-server": {
      "command": ["docker", "run", "-i", "--rm", "your-server-image"],
      "capabilities": ["your_capabilities"],
      "description": "Your server description"
    }
  }
}
```

For more MCP servers, check the [official MCP servers repository](https://github.com/modelcontextprotocol/servers) or community directories like [mcpservers.org](https://mcpservers.org).

## Workflow Types

SwarmDev provides 7 specialized workflows for different development scenarios:

### 1. Standard Project (`standard_project`) - Default
**Best for**: New projects requiring full development lifecycle  
**Process**: Research → Planning → Development → Documentation  
**Use when**: Starting from scratch with comprehensive requirements gathering

### 2. Research Only (`research_only`)
**Best for**: Technology exploration and information gathering  
**Process**: Comprehensive research phase only  
**Use when**: Need to analyze technologies, gather requirements, or explore solutions

### 3. Development Only (`development_only`)
**Best for**: Clear requirements, immediate implementation needed  
**Process**: Development → Documentation  
**Use when**: Requirements are well-defined and research/planning already done

### 4. Indefinite Improvement (`indefinite`)
**Best for**: Continuous project enhancement and optimization  
**Process**: Analysis → Planning → Implementation (repeats until stopped)  
**Use when**: Ongoing maintenance, feature addition, or continuous improvement

### 5. Ultimate Iteration (`iteration`) - **RECOMMENDED**

**Process**: Comprehensive Discovery → Strategic Research → Strategic Planning → Smart Implementation → Completion Evaluation (repeats intelligently)

**Features**: 
- Handles both new projects AND existing codebases
- Smart completion planning (no more "coat tails")
- Adaptive iteration adjustment (no upfront guessing)
- Version-aware development with semantic targets
- Risk assessment and compatibility preservation
- Combines the best patterns from iteration, refactor, and versioned workflows

**Usage Examples**:
```bash
# Basic usage with enhanced iteration workflow (recommended)
swarmdev build --goal goal.txt --workflow iteration --max-iterations 5

# Version-targeted development  
swarmdev build --goal goal.txt --workflow iteration --target-version 2.0 --completion-strategy version_driven

# Existing codebase improvement (replaces old refactor workflow)
swarmdev build --goal improve_performance.txt --workflow iteration --completion-strategy smart --adaptive

# Continuous improvement
swarmdev build --goal goal.txt --workflow indefinite
```

### 6. Refactor (`refactor`) - **DEPRECATED**

**Status**: DEPRECATED - Use `iteration` workflow instead
**Migration**: Use `--workflow iteration --completion-strategy smart --adaptive`

**Process**: Analysis → Planning → Refactoring → Documentation (repeats as needed)

### 7. Versioned Development (`versioned`) - **DEPRECATED**

**Status**: DEPRECATED - Use `iteration` workflow with `--target-version` instead  
**Migration**: Use `--workflow iteration --target-version X.Y --completion-strategy version_driven`

## Command Reference

### Goal Refinement
```bash
# Interactive goal refinement
swarmdev refine --output goal.txt

# Complete assistant (refinement + configuration + build)
swarmdev assistant
```

### Build Projects
```bash
swarmdev build --goal GOAL_FILE [OPTIONS]

# Required
--goal, -g PATH              Path to goal file

# Workflow Options  
--workflow {standard_project,research_only,development_only,
                         indefinite, iteration, refactor, versioned}
                         Workflow type to use (default: standard_project)
--max-iterations MAX_ITERATIONS     Initial iteration estimate for iteration workflow (can be adjusted dynamically)
--target-version VERSION     Target semantic version for iteration workflow (e.g., "2.0", "1.5")
--current-version VERSION    Current version for versioned workflow (auto-detected if not provided)
--completion-strategy {smart,fixed,version_driven}
                                Completion strategy for iteration workflow (default: smart)
--adaptive                    Enable adaptive iteration adjustment (default: True)
--no-adaptive                 Disable adaptive iteration adjustment

# Execution Options
--project-dir, -d PATH       Project directory (default: ./project)
--max-runtime SECONDS        Maximum runtime (default: 3600)
--background, -b            Run in background mode
--wait, -w                  Wait for completion (default)

# LLM Options
--llm-provider PROVIDER      Provider choice (default: auto)
                            [openai, anthropic, google, auto]
--llm-model MODEL           Specific model to use
```

### Monitor Progress
```bash
swarmdev status --project-id PROJECT_ID [OPTIONS]

# Display Options
--watch, -w                 Live monitoring with real-time updates
--detailed                  Show detailed task information  
--logs, -l                  Show recent activity logs
--refresh-rate N            Refresh rate for watch mode (default: 2 seconds)
```

### Workflow Information
```bash
# List all workflows
swarmdev workflows

# Detailed descriptions and usage examples  
swarmdev workflows --verbose
```

### Analyze Logs
```bash
swarmdev analyze-logs [OPTIONS]

# Options
--logs-dir DIR              Directory containing log files (default: .swarmdev/logs)
--output, -o FILE           Output file for analysis report (default: workflow_analysis.md)
--workflow-id ID            Filter analysis by specific workflow ID
--show-report               Display report summary in terminal
```

### Blueprint Management
```bash
# Show blueprint status
swarmdev blueprint status [--project-dir DIR]

# Display detailed blueprint
swarmdev blueprint show [--project-dir DIR] [--format markdown|json]

# Add user feedback
swarmdev blueprint feedback "Your feedback text" [--project-dir DIR] [--run-number N]

# Modify blueprint items
swarmdev blueprint modify [--project-dir DIR] [--phase PHASE] [--item ITEM] [--status STATUS]
```

### MCP Analysis
```bash
swarmdev mcp-analysis [--project-dir DIR]

# Analyzes MCP system performance and health
# Shows tool usage, success rates, and performance metrics
```

## Usage Examples

### Quick Start
```bash
# 1. Refine your idea
swarmdev refine --output my_goal.txt

# 2. Build with standard workflow
swarmdev build --goal my_goal.txt --project-dir ./my_project

# 3. Monitor progress
swarmdev status --project-id PROJECT_ID --watch
```

### Workflow-Specific Examples
```bash
# Research phase only
swarmdev build --goal goal.txt --workflow research_only

# Direct development (skip research/planning)
swarmdev build --goal goal.txt --workflow development_only

# Continuous improvement (runs until stopped)
swarmdev build --goal goal.txt --workflow indefinite --background

# Fixed improvement cycles
swarmdev build --goal goal.txt --workflow iteration --max-iterations 5

# Enhanced iteration workflow examples covered above
```

### Advanced Usage
```bash
# Analyze workflow performance
swarmdev analyze-logs --show-report

# Manage project blueprints
swarmdev blueprint status
swarmdev blueprint feedback "Add better error handling to the authentication module"

# Check MCP system health
swarmdev mcp-analysis
```