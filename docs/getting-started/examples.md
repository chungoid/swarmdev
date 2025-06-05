# Examples & Use Cases

This guide provides real-world examples of SwarmDev usage across different project types and scenarios. Each example includes the goal, recommended workflow, and expected outcomes.

## New Project Examples

### Web Applications

#### Simple Web App
```bash
swarmdev build \
  --goal "Create a Flask web application for personal expense tracking with categories, monthly summaries, and data visualization" \
  --workflow iteration \
  --max-iterations 3 \
  --project-dir ./expense-tracker
```

**Expected Output**: Complete Flask app with SQLite database, expense CRUD operations, categorization, monthly reports, and interactive charts.

#### REST API
```bash
swarmdev build \
  --goal "Build a FastAPI REST API for book management with CRUD operations, search functionality, JWT authentication, and PostgreSQL database" \
  --workflow iteration \
  --max-iterations 4 \
  --project-dir ./book-api
```

**Expected Output**: FastAPI application with database models, authentication system, comprehensive API endpoints, and OpenAPI documentation.

#### Real-time Application
```bash
swarmdev build \
  --goal "Create a real-time chat application using Flask-SocketIO with rooms, message history, user authentication, and emoji support" \
  --workflow iteration \
  --max-iterations 5 \
  --project-dir ./chat-app
```

**Expected Output**: WebSocket-based chat with multiple rooms, persistent message storage, user management, and modern UI.

### CLI Tools & Scripts

#### Data Processing Tool
```bash
swarmdev build \
  --goal "Create a Python CLI tool for CSV data analysis with filtering, aggregation, and statistical summaries" \
  --workflow standard_project \
  --project-dir ./data-analyzer
```

**Expected Output**: Command-line tool with argparse interface, pandas-based processing, and comprehensive output options.

#### System Utility
```bash
swarmdev build \
  --goal "Build a system monitoring CLI tool that displays CPU, memory, disk usage with alerts, logging, and configuration file support" \
  --workflow iteration \
  --max-iterations 3 \
  --project-dir ./system-monitor
```

**Expected Output**: Cross-platform monitoring tool with configurable thresholds, alert mechanisms, and detailed logging.

#### File Management Tool
```bash
swarmdev build \
  --goal "Create a command-line tool for organizing files by type, date, or custom rules with undo functionality and dry-run mode" \
  --workflow standard_project \
  --project-dir ./file-organizer
```

**Expected Output**: Robust file organization tool with safety features and flexible rule system.

### Data Science & ML

#### Machine Learning Pipeline
```bash
swarmdev build \
  --goal "Build a machine learning pipeline for customer churn prediction using scikit-learn with data preprocessing, model training, evaluation, and prediction API" \
  --workflow iteration \
  --max-iterations 4 \
  --project-dir ./churn-prediction
```

**Expected Output**: Complete ML pipeline with data preprocessing, multiple model training, evaluation metrics, and deployment-ready API.

#### Data Analysis Dashboard
```bash
swarmdev build \
  --goal "Create a Streamlit dashboard for sales data analysis with interactive visualizations, filtering, and automated report generation" \
  --workflow iteration \
  --max-iterations 3 \
  --project-dir ./sales-dashboard
```

**Expected Output**: Interactive Streamlit application with comprehensive data visualization and export capabilities.

### Automation & DevOps

#### CI/CD Pipeline
```bash
swarmdev build \
  --goal "Create GitHub Actions workflows for Python project with testing, linting, security scanning, and automated deployment to AWS" \
  --workflow standard_project \
  --project-dir ./ci-cd-setup
```

**Expected Output**: Complete CI/CD configuration with multi-stage testing, security checks, and deployment automation.

#### Infrastructure as Code
```bash
swarmdev build \
  --goal "Build Terraform modules for AWS infrastructure including VPC, ECS cluster, RDS database, and monitoring with CloudWatch" \
  --workflow iteration \
  --max-iterations 3 \
  --project-dir ./aws-infrastructure
```

**Expected Output**: Modular Terraform configuration with best practices for AWS infrastructure deployment.

## Existing Project Enhancement Examples

### Web Application Improvements

#### Add Authentication
```bash
swarmdev build \
  --goal "Add user authentication with JWT tokens and role-based access control to existing Flask application" \
  --workflow iteration \
  --project-dir ./existing-flask-app \
  --completion-strategy smart \
  --max-iterations 3
```

**Expected Changes**: Authentication system integration, user management, role-based middleware, and security enhancements.

#### Performance Optimization
```bash
swarmdev build \
  --goal "Optimize database queries, add Redis caching layer, and improve API response times" \
  --workflow iteration \
  --project-dir ./existing-api \
  --completion-strategy smart \
  --max-iterations 2
```

**Expected Changes**: Query optimization, caching implementation, and performance monitoring.

#### Frontend Modernization
```bash
swarmdev build \
  --goal "Refactor jQuery-based frontend to modern React components with TypeScript, responsive design, and improved UX" \
  --workflow iteration \
  --project-dir ./legacy-web-app \
  --completion-strategy version_driven \
  --target-version 2.0 \
  --max-iterations 4
```

**Expected Changes**: Complete frontend rewrite, component-based architecture, TypeScript integration, and responsive design.

### CLI Tool Enhancements

#### Add Configuration Support
```bash
swarmdev build \
  --goal "Add configuration file support, improved error handling, logging system, and plugin architecture to existing CLI tool" \
  --workflow iteration \
  --project-dir ./existing-cli \
  --completion-strategy smart \
  --max-iterations 2
```

