# SwarmDev: Multi-Agent Swarm Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Built with Swarms](https://img.shields.io/badge/built%20with-swarms-orange.svg)](https://github.com/kyegomez/swarms)

SwarmDev is a comprehensive multi-agent swarm platform that enables autonomous project development through collaborative AI agents. The platform transforms high-level ideas into fully implemented projects through guided conversation, autonomous swarm intelligence, and continuous iterative improvement.

## Features

- **Intelligent Interactive Agent**: LLM-powered conversation partner for goal refinement and project setup assistance
- **Multiple Workflow Types**: Choose from 5 different workflows for various development scenarios
- **Autonomous Development**: Swarm of specialized agents collaboratively researches, plans, and implements projects
- **Continuous Improvement**: Indefinite and iteration workflows for ongoing project enhancement
- **Real-time Monitoring**: Watch project progress in real-time with detailed status tracking
- **Flexible LLM Integration**: Support for various LLM providers (OpenAI, Anthropic) with auto-detection
- **Background Processing**: Run long projects in the background with status monitoring
- **MCP Tool Integration**: Connect to specialized reasoning tools through JSON configuration
- **Advanced Memory Systems**: Hierarchical vector storage for agent memory with semantic retrieval
- **Self-Optimization**: Automatic workflow optimization based on performance metrics

## Installation

### Prerequisites

- Python 3.9+
- OpenAI API key or Anthropic API key (or both)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/swarmdev.git
cd swarmdev

# Install the package
pip install -e .

# Set up your API keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
# or create a .env file with your keys
```

## Usage

SwarmDev provides a comprehensive command-line interface:

### Interactive Goal Refinement

The Interactive Agent is SwarmDev's intelligent conversation partner that helps you transform vague project ideas into concrete, actionable goals through guided dialogue.

#### Key Features

- **LLM-Powered Conversations**: Uses advanced language models to ask relevant clarifying questions
- **Goal Refinement**: Automatically structures and refines your project description
- **Context Awareness**: Maintains conversation history and builds on previous responses
- **Completion Detection**: Intelligently determines when enough information has been gathered
- **Direct Integration**: Seamlessly connects to the build system

#### Starting a Refinement Session

```bash
# Start an interactive conversation to refine your project idea
swarmdev refine --output goal.txt

# OR use the complete assistant for goal refinement + configuration + build
swarmdev assistant
```

#### Conversation Flow Example

```
Agent: Hello! I'm here to help you refine your project idea into an actionable goal. 
       Please describe the project you'd like the swarm to build for you.

You: I want to build a web scraper

Agent: Great! A web scraper is a useful project. To help me understand exactly what 
       you need, could you provide more details about:

       1. What specific websites or types of content do you want to scrape?
       2. What data are you trying to extract (text, images, links, etc.)?
       3. How do you want to store or use the scraped data?
       4. Are there any specific technologies you'd prefer to use?
       5. What would make this scraper successful for your needs?

You: I want to scrape news articles from BBC and CNN to get headlines and article text, 
     then save them to a JSON file. I'd like it to run daily and avoid duplicate articles.

Agent: Excellent! Based on our conversation, I've refined your goal to:

       REFINED GOAL:
       Create a web scraper that automatically extracts news articles from BBC and CNN 
       websites. The scraper should:
       - Extract article headlines and full text content
       - Save data in JSON format with structured fields
       - Run on a daily schedule to fetch new articles
       - Implement duplicate detection to avoid storing the same article twice
       - Handle website rate limiting and respectful crawling practices
       - Include error handling for network issues and website changes

       Is this accurate? If so, I can store this goal for the swarm to begin working on.

You: Yes, that's perfect!

Do you want to store this goal? (yes/no): yes

Agent: Goal stored successfully in goal.txt.
       You can now run the builder with:
         swarmdev build --goal goal.txt --project-dir ./news-scraper
```

#### Enhanced Interactive Agent (Future Roadmap)

We're planning to enhance the Interactive Agent with additional capabilities:

**Configuration Assistant**
- Help users understand and configure all SwarmDev options
- Interactive workflow selection with explanations
- LLM provider setup guidance
- Project structure recommendations

**Build Orchestration**
- Automatically start builds after goal refinement
- Suggest optimal workflow types based on project complexity
- Configure background processing preferences
- Set up monitoring and notifications

**External Tool Integration**
- Guide users through MCP (Model Context Protocol) tool setup
- Help configure external APIs and services
- Assist with environment variable configuration
- Provide integration testing and validation

**Smart Configuration Example (Available Now!)**
```bash
# Enhanced interactive session
swarmdev assistant

#### Complete Assistant Experience

For a fully guided experience that handles everything from goal refinement to build execution:

