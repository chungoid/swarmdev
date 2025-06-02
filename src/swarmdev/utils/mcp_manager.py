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
import pkg_resources  # Add this import for package path resolution
import sys
import uuid

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
            "discovery_failures": 0
        }
        
        # Enhanced MCP-specific logging
        self._setup_mcp_logging()
        
        # Initialize enhanced logging and metrics
        self.enhanced_logger = get_mcp_logger(str(self.project_dir))
        self.metrics_collector = get_metrics_collector()
        
        # Thread safety
        self._lock = threading.Lock()
        
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
        """
        Get built-in default MCP configuration with working Docker commands.
        This ensures SwarmDev works out of the box without requiring configuration files.
        """
        return {
            "servers": {
                "git": {
                    "command": ["docker", "run", "--rm", "-i", "mcp/git"],
                    "timeout": 30,
                    "enabled": True,
                    "description": "Git operations and repository management"
                },
                "time": {
                    "command": ["docker", "run", "--rm", "-i", "mcp/time"],
                    "timeout": 30,
                    "enabled": True,
                    "description": "Time zone operations and conversions"
                },
                "fetch": {
                    "command": ["docker", "run", "--rm", "-i", "mcp/fetch"],
                    "timeout": 30,
                    "enabled": True,
                    "description": "Web content fetching and processing"
                },
                "filesystem": {
                    "command": ["docker", "run", "--rm", "-i", "-v", "$(pwd):/workspace", "mcp/filesystem", "/workspace"],
                    "timeout": 30,
                    "enabled": True,
                    "description": "File system operations with current directory access"
                },
                "memory": {
                    "command": ["docker", "run", "--rm", "-i", "mcp/memory"],
                    "timeout": 30,
                    "enabled": True,
                    "description": "Persistent memory storage for context"
                },
                "sequential-thinking": {
                    "command": ["docker", "run", "--rm", "-i", "mcp/sequentialthinking"],
                    "timeout": 60,
                    "enabled": True,
                    "description": "Advanced reasoning through sequential thoughts"
                },
                "context7": {
                    "command": ["docker", "run", "--rm", "-i", "-e", "MCP_TRANSPORT=stdio", "context7-mcp"],
                    "timeout": 30,
                    "enabled": True,
                    "description": "Up-to-date documentation and code examples"
                }
            },
            "settings": {
                "defaultTimeout": 30,
                "persistentConnections": True,
                "autoDiscovery": True,
                "retryCount": 3,
                "retryDelay": 1.0
            }
        }
    
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
        """Initialize a single server on demand."""
        if server_id not in self.servers:
            self.mcp_logger.error(f"Server {server_id} not configured")
            return False
            
        server = self.servers[server_id]
        
        try:
            # Start the server process
            process = subprocess.Popen(
                server["command"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            self.mcp_logger.info(f"Process started for {server_id}, PID: {process.pid}")
            
            # MCP initialization handshake
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "swarmdev",
                        "version": "1.0.0"
                    }
                },
                "id": 1
            }
            
            # Send initialization
            process.stdin.write(json.dumps(init_request) + "\n")
            process.stdin.flush()
            
            # Read response with improved reliability
            if self._wait_for_response(process, self.init_timeout):
                # Try to read response, handling empty responses
                max_attempts = 3
                for attempt in range(max_attempts):
                    response_line = process.stdout.readline()
                    if response_line and response_line.strip():
                        try:
                            response = json.loads(response_line.strip())
                            if response.get("id") == 1 and not response.get("error"):
                                # Send initialized notification
                                notification = {
                                    "jsonrpc": "2.0",
                                    "method": "notifications/initialized"
                                }
                                process.stdin.write(json.dumps(notification) + "\n")
                                process.stdin.flush()
                                
                                # Store connection
                                self.connections[server_id] = {
                                    "process": process,
                                    "call_counter": 1,
                                    "last_used": datetime.now().isoformat()
                                }
                                
                                server["status"] = "connected"
                                
                                # Auto-discover capabilities if enabled
                                if self.auto_discovery:
                                    self._discover_capabilities(server_id)
                                
                                self.mcp_logger.info(f"Server {server_id} initialized successfully")
                                return True
                            else:
                                # Server returned error response
                                error_msg = response.get("error", "Unknown initialization error")
                                self.mcp_logger.error(f"Server {server_id} initialization error: {error_msg}")
                                break
                        except json.JSONDecodeError as e:
                            self.mcp_logger.warning(f"Server {server_id} attempt {attempt + 1}: Invalid JSON response: {repr(response_line)}")
                            if attempt < max_attempts - 1:
                                time.sleep(0.1)  # Brief pause before retry
                                continue
                            else:
                                self.mcp_logger.error(f"Server {server_id} failed after {max_attempts} attempts: {e}")
                                break
                    else:
                        self.mcp_logger.warning(f"Server {server_id} attempt {attempt + 1}: Empty response")
                        if attempt < max_attempts - 1:
                            time.sleep(0.1)  # Brief pause before retry
                            continue
                        else:
                            self.mcp_logger.error(f"Server {server_id} failed: Empty response after {max_attempts} attempts")
                            break
            else:
                self.mcp_logger.error(f"Server {server_id} initialization timeout")
            
            # If we get here, initialization failed
            process.terminate()
            server["status"] = "failed"
            server["last_error"] = "Initialization timeout or failed"
            
        except Exception as e:
            server["status"] = "failed"
            server["last_error"] = str(e)
            self.mcp_logger.error(f"Server {server_id} initialization failed: {e}")
        
        return False
    
    def _discover_capabilities(self, server_id: str):
        """Discover server capabilities generically."""
        try:
            result = self._call_server_method(server_id, "tools/list", {}, timeout=self.discovery_timeout)
            
            if result and not result.get("error") and "result" in result:
                tools = result["result"].get("tools", [])
                self.capabilities[server_id] = {
                    "tools": tools,
                    "discovered_at": datetime.now().isoformat()
                }
                self.mcp_logger.info(f"Server {server_id}: Discovered {len(tools)} tools")
            else:
                self.capabilities[server_id] = {"tools": [], "discovery_failed": True}
                self.mcp_logger.warning(f"Failed to discover tools for {server_id}")
                
        except Exception as e:
            self.mcp_logger.warning(f"Capability discovery failed for {server_id}: {e}")
            self.metrics["discovery_failures"] += 1
    
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
        
        # Enhanced logging: Call start
        self.enhanced_logger.log_call_start(
            call_id=call_id,
            tool_id=tool_id,
            method=method,
            params=params,
            timeout=timeout or self.servers[tool_id]["timeout"],
            agent_id=agent_id,
            context=context
        )
        
        # Original logging for backward compatibility
        self.mcp_logger.info(f"=== MCP CALL START ===")
        self.mcp_logger.info(f"Call ID: {call_id}")
        self.mcp_logger.info(f"Server: {tool_id}")
        self.mcp_logger.info(f"Method: {method}")
        self.mcp_logger.info(f"Agent: {agent_id or 'unknown'}")
        
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
            
            # Determine call status
            response_time = time.time() - start_time
            if result.get("error"):
                status = "failure"
            else:
                status = "success"
            
            # Enhanced logging: Call end
            self.enhanced_logger.log_call_end(
                call_id=call_id,
                status=status,
                duration=response_time,
                response=result,
                error=None if status == "success" else Exception(result.get("error", "unknown"))
            )
            
            # Update metrics and tool usage
            with self._lock:
                if status == "success":
                    self.metrics["successful_calls"] += 1
                    self.mcp_logger.info(f"Call SUCCEEDED in {response_time:.2f}s")
                else:
                    self.metrics["failed_calls"] += 1
                    self.mcp_logger.warning(f"Call FAILED ({status}) in {response_time:.2f}s")
            
            self.servers[tool_id]["last_used"] = datetime.now().isoformat()
            self.servers[tool_id]["usage_count"] += 1
            
            self.mcp_logger.info(f"=== MCP CALL END ===")
            
            return result
            
        except Exception as e:
            # Handle unexpected exceptions
            with self._lock:
                self.metrics["failed_calls"] += 1
            
            response_time = time.time() - start_time
            error_msg = f"Error calling MCP server '{tool_id}': {e}"
            
            # Enhanced logging: Exception
            self.enhanced_logger.log_call_end(
                call_id=call_id,
                status="exception",
                duration=response_time,
                response=None,
                error=e
            )
            
            self.mcp_logger.error(f"=== MCP CALL EXCEPTION ===")
            self.mcp_logger.error(f"Call ID: {call_id}")
            self.mcp_logger.error(f"Error: {error_msg}")
            return {"error": error_msg}

    def _call_server_method(self, server_id: str, method: str, params: Dict, timeout: Optional[int] = None) -> Dict:
        """Call a method on a server."""
        if server_id not in self.connections:
            return {"error": f"No connection to server {server_id}"}
        
        connection = self.connections[server_id]
        process = connection["process"]
        
        # Check if process is alive
        if process.poll() is not None:
            self.mcp_logger.warning(f"Server {server_id} process died, reinitializing")
            del self.connections[server_id]
            if self._initialize_server(server_id):
                return self._call_server_method(server_id, method, params, timeout)
            return {"error": f"Server {server_id} process died and reinitialization failed"}
        
        try:
            # Create request
            connection["call_counter"] += 1
            request = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": connection["call_counter"]
            }
            
            # Send request
            process.stdin.write(json.dumps(request) + "\n")
            process.stdin.flush()
            
            # Read response
            call_timeout = timeout or self.servers[server_id]["timeout"]
            if self._wait_for_response(process, call_timeout):
                response_line = process.stdout.readline()
                if response_line:
                    response = json.loads(response_line.strip())
                    connection["last_used"] = datetime.now().isoformat()
                    return response
            
            return {"error": "Response timeout"}
            
        except Exception as e:
            return {"error": f"Call failed: {e}"}
    
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
                if server["status"] in ["ready", "connected"]]
    
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
        """Get discovered capabilities for a server."""
        return self.capabilities.get(server_id, {})
    
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