# Quick Start Tutorial

Get up and running with SwarmDev in just 5 minutes! This tutorial will walk you through creating your first AI-powered project.

## Prerequisites

Before starting, ensure you have:
- ✅ SwarmDev installed ([Installation Guide](installation.md))
- ✅ Docker running and configured
- ✅ At least one API key configured (OpenAI, Anthropic, or Google)

## Step 1: Verify Your Setup

First, let's make sure everything is working:

```bash
# Check SwarmDev installation
swarmdev --version

# Test MCP servers are running
swarmdev status --mcp-only
```

You should see all 7 MCP servers running successfully.

## Step 2: Interactive Goal Setting

SwarmDev includes an interactive goal processor to help you refine your ideas:

```bash
# Start interactive goal setting
swarmdev goal
```

The system will guide you through:
1. **Initial idea discussion** - Share your project concept
2. **Goal refinement** - AI helps clarify and structure your goal
3. **Technical specification** - Convert ideas into actionable requirements
4. **Goal validation** - Ensure the goal is clear and achievable

**Example interaction:**
```
SwarmDev Goal Processor
What would you like to build today?

> I want to create a simple web scraper

Let me help you refine that goal...

Based on our discussion, here's your refined goal:
"Create a Python web scraper that can extract product information (name, price, description) from e-commerce websites, save data to CSV format, handle rate limiting, and include error handling for failed requests."

Does this capture what you want to build? (yes/no/modify):
> yes

Great! I'll save this goal for you.
```

## Step 3: Choose Your Workflow

SwarmDev offers several workflow types. For beginners, we recommend the **iteration** workflow:

### Option A: New Project (Recommended)
```bash
# Create a comprehensive project with iteration workflow
swarmdev build \
  --goal "Create a Python web scraper for e-commerce product data" \
  --workflow iteration \
  --max-iterations 3 \
  --project-dir ./my-webscraper
```

### Option B: Use Saved Goal
If you used the goal processor:
```bash
# Use your refined goal from Step 2
swarmdev build \
  --goal-file .swarmdev/goals/latest.txt \
  --workflow iteration \
  --max-iterations 3 \
  --project-dir ./my-webscraper
```

### Option C: Research First
For complex projects, start with research:
```bash
# Research phase only
swarmdev build \
  --goal "Build a machine learning model for image recognition" \
  --workflow research_only \
  --project-dir ./ml-research
```

## Step 4: Monitor Progress

SwarmDev provides real-time monitoring of your build:

### Built-in Progress Display
The CLI shows live progress including:
- Current workflow phase
- Active agents and their tasks
- MCP tool usage statistics
- Token consumption tracking
- Estimated completion time

### Status Commands
```bash
# Check current status
swarmdev status

# Watch real-time updates
swarmdev status --watch

# View detailed agent activity
swarmdev status --agents --verbose

# Check MCP tool usage
swarmdev status --mcp-tools
```

### Background Processing
For long-running projects:
```bash
# Run in background
swarmdev build \
  --goal "Complex full-stack application" \
  --workflow iteration \
  --background \
  --project-id my-app

# Monitor background job
swarmdev status --project-id my-app --watch
```

## Step 5: Explore Your Results

After completion, SwarmDev creates a comprehensive project structure:

```
my-webscraper/
├── src/                    # Generated source code
│   ├── scraper.py         # Main scraper implementation
│   ├── config.py          # Configuration handling
│   └── utils.py           # Utility functions
├── tests/                 # Generated test suite
│   └── test_scraper.py    # Unit tests
├── docs/                  # Auto-generated documentation
│   ├── README.md          # Project documentation
│   └── API.md             # API documentation
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
└── .swarmdev/            # SwarmDev metadata
    ├── goals/            # Goal history
    ├── iterations/       # Iteration logs
    └── analysis/         # Project analysis
```

### Review Generated Code
```bash
# View the main implementation
cat my-webscraper/src/scraper.py

# Check the documentation
cat my-webscraper/docs/README.md

# Run the generated tests
cd my-webscraper
python -m pytest tests/
```

