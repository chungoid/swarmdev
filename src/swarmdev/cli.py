#!/usr/bin/env python3
"""
SwarmDev CLI - Command-line interface for the SwarmDev platform.
 
This script provides a simple command-line interface for running the SwarmDev platform
with various options.
 
Usage:
    swarmdev assistant                              # Complete guided experience
    swarmdev refine [--output GOAL_FILE]           # Goal refinement only
    swarmdev build --goal GOAL_FILE [options]      # Build from goal file
    swarmdev status --project-id PROJECT_ID        # Check project status
    swarmdev workflows [--verbose]                 # List available workflows
    swarmdev --help
 
Examples:
    swarmdev assistant                              # Launch complete assistant
    swarmdev refine --output goal.txt              # Refine goal to file
    swarmdev build --goal goal.txt --project-dir ./my_project
    swarmdev status --project-id proj_12345 --watch
"""
 
import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv

from swarmdev.utils.llm_provider import OpenAIProvider, AnthropicProvider, GoogleProvider, ProviderRegistry
from swarmdev.utils.blueprint_manager import BlueprintManager
from swarmdev.interactive_agent import LLMEnabledInteractiveAgent
from swarmdev.interactive_agent.enhanced_agent import EnhancedInteractiveAgent
from swarmdev.goal_processor import GoalStorage, SwarmBuilder
from swarmdev.swarm_builder.workflows import list_available_workflows

# Load environment variables from .env file
load_dotenv()
 
# Initialize basic logging (will be reconfigured per command)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # Only console logging initially
)
 