**Expected Changes**: Configuration management, robust error handling, logging framework, and extensible plugin system.

#### Testing & CI/CD
```bash
swarmdev build \
  --goal "Add comprehensive unit tests, integration tests, GitHub Actions CI/CD pipeline, and automated release process" \
  --workflow standard_project \
  --project-dir ./existing-tool
```

**Expected Changes**: Complete test suite, CI/CD automation, and release management.

### Library & Package Improvements

#### Type Safety & Documentation
```bash
swarmdev build \
  --goal "Add complete type hints, improve documentation with examples, add docstring tests, and ensure mypy compatibility" \
  --workflow iteration \
  --project-dir ./existing-library \
  --completion-strategy smart \
  --max-iterations 2
```

**Expected Changes**: Full type annotation, enhanced documentation, doctest integration, and static type checking.

#### Async Support
```bash
swarmdev build \
  --goal "Add async/await support while maintaining backward compatibility, optimize performance, and update API design" \
  --workflow iteration \
  --project-dir ./sync-library \
  --completion-strategy version_driven \
  --target-version 2.0 \
  --max-iterations 3
```

**Expected Changes**: Async API addition, compatibility layer, performance improvements, and version migration guide.

## Research & Planning Examples

### Technology Evaluation
```bash
swarmdev build \
  --goal "Research and compare microservices frameworks (FastAPI, Flask, Django) for building scalable e-commerce platform" \
  --workflow research_only \
  --project-dir ./microservices-research
```

**Expected Output**: Comprehensive research report with framework comparison, pros/cons analysis, and recommendations.

### Architecture Planning
```bash
swarmdev build \
  --goal "Design system architecture for real-time analytics platform handling 1M+ events per minute with fault tolerance" \
  --workflow research_only \
  --project-dir ./analytics-architecture
```

**Expected Output**: Detailed architectural design, technology stack recommendations, scalability analysis, and implementation roadmap.

### Security Assessment
```bash
swarmdev build \
  --goal "Research security best practices for cloud-native applications including container security, API protection, and data encryption" \
  --workflow research_only \
  --project-dir ./security-research
```

**Expected Output**: Security guidelines, best practices documentation, threat analysis, and implementation recommendations.

## Advanced Workflow Examples

### Continuous Improvement
```bash
swarmdev build \
  --goal "Continuously improve and maintain the customer portal application with feature additions and optimizations" \
  --workflow indefinite \
  --project-dir ./customer-portal
```

**Usage**: For ongoing maintenance projects where continuous improvement is needed.

### Version-Driven Development
```bash
swarmdev build \
  --goal "Upgrade application to support new features while maintaining API compatibility" \
  --workflow iteration \
  --completion-strategy version_driven \
  --target-version 3.0 \
  --max-iterations 5 \
  --project-dir ./api-upgrade
```

**Usage**: When working toward specific version milestones with defined compatibility requirements.

### Background Processing
```bash
swarmdev build \
  --goal "Build comprehensive e-commerce platform with payment processing, inventory management, and order fulfillment" \
  --workflow iteration \
  --max-iterations 8 \
  --background \
  --project-id ecommerce-platform \
  --project-dir ./ecommerce
```

**Usage**: For complex, long-running projects that can be developed in the background.

## Goal Writing Best Practices

### Effective Goal Structure

**Good Example:**
```
"Create a Python FastAPI application for task management with:
- SQLAlchemy ORM with PostgreSQL database
- JWT authentication and user management
- CRUD operations for tasks with categories and priorities
- OpenAPI documentation with example requests
- Docker deployment configuration"
```

**Why it works:**
- Specifies technology stack
- Lists concrete features
- Includes technical requirements
- Mentions deployment considerations

### Goals to Avoid

**Too Vague:**
```
❌ "Build a website"
❌ "Make an API"
❌ "Fix the application"
```

**Too Complex for Single Run:**
```
❌ "Build a complete social media platform with mobile apps, web interface, recommendation engine, and admin dashboard"
```

**Better Approach:**
```
✅ "Build the core user management and posting system for a social media platform using Django REST Framework"
```

## Workflow Selection Guide

| Project Type | Recommended Workflow | Iterations | Notes |
|-------------|---------------------|------------|--------|
| Simple CLI tool | `standard_project` | N/A | Single comprehensive pass |
| Web application | `iteration` | 3-5 | Allows for refinement |
| API service | `iteration` | 2-4 | Iterative improvement |
| Data analysis | `research_only` then `development_only` | N/A | Research first approach |
| Existing codebase | `iteration` | 2-3 | Smart enhancement |
| Complex system | `iteration` with `indefinite` follow-up | 5-8 then ongoing | Long-term development |
| Library/package | `iteration` | 2-4 | Focus on API design |
| Infrastructure | `standard_project` | N/A | Comprehensive planning needed |

## Getting More Examples

- **CLI Help**: `swarmdev examples` - Built-in example generator
- **Community**: Check the [examples/](../../../examples/) directory
- **Templates**: Use `swarmdev template` for project scaffolding
- **Documentation**: Explore workflow-specific guides in [User Guide](../user-guide/workflows.md)

---

**Pro Tip**: Start with simpler goals and gradually increase complexity as you become familiar with SwarmDev's capabilities. The iteration workflow is excellent for learning as it allows for refinement and improvement. 