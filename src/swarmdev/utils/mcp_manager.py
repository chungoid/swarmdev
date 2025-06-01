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


class MCPManager:
    """
    Centralized MCP tool manager for the SwarmDev platform.
    
    This class handles initialization, connection management, and communication
    with external MCP servers through JSON-RPC protocol.
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
        self.mcp_tools = {}
        self.active_connections = {}
        self.persistent_processes = {}  # Store persistent MCP server processes
        self.tool_capabilities = {}
        self.connection_pool = {}
        self.enabled = config.get("enabled", False)
        self.docker_enabled = config.get("docker_enabled", True)
        self.docker_network = config.get("docker_network", None)  # Default to None
        self.global_timeout = config.get("global_timeout", 120)
        self.persistent_connections = config.get("persistent_connections", True)  # Enable by default
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "tools_used": {},
            "average_response_time": 0.0,
            "connection_tests": 0,
            "connection_successes": 0
        }
        
        # Enhanced MCP-specific logging
        self._setup_mcp_logging()
        
        # Thread safety
        self._lock = threading.Lock()
        
        if self.enabled:
            self.mcp_logger.info("=== MCP MANAGER INITIALIZATION ===")
            self.mcp_logger.info(f"Docker enabled: {self.docker_enabled}")
            self.mcp_logger.info(f"Docker network: {self.docker_network}")
            self.mcp_logger.info(f"Global timeout: {self.global_timeout}s")
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
        
        # Create console handler for immediate feedback
        mcp_console_handler = logging.StreamHandler()
        mcp_console_handler.setLevel(logging.INFO)
        
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
                merged_config = global_config.copy()
                self.mcp_logger.info(f"Global config loaded with {len(global_config.get('mcpServers', global_config.get('servers', {})))} servers")
            else:
                self.mcp_logger.warning(f"Global MCP config not found at: {global_config_path}")
            
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
                self.mcp_logger.info("No project-specific MCP config found, using global config only")
            
            # Step 3: Fallback if no configuration found
            if not merged_config:
                self.mcp_logger.error("No MCP configuration found in global or project locations")
                return
            
            self.mcp_logger.debug(f"Final merged MCP config: {json.dumps(merged_config, indent=2)}")
            
            # Step 4: Process the merged configuration
            # Load server configurations (support both old and new format)
            servers = merged_config.get("servers", merged_config.get("mcpServers", {}))
            settings = merged_config.get("settings", merged_config.get("mcpSettings", {}))
            
            self.mcp_logger.info(f"Final configuration contains {len(servers)} MCP servers")
            
            # Update global settings
            old_timeout = self.global_timeout
            old_network = self.docker_network
            old_persistent = self.persistent_connections
            self.global_timeout = settings.get("globalTimeout", self.global_timeout)
            self.docker_network = settings.get("dockerNetwork", self.docker_network)
            self.persistent_connections = settings.get("persistentConnections", self.persistent_connections)
            
            if old_timeout != self.global_timeout:
                self.mcp_logger.info(f"Updated global timeout: {old_timeout}s -> {self.global_timeout}s")
            if old_network != self.docker_network:
                self.mcp_logger.info(f"Updated docker network: {old_network} -> {self.docker_network}")
            if old_persistent != self.persistent_connections:
                self.mcp_logger.info(f"Updated persistent connections: {old_persistent} -> {self.persistent_connections}")
            
            # Initialize tools from configuration
            for tool_id, server_config in servers.items():
                if not server_config.get("disabled", False):
                    self.mcp_logger.debug(f"Registering tool: {tool_id}")
                    self._register_tool(tool_id, server_config)
                else:
                    self.mcp_logger.info(f"Skipping disabled tool: {tool_id}")
            
            self.mcp_logger.info(f"Successfully loaded {len(self.mcp_tools)} MCP tools from hierarchical configuration")
            
        except Exception as e:
            self.mcp_logger.error(f"Failed to load MCP configuration: {e}", exc_info=True)
    
    def _merge_mcp_configs(self, global_config: Dict, project_config: Dict) -> Dict:
        """
        Merge project MCP config over global config, with project settings taking priority.
        
        Args:
            global_config: Global MCP configuration
            project_config: Project-specific MCP configuration
            
        Returns:
            Dict: Merged configuration with project overrides
        """
        import copy
        merged = copy.deepcopy(global_config)
        
        # Merge server configurations
        global_servers = merged.get("servers", merged.get("mcpServers", {}))
        project_servers = project_config.get("servers", project_config.get("mcpServers", {}))
        
        # Project servers override global servers by ID
        for server_id, server_config in project_servers.items():
            if server_id in global_servers:
                self.mcp_logger.debug(f"Project config overriding global server: {server_id}")
            else:
                self.mcp_logger.debug(f"Project config adding new server: {server_id}")
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
    
    def _register_tool(self, tool_id: str, server_config: Dict):
        """Register an MCP tool."""
        try:
            self.mcp_logger.debug(f"Registering MCP tool: {tool_id}")
            self.mcp_logger.debug(f"Server config: {json.dumps(server_config, indent=2)}")
            
            capabilities = server_config.get("capabilities", [])
            timeout = server_config.get("timeout", 30)
            command = server_config.get("command", "unknown")
            args = server_config.get("args", [])
            
            self.mcp_tools[tool_id] = {
                "config": server_config,
                "capabilities": capabilities,
                "timeout": timeout,
                "status": "registered",
                "last_used": None,
                "usage_count": 0,
                "command": command,
                "args": args,
                "registration_time": datetime.now().isoformat()
            }
            
            self.tool_capabilities[tool_id] = capabilities
            self.metrics["tools_used"][tool_id] = 0
            
            self.mcp_logger.info(f"Successfully registered MCP tool '{tool_id}'")
            self.mcp_logger.info(f"  Command: {command}")
            self.mcp_logger.info(f"  Args: {args}")
            self.mcp_logger.info(f"  Capabilities: {capabilities}")
            self.mcp_logger.info(f"  Timeout: {timeout}s")
            
        except Exception as e:
            self.mcp_logger.error(f"Failed to register MCP tool '{tool_id}': {e}", exc_info=True)
    
    def initialize_tools(self) -> bool:
        """Initialize MCP tools with optimistic approach - like Cursor does."""
        if not self.enabled:
            self.mcp_logger.info("MCP tools disabled, skipping initialization")
            return False
        
        self.mcp_logger.info("=== OPTIMISTIC MCP INITIALIZATION ===")
        self.mcp_logger.info(f"Found {len(self.mcp_tools)} tools to make available")
        self.mcp_logger.info("Using optimistic initialization - tools available immediately")
        
        # Optimistic approach: Mark all registered tools as ready immediately
        # Initialize connections lazily on first use (like Cursor)
        ready_count = 0
        for tool_id, tool_info in self.mcp_tools.items():
            if tool_info["status"] == "registered":
                tool_info["status"] = "ready"  # Optimistically mark as ready
                tool_info["initialization_time"] = "optimistic"
                ready_count += 1
                self.mcp_logger.info(f"✅ {tool_id} marked as available (lazy initialization)")
        
        self.mcp_logger.info(f"=== INITIALIZATION COMPLETE ===")
        self.mcp_logger.info(f"Available tools: {ready_count}/{len(self.mcp_tools)}")
        self.mcp_logger.info("Tools will initialize on first use with proper error handling")
        
        return ready_count > 0
    
    def _start_persistent_connection_with_timeout(self, tool_id: str, timeout: int = 10) -> bool:
        """Start persistent connection with timeout - prevents hanging like Cursor does."""
        import signal
        import threading
        
        result = {"success": False}
        
        def connection_worker():
            try:
                result["success"] = self._start_persistent_connection(tool_id)
            except Exception as e:
                self.mcp_logger.error(f"Connection worker exception for {tool_id}: {e}")
                result["success"] = False
        
        # Start connection in thread with timeout
        thread = threading.Thread(target=connection_worker, daemon=True)
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            self.mcp_logger.warning(f"Connection timeout ({timeout}s) for {tool_id} - continuing without blocking")
            return False
        
        return result["success"]
    
    def _start_persistent_connection(self, tool_id: str) -> bool:
        """Start a persistent MCP connection for a tool."""
        try:
            tool_config = self.mcp_tools[tool_id]["config"]
            self.mcp_logger.debug(f"Starting persistent connection for: {tool_id}")
            
            # Build command
            command_type = tool_config.get("command")
            if command_type == "docker":
                full_command = self._build_docker_command(tool_config, persistent=True)
            else:
                command = tool_config.get("command")
                args = tool_config.get("args", [])
                full_command = [command] + args
            
            self.mcp_logger.info(f"Starting persistent MCP server: {' '.join(full_command)}")
            
            # Start the process
            process = subprocess.Popen(
                full_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send initialization request
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
            
            init_json = json.dumps(init_request) + '\n'
            process.stdin.write(init_json)
            process.stdin.flush()
            
            # Read initialization response
            try:
                response_line = process.stdout.readline()
                if not response_line.strip():
                    self.mcp_logger.error(f"No initialization response from {tool_id}")
                    process.kill()
                    return False
                
                init_response = json.loads(response_line.strip())
                if init_response.get("error"):
                    self.mcp_logger.error(f"Initialization failed for {tool_id}: {init_response['error']}")
                    process.kill()
                    return False
                
                # Store the persistent connection
                self.persistent_processes[tool_id] = {
                    "process": process,
                    "initialized": True,
                    "last_used": datetime.now().isoformat(),
                    "call_counter": 1
                }
                
                # Test with tools/list to get available tools
                tools_result = self._call_persistent_tool(tool_id, "tools/list", {})
                if tools_result and not tools_result.get("error"):
                    tools_list = tools_result.get("result", {}).get("tools", [])
                    if tools_list:
                        self.mcp_tools[tool_id]["available_tools"] = tools_list
                        self.mcp_logger.info(f"Found {len(tools_list)} available tools for '{tool_id}'")
                
                self.mcp_tools[tool_id]["status"] = "ready"
                self.mcp_tools[tool_id]["connection_type"] = "persistent"
                self.mcp_logger.info(f"Persistent connection established for '{tool_id}'")
                return True
                
            except json.JSONDecodeError as e:
                self.mcp_logger.error(f"Invalid initialization response from {tool_id}: {e}")
                process.kill()
                return False
                
        except Exception as e:
            self.mcp_logger.error(f"Failed to start persistent connection for {tool_id}: {e}", exc_info=True)
            if tool_id in self.persistent_processes:
                try:
                    self.persistent_processes[tool_id]["process"].kill()
                    del self.persistent_processes[tool_id]
                except:
                    pass
            return False
    
    def _build_docker_command(self, tool_config: Dict, persistent: bool = False) -> List[str]:
        """Build Docker command with proper flags for persistent or one-shot usage."""
        docker_args = tool_config.get("args", []).copy()
        
        if persistent:
            # Remove --rm flag for persistent connections
            modified_args = []
            for arg in docker_args:
                if arg != "--rm":
                    modified_args.append(arg)
            docker_args = modified_args
            self.mcp_logger.debug(f"Removed --rm flag for persistent connection")
        
        # Add network if specified
        if self.docker_enabled and self.docker_network and docker_args and docker_args[0] == "run":
            docker_args = docker_args[:1] + ["--network", self.docker_network] + docker_args[1:]
        
        return ["docker"] + docker_args
    
    def _call_persistent_tool(self, tool_id: str, method: str, params: Dict) -> Dict:
        """Call a tool using an existing persistent connection."""
        if tool_id not in self.persistent_processes:
            return {"error": f"No persistent connection for tool '{tool_id}'"}
        
        connection = self.persistent_processes[tool_id]
        process = connection["process"]
        
        # Check if process is still alive
        if process.poll() is not None:
            self.mcp_logger.warning(f"Persistent connection for {tool_id} died, attempting to restart")
            del self.persistent_processes[tool_id]
            if self._start_persistent_connection(tool_id):
                return self._call_persistent_tool(tool_id, method, params)
            else:
                return {"error": f"Failed to restart persistent connection for {tool_id}"}
        
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
            request_json = json.dumps(request) + '\n'
            process.stdin.write(request_json)
            process.stdin.flush()
            
            # Read response
            response_line = process.stdout.readline()
            if not response_line.strip():
                return {"error": "No response from persistent connection"}
            
            response = json.loads(response_line.strip())
            connection["last_used"] = datetime.now().isoformat()
            
            return response
            
        except Exception as e:
            self.mcp_logger.error(f"Error calling persistent tool {tool_id}: {e}")
            return {"error": f"Persistent call error: {e}"}
    
    def call_tool(self, tool_id: str, method: str, params: Dict, timeout: Optional[int] = None) -> Dict:
        """
        Call a specific MCP tool with JSON-RPC.
        
        Args:
            tool_id: ID of the MCP tool to call
            method: JSON-RPC method name
            params: Parameters for the method call
            timeout: Optional timeout override
            
        Returns:
            Dict: Response from the MCP tool
        """
        if not self.enabled:
            self.mcp_logger.debug("MCP tools disabled, skipping tool call")
            return {"error": "MCP tools disabled"}
        
        if tool_id not in self.mcp_tools:
            self.mcp_logger.error(f"MCP tool '{tool_id}' not found")
            self.mcp_logger.debug(f"Available tools: {list(self.mcp_tools.keys())}")
            return {"error": f"Tool '{tool_id}' not found"}
        
        call_id = int(time.time() * 1000000)  # Unique call ID
        start_time = time.time()
        
        with self._lock:
            self.metrics["total_calls"] += 1
            self.metrics["tools_used"][tool_id] += 1
        
        self.mcp_logger.info(f"=== MCP CALL START ===")
        self.mcp_logger.info(f"Call ID: {call_id}")
        self.mcp_logger.info(f"Tool: {tool_id}")
        self.mcp_logger.info(f"Method: {method}")
        self.mcp_logger.debug(f"Params: {json.dumps(params, indent=2)}")
        
        try:
            tool_config = self.mcp_tools[tool_id]["config"]
            tool_timeout = timeout or self.mcp_tools[tool_id]["timeout"]
            
            self.mcp_logger.debug(f"Using timeout: {tool_timeout}s")
            self.mcp_logger.debug(f"Tool config: {json.dumps(tool_config, indent=2)}")
            
            # Create JSON-RPC request
            request = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": call_id
            }
            
            self.mcp_logger.debug(f"JSON-RPC request: {json.dumps(request, indent=2)}")
            
            # Lazy initialization: establish connection on first use
            if tool_id not in self.persistent_processes:
                self.mcp_logger.info(f"Lazy initialization: establishing connection for {tool_id}")
                if not self._start_persistent_connection_with_timeout(tool_id, timeout=10):
                    # Graceful fallback - tool still marked as ready but call fails
                    self.mcp_logger.warning(f"Lazy initialization failed for {tool_id}, but keeping tool available")
                    response = {"error": f"Connection failed for {tool_id} - will retry on next call"}
                else:
                    self.mcp_logger.info(f"Lazy initialization successful for {tool_id}")
                    response = self._call_persistent_tool(tool_id, method, params)
            else:
                self.mcp_logger.debug(f"Using existing persistent connection for {tool_id}")
                response = self._call_persistent_tool(tool_id, method, params)
            
            # Update metrics and tool usage
            response_time = time.time() - start_time
            with self._lock:
                if response.get("error"):
                    self.metrics["failed_calls"] += 1
                    self.mcp_logger.warning(f"Call FAILED in {response_time:.2f}s")
                else:
                    self.metrics["successful_calls"] += 1
                    self.mcp_logger.info(f"Call SUCCEEDED in {response_time:.2f}s")
                
                # Update average response time
                current_avg = self.metrics["average_response_time"]
                total_calls = self.metrics["total_calls"]
                self.metrics["average_response_time"] = (current_avg * (total_calls - 1) + response_time) / total_calls
            
            self.mcp_tools[tool_id]["last_used"] = datetime.now().isoformat()
            self.mcp_tools[tool_id]["usage_count"] += 1
            
            self.mcp_logger.info(f"=== MCP CALL END ===")
            self.mcp_logger.debug(f"Final response: {json.dumps(response, indent=2)}")
            
            return response
            
        except Exception as e:
            with self._lock:
                self.metrics["failed_calls"] += 1
            
            response_time = time.time() - start_time
            error_msg = f"Error calling MCP tool '{tool_id}': {e}"
            self.mcp_logger.error(f"=== MCP CALL EXCEPTION ===")
            self.mcp_logger.error(f"Call ID: {call_id}")
            self.mcp_logger.error(f"Error: {error_msg}")
            self.mcp_logger.error(f"Duration: {response_time:.2f}s", exc_info=True)
            return {"error": error_msg}

    def get_available_tools(self, capabilities: Optional[List[str]] = None) -> List[str]:
        """
        Get tools matching specific capabilities.
        
        Args:
            capabilities: List of required capabilities
            
        Returns:
            List[str]: List of matching tool IDs
        """
        if not self.enabled:
            self.mcp_logger.debug("MCP tools disabled, returning empty tool list")
            return []
        
        available_tools = []
        
        self.mcp_logger.debug(f"Finding tools with capabilities: {capabilities}")
        
        for tool_id, tool_info in self.mcp_tools.items():
            tool_status = tool_info["status"]
            tool_capabilities = set(tool_info["capabilities"])
            
            self.mcp_logger.debug(f"Tool {tool_id}: status={tool_status}, capabilities={tool_capabilities}")
            
            if tool_status != "ready":
                self.mcp_logger.debug(f"Skipping {tool_id} - not ready (status: {tool_status})")
                continue
            
            if capabilities is None:
                available_tools.append(tool_id)
                self.mcp_logger.debug(f"Added {tool_id} - no capability filter")
            else:
                required_capabilities = set(capabilities)
                
                if required_capabilities.issubset(tool_capabilities):
                    available_tools.append(tool_id)
                    self.mcp_logger.debug(f"Added {tool_id} - capabilities match")
                else:
                    self.mcp_logger.debug(f"Skipped {tool_id} - missing capabilities: {required_capabilities - tool_capabilities}")
        
        self.mcp_logger.info(f"Found {len(available_tools)} tools matching capabilities {capabilities}: {available_tools}")
        return available_tools
    
    def get_tool_info(self, tool_id: str) -> Optional[Dict]:
        """Get information about a specific tool."""
        tool_info = self.mcp_tools.get(tool_id)
        if tool_info:
            self.mcp_logger.debug(f"Retrieved info for tool {tool_id}: {json.dumps(tool_info, indent=2)}")
        else:
            self.mcp_logger.warning(f"No info found for tool: {tool_id}")
        return tool_info
    
    def call_specific_tool(self, tool_id: str, tool_name: str, arguments: Dict, timeout: Optional[int] = None) -> Dict:
        """
        Call a specific tool within an MCP server.
        
        Args:
            tool_id: ID of the MCP server
            tool_name: Name of the specific tool to call
            arguments: Arguments for the tool
            timeout: Optional timeout override
            
        Returns:
            Dict: Response from the tool
        """
        return self.call_tool(tool_id, "tools/call", {
            "name": tool_name,
            "arguments": arguments
        }, timeout)
    
    def get_available_tool_names(self, tool_id: str) -> List[str]:
        """Get the names of available tools for a specific MCP server."""
        if tool_id not in self.mcp_tools:
            return []
        
        available_tools = self.mcp_tools[tool_id].get("available_tools", [])
        return [tool.get("name", "") for tool in available_tools if tool.get("name")]
    
    def get_tools_by_capability(self, capability: str) -> List[str]:
        """Get all MCP servers that have the specified capability."""
        if not self.enabled:
            return []
        
        matching_tools = []
        for tool_id, tool_info in self.mcp_tools.items():
            if tool_info.get("status") == "ready" and capability in tool_info.get("capabilities", []):
                matching_tools.append(tool_id)
        
        return matching_tools
    
    def get_actual_tool_names(self, server_id: str) -> List[Dict[str, str]]:
        """Get the actual tool names and schemas from an MCP server."""
        if server_id not in self.mcp_tools:
            return []
        
        # Get available tools from stored info
        available_tools = self.mcp_tools[server_id].get("available_tools", [])
        
        # Return tool info with names and descriptions
        tool_info = []
        for tool in available_tools:
            if tool.get("name"):
                tool_info.append({
                    "name": tool.get("name"),
                    "description": tool.get("description", ""),
                    "input_schema": tool.get("inputSchema", {})
                })
        
        return tool_info
    
    def get_metrics(self) -> Dict:
        """Get usage metrics for MCP tools."""
        metrics = self.metrics.copy()
        self.mcp_logger.debug(f"Current metrics: {json.dumps(metrics, indent=2)}")
        return metrics
    
    def is_enabled(self) -> bool:
        """Check if MCP tools are enabled."""
        return self.enabled
    
    def shutdown(self):
        """Clean shutdown of all MCP connections."""
        if not self.enabled:
            return
        
        self.mcp_logger.info("=== MCP MANAGER SHUTDOWN ===")
        
        # Log final usage summary
        self.log_tool_usage_summary()
        
        # Close persistent connections
        if self.persistent_processes:
            self.mcp_logger.info(f"Closing {len(self.persistent_processes)} persistent connections")
            for tool_id, connection in self.persistent_processes.items():
                try:
                    process = connection["process"]
                    self.mcp_logger.debug(f"Closing persistent connection for {tool_id}")
                    
                    # Try graceful shutdown first
                    try:
                        process.stdin.close()
                        process.terminate()
                        process.wait(timeout=5)
                        self.mcp_logger.debug(f"Gracefully closed connection for {tool_id}")
                    except subprocess.TimeoutExpired:
                        self.mcp_logger.warning(f"Force killing connection for {tool_id}")
                        process.kill()
                        process.wait()
                    
                except Exception as e:
                    self.mcp_logger.error(f"Error closing persistent connection to '{tool_id}': {e}")
        
        # Close any other connections
        for tool_id in self.active_connections:
            try:
                # Any other cleanup
                pass
            except Exception as e:
                self.mcp_logger.error(f"Error closing connection to '{tool_id}': {e}")
        
        self.persistent_processes.clear()
        self.active_connections.clear()
        self.mcp_logger.info("MCP Manager shutdown complete")
    
    def log_tool_usage_summary(self):
        """Log a summary of tool usage."""
        if not self.enabled:
            return
        
        self.mcp_logger.info("=== MCP TOOL USAGE SUMMARY ===")
        self.mcp_logger.info(f"Total calls: {self.metrics['total_calls']}")
        self.mcp_logger.info(f"Successful: {self.metrics['successful_calls']}")
        self.mcp_logger.info(f"Failed: {self.metrics['failed_calls']}")
        self.mcp_logger.info(f"Success rate: {(self.metrics['successful_calls'] / max(self.metrics['total_calls'], 1)) * 100:.1f}%")
        self.mcp_logger.info(f"Average response time: {self.metrics['average_response_time']:.2f}s")
        self.mcp_logger.info(f"Connection tests: {self.metrics['connection_tests']}")
        self.mcp_logger.info(f"Connection successes: {self.metrics['connection_successes']}")
        
        self.mcp_logger.info("Per-tool usage:")
        for tool_id, usage_count in self.metrics["tools_used"].items():
            tool_info = self.mcp_tools.get(tool_id, {})
            status = tool_info.get("status", "unknown")
            capabilities = tool_info.get("capabilities", [])
            last_used = tool_info.get("last_used", "never")
            self.mcp_logger.info(f"  {tool_id}: {usage_count} calls, status={status}, last_used={last_used}")
            self.mcp_logger.info(f"    capabilities: {capabilities}")
        
        self.mcp_logger.info("=== END USAGE SUMMARY ===")
    
    def diagnose_tools(self):
        """Run diagnostic tests on all MCP tools."""
        self.mcp_logger.info("=== MCP TOOLS DIAGNOSTIC ===")
        self.mcp_logger.info(f"Persistent connections enabled: {self.persistent_connections}")
        self.mcp_logger.info(f"Active persistent connections: {len(self.persistent_processes)}")
        
        if not self.enabled:
            self.mcp_logger.info("MCP tools are disabled")
            return
        
        for tool_id, tool_info in self.mcp_tools.items():
            self.mcp_logger.info(f"Diagnosing tool: {tool_id}")
            self.mcp_logger.info(f"  Status: {tool_info['status']}")
            self.mcp_logger.info(f"  Command: {tool_info['command']}")
            self.mcp_logger.info(f"  Args: {tool_info['args']}")
            self.mcp_logger.info(f"  Capabilities: {tool_info['capabilities']}")
            self.mcp_logger.info(f"  Usage count: {tool_info['usage_count']}")
            self.mcp_logger.info(f"  Connection type: {tool_info.get('connection_type', 'one-shot')}")
            
            # Check persistent connection status
            if tool_id in self.persistent_processes:
                conn = self.persistent_processes[tool_id]
                process = conn["process"]
                is_alive = process.poll() is None
                self.mcp_logger.info(f"  Persistent connection: {'ALIVE' if is_alive else 'DEAD'}")
                self.mcp_logger.info(f"  Last used: {conn.get('last_used', 'never')}")
                self.mcp_logger.info(f"  Call counter: {conn.get('call_counter', 0)}")
            else:
                self.mcp_logger.info(f"  Persistent connection: NONE")
            
            if 'last_error' in tool_info:
                self.mcp_logger.error(f"  Last error: {tool_info['last_error']}")
            
            if 'last_test' in tool_info:
                self.mcp_logger.info(f"  Last test: {tool_info['last_test']}")
            
            # Persistent connections are required for MCP tools
            self.mcp_logger.info(f"  MCP tools require persistent connections")
        
        self.mcp_logger.info("=== END DIAGNOSTIC ===") 