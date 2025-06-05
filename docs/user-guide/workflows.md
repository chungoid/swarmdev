# Workflows Guide

SwarmDev offers multiple specialized workflow types designed for different development scenarios. This guide explains each workflow, when to use them, and how to get the best results.

## Overview

SwarmDev provides 5 distinct workflow patterns that orchestrate AI agents to handle different development needs:

| Workflow | Best For | Agent Flow | Duration |
|----------|----------|------------|----------|
| `iteration` | Most projects, continuous improvement | Enhanced multi-phase with smart completion | 3-8 iterations |
| `standard_project` | New comprehensive projects | Research → Planning → Development → Documentation | Single pass |
| `research_only` | Information gathering, technology evaluation | Research only | Single pass |
| `development_only` | Clear requirements, immediate implementation | Development → Documentation | Single pass |
| `indefinite` | Ongoing improvement, maintenance | Analysis → Planning → Implementation (repeats) | Continuous |

## Enhanced Iteration Workflow (Recommended)

The **iteration workflow** is our most advanced and recommended workflow for most projects. It combines the best patterns from multiple workflows with intelligent completion strategies.

### Key Features

- **Handles both new projects AND existing codebases**
- **Smart completion planning** - no more "coat tails" problem
- **Adaptive iteration adjustment** - no upfront guessing needed
- **Version-aware development** with semantic targets
- **Risk assessment and compatibility preservation**
- **Parameter-aware agents** that adapt based on workflow configuration

### Usage Examples

#### Basic Enhanced Iteration
```bash
# Recommended for most projects
swarmdev build \
  --goal "Create a task management API with authentication" \
  --workflow iteration \
  --max-iterations 5
```

#### Version-Targeted Development
```bash
# When working toward a specific version
swarmdev build \
  --goal "Add advanced features to existing application" \
  --workflow iteration \
  --target-version 2.0 \
  --completion-strategy version_driven \
  --max-iterations 6
```

#### Smart Existing Codebase Enhancement
```bash
# For improving existing projects (replaces old refactor workflow)
swarmdev build \
  --goal "Add authentication and improve performance" \
  --workflow iteration \
  --completion-strategy smart \
  --adaptive \
  --project-dir ./existing-project
```

### Completion Strategies

The iteration workflow supports multiple completion strategies:

#### Smart Completion (Default)
```bash
--completion-strategy smart
```
- **Best for**: Most projects
- **Behavior**: Intelligently determines when enough improvement has been made
- **Stops when**: Critical issues resolved and major features complete

#### Version-Driven Completion
```bash
--completion-strategy version_driven --target-version 2.1.0
```
- **Best for**: Semantic versioning projects
- **Behavior**: Works toward specific version milestones
- **Stops when**: Version-specific requirements are met

#### Fixed Iterations
```bash
--completion-strategy fixed --max-iterations 4
```
- **Best for**: Time-boxed development
- **Behavior**: Runs exactly the specified number of iterations
- **Stops when**: Maximum iterations reached

## Standard Project Workflow

The standard project workflow provides a comprehensive, single-pass development approach.

### When to Use
- **New projects** requiring full development lifecycle
- **Well-defined requirements** that don't need iteration
- **Time-constrained projects** needing one comprehensive implementation

### Agent Flow
1. **Research Agent**: Gathers information and analyzes requirements
2. **Planning Agent**: Creates detailed implementation plan
3. **Development Agent**: Implements the solution
4. **Documentation Agent**: Creates comprehensive documentation

### Usage
```bash
swarmdev build \
  --goal "Create a complete expense tracking application" \
  --workflow standard_project \
  --project-dir ./expense-tracker
```

## Research Only Workflow

Dedicated to information gathering and analysis without implementation.

### When to Use
- **Technology evaluation** and comparison
- **Market research** and competitive analysis  
- **Architecture planning** and design decisions
- **Pre-project investigation** phase

### Usage Examples

#### Technology Comparison
```bash
swarmdev build \
  --goal "Compare FastAPI vs Flask vs Django for building a microservices API" \
  --workflow research_only \
  --project-dir ./framework-research
```

### Output
- Comprehensive research reports
- Technology comparisons
- Best practices documentation
- Implementation recommendations

## Development Only Workflow

Focuses purely on implementation when research and planning are already complete.

### When to Use
- **Clear, detailed requirements** already exist
- **Architecture and design** are predetermined
- **Research phase** completed separately
- **Quick implementation** needed

### Usage
```bash
swarmdev build \
  --goal "Implement the user authentication system as specified in auth-requirements.md" \
  --workflow development_only \
  --project-dir ./existing-app
```

## Indefinite Workflow

Provides continuous improvement and maintenance through ongoing iterations.

### When to Use
- **Long-term maintenance** projects
- **Continuous improvement** initiatives
- **Evolving requirements** that change over time
- **Production applications** needing ongoing enhancement

### Usage
```bash
swarmdev build \
  --goal "Continuously improve and maintain the customer portal with feature additions and optimizations" \
  --workflow indefinite \
  --project-dir ./customer-portal \
  --background
```

## Workflow Selection Guide

### Decision Tree

**Do you have existing code?**
- **Yes**: Use `iteration` workflow with smart completion
- **No**: Continue below

**Do you need comprehensive development?**
- **Yes**: Use `iteration` (recommended) or `standard_project`
- **No**: Continue below

**What's your primary need?**
- **Research/Analysis**: Use `research_only`
- **Implementation Only**: Use `development_only`
- **Ongoing Improvement**: Use `indefinite`

### Project Type Recommendations

| Project Type | Primary Workflow | Alternative | Notes |
|-------------|------------------|-------------|--------|
| Web Application | `iteration` | `standard_project` | Iteration allows refinement |
| CLI Tool | `standard_project` | `iteration` | Usually well-defined scope |
| API Service | `iteration` | `standard_project` | Benefits from iterative design |
| Library/Package | `iteration` | `standard_project` | API design benefits from iteration |
| Existing Enhancement | `iteration` | N/A | Only sensible choice |
| Research Project | `research_only` | N/A | Dedicated research phase |
| Quick Implementation | `development_only` | `standard_project` | When requirements are clear |
| Long-term Maintenance | `indefinite` | `iteration` | Ongoing improvement |

## Best Practices

### Goal Writing for Workflows

#### For Iteration Workflow
```bash
# Good: Specific with room for improvement
"Create a Flask API for task management with JWT authentication, CRUD operations, and PostgreSQL database"

# Better: Includes quality considerations
"Create a production-ready Flask API for task management with JWT authentication, comprehensive error handling, input validation, CRUD operations, PostgreSQL database, and API documentation"
```

### Monitoring Best Practices

1. **Use `--watch`** for active monitoring
2. **Check logs regularly** for issues
3. **Monitor resource usage** to control costs
4. **Review iteration results** to understand progress
5. **Use background processing** for complex projects

---

The workflow system is designed to be flexible and adaptive to your development needs. The enhanced iteration workflow is recommended for most projects due to its intelligent adaptation and comprehensive feature set. 