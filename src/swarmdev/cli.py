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
from pathlib import Path
import subprocess

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
    assistant_parser.add_argument('--project-dir', '-d', help='Project directory for the assistant (defaults to current directory)')
    
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
    build_parser.add_argument('--workflow', choices=['standard_project', 'research_only', 'development_only', 'indefinite', 'iteration', 'refactor', 'versioned'], 
                             default='standard_project', help='Workflow type to use')
    build_parser.add_argument('--max-iterations', type=int, default=3, help='Maximum iterations for iteration workflow')
    build_parser.add_argument('--target-version', help='Target version for versioned workflow (e.g., "2.0", "1.5")')
    build_parser.add_argument('--current-version', help='Current version for versioned workflow (auto-detected if not provided)')
    
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
    
    # MCP analysis command
    mcp_analysis_parser = subparsers.add_parser('mcp-analysis', help='Analyze MCP system performance and health')
    mcp_analysis_parser.add_argument('--project-dir', '-d', default='.', help='Project directory')

    # Pull MCP Images command
    pull_images_parser = subparsers.add_parser('pull-images', help='Download and set up MCP Docker images from GHCR')
    pull_images_parser.epilog = """
Examples:
  swarmdev pull-images                    # Download all MCP Docker images
  
If you get "permission denied" or "broken pipe" errors, try:
  swarmdev fix-docker-group              # Fix Docker group membership issues
"""
    
    # Fix Docker Group command
    fix_docker_parser = subparsers.add_parser('fix-docker-group', help='Fix Docker group membership issues that prevent MCP containers from running')
    fix_docker_parser.epilog = """
This command helps fix common Docker permission issues including:
  - User not in docker group
  - Group membership not active in current session
  - Permission denied errors when running Docker commands

Examples:
  swarmdev fix-docker-group              # Diagnose and fix Docker group issues
  
After running this, you may need to:
  - Log out and log back in
  - Start a new terminal session
  - Run 'newgrp docker' in your current session
"""
    
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
        try:
            return registry.get_provider()
        except ValueError as e:
            # No providers available, provide helpful error message
            available_apis = []
            if os.environ.get('OPENAI_API_KEY'):
                available_apis.append('OpenAI')
            if os.environ.get('ANTHROPIC_API_KEY'):
                available_apis.append('Anthropic')
            if os.environ.get('GOOGLE_API_KEY'):
                available_apis.append('Google')
            
            if available_apis:
                logger.error(f"Auto-detection failed but API keys found for: {', '.join(available_apis)}")
                logger.error("Try specifying a provider explicitly with --llm-provider")
            else:
                logger.error("No LLM provider API keys found in environment variables!")
                logger.error("Please set one of:")
                logger.error("  export OPENAI_API_KEY='your-openai-key'")
                logger.error("  export ANTHROPIC_API_KEY='your-anthropic-key'")
                logger.error("  export GOOGLE_API_KEY='your-google-key'")
                logger.error("")
                logger.error("Or specify a provider manually: swarmdev assistant --llm-provider openai")
            raise e
    
    elif provider_name == 'openai':
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            sys.exit(1)
        return OpenAIProvider(api_key=api_key, model=model or 'o4-mini-2025-04-16')
    
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
    """Enhanced collaborative assistant mode with persistent session and workflow management."""
    from .interactive_agent.collaborative_agent import CollaborativeAgent
    from .utils.mcp_manager import MCPManager
    
    # Set cleaner logging levels for better UX, but allow MCP debugging in verbose mode
    import logging
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Only suppress MCP logging if not in verbose mode
    if not getattr(args, 'verbose', False):
        logging.getLogger("swarmdev.mcp").setLevel(logging.WARNING)
        logging.getLogger("swarmdev.collaborative_agent").setLevel(logging.WARNING)
    else:
        print("Verbose mode enabled - showing detailed MCP tool debugging")
        logging.getLogger("swarmdev.mcp").setLevel(logging.DEBUG)
        logging.getLogger("swarmdev.collaborative_agent").setLevel(logging.DEBUG)
    
    print("SwarmDev Collaborative Assistant")
    print("=" * 50)
    
    # Initialize LLM provider
    try:
        llm_provider = get_llm_provider(args.llm_provider, args.llm_model)
        print(f"LLM Provider: {llm_provider.__class__.__name__}")
    except Exception as e:
        print(f"Failed to initialize LLM provider: {e}")
        return
    
    # Initialize MCP manager with enhanced diagnostics
    mcp_manager = None
    try:
        mcp_config = {
            "enabled": True,
            "config_file": ".swarmdev/mcp_config.json"
        }
        # Get project directory, defaulting to current working directory
        project_dir = getattr(args, 'project_dir', None) or os.getcwd()
        mcp_manager = MCPManager(mcp_config, project_dir)
        
        print("Initializing MCP tools...")
        mcp_manager.initialize_tools()
        available_tools = mcp_manager.get_available_tools()
        print(f"MCP Tools: {len(available_tools)} ready")
        
        # Show detailed tool information in verbose mode
        if getattr(args, 'verbose', False):
            print("\nMCP Tool Details:")
            for tool_id in available_tools:
                tool_info = mcp_manager.get_tool_info(tool_id)
                if tool_info:
                    print(f"   {tool_id}:")
                    print(f"     Status: {tool_info.get('status', 'unknown')}")
                    print(f"     Command: {tool_info.get('command', 'unknown')}")
    
            print()
        
        # Show MCP metrics in verbose mode
        if getattr(args, 'verbose', False):
            print("MCP Metrics:")
            metrics = mcp_manager.get_metrics()
            print(f"  Total calls: {metrics.get('total_calls', 0)}")
            print(f"  Successful: {metrics.get('successful_calls', 0)}")
            print(f"  Failed: {metrics.get('failed_calls', 0)}")
            print()
            
    except Exception as e:
        print(f"MCP initialization failed: {e}")
        if getattr(args, 'verbose', False):
            import traceback
            print("Full MCP initialization error:")
            traceback.print_exc()
        print("   Continuing without MCP tools...")
        mcp_manager = None
    
    # Create collaborative agent
    try:
        agent = CollaborativeAgent(
            llm_provider=llm_provider,
            mcp_manager=mcp_manager,
            project_dir=getattr(args, 'project_dir', None),  # Use None to trigger current directory detection
            config={"verbose": getattr(args, 'verbose', False)}
        )
        
        # Start session
        welcome_message = agent.start_session()
        print("\n" + welcome_message)
        
    except Exception as e:
        print(f"Failed to initialize Collaborative Agent: {e}")
        if getattr(args, 'verbose', False):
            import traceback
            print("Full agent initialization error:")
            traceback.print_exc()
        return
    
    # Interactive loop
    print("\n" + "="*50)
    print("COLLABORATIVE SESSION STARTED")
    print("   Commands: 'exit', 'quit', 'status', 'pause', 'resume'")
    if getattr(args, 'verbose', False):
        print("   Debug Commands: 'mcp-status', 'mcp-test'")
    print("   Or just chat naturally with the agent!")
    print("="*50 + "\n")
    
    try:
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                # Handle special commands
                if user_input.lower() in ['exit', 'quit']:
                    response = agent.stop_session()
                    print(f"\nAgent: {response}")
                    break
                
                elif user_input.lower() == 'status':
                    status = agent.get_status()
                    print(f"\nAgent Status:")
                    print(f"  Session ID: {status['session_id']}")
                    print(f"  Active: {status['is_active']}")
                    print(f"  Conversation Length: {status['conversation_length']}")
                    print(f"  MCP Tools: {len(status['mcp_tools_available'])}")
                    
                    if status['current_workflow']:
                        wf = status['current_workflow']
                        print(f"  Current Workflow:")
                        print(f"    Type: {wf['workflow_id']}")
                        print(f"    Status: {wf['status']}")
                        print(f"    Phase: {wf['current_phase']}")
                        print(f"    Started: {wf['started_at']}")
                    else:
                        print(f"  Current Workflow: None")
                    continue
                
                elif user_input.lower() == 'mcp-status' and getattr(args, 'verbose', False):
                    # Debug command to check MCP status
                    if mcp_manager:
                        print("\nMCP Manager Status:")
                        print(f"  Enabled: {mcp_manager.is_enabled()}")
                        available_tools = mcp_manager.get_available_tools()
                        print(f"  Available tools: {available_tools}")
                        
                        metrics = mcp_manager.get_metrics()
                        print(f"  Total calls: {metrics.get('total_calls', 0)}")
                        print(f"  Successful calls: {metrics.get('successful_calls', 0)}")
                        print(f"  Failed calls: {metrics.get('failed_calls', 0)}")
                        
                        for tool_id in available_tools:
                            tool_info = mcp_manager.get_tool_info(tool_id)
                            print(f"  {tool_id}: {tool_info.get('status', 'unknown')} (used {tool_info.get('usage_count', 0)} times)")
                    else:
                        print("\nMCP Manager is not initialized")
                    continue
                
                elif user_input.lower() == 'mcp-test' and getattr(args, 'verbose', False):
                    # Debug command to test MCP tools
                    if mcp_manager and mcp_manager.get_available_tools():
                        print("\nTesting MCP tools...")
                        for tool_id in mcp_manager.get_available_tools()[:3]:  # Test first 3 tools
                            print(f"Testing {tool_id}...")
                            try:
                                # Try a simple test call
                                result = mcp_manager.call_tool(tool_id, "tools/list", {}, timeout=5)
                                if result.get("error"):
                                    print(f"  ERROR {tool_id}: {result['error']}")
                                else:
                                    print(f"  OK {tool_id}: OK")
                            except Exception as e:
                                print(f"  ERROR {tool_id}: Exception - {e}")
                    else:
                        print("\nNo MCP tools available to test")
                    continue
                
                elif user_input.lower() == 'pause':
                    response = agent.pause_workflow()
                    print(f"\nAgent: {response}")
                    continue
                
                elif user_input.lower() == 'resume':
                    response = agent.resume_workflow()
                    print(f"\nAgent: {response}")
                    continue
                
                elif not user_input:
                    continue
                
                # Send message to agent
                response = agent.send_message(user_input)
                print(f"\nAgent: {response}")
                
                # Check if user wants to start a workflow
                if any(keyword in user_input.lower() for keyword in ['build', 'create', 'develop', 'start workflow']):
                    workflow_prompt = """
                    
Would you like me to start a workflow for this project? I can:
• **research_only** - Just research and gather information
• **standard_project** - Full development lifecycle (research → planning → development → docs)
• **development_only** - Skip research, go straight to implementation
• **indefinite** - Continuous improvement cycles
• **iteration** - Fixed number of improvement cycles
• **refactor** - Focus on improving existing code

Just say "start [workflow_type]" or tell me what you'd like to do!"""
                    print(workflow_prompt)
                
            except KeyboardInterrupt:
                print("\n\nInterrupted - stopping session...")
                agent.stop_session()
                break
            except EOFError:
                print("\n\nSession ended")
                agent.stop_session()
                break
            except Exception as e:
                print(f"\nError during conversation: {e}")
                print("The agent is still active. Try again or type 'exit' to quit.")
                
    except Exception as e:
        print(f"Critical error in assistant session: {e}")
    
    finally:
        if 'agent' in locals():
            try:
                agent.stop_session()
            except:
                pass
        print("\nCollaborative session ended. Thank you!")


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
    
    # Load config file from .swarmdev directory if it exists
    config_file = os.path.join(args.project_dir, '.swarmdev', 'swarmdev_config.json')
    file_config = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
            logger.info(f"Loaded config from: {config_file}")
        except Exception as e:
            logger.warning(f"Failed to load config file {config_file}: {e}")
    
    # Merge file config with CLI args (CLI args take precedence)
    # Start with file config, then override with CLI args
    merged_config = file_config.copy()
    
    # Extract LLM settings from file config first
    if "llm" in file_config:
        llm_config = file_config["llm"]
        if "provider" in llm_config:
            merged_config["llm_provider"] = llm_config["provider"]
        if "model" in llm_config:
            merged_config["llm_model"] = llm_config["model"]
    
    # CLI arguments override file config
    cli_config = {
        "max_runtime": args.max_runtime,
        "verbose": args.verbose if hasattr(args, 'verbose') else False,
        "workflow": args.workflow,
        "max_iterations": args.max_iterations,
        "target_version": getattr(args, 'target_version', None),
        "current_version": getattr(args, 'current_version', None)
    }
    
    # Only override llm settings if explicitly provided in CLI
    if args.llm_provider != 'auto':  # CLI default is 'auto'
        cli_config["llm_provider"] = args.llm_provider
    
    if args.llm_model:  # CLI default is None
        cli_config["llm_model"] = args.llm_model
    
    # Update merged config with CLI overrides
    merged_config.update(cli_config)
    
    logger.info(f"Final config - LLM Provider: {merged_config.get('llm_provider', 'auto')}, LLM Model: {merged_config.get('llm_model', 'default')}")
    
    # Initialize the swarm builder with the merged config
    builder = SwarmBuilder(
        project_dir=args.project_dir,
        goal_file=args.goal,
        config=merged_config
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
            print(f"  ERROR: Agent {agent_id} has no MCP metrics!")
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
                elif workflow['id'] == 'refactor':
                    print(f"  Usage: swarmdev build --goal refactor_goal.txt --workflow {workflow['id']} --project-dir ./existing_project")
                    print(f"  Note: Analyzes existing codebase and refactors according to goal")
                elif workflow['id'] == 'versioned':
                    print(f"  Usage: swarmdev build --goal goal.txt --workflow {workflow['id']} --target-version 2.0 --max-iterations 15")
                    print(f"  Note: Version-driven development with incremental progression (1.3→1.4→...→2.0)")
                    print(f"  Advanced: Can overshoot max-iterations to reach target version, or stop early if target reached")
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
        
        print(f"\nAnalysis complete! Report saved to: {args.output}")
        
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


def cmd_mcp_analysis(args):
    """Analyze MCP system performance and health."""
    try:
        print("=== MCP SYSTEM ANALYSIS ===")
        
        # Initialize MCP manager to get metrics
        config = {
            "enabled": True,
            "docker_enabled": True,
            "global_timeout": 120,
            "persistent_connections": True
        }
        
        from swarmdev.utils.mcp_manager import MCPManager
        from swarmdev.utils.mcp_metrics import get_mcp_logger, get_metrics_collector
        
        manager = MCPManager(config, args.project_dir)
        
        if not manager.is_enabled():
            print("MCP system is disabled.")
            return
        
        print(f"Project Directory: {args.project_dir}")
        print(f"Available Tools: {len(manager.get_available_tools())}")
        print(f"Tools: {', '.join(manager.get_available_tools())}")
        print()
        
        # Get basic metrics
        basic_metrics = manager.get_metrics()
        print("BASIC METRICS:")
        print(f"  Total Calls: {basic_metrics.get('total_calls', 0)}")
        print(f"  Successful: {basic_metrics.get('successful_calls', 0)}")
        print(f"  Failed: {basic_metrics.get('failed_calls', 0)}")
        
        if basic_metrics.get('total_calls', 0) > 0:
            success_rate = basic_metrics.get('successful_calls', 0) / basic_metrics.get('total_calls', 1)
            print(f"  Success Rate: {success_rate:.1%}")
        
        print(f"  Average Response Time: {basic_metrics.get('average_response_time', 0):.2f}s")
        print()
        
        # Tool usage breakdown
        tools_used = basic_metrics.get('tools_used', {})
        if tools_used:
            print("TOOL USAGE:")
            for tool_id, count in sorted(tools_used.items(), key=lambda x: x[1], reverse=True):
                print(f"  {tool_id}: {count} calls")
            print()
        
        # Enhanced health report
        try:
            health_report = manager.get_health_report()
            if "error" not in health_report:
                print("ENHANCED HEALTH ANALYSIS:")
                system_metrics = health_report.get("system_metrics", {})
                print(f"  System Success Rate: {system_metrics.get('successful_calls', 0) / max(system_metrics.get('total_calls', 1), 1):.1%}")
                print(f"  Tools Healthy: {system_metrics.get('tools_healthy', 0)}")
                print(f"  Tools Degraded: {system_metrics.get('tools_degraded', 0)}")
                print(f"  Tools Unhealthy: {system_metrics.get('tools_unhealthy', 0)}")
                print()
                
                # Individual tool health
                tool_health = health_report.get("tool_health", {})
                if tool_health:
                    print("INDIVIDUAL TOOL HEALTH:")
                    for tool_id, health in tool_health.items():
                        status_icon = {
                            "healthy": "✅",
                            "degraded": "⚠️", 
                            "unhealthy": "❌",
                            "unknown": "❓"
                        }.get(health.get("connection_status", "unknown"), "❓")
                        
                        print(f"  {status_icon} {tool_id}:")
                        print(f"    Health Score: {health.get('health_score', 0):.2f}")
                        print(f"    Total Calls: {health.get('total_calls', 0)}")
                        print(f"    Success Rate: {health.get('successful_calls', 0) / max(health.get('total_calls', 1), 1):.1%}")
                        print(f"    Avg Response: {health.get('avg_response_time', 0):.2f}s")
                        print(f"    Consecutive Failures: {health.get('consecutive_failures', 0)}")
                        
                        if health.get('last_failure_time'):
                            print(f"    Last Failure: {health.get('last_failure_time', 'N/A')}")
                    print()
        except Exception as e:
            print(f"Enhanced analysis unavailable: {e}")
        
        # Performance report
        try:
            performance_report = manager.generate_performance_report()
            if performance_report and not performance_report.startswith("Performance report generation failed"):
                print("PERFORMANCE REPORT:")
                print(performance_report)
        except Exception as e:
            print(f"Performance report unavailable: {e}")
        
        # Log file analysis
        logs_dir = Path(args.project_dir) / ".swarmdev" / "logs"
        if logs_dir.exists():
            print("LOG FILE ANALYSIS:")
            
            # Check for various log files
            log_files = {
                "mcp.log": "Main MCP log",
                "mcp_detailed.log": "Detailed MCP operations",
                "mcp_performance.log": "Performance metrics",
                "mcp_errors.log": "Error tracking"
            }
            
            for log_file, description in log_files.items():
                log_path = logs_dir / log_file
                if log_path.exists():
                    size = log_path.stat().st_size
                    print(f"  {log_file}: {size:,} bytes ({description})")
                else:
                    print(f"  {log_file}: Not found")
            print()
        
        # Recent activity analysis (if logs exist)
        mcp_log_path = logs_dir / "mcp.log" if logs_dir.exists() else None
        if mcp_log_path and mcp_log_path.exists():
            print("RECENT ACTIVITY (Last 10 calls):")
            try:
                import subprocess
                result = subprocess.run(
                    ["tail", "-n", "50", str(mcp_log_path)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    call_starts = [line for line in lines if "MCP CALL START" in line][-10:]
                    
                    for line in call_starts:
                        # Extract basic info from log line
                        if " Tool: " in line and " Method: " in line:
                            try:
                                tool_part = line.split(" Tool: ")[1].split(" | ")[0]
                                method_part = line.split(" Method: ")[1].split(" | ")[0]
                                timestamp = line.split(" | ")[0]
                                print(f"  {timestamp} - {tool_part}.{method_part}")
                            except:
                                print(f"  {line}")
                else:
                    print("  Could not read recent activity from logs")
            except Exception as e:
                print(f"  Error reading recent activity: {e}")
        
        print("\n=== ANALYSIS COMPLETE ===")
        
    except Exception as e:
        print(f"MCP analysis failed: {e}")
        import traceback
        if args.verbose:
            traceback.print_exc()


def cmd_pull_images(args):
    """Handles the 'pull-images' command to download MCP Docker images."""
    logger.info("Starting MCP Docker image download process...")
    try:
        # Try to find the script in multiple locations to handle both development and installed modes
        
        # Option 1: Development mode (running from project directory)
        cli_file_path = os.path.abspath(__file__)
        src_swarmdev_dir = os.path.dirname(cli_file_path)
        dev_script_path = os.path.join(src_swarmdev_dir, "scripts", "pull_mcp_images.py")
        
        # Option 2: Installed mode (package installation)
        import swarmdev
        package_dir = os.path.dirname(swarmdev.__file__)
        installed_script_path = os.path.join(package_dir, "scripts", "pull_mcp_images.py")
        
        # Choose the script path
        if os.path.exists(dev_script_path):
            script_path = dev_script_path
            logger.debug(f"Using development script: {script_path}")
        elif os.path.exists(installed_script_path):
            script_path = installed_script_path
            logger.debug(f"Using installed script: {script_path}")
        else:
            logger.error(f"Image pulling script not found in either location:")
            logger.error(f"  Development: {dev_script_path}")
            logger.error(f"  Installed: {installed_script_path}")
            sys.exit(1)

        # Run the script as a subprocess
        process = subprocess.run([sys.executable, script_path], check=False, text=True)
        
        if process.returncode != 0:
            logger.error("MCP Docker image download process failed. See output from the script above for details.")
            sys.exit(process.returncode)
        else:
            # The script itself prints success, so just a confirmation from CLI
            logger.info("MCP Docker image download process completed successfully.")

    except FileNotFoundError: 
        logger.error(f"Python interpreter not found at: {sys.executable}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred while trying to run the image pulling script: {e}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def cmd_fix_docker_group(args):
    """Handles the 'fix-docker-group' command to fix Docker group membership issues."""
    logger.info("Starting Docker group membership fix...")
    try:
        # Construct path to the fix script
        cli_file_path = os.path.abspath(__file__)
        src_swarmdev_dir = os.path.dirname(cli_file_path)
        script_path = os.path.join(src_swarmdev_dir, "scripts", "fix_docker_group.py")

        if not os.path.exists(script_path):
            logger.error(f"Docker group fix script not found at: {script_path}")
            logger.error("Please ensure 'scripts/fix_docker_group.py' exists in the correct location relative to 'cli.py'.")
            sys.exit(1)

        # Run the script as a subprocess
        process = subprocess.run([sys.executable, script_path], check=False, text=True)
        
        if process.returncode != 0:
            logger.error("Docker group fix process failed. See output from the script above for details.")
            sys.exit(process.returncode)
        else:
            logger.info("Docker group fix process completed. Check script output for results.")

    except FileNotFoundError: 
        logger.error(f"Python interpreter not found at: {sys.executable}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred while trying to run the Docker group fix script: {e}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


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
    elif args.command == "mcp-analysis":
        cmd_mcp_analysis(args)
    elif args.command == "pull-images":
        cmd_pull_images(args)
    elif args.command == "fix-docker-group":
        cmd_fix_docker_group(args)
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()


if __name__ == "__main__":
    main() 