```bash
# Launch the complete assistant
swarmdev assistant

# Example session:
Assistant: Hello! I'm your SwarmDev assistant. I'll help you define your project, 
          configure the optimal settings, and get your build started.

          Let's begin with your project idea. What would you like to build?

You: I want to create a task management API with user authentication
swarmdev build --goal goal.txt --project-dir ./my_project --workflow development_only

# Research only (no implementation)
swarmdev build --goal goal.txt --project-dir ./my_project --workflow research_only

# Continuous improvement (runs until manually stopped)
swarmdev build --goal goal.txt --project-dir ./my_project --workflow indefinite

# Iterative improvement (configurable cycles)
swarmdev build --goal goal.txt --project-dir ./my_project --workflow iteration --max-iterations 5
```

### Background Processing

For long-running projects, use background mode:

```bash
# Run in background
swarmdev build --goal goal.txt --project-dir ./my_project --workflow indefinite --background

# Monitor progress
swarmdev status --project-id PROJECT_ID --watch
```

### Status Monitoring

Check project status with various options:

```bash
# Basic status check
swarmdev status --project-id PROJECT_ID

# Live monitoring (refreshes every 2 seconds)
swarmdev status --project-id PROJECT_ID --watch

# Detailed task information
swarmdev status --project-id PROJECT_ID --detailed

# Show recent logs
swarmdev status --project-id PROJECT_ID --logs

# Custom refresh rate for live monitoring
swarmdev status --project-id PROJECT_ID --watch --refresh-rate 5

# Combine options
swarmdev status --project-id PROJECT_ID --watch --detailed --logs
```

### Workflow Management

List and explore available workflows:

```bash
# List all workflows
swarmdev workflows

# Detailed workflow descriptions and usage examples
swarmdev workflows --verbose
```

### Command Options

#### Build Command Options

```bash
swarmdev build [OPTIONS]

Required:
  --goal, -g PATH              Path to goal file

Options:
  --project-dir, -d PATH       Project directory (default: ./project)
  --workflow TYPE              Workflow type (default: standard_project)
                              Choices: [standard_project, research_only, 
                                       development_only, indefinite, iteration]
  --max-iterations N           Maximum iterations for iteration workflow (default: 3)
  --max-runtime SECONDS        Maximum runtime in seconds (default: 3600)
  --llm-provider PROVIDER      LLM provider (default: auto)
                              Choices: [openai, anthropic, auto]
  --llm-model MODEL           Specific model to use
  --background, -b            Run in background mode
  --wait, -w                  Wait for completion (default behavior)
```

#### Status Command Options

```bash
swarmdev status [OPTIONS]

Required:
  --project-id, -p ID         Project ID

Options:
  --watch, -w                 Live monitoring with real-time updates
  --detailed                  Show detailed task information
  --logs, -l                  Show recent activity logs
  --refresh-rate N            Refresh rate for watch mode in seconds (default: 2)
```

## Workflow Types

SwarmDev supports 5 different workflow types for various scenarios:

### 1. **Standard Project** (`standard_project`)
**Best for**: New projects from scratch
**Process**: Research → Planning → Development → Documentation
```bash
swarmdev build --goal goal.txt --workflow standard_project
```

### 2. **Research Only** (`research_only`)
**Best for**: Exploring technologies and gathering information
**Process**: Comprehensive research phase only
```bash
swarmdev build --goal goal.txt --workflow research_only
```

### 3. **Development Only** (`development_only`)
**Best for**: When you have clear requirements and want immediate implementation
**Process**: Development → Documentation
```bash
swarmdev build --goal goal.txt --workflow development_only
```

### 4. **Indefinite Improvement** (`indefinite`)
**Best for**: Continuous project enhancement and optimization
**Process**: Analysis → Planning → Implementation → Analysis (repeats until stopped)
```bash
swarmdev build --goal goal.txt --workflow indefinite
# Stop with Ctrl+C or by canceling the project
```

### 5. **Iteration Improvement** (`iteration`)
**Best for**: Controlled project improvement with specific enhancement cycles
**Process**: Analysis → Planning → Implementation → Analysis (repeats N times)
```bash
swarmdev build --goal goal.txt --workflow iteration --max-iterations 3
```

## Architecture

SwarmDev follows a modular, agent-based architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                     Command Line Interface                  │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                   Interactive Agent Layer                   │
│           (Goal Refinement & User Interaction)              │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                    Goal Processing Layer                    │
│              (Storage, Versioning, Builder)                 │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                     Swarm Builder Layer                     │
├─────────────┬─────────────────┬────────────────┬────────────┤
│   Agents    │  Orchestration  │   Workflows    │   Memory   │
│             │                 │                │            │
│ • Research  │ • Task Queue    │ • Standard     │ • Vector   │
│ • Planning  │ • Dependencies  │ • Research     │   Storage  │
│ • Dev       │ • Monitoring    │ • Development  │ • Semantic │
│ • Docs      | • Status        │ • Indefinite   │   Search   │
│ • Analysis  │ • Iteration     │ • Iteration    │ • History  │
└─────────────┴─────────────────┴────────────────┴────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                      Utility Layer                          │
├─────────────┬─────────────────┬────────────────┬────────────┤
│LLM Providers│   MCP Tools     │ Vector Storage │Optimization│
│ • OpenAI    │ • Code Gen      │ • ChromaDB     │ • Metrics  │
│ • Anthropic │ • Analysis      │ • Embeddings   │ • Auto-tune│
│ • Auto      │ • File Ops      │ • Similarity   │ • Learning │
└─────────────┴─────────────────┴────────────────┴────────────┘
```

### Specialized Agents

- **ResearchAgent**: Gathers information, analyzes requirements, identifies technologies
- **PlanningAgent**: Creates project blueprints, defines architecture, plans implementation
- **DevelopmentAgent**: Implements code, creates files, handles technical execution
- **DocumentationAgent**: Generates user guides, API docs, and project documentation
- **AnalysisAgent**: Evaluates project state, suggests improvements, manages iteration cycles

## Project Monitoring

### Real-time Status Tracking

Monitor your projects with live updates:

```bash
# Live monitoring with progress bars and task details
swarmdev status --project-id proj_123 --watch --detailed