logger = logging.getLogger('swarmdev_cli')
 
 
def setup_parser():
    """Set up the argument parser with all supported commands and options."""
    parser = argparse.ArgumentParser(
        description='SwarmDev - Multi-Agent Swarm Platform',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress all output except errors')
    parser.add_argument('--log-level', choices=['debug', 'info', 'warning', 'error'], default='info',
                        help='Set logging level')
    parser.add_argument('--config', help='Path to configuration file')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Refine command
    refine_parser = subparsers.add_parser('refine', help='Refine a project goal through conversation')
    refine_parser.add_argument('--output', '-o', help='Output file for the refined goal')
    
    # Assistant command (enhanced interactive agent)
    assistant_parser = subparsers.add_parser('assistant', help='Interactive assistant for complete project setup')
    assistant_parser.add_argument('--llm-provider', choices=['openai', 'anthropic', 'google', 'auto'], default='auto',
                                 help='LLM provider to use')
    assistant_parser.add_argument('--llm-model', help='LLM model to use')
    
    # Build command
    build_parser = subparsers.add_parser('build', help='Build a project from a goal')
    build_parser.add_argument('--goal', '-g', required=True, help='Path to goal file')
    build_parser.add_argument('--project-dir', '-d', default='./project', help='Project directory')
    build_parser.add_argument('--max-runtime', type=int, default=3600, help='Maximum runtime in seconds')
    build_parser.add_argument('--llm-provider', choices=['openai', 'anthropic', 'google', 'auto'], default='auto',
                             help='LLM provider to use')
    build_parser.add_argument('--llm-model', help='LLM model to use')
    build_parser.add_argument('--background', '-b', action='store_true', help='Run build in background and return immediately')
    build_parser.add_argument('--wait', '-w', action='store_true', help='Wait for build to complete (default behavior)')
    build_parser.add_argument('--workflow', choices=['standard_project', 'research_only', 'development_only', 'indefinite', 'iteration'], 
                             default='standard_project', help='Workflow type to use')
    build_parser.add_argument('--max-iterations', type=int, default=3, help='Maximum iterations for iteration workflow')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check the status of a project')
    status_parser.add_argument('--project-id', '-p', required=True, help='Project ID')
    status_parser.add_argument('--watch', '-w', action='store_true', help='Watch status in real-time (updates every 2 seconds)')
    status_parser.add_argument('--logs', '-l', action='store_true', help='Show recent logs from agents')
    status_parser.add_argument('--detailed', action='store_true', help='Show detailed task information')
    status_parser.add_argument('--refresh-rate', type=int, default=2, help='Refresh rate in seconds for --watch mode')
    
    # List workflows command
    workflows_parser = subparsers.add_parser('workflows', help='List available workflows')
    workflows_parser.add_argument('--verbose', action='store_true', help='Show detailed workflow descriptions')
    
    # Analyze logs command
    logs_parser = subparsers.add_parser('analyze-logs', help='Analyze agent logs and generate workflow report')
    logs_parser.add_argument('--logs-dir', default='.swarmdev/logs', help='Directory containing log files')
    logs_parser.add_argument('--output', '-o', default='workflow_analysis.md', help='Output file for analysis report')
    logs_parser.add_argument('--workflow-id', help='Filter analysis by specific workflow ID')
    logs_parser.add_argument('--show-report', action='store_true', help='Display report summary in terminal')
    
    # Blueprint management command
    blueprint_parser = subparsers.add_parser('blueprint', help='Manage project blueprints and user feedback')
    blueprint_subparsers = blueprint_parser.add_subparsers(dest='blueprint_action', help='Blueprint management actions')
    
    # Blueprint status
    status_bp = blueprint_subparsers.add_parser('status', help='Show current blueprint status')
    status_bp.add_argument('--project-dir', '-d', default='.', help='Project directory')
    
    # Blueprint show
    show_bp = blueprint_subparsers.add_parser('show', help='Display detailed blueprint')
    show_bp.add_argument('--project-dir', '-d', default='.', help='Project directory')
    show_bp.add_argument('--format', choices=['markdown', 'json'], default='markdown', help='Output format')
    
    # Blueprint feedback
    feedback_bp = blueprint_subparsers.add_parser('feedback', help='Add user feedback to guide development')
    feedback_bp.add_argument('feedback_text', help='Feedback text to add')
    feedback_bp.add_argument('--project-dir', '-d', default='.', help='Project directory')
    feedback_bp.add_argument('--run-number', type=int, help='Run number for feedback (auto-detected if not provided)')
    
    # Blueprint modify
    modify_bp = blueprint_subparsers.add_parser('modify', help='Modify specific blueprint items')
    modify_bp.add_argument('--project-dir', '-d', default='.', help='Project directory')
    modify_bp.add_argument('--phase', help='Phase name or ID to modify')
    modify_bp.add_argument('--item', help='Item description to modify')
    modify_bp.add_argument('--status', choices=['complete', 'in_progress', 'not_started', 'removed', 'high_priority'], 
                          help='New status for the item')
    
    return parser
 
 
def configure_logging(args, project_dir=None):
    """Configure logging based on command-line arguments."""
    if args.quiet:
        logging.root.setLevel(logging.ERROR)
    elif args.verbose:
        logging.root.setLevel(logging.DEBUG)
    else:
        log_level = getattr(logging, args.log_level.upper())
        logging.root.setLevel(log_level)
    
    # Set up project-specific file logging if project_dir is provided
    if project_dir:
        setup_project_logging(project_dir)


def setup_project_logging(project_dir: str):
    """Set up logging to write to the project's .swarmdev/logs directory."""
    # Create .swarmdev/logs directory in the PROJECT directory, not the current directory
    logs_dir = os.path.join(project_dir, '.swarmdev', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Add file handler for project-specific logging
    log_file = os.path.join(logs_dir, 'swarmdev.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Add to root logger
    logging.root.addHandler(file_handler)
    
    logger.info(f"Project logging initialized: {log_file}")
 
 
def get_llm_provider(provider_name, model=None):
    """Get an LLM provider based on name and model."""
    if provider_name == 'auto':
        # Use provider registry to auto-detect available providers
        registry = ProviderRegistry()
        registry.discover_providers()
        return registry.get_provider()
    
    elif provider_name == 'openai':
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            sys.exit(1)
        return OpenAIProvider(api_key=api_key, model=model or 'gpt-4o')
    
    elif provider_name == 'anthropic':
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            logger.error("ANTHROPIC_API_KEY environment variable not set")
            sys.exit(1)
        return AnthropicProvider(api_key=api_key, model=model or 'claude-3-opus-20240229')
    
    elif provider_name == 'google':
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            logger.error("GOOGLE_API_KEY environment variable not set")
            sys.exit(1)
        return GoogleProvider(api_key=api_key, model=model or 'gemini-2.0-flash-001')
    
    else:
        logger.error(f"Unknown provider: {provider_name}")
        logger.error("Available providers: auto, openai, anthropic, google")
        sys.exit(1)
 
 
def cmd_refine(args):
    """Run the refine command to refine a project goal through conversation."""
    logger.info("Starting goal refinement conversation")
    
    # Get the LLM provider
    provider = get_llm_provider(args.llm_provider if hasattr(args, 'llm_provider') else 'auto', 
                               args.llm_model if hasattr(args, 'llm_model') else None)
    
    # Create the interactive agent
    agent = LLMEnabledInteractiveAgent(provider)
    
    # Start the conversation
    greeting = agent.start_conversation()
    print(f"Agent: {greeting}")
    
    # Main conversation loop
    while True:
        # Get user input
        try:
            user_input = input("You: ")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting conversation.")
            return
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Agent: Goodbye! Thank you for using the SwarmDev platform.")
            break
        
        # Process the message
        response = agent.process_message(user_input)
        print(f"Agent: {response}")
        
        # Check if the goal is complete
        if "Is this accurate?" in response and "I can store this goal" in response:
            # Ask if the user wants to store the goal
            store_input = input("Do you want to store this goal? (yes/no): ")
            
            if store_input.lower() in ["yes", "y"]:
                # Store the goal
                goal_file = args.output or "goal.txt"
                if agent.store_goal(goal_file):
                    print(f"Agent: Goal stored successfully in {goal_file}.")
                    print("You can now run the builder with:")
                    print(f"  swarmdev build --goal {goal_file} --project-dir ./project")
                else:
                    print("Agent: Failed to store the goal.")
                
                break
 

def cmd_assistant(args):
    """Run the enhanced assistant for complete project setup."""
    logger.info("Starting enhanced interactive assistant")
    
    # Get the LLM provider
    provider = get_llm_provider(args.llm_provider, args.llm_model)
    
    # Create the enhanced interactive agent
    agent = EnhancedInteractiveAgent(provider)
    
    # Start the assistant mode
    greeting = agent.start_assistant_mode()
    print(f"Assistant: {greeting}")
    
    # Main conversation loop
    while True:
        # Get user input
        try:
            user_input = input("\nYou: ")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting assistant. Thanks for using SwarmDev!")
            return
        
        # Check for exit commands
        if user_input.lower() in ["exit", "quit", "bye", "stop"]:
            print("Assistant: Goodbye! Feel free to use the assistant anytime.")
            break
        
        # Check for help commands
        if user_input.lower().startswith("help"):
            if "workflow" in user_input.lower():
                help_text = agent.get_configuration_help("workflows")
                print(f"Assistant: {help_text}")
            elif "background" in user_input.lower():
                help_text = agent.get_configuration_help("background")
                print(f"Assistant: {help_text}")
            elif "llm" in user_input.lower():
                help_text = agent.get_configuration_help("llm")
                print(f"Assistant: {help_text}")
            elif "transition" in user_input.lower() or "phase" in user_input.lower():
                print("Assistant: Here are the transition commands:\n"
                      "- To move from goal refinement to configuration: 'configure', 'next phase', 'config'\n"
                      "- To go back from configuration to goal refinement: 'refine more', 'go back'\n"
                      "- The assistant will also suggest transitions when appropriate.")
            else:
                print("Assistant: I can help with 'workflows', 'background', 'llm', or 'transition' commands. "
                      "Try 'help workflows' or 'help transition' for example.")
            continue
        
        # Process the message
        try:
            response = agent.process_assistant_message(user_input)
            print(f"Assistant: {response}")
            
            # Check if build was started
            if "Build started successfully!" in response:
                print("\nYour SwarmDev project is now running!")
                print("Use the monitoring commands shown above to track progress.")
                break
                
        except Exception as e:
            logger.error(f"Error processing assistant message: {e}")
            print(f"Assistant: I encountered an error: {e}")
            print("Please try rephrasing your message or type 'help' for assistance.")


def cmd_build(args):
    """Run the build command to build a project from a goal."""
    logger.info(f"Starting build process with goal file: {args.goal}")
    
    # Check if the goal file exists
    if not os.path.exists(args.goal):
        logger.error(f"Goal file not found: {args.goal}")
        sys.exit(1)
    
    # Create the project directory
    os.makedirs(args.project_dir, exist_ok=True)
    
    # Set up project-specific logging AFTER creating the project directory
    setup_project_logging(args.project_dir)
    
    # Initialize the swarm builder with the goal file
    builder = SwarmBuilder(
        project_dir=args.project_dir,
        goal_file=args.goal,
        config={
            "max_runtime": args.max_runtime,
            "llm_provider": args.llm_provider,
            "llm_model": args.llm_model,
            "verbose": args.verbose if hasattr(args, 'verbose') else False,
            "workflow": args.workflow,
            "max_iterations": args.max_iterations
        }
    )
    
    try:
        logger.info("Starting build process...")
        project_id = builder.build()
        
        logger.info("Build process started successfully!")
        print(f"Build process started with project ID: {project_id}")
        print(f"Project files will be created in: {args.project_dir}")
        
        if args.background:
            print("Running in background mode.")
            print("You can check the status with:")
            print(f"  swarmdev status --project-id {project_id}")
            print(f"  swarmdev status --project-id {project_id} --watch")
            return project_id
        else:
            print("Monitoring build progress... (Press Ctrl+C to detach and run in background)")
            print("="*60)
            
            # Monitor the build process
            try:
                _monitor_build_progress(builder, project_id, args.project_dir)
            except KeyboardInterrupt:
                print(f"\nBuild detached and running in background.")
                print(f"Monitor progress with: swarmdev status --project-id {project_id} --watch")
            
            return project_id
    
    except KeyboardInterrupt:
        logger.info("Build process interrupted by user")
        print("\nBuild process stopped.")
    except Exception as e:
        logger.error(f"Unexpected error during build: {e}")
        print(f"An error occurred: {e}")
        sys.exit(1)


def cmd_status(args):
    """Run the status command to check the status of a project."""
    logger.info(f"Checking status for project: {args.project_id}")
    
    try:
        # Find the project directory
        project_dir = _find_project_directory(args.project_id)
        
        if not project_dir:
            print(f"Project not found: {args.project_id}")
            print("Make sure you have the correct project ID and that the project directory exists.")
            return
        
        # Initialize builder to get status
        builder = SwarmBuilder(project_dir=project_dir)
        
        if args.watch:
            _watch_status(builder, args)
        else:
            _display_status(builder, args, project_dir)
    
    except KeyboardInterrupt:
        print("\nStatus monitoring stopped.")
    except Exception as e:
        logger.error(f"Error retrieving project status: {e}")
        print(f"Error: {e}")


def _find_project_directory(project_id: str) -> str:
    """Find the project directory containing the given project ID."""
    possible_paths = [
        ".",  # Current directory
        f"./project",  # Default project directory
        f"./{project_id}",  # Project ID as directory name
        f"./projects/{project_id}",  # Projects subdirectory
    ]
    
    for path in possible_paths:
        # Look in .swarmdev first, then fallback to legacy location
        metadata_file = os.path.join(path, ".swarmdev", "project_metadata.json")
        if not os.path.exists(metadata_file):
            metadata_file = os.path.join(path, "project_metadata.json")
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    if metadata.get("project_id") == project_id:
                        return path
            except (json.JSONDecodeError, FileNotFoundError):
                continue
    
    return None


def _watch_status(builder: SwarmBuilder, args):
    """Watch status in real-time with updates."""
    print(f"Watching project status: {args.project_id} (Press Ctrl+C to stop)")
    print(f"Refresh rate: {args.refresh_rate} seconds\n")
    
    try:
        while True:
            # Clear screen (works on most terminals)
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print(f"Live Status - {datetime.now().strftime('%H:%M:%S')}")
            print("=" * 60)
            
            # Get and display current status
            status = builder.get_status()
            _display_status_content(status, args, detailed_header=False)
            
            # Check if build is complete
            if status.get('status') in ['completed', 'failed', 'cancelled']:
                print(f"\nBuild finished with status: {status.get('status').upper()}")
                break
            
            print(f"\nRefreshing in {args.refresh_rate} seconds... (Press Ctrl+C to stop)")
            time.sleep(args.refresh_rate)
            
    except KeyboardInterrupt:
        print("\nStatus monitoring stopped.")


def _display_status(builder: SwarmBuilder, args, project_dir: str):
    """Display status information once."""
    status = builder.get_status()
    
    print(f"\nProject Status: {args.project_id}")
    print("=" * 60)
    print(f"Directory: {project_dir}")
    
    _display_status_content(status, args)


def _display_status_content(status: dict, args, detailed_header: bool = True):
    """Display the main status content."""
    if detailed_header:
        print(f"Status: {status.get('status', 'Unknown').title()}")
        print(f"Created: {status.get('created_at', 'Unknown')}")
    else:
        print(f"Status: {status.get('status', 'Unknown').title()}")
    
    if status.get('started_at'):
        print(f"Started: {status['started_at']}")
    
    if status.get('execution_id'):
        print(f"Execution ID: {status['execution_id']}")
    
    # Show execution status if available
    if status.get('execution_status'):
        exec_status = status['execution_status']
        total = exec_status.get('total_tasks', 0)
        completed = exec_status.get('completed_tasks', 0)
        failed = exec_status.get('failed_tasks', 0)
        
        print(f"\nExecution Progress:")
        if total > 0:
            progress_percent = (completed / total) * 100
            progress_bar = "#" * int(progress_percent / 5) + "-" * (20 - int(progress_percent / 5))
            print(f"  [{progress_bar}] {progress_percent:.1f}%")
        
        print(f"  Total Tasks: {total}")
        print(f"  Completed: {completed}")
        print(f"  Failed: {failed}")
        print(f"  In Progress: {total - completed - failed}")
        
        # Show individual task status
        if exec_status.get('tasks') and (args.detailed if hasattr(args, 'detailed') else False):
            print(f"\nTask Details:")
            for task_id, task_status in exec_status['tasks'].items():
                print(f"  {task_id.replace('exec_', '').replace(args.project_id.split('_')[-1] + '_', '')}: {task_status}")
    
    # Show MCP tool usage metrics
    if status.get('mcp_metrics'):
        _display_mcp_metrics(status['mcp_metrics'])
    
    # Show LLM usage metrics
    if status.get('llm_metrics'):
        _display_llm_metrics(status['llm_metrics'])
    
    # Show recent logs if requested
    if hasattr(args, 'logs') and args.logs:
        _display_recent_logs(status)
    
    if status.get('goal') and (not hasattr(args, 'detailed') or args.detailed):
        goal_preview = status['goal'][:150] + "..." if len(status['goal']) > 150 else status['goal']
        print(f"\nGoal: {goal_preview}")
    
    if status.get('status') in ['cancelled', 'failed'] and status.get('error'):
        print(f"\nError: {status['error']}")
    
    if status.get('completed_at'):
        print(f"\nCompleted: {status['completed_at']}")


def _display_mcp_metrics(mcp_metrics: dict):
    """Display MCP tool usage metrics - SINGLE SOURCE OF TRUTH from BaseAgent.use_mcp_tool()."""
    print(f"\nMCP Tool Usage:")
    
    # NO FALLBACKS - ONLY use agent-level metrics from BaseAgent.use_mcp_tool()
    total_calls = 0
    total_successful = 0
    total_failed = 0
    total_cache_hits = 0
    total_cache_misses = 0
    total_throttled = 0
    all_server_calls = {}
    
    for agent_id, agent_metrics in mcp_metrics.items():
        if not agent_metrics:
            continue
            
        # ONLY get metrics from agent_metrics (BaseAgent.use_mcp_tool tracking)
        agent_data = agent_metrics.get("agent_metrics", {})
        
        # Fail loudly if agent metrics are missing
        if not agent_data:
            print(f"  ❌ ERROR: Agent {agent_id} has no MCP metrics!")
            print(f"  This means the agent is NOT using BaseAgent.use_mcp_tool()!")
            print(f"  ALL MCP calls must go through the unified interface!")
            continue
        
        # Extract unified metrics
        agent_total = agent_data.get("total_calls", 0)
        agent_success = agent_data.get("successful_calls", 0)
        agent_failed = agent_data.get("failed_calls", 0)
        agent_cache_hits = agent_data.get("cache_hits", 0)
        agent_cache_misses = agent_data.get("cache_misses", 0)
        agent_throttled = agent_data.get("throttled_calls", 0)
        
        total_calls += agent_total
        total_successful += agent_success
        total_failed += agent_failed
        total_cache_hits += agent_cache_hits
        total_cache_misses += agent_cache_misses
        total_throttled += agent_throttled
        
        # Get tool usage from agent metrics ONLY
        tools_used = agent_data.get("tools_used", {})
        for tool_id, count in tools_used.items():
            # Map tool_id to readable server name
            server_name = tool_id  # Could be enhanced with name mapping
            all_server_calls[server_name] = all_server_calls.get(server_name, 0) + count
    
    # Display unified metrics
    print(f"  Total MCP Calls: {total_calls}")
    if total_calls > 0:
        success_rate = (total_successful / total_calls) * 100
        print(f"  Success Rate: {success_rate:.1f}% ({total_successful} successful, {total_failed} failed)")
        
        # EFFICIENCY METRICS
        if total_cache_hits > 0 or total_cache_misses > 0:
            cache_rate = (total_cache_hits / (total_cache_hits + total_cache_misses)) * 100
            print(f"  Cache Efficiency: {cache_rate:.1f}% ({total_cache_hits} hits, {total_cache_misses} misses)")
        
        if total_throttled > 0:
            print(f"  Throttled Calls: {total_throttled} (prevented wasteful usage)")
    
    # Display per-server usage (from unified tracking)
    if all_server_calls:
        print(f"  Server Usage:")
        for server_name, call_count in sorted(all_server_calls.items()):
            print(f"    {server_name}: {call_count} calls")
    else:
        if total_calls == 0:
            print(f"  No MCP calls made through unified interface")
        else:
            print(f"  ERROR: Calls detected but no server mapping!")
            print(f"  This indicates a bug in the metrics collection!")


def _display_llm_metrics(llm_metrics: dict):
    """Display LLM usage metrics."""
    print(f"\nLLM Usage:")
    
    # Aggregate metrics across all agents
    total_calls = 0
    total_input_tokens = 0
    total_output_tokens = 0
    models_used = set()
    providers_used = set()
    
    for agent_id, agent_metrics in llm_metrics.items():
        if not agent_metrics:
            continue
            
        total_calls += agent_metrics.get("total_calls", 0)
        total_input_tokens += agent_metrics.get("total_input_tokens", 0)
        total_output_tokens += agent_metrics.get("total_output_tokens", 0)
        
        model = agent_metrics.get("model", "unknown")
        provider = agent_metrics.get("provider", "unknown")
        
        if model != "unknown":
            models_used.add(model)
        if provider != "unknown":
            providers_used.add(provider)
    
    # Display model information
    if models_used:
        print(f"  Model(s): {', '.join(sorted(models_used))}")
    if providers_used:
        print(f"  Provider(s): {', '.join(sorted(providers_used))}")
    
    # Display token usage
    print(f"  Total LLM Calls: {total_calls}")
    print(f"  Input Tokens: {total_input_tokens:,}")
    print(f"  Output Tokens: {total_output_tokens:,}")
    print(f"  Total Tokens: {(total_input_tokens + total_output_tokens):,}")
    
    if total_input_tokens + total_output_tokens == 0:
        print(f"  No token usage recorded")


def _monitor_build_progress(builder: SwarmBuilder, project_id: str, project_dir: str):
    """Monitor build progress in real-time until completion."""
    refresh_rate = 2  # seconds
    
    while True:
        # Get current status
        status = builder.get_status()
        build_status = status.get('status', '').lower()
        
        # Display current status
        mock_args = type('Args', (), {'detailed': True, 'logs': True, 'project_id': project_id})()
        _display_status_content(status, mock_args)
        
        # Check if build is complete
        if build_status in ['completed', 'failed', 'cancelled']:
            if build_status == 'completed':
                print(f"\nBuild completed successfully!")
                print(f"Project files are available in: {project_dir}")
            elif build_status == 'failed':
                print(f"\nBuild failed!")
                if status.get('error'):
                    print(f"Error: {status['error']}")
            else:
                print(f"\nBuild was cancelled.")
            break
        
        print(f"\nRefreshing in {refresh_rate} seconds... (Press Ctrl+C to detach)")
        time.sleep(refresh_rate)
        
        # Clear screen for next update
        os.system('clear' if os.name == 'posix' else 'cls')
        print(f"Build Progress - {datetime.now().strftime('%H:%M:%S')}")
        print(f"Project ID: {project_id}")
        print("=" * 60)


def _display_recent_logs(status: dict):
    """Display recent logs from the project."""
    print(f"\nRecent Activity:")
    
    # This is a placeholder - in a real implementation, you would
    # read actual log files or get logs from the orchestrator
    if status.get('execution_status', {}).get('tasks'):
        tasks = status['execution_status']['tasks']
        for task_id, task_status in list(tasks.items())[-3:]:  # Show last 3 tasks
            task_name = task_id.split('_')[-1] if '_' in task_id else task_id
            print(f"  {task_name}: {task_status}")
    else:
        print(f"  Project status: {status.get('status', 'unknown')}")
        if status.get('started_at'):
            print(f"  Started at: {status['started_at']}")


def cmd_workflows(args):
    """Run the workflows command to list available workflows."""
    logger.info("Listing available workflows")
    
    try:
        workflows = list_available_workflows()
        
        print("\nAvailable Workflows:")
        print("=" * 60)
        
        for workflow in workflows:
            print(f"\n{workflow['name']} ({workflow['id']})")
            if args.verbose:
                print(f"  Description: {workflow['description']}")
                
                # Add usage examples for each workflow
                if workflow['id'] == 'standard_project':
                    print(f"  Usage: swarmdev build --goal goal.txt --workflow {workflow['id']}")
                elif workflow['id'] == 'indefinite':
                    print(f"  Usage: swarmdev build --goal goal.txt --workflow {workflow['id']}")
                    print(f"  Note: Runs continuously until manually stopped")
                elif workflow['id'] == 'iteration':
                    print(f"  Usage: swarmdev build --goal goal.txt --workflow {workflow['id']} --max-iterations 5")
                    print(f"  Note: Runs specified number of improvement cycles")
                else:
                    print(f"  Usage: swarmdev build --goal goal.txt --workflow {workflow['id']}")
            else:
                print(f"  {workflow['description']}")
        
        print(f"\nUse --verbose for detailed descriptions and usage examples.")
        print(f"Example: swarmdev workflows --verbose")
        
    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        print(f"Error: {e}")


# Helper function to get all available status commands
def cmd_analyze_logs(args):
    """Analyze agent logs and generate workflow performance report."""
    try:
        from swarmdev.utils.log_analyzer import LogAnalyzer
        
        print(f"Analyzing logs from: {args.logs_dir}")
        
        # Create analyzer
        analyzer = LogAnalyzer(args.logs_dir)
        
        if not analyzer.log_files:
            print(f"No log files found in {args.logs_dir}")
            print("Make sure you have run some workflows to generate logs.")
            return
        
        print(f"Found {len(analyzer.log_files)} log files:")
        for agent_type, log_file in analyzer.log_files.items():
            print(f"  - {agent_type}: {log_file}")
        
        # Generate analysis
        print("\nAnalyzing workflow execution...")
        analysis = analyzer.analyze_workflow_execution(args.workflow_id)
        
        # Generate report
        print(f"Generating report to: {args.output}")
        report = analyzer.generate_workflow_report(args.output)
        
        print(f"\n✓ Analysis complete! Report saved to: {args.output}")
        
        # Show summary if requested
        if args.show_report:
            print("\n" + "="*60)
            print("WORKFLOW ANALYSIS SUMMARY")
            print("="*60)
            
            # Show key metrics
            summary = analysis.get('workflow_summary', {})
            metrics = analysis.get('performance_metrics', {})
            
            print(f"\nEXECUTION SUMMARY")
            print(f"  Duration: {summary.get('total_duration', 0):.1f} seconds")
            print(f"  Tasks: {summary.get('total_tasks', 0)}")
            print(f"  Success Rate: {summary.get('success_rate', 0)*100:.1f}%")
            print(f"  Files Created: {summary.get('total_files_created', 0)}")
            print(f"  Files Modified: {summary.get('total_files_modified', 0)}")
            
            print(f"\nPERFORMANCE METRICS")
            print(f"  Avg Task Duration: {metrics.get('avg_task_duration', 0):.1f}s")
            print(f"  Total LLM Calls: {metrics.get('total_llm_calls', 0)}")
            print(f"  Productivity Score: {metrics.get('productivity_score', 0):.2f}")
            print(f"  Error Rate: {metrics.get('error_rate', 0)*100:.1f}%")
            
            # Show agent breakdown
            print(f"\nAGENT PERFORMANCE")
            for agent_type, agent_metrics in analysis.get('agent_executions', {}).items():
                print(f"  {agent_type.title()}Agent:")
                print(f"    Tasks: {agent_metrics['total_tasks']} ({agent_metrics['completed_tasks']} completed)")
                print(f"    Files: {agent_metrics['files_created']} created, {agent_metrics['files_modified']} modified")
                print(f"    Avg Duration: {agent_metrics['avg_duration']:.1f}s")
            
            # Show insights
            insights = analysis.get('insights', [])
            if insights:
                print(f"\nINSIGHTS")
                for insight in insights:
                    print(f"  - {insight}")
            
            # Show recommendations  
            recommendations = analysis.get('recommendations', [])
            if recommendations:
                print(f"\nRECOMMENDATIONS")
                for rec in recommendations:
                    print(f"  - {rec}")
            
            print(f"\nFull report available in: {args.output}")
        
    except ImportError as e:
        logger.error(f"Failed to import log analyzer: {e}")
        print("Make sure the swarmdev package is properly installed.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error analyzing logs: {e}")
        print(f"Failed to analyze logs: {e}")
        sys.exit(1)


def cmd_blueprint(args):
    """Handle blueprint management commands."""
    try:
        # Initialize blueprint manager
        blueprint_manager = BlueprintManager(args.project_dir, logger)
        
        if args.blueprint_action == 'status':
            # Show blueprint status
            blueprint = blueprint_manager.load_existing_blueprint()
            
            if blueprint is None:
                print("No blueprint found for this project.")
                print("Run a SwarmDev build to create an initial blueprint.")
                return
            
            status = blueprint_manager.get_blueprint_status(blueprint)
            
            print(f"\nBlueprint Status for: {blueprint.project_name}")
            print("=" * 60)
            print(f"Created: {blueprint.created_date[:10]}")
            print(f"Last Updated: {blueprint.last_updated[:10]}")
            print(f"Current Run: {blueprint.run_number}")
            print(f"Total Phases: {status['total_phases']}")
            print(f"Total Items: {status['total_items']}")
            print(f"Completion: {status['completion_percentage']:.1f}%")
            print(f"Complete: {status['complete_items']}")
            print(f"In Progress: {status['in_progress_items']}")
            print(f"High Priority: {status['high_priority_items']}")
            print(f"Removed: {status['removed_items']}")
            print(f"Feedback Entries: {status['feedback_entries']}")
            
            # Show incomplete items summary
            incomplete_items = blueprint_manager.get_incomplete_items(blueprint)
            if incomplete_items:
                print(f"\nNext Priority Items:")
                for item in incomplete_items[:5]:
                    status_symbol = {
                        'high_priority': '!',
                        'in_progress': '~',
                        'not_started': ' '
                    }.get(item.status, ' ')
                    print(f"  [{status_symbol}] {item.description}")
                
                if len(incomplete_items) > 5:
                    print(f"  ... and {len(incomplete_items) - 5} more items")
            else:
                print("\nAll blueprint items complete!")
                print("Future runs will generate creative expansions.")
        
        elif args.blueprint_action == 'show':
            # Show detailed blueprint
            blueprint = blueprint_manager.load_existing_blueprint()
            
            if blueprint is None:
                print("No blueprint found for this project.")
                return
            
            if args.format == 'json':
                import json
                from dataclasses import asdict
                print(json.dumps(asdict(blueprint), indent=2, default=str))
            else:
                # Read and display the markdown blueprint
                blueprint_file = os.path.join(args.project_dir, '.swarmdev', 'project_blueprint.md')
                if os.path.exists(blueprint_file):
                    with open(blueprint_file, 'r') as f:
                        print(f.read())
                else:
                    print("Blueprint file not found.")
        
        elif args.blueprint_action == 'feedback':
            # Add user feedback
            blueprint = blueprint_manager.load_existing_blueprint()
            
            if blueprint is None:
                print("No blueprint found for this project.")
                print("Run a SwarmDev build first to create a blueprint.")
                return
            
            # Determine run number
            run_number = args.run_number or (blueprint.run_number + 1)
            
            # Add feedback
            success = blueprint_manager.add_user_feedback(args.feedback_text, run_number)
            
            if success:
                print(f"Feedback added for run {run_number}:")
                print(f"  \"{args.feedback_text}\"")
                print("\nThis feedback will be applied in the next SwarmDev run.")
            else:
                print("Failed to add feedback.")
        
        elif args.blueprint_action == 'modify':
            # Modify blueprint item
            blueprint = blueprint_manager.load_existing_blueprint()
            
            if blueprint is None:
                print("No blueprint found for this project.")
                return
            
            if not args.item or not args.status:
                print("Both --item and --status are required for modify command.")
                return
            
            # Update item status
            success = blueprint_manager.update_item_status(
                blueprint, args.item, args.status, datetime.now().isoformat()
            )
            
            if success:
                blueprint_manager.save_blueprint(blueprint)
                print(f"Updated item status: {args.item[:50]}...")
                print(f"New status: {args.status}")
            else:
                print(f"Item not found: {args.item}")
                print("Use 'swarmdev blueprint show' to see available items.")
        
        else:
            print(f"Unknown blueprint action: {args.blueprint_action}")
            print("Available actions: status, show, feedback, modify")
    
    except Exception as e:
        logger.error(f"Blueprint command failed: {e}")
        print(f"Error: {e}")


def show_status_help():
    """Show available status commands and examples."""
    print("""
SwarmDev Status Commands:

Basic status check:
  swarmdev status --project-id PROJECT_ID

Live monitoring (watch mode):
  swarmdev status --project-id PROJECT_ID --watch
  swarmdev status --project-id PROJECT_ID -w

Show detailed task information:
  swarmdev status --project-id PROJECT_ID --detailed

Show recent logs:
  swarmdev status --project-id PROJECT_ID --logs

Combine options:
  swarmdev status --project-id PROJECT_ID --watch --detailed --logs

Custom refresh rate for watch mode:
  swarmdev status --project-id PROJECT_ID --watch --refresh-rate 5

Examples:
  # Watch a build in real-time
  swarmdev status -p project_20250530_223934 -w
  
  # Get detailed status with logs
  swarmdev status -p project_20250530_223934 --detailed --logs
  
  # Fast refresh live monitoring
  swarmdev status -p project_20250530_223934 -w --refresh-rate 1
    """)


def main():
    """Main entry point for the SwarmDev CLI."""
    parser = setup_parser()
    args = parser.parse_args()
    
    # Configure logging
    configure_logging(args)
    
    # Handle missing command
    if not args.command:
        parser.print_help()
        return
    
    # Route to the appropriate command handler
    if args.command == "refine":
        cmd_refine(args)
    elif args.command == "assistant":
        cmd_assistant(args)
    elif args.command == "build":
        cmd_build(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "workflows":
        cmd_workflows(args)
    elif args.command == "analyze-logs":
        cmd_analyze_logs(args)
    elif args.command == "blueprint":
        cmd_blueprint(args)
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()


if __name__ == "__main__":
    main() 