## Step 6: Iteration and Improvement

The iteration workflow automatically improves your project. You can also trigger manual iterations:

```bash
# Continue improving the project
swarmdev build \
  --goal "Add database storage and web UI to the scraper" \
  --workflow iteration \
  --project-dir ./my-webscraper \
  --max-iterations 2
```

## Common Workflows

### Simple Script/Tool
```bash
swarmdev build \
  --goal "Create a command-line password generator with customizable options" \
  --workflow standard_project \
  --project-dir ./password-gen
```

### Web Application
```bash
swarmdev build \
  --goal "Build a Flask web app for task management with user authentication" \
  --workflow iteration \
  --max-iterations 4 \
  --project-dir ./task-manager
```

### Existing Codebase Enhancement
```bash
swarmdev build \
  --goal "Add authentication and user management to existing Flask app" \
  --workflow iteration \
  --project-dir ./existing-app \
  --completion-strategy smart
```

### Research and Planning
```bash
swarmdev build \
  --goal "Research best practices for building a microservices architecture" \
  --workflow research_only \
  --project-dir ./microservices-research
```

## Understanding Workflow Types

### Standard Project
**Best for**: New projects, complete development lifecycle
- Research → Planning → Development → Documentation
- Comprehensive but single-pass

### Iteration (Recommended)
**Best for**: Complex projects, continuous improvement
- Enhanced multi-phase approach with smart completion
- Handles both new and existing projects
- Adaptive iteration planning

### Research Only
**Best for**: Information gathering, technology evaluation
- Comprehensive research phase only
- Great for decision-making

### Development Only
**Best for**: Clear requirements, immediate implementation
- Development → Documentation
- When planning is already done

### Indefinite
**Best for**: Ongoing improvement, maintenance
- Continuous iteration until manually stopped
- Great for long-term projects

## Tips for Success

### Writing Effective Goals
**Good goals are:**
- Specific about functionality
- Include technical requirements
- Mention target technologies
- Specify output format/interface

**Examples:**
```
❌ "Build a website"
✅ "Create a responsive Flask web application for recipe management with user authentication, search functionality, and SQLite database"

❌ "Make an API"
✅ "Build a REST API using FastAPI that manages book inventory with CRUD operations, JWT authentication, and PostgreSQL database"
```

### Choosing Iterations
- **3-5 iterations**: Standard projects
- **2-3 iterations**: Simple tools/scripts
- **5-8 iterations**: Complex applications
- **Indefinite**: Continuous improvement projects

### Monitoring Best Practices
- Use `--watch` for real-time monitoring
- Check `--mcp-tools` to see tool usage
- Review iteration logs in `.swarmdev/iterations/`
- Monitor token usage for cost control

## Next Steps

Now that you've built your first project:

1. **Explore Examples**: Check out [Examples & Use Cases](examples.md)
2. **Learn Workflows**: Deep dive into [Workflows Guide](../user-guide/workflows.md)
3. **Configure**: Customize SwarmDev with [Configuration Guide](../configuration/README.md)
4. **Advanced Features**: Explore the [Architecture Documentation](../architecture/README.md)

## Troubleshooting

### Build Fails to Start
- Check API keys: `echo $OPENAI_API_KEY`
- Verify Docker: `docker ps`
- Test MCP: `swarmdev status --mcp-only`

### Slow Performance
- Check internet connection
- Monitor token usage: `swarmdev status --usage`
- Consider using faster models: `--model gpt-4o-mini`

### Unexpected Results
- Review the goal clarity
- Check iteration logs: `.swarmdev/iterations/`
- Try a different workflow type

### Getting Help
- CLI help: `swarmdev build --help`
- Documentation: Browse other sections
- Issues: [GitHub Issues](https://github.com/chungoid/swarmdev/issues)

---

**Congratulations!** You've successfully built your first project with SwarmDev. The platform's AI agents have handled research, planning, development, and documentation automatically. 