# Output example:
Live Status - 14:32:15
============================================================
Status: In_Progress
Started: 2025-05-30T14:30:00.000000
Execution ID: exec_20250530_143000

Execution Progress:
  [████████████░░░░░░░░] 60.0%
  Total Tasks: 5
  Completed: 3
  Failed: 0
  In Progress: 2

Task Details:
  research: completed
  planning: completed  
  development: processing
  documentation: waiting
  analysis: waiting
```

### Background Project Management

Run long projects in the background:

```bash
# Start indefinite improvement in background
swarmdev build --goal goal.txt --workflow indefinite --background

# Output:
Build process started with project ID: project_20250530_143000
Running in background mode.
Monitor with: swarmdev status --project-id project_20250530_143000 --watch

# Monitor anytime
swarmdev status --project-id project_20250530_143000 --watch
```

## Configuration

SwarmDev can be configured through:

1. **Command-line arguments** (highest priority)
2. **Environment variables** 
3. **Configuration files** (.env, JSON, YAML)

### Environment Variables

```bash
# LLM Provider Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Default Settings
SWARMDEV_DEFAULT_WORKFLOW=standard_project
SWARMDEV_DEFAULT_LLM_PROVIDER=auto
SWARMDEV_MAX_RUNTIME=3600
```

### .env File Example

```bash
# .env file
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
SWARMDEV_DEFAULT_WORKFLOW=indefinite
SWARMDEV_DEFAULT_LLM_PROVIDER=openai
```

## Examples

### Quick Start Example

```bash
# 1. Create a simple goal
echo "Create a Python web scraper that extracts article titles from news websites" > my_goal.txt

# 2. Build with standard workflow
swarmdev build --goal my_goal.txt --project-dir ./web_scraper

# 3. Improve with iterations
swarmdev build --goal my_goal.txt --project-dir ./web_scraper --workflow iteration --max-iterations 3
```

### Advanced Usage Example

```bash
# 1. Refine your idea interactively
swarmdev refine --output refined_goal.txt

# 2. Research phase only
swarmdev build --goal refined_goal.txt --workflow research_only --project-dir ./research

# 3. Development with background processing
swarmdev build --goal refined_goal.txt --workflow indefinite --project-dir ./my_app --background

# 4. Monitor in real-time
swarmdev status --project-id PROJECT_ID --watch --detailed --logs
```

### Iteration Workflow Example

```bash
# Start with basic implementation
swarmdev build --goal goal.txt --workflow development_only --project-dir ./app

# Improve iteratively
swarmdev build --goal goal.txt --workflow iteration --max-iterations 5 --project-dir ./app
```

## Troubleshooting

### Common Issues

1. **No files created**: Ensure the workflow completes (don't interrupt with Ctrl+C)
2. **Background process stops**: Check project status and restart if needed
3. **API rate limits**: Use `--max-runtime` to control execution time
4. **Memory issues**: Limit iterations with `--max-iterations`

### Status Debugging

```bash
# Check detailed status
swarmdev status --project-id PROJECT_ID --detailed --logs

# Monitor live with faster refresh
swarmdev status --project-id PROJECT_ID --watch --refresh-rate 1
```

## Documentation

- [API Documentation](docs/api/README.md)
- [Architecture Documentation](docs/architecture/README.md)
- [Configuration Guide](docs/configuration/README.md)
- [Environment Variables Reference](docs/configuration/environment_variables.md)
- [Workflow Development Guide](docs/workflows/README.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
git clone https://github.com/yourusername/swarmdev.git
cd swarmdev
pip install -e ".[dev]"
```

### Adding New Workflows

1. Create a new workflow class in `src/swarmdev/swarm_builder/workflows/workflow_definitions.py`
2. Register it in the workflow registry
3. Add CLI support in `src/swarmdev/cli.py`
4. Update documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Swarms](https://github.com/kyegomez/swarms)
- Inspired by multi-agent systems research
- Powered by OpenAI and Anthropic LLMs
