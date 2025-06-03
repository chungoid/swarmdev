"""
MCP Manager for the SwarmDev platform.
This module provides centralized management of MCP (Model Context Protocol) tools.
"""

import json
import logging
import subprocess
import threading
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import sys
import uuid
import fcntl

# Import enhanced MCP logging and metrics
from .mcp_metrics import get_mcp_logger, get_metrics_collector, MCPLogger, MCPMetricsCollector


class MCPManager:
    """
    Generic MCP tool manager for the SwarmDev platform.
    
    This class handles initialization, connection management, and communication
    with external MCP servers through JSON-RPC protocol using only configuration.
    """
    
    def __init__(self, config: Dict, project_dir: str = "."):
        """
        Initialize the MCP Manager.
        
        Args:
            config: MCP configuration dictionary
            project_dir: Project directory for logging and config files
        """
        self.project_dir = project_dir
        self.config = config
        self.servers = {}  # server_id -> server_info
        self.connections = {}  # server_id -> connection
        self.capabilities = {}  # server_id -> discovered capabilities
        self.enabled = config.get("enabled", False)
        
        # Get settings with sensible defaults
        settings = config.get("mcpSettings", config.get("settings", {}))
        self.default_timeout = settings.get("defaultTimeout", settings.get("globalTimeout", 30))
        self.init_timeout = settings.get("initializationTimeout", 15)
        self.discovery_timeout = settings.get("discoveryTimeout", 10)
        self.persistent_connections = settings.get("persistentConnections", True)
        self.auto_discovery = settings.get("autoDiscovery", True)
        self.retry_count = settings.get("retryCount", 3)
        self.retry_delay = settings.get("retryDelay", 1.0)
        
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "servers_available": 0,
            "discovery_failures": 0,
            "timeouts": 0
        }
        
        # Enhanced MCP-specific logging
        self._setup_mcp_logging()
        
        # Initialize enhanced logging and metrics
        self.enhanced_logger = get_mcp_logger(str(self.project_dir))
        self.metrics_collector = get_metrics_collector()
        
        # Thread safety
        self._lock = threading.RLock()
        
        if self.enabled:
            self.mcp_logger.info("=== MCP MANAGER INITIALIZATION ===")
            self.mcp_logger.info(f"Default timeout: {self.default_timeout}s")
            self.mcp_logger.info(f"Persistent connections: {self.persistent_connections}")
            self.mcp_logger.info("MCP Manager initialized - MCP tools enabled")
            self._load_mcp_config()
        else:
            self.mcp_logger.info("MCP Manager initialized - MCP tools disabled")
    
    def _setup_mcp_logging(self):
        """Set up dedicated MCP logging to mcp.log file."""
        # Create .swarmdev/logs directory in the PROJECT directory
        logs_dir = os.path.join(self.project_dir, ".swarmdev", "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create MCP-specific logger
        self.mcp_logger = logging.getLogger("swarmdev.mcp")
        self.mcp_logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.mcp_logger.handlers[:]:
            self.mcp_logger.removeHandler(handler)
        
        # Create file handler for mcp.log in the PROJECT directory
        mcp_log_file = os.path.join(logs_dir, "mcp.log")
        mcp_file_handler = logging.FileHandler(mcp_log_file)
        mcp_file_handler.setLevel(logging.DEBUG)
        
        # Create console handler for immediate feedback - REDUCED SPAM
        mcp_console_handler = logging.StreamHandler()
        # Only show WARNING and above on console to reduce spam
        mcp_console_handler.setLevel(logging.WARNING)
        
        # Create detailed formatter
        mcp_formatter = logging.Formatter(
            '%(asctime)s | MCP | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s'
        )
        mcp_file_handler.setFormatter(mcp_formatter)
        mcp_console_handler.setFormatter(mcp_formatter)
        
        # Add handlers
        self.mcp_logger.addHandler(mcp_file_handler)
        self.mcp_logger.addHandler(mcp_console_handler)
        
        # Prevent propagation to root logger
        self.mcp_logger.propagate = False
        
        self.mcp_logger.info("=== MCP LOGGING INITIALIZED ===")
    
    def _load_mcp_config(self):
        """Load MCP configuration with hierarchical merging: global config + project overrides."""
        try:
            # Step 1: Load global configuration first
            global_config_path = os.path.expanduser("~/.swarmdev/mcp_config.json")
            merged_config = {}
            
            if os.path.exists(global_config_path):
                self.mcp_logger.info(f"Loading global MCP config from: {global_config_path}")
                with open(global_config_path, 'r') as f:
                    global_config = json.load(f)
                
                # Handle both legacy format (servers at root) and new format (servers under key)
                if 'servers' in global_config or 'mcpServers' in global_config:
                    # New format: servers under specific key
                    merged_config = global_config.copy()
                    servers_count = len(global_config.get('mcpServers', global_config.get('servers', {})))
                else:
                    # Legacy format: servers directly at root level (like current global config)
                    # Convert to new format
                    merged_config = {"servers": global_config.copy()}
                    servers_count = len(global_config)
                
                self.mcp_logger.info(f"Global config loaded with {servers_count} servers")
            else:
                self.mcp_logger.info(f"Global MCP config not found at: {global_config_path}, using built-in defaults")
                # Use built-in default configuration
                merged_config = self._get_default_mcp_config()
            
            # Step 2: Look for project-specific config and merge
            project_config_paths = [
                "./.swarmdev/mcp_config.json",  # Preferred location
                "./mcp_config.json",           # Legacy fallback
                self.config.get("config_file") # Explicit override
            ]
            
            project_config_found = False
            for config_path in project_config_paths:
                if config_path and os.path.exists(config_path):
                    self.mcp_logger.info(f"Loading project MCP config from: {config_path}")
                    with open(config_path, 'r') as f:
                        project_config = json.load(f)
                    
                    # Merge project config over global config
                    merged_config = self._merge_mcp_configs(merged_config, project_config)
                    project_servers = len(project_config.get('mcpServers', project_config.get('servers', {})))
                    self.mcp_logger.info(f"Project config merged with {project_servers} servers")
                    project_config_found = True
                    break
            
            if not project_config_found:
                self.mcp_logger.info("No project-specific MCP config found, using global/default config")
            
            # Step 3: Fallback if still no configuration
            if not merged_config:
                self.mcp_logger.warning("No MCP configuration found anywhere, using built-in defaults")
                merged_config = self._get_default_mcp_config()

            # Step 3.5: Merge server configurations from self.config (constructor argument) if provided
            # This allows programmatic override of server definitions, e.g., for testing.
            if "mcpServers" in self.config:
                self.mcp_logger.info("Merging mcpServers from constructor config over loaded/default config.")
                constructor_servers = self.config.get("mcpServers", {})
                # Ensure merged_config has an mcpServers key to merge into
                if "mcpServers" not in merged_config:
                    # If merged_config used legacy 'servers' key, adapt or initialize
                    if "servers" in merged_config and isinstance(merged_config["servers"], dict):
                        merged_config["mcpServers"] = merged_config.pop("servers")
                    else:
                        merged_config["mcpServers"] = {}
                
                for server_id, server_conf in constructor_servers.items():
                    self.mcp_logger.debug(f"  Overriding/setting server '{server_id}' from constructor config.")
                    merged_config["mcpServers"][server_id] = server_conf
            
            # Step 4: Process the merged configuration
            # Load server configurations (support both old and new format)
            servers = merged_config.get("servers", merged_config.get("mcpServers", {}))
            settings = merged_config.get("settings", merged_config.get("mcpSettings", {}))
            
            self.mcp_logger.info(f"Final configuration contains {len(servers)} MCP servers")
            
            # Update global settings
            self.default_timeout = settings.get("defaultTimeout", settings.get("globalTimeout", self.default_timeout))
            self.persistent_connections = settings.get("persistentConnections", self.persistent_connections)
            
            # Initialize servers from configuration
            for server_id, server_config in servers.items():
                if not server_config.get("disabled", False):
                    self.mcp_logger.debug(f"Registering server: {server_id}")
                    self._register_server(server_id, server_config)
                else:
                    self.mcp_logger.info(f"Skipping disabled server: {server_id}")
            
            self.mcp_logger.info(f"Successfully loaded {len(self.servers)} MCP servers from configuration")
            
        except Exception as e:
            self.mcp_logger.error(f"Failed to load MCP configuration: {e}", exc_info=True)
    
    def _get_default_mcp_config(self) -> Dict:
        """Return the default MCP configuration if no file is found or is invalid."""
        default_config = {
            "servers": {
                "git": {
                    "command": ["docker", "run", "-i", "--rm", "-v", "$(pwd):/workspace", 
                               "ghcr.io/chungoid/git:latest"],
                    "timeout": 30,
                    "enabled": True,
                    "description": "Git operations and repository management"
                },
                "time": {
                    "command": ["docker", "run", "-i", "--rm", "ghcr.io/chungoid/time:latest"],
                    "timeout": 30,
                    "enabled": True,
                    "description": "Time zone operations and conversions"
                },
                "fetch": {
                    "command": ["docker", "run", "-i", "--rm", "ghcr.io/chungoid/fetch:latest"],
                    "timeout": 30,
                    "enabled": True,
                    "description": "Web content fetching and processing"
                },
                "filesystem": {
                    "command": ["docker", "run", "-i", "--rm", "-v", "$(pwd):/workspace", 
                               "ghcr.io/chungoid/filesystem:latest", "/workspace"],
                    "timeout": 30,
                    "enabled": True,
                    "description": "File system operations with current directory access"
                },
                "memory": {
                    "command": ["docker", "run", "-i", "--rm", "ghcr.io/chungoid/memory:latest"],
                    "timeout": 30,
                    "enabled": True,
                    "description": "Persistent memory storage for context"
                },
                "sequential-thinking": {
                    "command": ["docker", "run", "-i", "--rm", "ghcr.io/chungoid/sequentialthinking:latest"],
                    "timeout": 60,
                    "enabled": True,
                    "description": "Advanced reasoning through sequential thoughts"
                },
                "everything": {
                    "command": ["docker", "run", "-i", "--rm", "ghcr.io/chungoid/everything:latest"],
                    "timeout": 30,
                    "enabled": True,
                    "description": "Reference MCP server with comprehensive tools"
                }
            }
        }
        return default_config
    
    def _merge_mcp_configs(self, global_config: Dict, project_config: Dict) -> Dict:
        """
        Merge project MCP config over global config, with project settings taking priority.
        """
        import copy
        merged = copy.deepcopy(global_config)
        
        # Merge server configurations
        global_servers = merged.get("servers", merged.get("mcpServers", {}))
        project_servers = project_config.get("servers", project_config.get("mcpServers", {}))
        
        # Project servers override global servers by ID
        for server_id, server_config in project_servers.items():
            global_servers[server_id] = server_config
        
        # Update the merged config with the unified server key
        if "mcpServers" in merged or "mcpServers" in project_config:
            merged["mcpServers"] = global_servers
        else:
            merged["servers"] = global_servers
        
        # Merge settings with project taking priority
        global_settings = merged.get("settings", merged.get("mcpSettings", {}))
        project_settings = project_config.get("settings", project_config.get("mcpSettings", {}))
        
        merged_settings = {**global_settings, **project_settings}
        
        # Update the merged config with the unified settings key
        if "mcpSettings" in merged or "mcpSettings" in project_config:
            merged["mcpSettings"] = merged_settings
        else:
            merged["settings"] = merged_settings
        
        return merged
    
    def _register_server(self, server_id: str, server_config: Dict):
        """Register an MCP server from configuration."""
        try:
            # Extract command - support both array and string formats
            command = server_config.get("command", [])
            if isinstance(command, str):
                command = [command]
            elif not isinstance(command, list):
                self.mcp_logger.error(f"Invalid command format for {server_id}: {command}")
                return
            
            # Add args if present
            args = server_config.get("args", [])
            if args:
                if isinstance(args, list):
                    command.extend(args)
                else:
                    command.append(args)
            
            # Handle shell expansions in command
            for i, arg in enumerate(command):
                if isinstance(arg, str):
                    # Replace $(pwd) with actual current directory
                    if "$(pwd)" in arg:
                        command[i] = arg.replace("$(pwd)", self.project_dir)
                    # Replace ${pwd} variant
                    elif "${pwd}" in arg:
                        command[i] = arg.replace("${pwd}", self.project_dir)
            
            timeout = server_config.get("timeout", self.default_timeout)
            
            self.servers[server_id] = {
                "id": server_id,
                "command": command,
                "description": server_config.get("description", ""),
                "timeout": timeout,
                "status": "configured",
                "attempts": 0,
                "last_error": None,
                "usage_count": 0,
                "last_used": None,
                "registration_time": datetime.now().isoformat()
            }
            
            self.mcp_logger.info(f"Successfully registered MCP server '{server_id}'")
            self.mcp_logger.info(f"  Command: {' '.join(command)}")
            self.mcp_logger.info(f"  Timeout: {timeout}s")
            # Debug filesystem registration
            if server_id == "filesystem":
                self.mcp_logger.debug(f"Registered filesystem server: {self.servers[server_id]['command']}")
            
        except Exception as e:
            self.mcp_logger.error(f"Failed to register MCP server '{server_id}': {e}", exc_info=True)
    
    def initialize_tools(self) -> bool:
        """Initialize MCP servers with lazy loading approach."""
        if not self.enabled:
            self.mcp_logger.info("MCP tools disabled, skipping initialization")
            return False
        
        self.mcp_logger.info("=== LAZY MCP INITIALIZATION ===")
        self.mcp_logger.info(f"Found {len(self.servers)} servers to make available")
        self.mcp_logger.info("Using lazy initialization - servers will connect on first use")
        
        # Mark all configured servers as ready for lazy initialization
        ready_count = 0
        for server_id, server_info in self.servers.items():
            if server_info["status"] == "configured":
                server_info["status"] = "ready"
                ready_count += 1
                self.mcp_logger.info(f"✅ {server_id} marked as available (lazy initialization)")
        
        self.mcp_logger.info(f"=== INITIALIZATION COMPLETE ===")
        self.mcp_logger.info(f"Available servers: {ready_count}/{len(self.servers)}")
        
        return ready_count > 0
    
    def _initialize_server(self, server_id: str) -> bool:
        """Initialize or re-initialize a connection to a server."""
        if server_id not in self.servers:
            self.mcp_logger.error(f"Attempted to initialize unknown server: {server_id}")
            return False

        server_config = self.servers[server_id]
        command = server_config.get('command')
        cwd = server_config.get('cwd')
        env_vars = server_config.get('env')

        if not command:
            self.mcp_logger.error(f"No command specified for server: {server_id}")
            return False

        self.mcp_logger.info(f"Initializing server: {server_id} with command: '{command}'")
        if cwd:
            self.mcp_logger.info(f"  Working directory: {cwd}")
        if env_vars:
            self.mcp_logger.info(f"  Environment variables: {env_vars}")
            current_env = os.environ.copy()
            current_env.update(env_vars)
            env_vars = current_env
        
        process = None
        try:
            # Start the server process
            self.mcp_logger.debug(f"Starting subprocess for {server_id}: {command}")
            self.mcp_logger.debug(f"Starting {server_id} server: {' '.join(command)}")
                        # Debug for filesystem command execution (reduced to debug level)
            if server_id == "filesystem":
                self.mcp_logger.debug(f"Filesystem command: {command}")
            
            process = subprocess.Popen(
                command, 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                # text=True, # text=True can cause issues with precise byte control needed for some protocols
                # bufsize=0, # Might be useful for unbuffered, but let's test default first with handshake
                shell=isinstance(command, str),
                cwd=cwd,
                env=env_vars
            )
            
            self.mcp_logger.debug(f"Started {server_id} server with PID: {process.pid if process else 'None'}")
            self.mcp_logger.info(f"Subprocess for {server_id} started. PID: {process.pid}")
            
            # Brief pause to allow server to actually start its process before handshake
            # The old code did not have an explicit sleep here before handshake, relying on readline timeout.
            # The init_delay of 2.0s is now effectively before this handshake.
            time.sleep(server_config.get('init_delay', 0.2)) # Short delay for process to spawn, main delay before was too long for handshake

            # MCP Initialization Handshake
            init_request_id = str(uuid.uuid4())
            init_payload = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "processId": os.getpid(), # Client process ID
                    "protocolVersion": "1.0", # Added protocolVersion
                    "clientInfo": {
                        "name": "SwarmDevMCPManager",
                        "version": "1.0.0", 
                        # Client capabilities can be an empty object if not detailed
                        "capabilities": {}
                    },
                    # Server capabilities expected by the initialize handshake
                    "capabilities": {}, # Added server capabilities placeholder
                    # "rootUri": Path(self.project_dir).as_uri(),
                    # "trace": "off" # Optional trace setting
                },
                "id": init_request_id
            }
            
            self.mcp_logger.info(f"Sending 'initialize' handshake to {server_id} (PID: {process.pid}), request_id: {init_request_id}")
            payload_str = json.dumps(init_payload) + "\n"
            process.stdin.write(payload_str.encode('utf-8'))
            process.stdin.flush()

            self.mcp_logger.debug(f"[{server_id} - {init_request_id}] Waiting for 'initialize' response...")

            response_json = None
            if self._wait_for_response(process, self.init_timeout): # Use self.init_timeout
                raw_response_text = process.stdout.readline().decode('utf-8').strip()
                self.mcp_logger.debug(f"Raw 'initialize' response from {server_id} (PID: {process.pid}): '{raw_response_text}'")
                if raw_response_text:
                    try:
                        response_json = json.loads(raw_response_text)
                        if response_json.get("id") != init_request_id:
                            self.mcp_logger.error(f"Initialize response ID mismatch for {server_id}. Expected '{init_request_id}', got '{response_json.get('id')}'")
                            response_json = None # Invalid response
                        elif "error" in response_json:
                            self.mcp_logger.error(f"Server {server_id} returned error during initialize: {response_json['error']}")
                            response_json = None # Error response
                    except json.JSONDecodeError as e:
                        self.mcp_logger.error(f"Failed to decode JSON initialize response from {server_id}: {e}. Raw: '{raw_response_text}'")
                        response_json = None
                else:
                    self.mcp_logger.error(f"Empty 'initialize' response from {server_id} (PID: {process.pid})")
            else:
                self.mcp_logger.error(f"Timeout waiting for 'initialize' response from {server_id} (PID: {process.pid})")

            if response_json and "result" in response_json:
                self.mcp_logger.info(f"Server {server_id} initialized successfully (handshake part 1). Response: {response_json.get('result')}")
                
                # Send 'initialized' notification (note: no "id" for notifications)
                initialized_notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {}
                }
                self.mcp_logger.info(f"Sending 'initialized' notification to {server_id} (PID: {process.pid})")
                notification_str = json.dumps(initialized_notification) + "\n"
                process.stdin.write(notification_str.encode('utf-8'))
                process.stdin.flush()

                with self._lock:
                    self.connections[server_id] = process # Store the raw process object
                    self.servers[server_id]['pid'] = process.pid
                    self.servers[server_id]['status'] = 'running' # Or 'initialized_handshake_complete'
                
                # Optional: Discover capabilities right after successful handshake
                if self.auto_discovery:
                    self.mcp_logger.info(f"Performing capability discovery for {server_id} after successful handshake.")
                    self._discover_capabilities(server_id)
                
                return True
            else:
                # Initialization failed
                self.mcp_logger.error(f"MCP Handshake failed for {server_id} (PID: {process.pid}). Terminating process.")
                stderr_output = self._read_stderr_non_blocking(process) # Try to get any last words
                if stderr_output:
                    self.mcp_logger.error(f"Stderr from {server_id} (PID: {process.pid}) on handshake failure: {stderr_output}")
                process.terminate()
                try:
                    process.wait(timeout=1.0) # Give it a moment to terminate
                except subprocess.TimeoutExpired:
                    process.kill()
                self.servers[server_id]['status'] = 'failed_handshake'
                self.servers[server_id]['last_error'] = "MCP Handshake failed"
                return False

        except FileNotFoundError:
            self.mcp_logger.error(f"Command not found for server {server_id}: {command.split()[0] if isinstance(command, str) else command[0]}", exc_info=True)
            if process: process.kill() # Ensure it's killed if Popen partially succeeded
            return False
        except (OSError, subprocess.SubprocessError) as e:
            self.mcp_logger.error(f"Failed to start server {server_id} (command: '{command}'): {e}", exc_info=True)
            if process: process.kill() # Ensure it's killed
            return False
        except Exception as e: # Catch any other unexpected error during initialization
            self.mcp_logger.critical(f"Unexpected error initializing server {server_id}: {e}", exc_info=True)
            if process: process.kill()
            return False
    
    def _discover_capabilities(self, server_id: str):
        """Discover capabilities of a server using tools/list."""
        if not self.auto_discovery:
            self.mcp_logger.info(f"Auto-discovery disabled for {server_id}, skipping capability discovery.")
            return

        self.mcp_logger.info(f"Discovering capabilities for server: {server_id} using 'tools/list'...")
        capabilities_data = {}
        discovery_method_name = "tools/list" # Standard MCP method for listing tools

        try:
            self.mcp_logger.debug(f"Attempting to call {discovery_method_name} on {server_id}")
            # _call_server_method will log raw request and response
            response = self._call_server_method(server_id, discovery_method_name, {}, timeout=self.discovery_timeout)
            
            if response and not response.get("error"):
                # Assuming tools/list returns a list of tool definitions under "result".
                # The exact structure can vary, this is a common pattern.
                tools_list = response.get("result")
                if isinstance(tools_list, list): # If result is directly the list
                    capabilities_data = {"tools": tools_list} 
                elif isinstance(tools_list, dict) and "tools" in tools_list: # If result is an object containing a 'tools' list
                    capabilities_data = {"tools": tools_list["tools"]}
                else: # If the structure is different, store raw result for inspection
                    self.mcp_logger.warning(f"Unexpected format from {discovery_method_name} on {server_id}. Got: {tools_list}")
                    capabilities_data = {"tools": [], "raw_response": tools_list}
                
                self.mcp_logger.info(f"Successfully discovered/processed capabilities for {server_id} using {discovery_method_name}.")
                self.mcp_logger.debug(f"Discovered tools for {server_id}: {json.dumps(capabilities_data.get('tools', []), indent=2)}")
            else:
                error_detail = response.get("error", f"Unknown error during {discovery_method_name}")
                self.mcp_logger.error(f"Failed to discover capabilities for {server_id} using {discovery_method_name}. Error: {error_detail}. Setting empty capabilities.")
                self.metrics["discovery_failures"] += 1
                capabilities_data = {"tools": [], "discovery_failed": True, "error_details": error_detail}

        except Exception as e:
            self.mcp_logger.error(f"Exception during capability discovery ({discovery_method_name}) for {server_id}: {e}", exc_info=True)
            self.metrics["discovery_failures"] += 1
            capabilities_data = {"tools": [], "discovery_failed": True, "exception_details": str(e)}
        
        with self._lock:
            self.capabilities[server_id] = capabilities_data
            if server_id in self.servers:
                self.servers[server_id]['capabilities'] = capabilities_data
            self.mcp_logger.debug(f"Stored capabilities for {server_id}: {json.dumps(capabilities_data, indent=2)}")
    
    def call_tool(self, tool_id: str, method: str, params: Dict, timeout: Optional[int] = None, 
                  agent_id: str = None, context: Dict = None) -> Dict:
        """
        Call a specific MCP tool with JSON-RPC.
        
        Args:
            tool_id: ID of the MCP server
            method: JSON-RPC method name
            params: Parameters for the method call
            timeout: Optional timeout override
            agent_id: Optional agent identifier for tracking
            context: Optional context information for logging
            
        Returns:
            Dict: Response from the MCP server
        """
        if not self.enabled:
            self.mcp_logger.debug("MCP tools disabled, skipping tool call")
            return {"error": "MCP tools disabled"}
        
        if tool_id not in self.servers:
            self.mcp_logger.error(f"MCP server '{tool_id}' not found")
            return {"error": f"Server '{tool_id}' not found"}
        
        # Generate unique call ID
        call_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Update basic metrics
        with self._lock:
            self.metrics["total_calls"] += 1
        
        # Enhanced logging: Call start (debug level only)
        # self.enhanced_logger.log_call_start(
        #     call_id=call_id,
        #     tool_id=tool_id,
        #     method=method,
        #     params=params,
        #     timeout=timeout or self.servers[tool_id]["timeout"],
        #     agent_id=agent_id,
        #     context=context
        # )
        
        # Minimal logging for user experience
        self.mcp_logger.debug(f"MCP call: {tool_id}.{method} (ID: {call_id})")
        
        try:
            # Ensure server is connected
            if tool_id not in self.connections:
                self.mcp_logger.info(f"Lazy initialization: establishing connection for {tool_id}")
                if not self._initialize_server(tool_id):
                    response = {"error": f"Failed to initialize server {tool_id}"}
                    response_time = time.time() - start_time
                    
                    self.enhanced_logger.log_call_end(
                        call_id=call_id,
                        status="connection_failure",
                        duration=response_time,
                        response=response,
                        error=Exception(response["error"])
                    )
                    
                    with self._lock:
                        self.metrics["failed_calls"] += 1
                    
                    self.mcp_logger.warning(f"Call FAILED (connection) in {response_time:.2f}s")
                    return response
            
            # Call the method
            result = self._call_server_method(tool_id, method, params, timeout)
            
            # Multi-call support disabled temporarily - causing infinite loops
            # if not result.get("error") and method == "tools/call":
            #     result = self._handle_multi_call_tool(tool_id, params, result, timeout)
            
            # Determine call status
            response_time = time.time() - start_time
            if result.get("error"):
                status = "failure"
            else:
                status = "success"
            
            # Enhanced logging: Call end (debug level only)
            # self.enhanced_logger.log_call_end(
            #     call_id=call_id,
            #     status=status,
            #     duration=response_time,
            #     response=result,
            #     error=None if status == "success" else Exception(result.get("error", "unknown"))
            # )
            
            # Update metrics and tool usage
            with self._lock:
                if status == "success":
                    self.metrics["successful_calls"] += 1
                    self.mcp_logger.debug(f"Call SUCCEEDED in {response_time:.2f}s")
                else:
                    self.metrics["failed_calls"] += 1
                    self.mcp_logger.warning(f"Call FAILED ({status}) in {response_time:.2f}s")
            
            self.servers[tool_id]["last_used"] = datetime.now().isoformat()
            self.servers[tool_id]["usage_count"] += 1
            
            return result
            
        except Exception as e:
            # Handle unexpected exceptions
            with self._lock:
                self.metrics["failed_calls"] += 1
            
            response_time = time.time() - start_time
            error_msg = f"Error calling MCP server '{tool_id}': {e}"
            
            # Enhanced logging: Exception (debug level only)
            # self.enhanced_logger.log_call_end(
            #     call_id=call_id,
            #     status="exception",
            #     duration=response_time,
            #     response=None,
            #     error=e
            # )
            
            self.mcp_logger.error(f"MCP call exception: {error_msg} (ID: {call_id})")
            return {"error": error_msg}

    def _create_error_response(self, code: int, message: str, request_id: Optional[str]) -> Dict:
        """Create a standardized JSON-RPC error response."""
        return {
            "jsonrpc": "2.0",
            "error": {"code": code, "message": message},
            "id": request_id
        }

    def _read_stderr_non_blocking(self, process: subprocess.Popen) -> str:
        """Read from a process's stderr stream without blocking."""
        stderr_output = ""
        if not process or not hasattr(process, 'stderr') or not process.stderr:
            return stderr_output
        
        # Ensure the process is not None and stderr is a valid stream object
        if process.stderr is None: # Explicitly check for None stderr
            return stderr_output

        try:
            fd = process.stderr.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            try:
                err_bytes = process.stderr.read()
                if err_bytes:
                    stderr_output = err_bytes.decode(errors='ignore').strip()
                    if stderr_output: # Log only if there's actual output
                        self.mcp_logger.debug(f"Read from stderr (non-blocking) for PID {process.pid}: {stderr_output}")
            except TypeError: # Can happen if read() returns None after non-blocking set
                pass
            except BlockingIOError: # No data to read, which is expected in non-blocking
                pass
            except ValueError: # fileno() can raise this if stream is closed
                self.mcp_logger.debug(f"Stderr stream closed for PID {process.pid} (ValueError on fileno/read).")
            except Exception as e: # Catch other potential read errors
                 self.mcp_logger.error(f"Unexpected error reading stderr (non-blocking) for PID {process.pid}: {e}")
            finally:
                # Attempt to restore blocking mode only if fd was valid
                if 'fd' in locals() and isinstance(fd, int) and fd >=0:
                    try:
                        fcntl.fcntl(fd, fcntl.F_SETFL, fl)
                    except Exception as e_fcntl_restore:
                        self.mcp_logger.debug(f"Could not restore fcntl flags for PID {process.pid}: {e_fcntl_restore}")
        except ValueError: # fileno() can raise this if stream is already closed
            self.mcp_logger.debug(f"Stderr stream likely closed for PID {process.pid} before non-blocking read attempt.")
        except Exception as stderr_e:
            self.mcp_logger.error(f"Error setting up non-blocking stderr read for PID {process.pid}: {stderr_e}")
        return stderr_output

    def _handle_multi_call_tool(self, tool_id: str, original_params: Dict, initial_result: Dict, timeout: Optional[int] = None) -> Dict:
        """Handle tools that require multiple calls to complete (e.g., sequential-thinking)."""
        try:
            result = initial_result
            
            # Check if this is a multi-call tool by examining the response structure
            result_content = result.get("result", {})
            if isinstance(result_content, dict) and result_content.get("content"):
                try:
                    content_text = result_content["content"][0].get("text", "{}")
                    parsed_content = json.loads(content_text)
                    
                    # If tool indicates it needs more calls, continue automatically
                    while parsed_content.get("nextThoughtNeeded"):
                        # Prepare next call parameters
                        next_params = original_params.copy()
                        if "arguments" in next_params:
                            next_params["arguments"]["thoughtNumber"] = parsed_content.get("thoughtNumber", 1) + 1
                        
                        self.mcp_logger.debug(f"Multi-call {tool_id}: continuing to thought {next_params['arguments']['thoughtNumber']}")
                        
                        # Make the next call
                        next_result = self._call_server_method(tool_id, "tools/call", next_params, timeout)
                        
                        if next_result and not next_result.get("error"):
                            # Parse the new result
                            next_content = next_result.get("result", {}).get("content", [{}])[0].get("text", "{}")
                            parsed_content = json.loads(next_content)
                            result = next_result  # Use latest result as final
                        else:
                            self.mcp_logger.warning(f"Multi-call {tool_id}: chain failed at thought {next_params['arguments']['thoughtNumber']}")
                            break
                    
                    self.mcp_logger.debug(f"Multi-call {tool_id}: completed with {parsed_content.get('thoughtNumber', 1)} thoughts")
                    
                except (json.JSONDecodeError, KeyError, IndexError):
                    # Not a multi-call tool or unexpected format, return original result
                    pass
                    
            return result
            
        except Exception as e:
            self.mcp_logger.error(f"Error in multi-call handler for {tool_id}: {e}")
            return initial_result  # Return original result on error

    def _call_server_method(self, server_id: str, method: str, params: Dict, timeout: Optional[int] = None) -> Dict:
        """Internal method to call a server method via JSON-RPC."""
        # If method is 'initialize', it's part of the handshake, use init_timeout.
        # Otherwise, use the provided timeout or server/default timeout.
        if method == "initialize":
             call_timeout = self.init_timeout
        else:
             call_timeout = timeout if timeout is not None else self.servers.get(server_id, {}).get("timeout", self.default_timeout)
        
        request_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id
        }
        payload_str = json.dumps(payload)

        self.mcp_logger.debug(f"Calling server '{server_id}', method '{method}', params: {json.dumps(params)}, timeout: {call_timeout}s, request_id: {request_id}")
        self.enhanced_logger.log_call_start(
            call_id=request_id,
            tool_id=server_id,
            method=method,
            params=params,
            timeout=float(call_timeout)
        )

        start_time = time.monotonic()
        response_json: Dict = {}
        error_response: Optional[Dict] = None
        raw_response_text = ""
        conn: Optional[subprocess.Popen] = None

        try:
            with self._lock:
                if server_id not in self.connections or self.connections[server_id].poll() is not None:
                    self.mcp_logger.info(f"No active connection to {server_id} or process terminated. Attempting to re-initialize.")
                    if not self._initialize_server(server_id):
                        # _initialize_server logs its own errors
                        raise ConnectionError(f"Failed to initialize or connect to server: {server_id}")
                conn = self.connections[server_id]
            
            if conn is None: # Should be caught by ConnectionError above, but as a safeguard
                 raise ConnectionError(f"Connection object for {server_id} is None after initialization attempt.")

            self.mcp_logger.debug(f"Sending payload to {server_id} (PID: {conn.pid}): {payload_str}")
            conn.stdin.write(payload_str.encode('utf-8') + b'\n')
            conn.stdin.flush()

            self.mcp_logger.debug(f"[{server_id} - {request_id}] Waiting for response data...")
            if not self._wait_for_response(conn, call_timeout):
                self.mcp_logger.error(f"Timeout waiting for stdout response from {server_id} (PID: {conn.pid}, method: {method}, request_id: {request_id})")
                stderr_output = self._read_stderr_non_blocking(conn)
                error_message = f"Timeout waiting for response from {server_id} (method: {method})."
                if stderr_output:
                    error_message += f" Server stderr: {stderr_output}"
                error_response = self._create_error_response(-32000, error_message, request_id)
                self.metrics["timeouts"] += 1
            else:
                # Response data is expected, try to read it
                raw_response_text = conn.stdout.readline().decode('utf-8').strip()
                self.mcp_logger.debug(f"Raw response from {server_id} (PID: {conn.pid}, request_id: {request_id}): '{raw_response_text}'")

                if not raw_response_text:
                    # Empty response could mean server closed stdout or crashed
                    exit_code = conn.poll()
                    stderr_output = self._read_stderr_non_blocking(conn)
                    if exit_code is not None:
                        self.mcp_logger.error(f"Empty response from {server_id} (PID: {conn.pid}, request_id: {request_id}). Server process terminated with exit code {exit_code}.")
                        error_message = f"Empty response and server {server_id} terminated (exit code {exit_code})."
                    else:
                        self.mcp_logger.warning(f"Empty response from {server_id} (PID: {conn.pid}, request_id: {request_id}), but server process still running.")
                        error_message = f"Empty response from server {server_id}."
                    if stderr_output:
                        error_message += f" Server stderr: {stderr_output}"
                    error_response = self._create_error_response(-32000, error_message, request_id)
                else:
                    try:
                        response_json = json.loads(raw_response_text)
                        if response_json.get("id") != request_id:
                            self.mcp_logger.warning(f"Response ID mismatch for {server_id} (request_id: {request_id}). Expected '{request_id}', got '{response_json.get('id')}'. Response: {raw_response_text}")
                            error_response = self._create_error_response(-32603, f"Response ID mismatch. Expected '{request_id}', got '{response_json.get('id')}'", request_id)
                            response_json = {} # Clear parsed JSON if it's not for us or is an error itself
                        elif "error" in response_json:
                            self.mcp_logger.warning(f"Server {server_id} (PID: {conn.pid}, request_id: {request_id}) returned an error: {response_json['error']}")
                            # This is a valid JSON-RPC error response from the server, not a transport error.
                            # We let it pass through as response_json and the caller can inspect it.
                            pass
                    except json.JSONDecodeError as e_json:
                        self.mcp_logger.error(f"JSONDecodeError from {server_id} (PID: {conn.pid}, request_id: {request_id}): {e_json}. Raw response: '{raw_response_text}'")
                        stderr_output = self._read_stderr_non_blocking(conn)
                        error_message = f"Invalid JSON response from server {server_id}: {e_json}. Raw: '{raw_response_text}'"
                        if stderr_output:
                            error_message += f". Server stderr: {stderr_output}"
                        error_response = self._create_error_response(-32700, error_message, request_id) # Parse error

            # Additional check: if process terminated after we thought we got a response but didn't form an error_response yet
            if conn.poll() is not None and not error_response and not ("result" in response_json or "error" in response_json) :
                exit_code = conn.returncode
                self.mcp_logger.error(f"Server {server_id} (PID: {conn.pid}) terminated unexpectedly (exit code {exit_code}) after potential read for request_id: {request_id}. Raw response was: '{raw_response_text}'")
                stderr_output = self._read_stderr_non_blocking(conn)
                error_message = f"Server {server_id} terminated unexpectedly (exit code {exit_code})."
                if stderr_output:
                    error_message += f" Server stderr: {stderr_output}"
                error_response = self._create_error_response(-32003, error_message, request_id)
                response_json = {} # Clear any partial/invalid json

        except ConnectionRefusedError as e_conn_refused:
            self.mcp_logger.error(f"Connection refused by {server_id} (method: {method}, request_id: {request_id}): {e_conn_refused}")
            error_response = self._create_error_response(-32001, f"Connection refused by server {server_id}: {str(e_conn_refused)}", request_id)
            self.metrics["failed_calls"] += 1
        except ConnectionError as e_conn_err: # For failure from _initialize_server
            self.mcp_logger.error(f"Connection error for {server_id} (method: {method}, request_id: {request_id}): {e_conn_err}")
            error_response = self._create_error_response(-32001, f"Connection error with server {server_id}: {str(e_conn_err)}", request_id)
            self.metrics["failed_calls"] += 1
        except BrokenPipeError as e_broken_pipe:
            self.mcp_logger.error(f"Broken pipe error with {server_id} (PID: {conn.pid if conn else 'N/A'}, method: {method}, request_id: {request_id}): {e_broken_pipe}")
            stderr_output = self._read_stderr_non_blocking(conn) if conn else ""
            error_message = f"Broken pipe error with server {server_id}: {str(e_broken_pipe)}"
            if stderr_output:
                error_message += f". Server stderr: {stderr_output}"
            error_response = self._create_error_response(-32002, error_message, request_id)
            self.metrics["failed_calls"] += 1
        except Exception as e_generic:
            self.mcp_logger.critical(f"Unexpected error calling {server_id} (PID: {conn.pid if conn else 'N/A'}, request_id: {request_id}): {e_generic}", exc_info=True)
            stderr_output = self._read_stderr_non_blocking(conn) if conn else ""
            error_message = f"Unexpected server error with {server_id}: {str(e_generic)}"
            if stderr_output:
                error_message += f". Server stderr: {stderr_output}"
            error_response = self._create_error_response(-32000, error_message, request_id)
            self.metrics["failed_calls"] += 1
        finally:
            duration = time.monotonic() - start_time
            log_status = "failure"
            log_response = {}
            log_error_obj = None

            if error_response:
                log_response = error_response
                log_error_obj = error_response.get("error") # This is a dict, as per JSON-RPC spec
            elif response_json: # This means no error_response was set
                if "result" in response_json:
                    log_status = "success"
                # If "error" is in response_json, it's an error from the server itself, still a "failure" for this layer's success metric
                # but the response itself is valid JSON-RPC
                log_response = response_json
                log_error_obj = response_json.get("error") # This is a dict
            else: # Should not happen if logic is correct, but as a fallback
                log_response = {"error": {"code": -32000, "message": "Internal error: No response or error_response set"}}
                log_error_obj = log_response.get("error")


            self.enhanced_logger.log_call_end(
                call_id=request_id,
                status=log_status,
                duration=duration,
                response=log_response,
                error=log_error_obj # Pass the error object (dict) or None
            )
            self.mcp_logger.debug(f"Call to {server_id} method {method} (request_id: {request_id}) ended with status '{log_status}', took {duration:.4f}s")

        if error_response:
            return error_response
        return response_json # Return the parsed JSON or an empty dict if parsing failed but no transport error occurred
    
    def _wait_for_response(self, process: subprocess.Popen, timeout: float) -> bool:
        """Wait for response with timeout."""
        import select
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if sys.platform != 'win32':
                ready, _, _ = select.select([process.stdout], [], [], 0.1)
                if ready:
                    return True
            else:
                # Windows fallback
                time.sleep(0.1)
                if process.stdout.readable():
                    return True
            
            if process.poll() is not None:
                return False
        
        return False

    def get_available_tools(self) -> List[str]:
        """Get all ready servers."""
        if not self.enabled:
            return []
        
        return [server_id for server_id, server in self.servers.items() 
                if server["status"] in ["ready", "connected", "running"]]
    
    def get_tool_info(self, tool_id: str) -> Optional[Dict]:
        """Get information about a specific server."""
        return self.servers.get(tool_id)
    
    def call_specific_tool(self, tool_id: str, tool_name: str, arguments: Dict, timeout: Optional[int] = None) -> Dict:
        """
        Call a specific tool within an MCP server.
        """
        return self.call_tool(tool_id, "tools/call", {
            "name": tool_name,
            "arguments": arguments
        }, timeout)
    
    def get_server_capabilities(self, server_id: str) -> Dict:
        """Get discovered capabilities for a specific server."""
        with self._lock:
            # Ensure that capabilities for this server_id are attempted to be loaded if not present.
            # This can happen if initialize_tools wasn't called or a server was added dynamically.
            if server_id not in self.capabilities and server_id in self.servers:
                self.mcp_logger.info(f"Capabilities for {server_id} not yet discovered. Attempting discovery now.")
                self._discover_capabilities(server_id) # This will populate self.capabilities[server_id]
            
            # Fallback to server's stored capabilities if primary self.capabilities is missing entry
            # though _discover_capabilities should ensure self.capabilities[server_id] exists.
            caps = self.capabilities.get(server_id, self.servers.get(server_id, {}).get('capabilities', {}))
            self.mcp_logger.debug(f"Returning capabilities for server '{server_id}': {json.dumps(caps, indent=2)}")
            return caps
    
    def get_metrics(self) -> Dict:
        """Get usage metrics for MCP servers."""
        return self.metrics.copy()
    
    def get_health_report(self) -> Dict:
        """Get comprehensive health report for all MCP servers."""
        try:
            health_data = self.metrics_collector.get_system_health()
            
            # Log server health checks
            for server_id in self.servers.keys():
                tool_health = self.metrics_collector.get_tool_health(server_id)
                if tool_health:
                    self.enhanced_logger.log_tool_health_check(server_id, tool_health)
            
            return health_data
        except Exception as e:
            self.mcp_logger.error(f"Failed to generate health report: {e}")
            return {"error": str(e)}
    
    def is_enabled(self) -> bool:
        """Check if MCP tools are enabled."""
        return self.enabled
    
    def shutdown(self):
        """Clean shutdown of all MCP connections."""
        if not self.enabled:
            return
        
        self.mcp_logger.info("=== MCP MANAGER SHUTDOWN ===")
        
        # Close connections
        if self.connections:
            self.mcp_logger.info(f"Closing {len(self.connections)} connections")
            for server_id, connection in self.connections.items():
                try:
                    process = connection["process"]
                    process.stdin.close()
                    process.terminate()
                    process.wait(timeout=5)
                    self.mcp_logger.debug(f"Gracefully closed connection for {server_id}")
                except Exception as e:
                    self.mcp_logger.error(f"Error closing connection to '{server_id}': {e}")
        
        self.connections.clear()
        self.mcp_logger.info("MCP Manager shutdown complete") 