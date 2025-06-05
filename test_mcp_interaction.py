import json
import logging
import os
import time
import uuid

# Assuming MCPManager is in src.swarmdev.utils.mcp_manager
# Adjust the import path if your project structure is different
# For a self-contained script, you might need to adjust PYTHONPATH or copy MCPManager
# For now, assuming it can be imported if script is in workspace root and src is on PYTHONPATH
from src.swarmdev.utils.mcp_manager import MCPManager

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("MCPTestScript")

TEMP_MCP_CONFIG_PATH = "temp_mcp_config_for_test.json"

# Define a minimal MCP config for the test
# We pre-configure memory server's capabilities to bypass tools/list for this specific test,
# as we are testing INVOCATION, not DISCOVERY.
# The 'filesystem' server is often pre-configured or discoverable.
TEST_MCP_CONFIG = {
    "enabled": True, # Correct key for MCPManager's master enable flag
    "version": "1.0",
    "global_settings": {
        "log_level": "DEBUG",
        "start_timeout_seconds": 60,
        "shutdown_timeout_seconds": 10,
        "default_network_mode": "bridge" # Or "host" depending on Docker setup
    },
    "mcpServers": { # Correct key for server definitions to be merged from constructor
        "filesystem": {
            "enabled": True,
            # Replace structured config with explicit command for testing _register_server directly
            "command": ["docker", "run", "-i", "--rm", "-v", "$(pwd):/workspace", "ghcr.io/chungoid/filesystem:latest", "/workspace"],
            "timeout": 30, # Add a default timeout
            "discover_capabilities": True # Filesystem server supports tools/list
        },
        "memory": { # User's memory server
            "enabled": True,
            # Replace structured config with explicit command
            "command": ["docker", "run", "-i", "--rm", "ghcr.io/chungoid/memory:latest"],
            "timeout": 30, # Add a default timeout
            "discover_capabilities": False, # Set to False for this test
            "capabilities": {
                "tools": [
                    {
                        "name": "create_entities",
                        "description": "Create multiple new entities in the knowledge graph",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "entities": {
                                    "type": "array",
                                    "items": {"type": "object"}
                                }
                            },
                            "required": ["entities"]
                        }
                    }
                    # Add other known methods if you want to test them via tools/call
                ]
            }
        }
    }
}

def create_temp_config():
    logger.info(f"Creating temporary MCP config at {TEMP_MCP_CONFIG_PATH}")
    with open(TEMP_MCP_CONFIG_PATH, 'w') as f:
        json.dump(TEST_MCP_CONFIG, f, indent=2)

def remove_temp_config():
    logger.info(f"Removing temporary MCP config from {TEMP_MCP_CONFIG_PATH}")
    if os.path.exists(TEMP_MCP_CONFIG_PATH):
        os.remove(TEMP_MCP_CONFIG_PATH)

def run_tests():
    create_temp_config()
    mcp_manager = None
    try:
        # Load the config dictionary from the temporary file
        with open(TEMP_MCP_CONFIG_PATH, 'r') as f_config:
            config_dict = json.load(f_config)

        # Initialize MCPManager with the loaded config dictionary
        logger.info("Initializing MCPManager...")
        mcp_manager = MCPManager(config=config_dict, project_dir=".")

        if not mcp_manager.is_enabled():
            logger.error("MCPManager is not enabled. Check config or environment.")
            return

        logger.info("Attempting to initialize tools (start servers)...")
        if mcp_manager.initialize_tools():
            logger.info("MCPManager tools initialized (servers should be starting/started).")
            
            # Log discovered capabilities for the filesystem server
            fs_caps = mcp_manager.get_server_capabilities("filesystem")
            logger.info(f"Discovered capabilities for 'filesystem' server: {json.dumps(fs_caps, indent=2)}")

        else:
            logger.error("MCPManager.initialize_tools() failed. Servers might not be running.")

        # Wait a bit for servers to be fully ready after initialize_tools returns
        logger.info("Waiting a few seconds for servers to stabilize...")
        time.sleep(10) # Adjust if servers take longer

        # --- Test 1: Memory Server - Direct Call Style ---
        logger.info("\n--- Test 1: Memory Server - Direct Call Style (method: 'create_entities') ---")
        direct_call_params = {"entities": [{"name": f"test_direct_{uuid.uuid4().hex[:6]}", "entityType": "Test", "observations": ["direct_call"]}]}
        try:
            direct_result = mcp_manager.call_tool(
                tool_id="memory",
                method="create_entities", # Calling 'create_entities' as the top-level JSON-RPC method
                params=direct_call_params
            )
            logger.info(f"Direct call to memory.create_entities result: {json.dumps(direct_result, indent=2)}")
            error_val_test1 = direct_result.get("error")
            if error_val_test1 and isinstance(error_val_test1, dict) and error_val_test1.get("message") == "Method not found":
                logger.info("CONCLUSION Test 1: As expected, 'Method not found' for direct call if server expects 'tools/call'.")
            elif not error_val_test1:
                logger.warning("CONCLUSION Test 1: Direct call succeeded. This implies the memory server has 'create_entities' as a top-level JSON-RPC method.")
            else:
                logger.warning(f"CONCLUSION Test 1: Direct call failed with an unexpected error: {error_val_test1}")

        except Exception as e:
            logger.error(f"Exception during direct call to memory.create_entities: {e}", exc_info=True)
            logger.info("CONCLUSION Test 1: Exception likely means direct call is not supported as hypothesized.")

        # --- Test 2: Memory Server - 'tools/call' Wrapped Style ---
        logger.info("\n--- Test 2: Memory Server - 'tools/call' Wrapped Style (method: 'tools/call', name: 'create_entities') ---")
        wrapped_call_params = {
            "name": "create_entities", # The actual tool/method name for the memory server
            "arguments": {"entities": [{"name": f"test_wrapped_{uuid.uuid4().hex[:6]}", "entityType": "Test", "observations": ["wrapped_call"]}]}
        }
        try:
            wrapped_result = mcp_manager.call_tool(
                tool_id="memory",
                method="tools/call", # Using the standard MCP dispatch method
                params=wrapped_call_params
            )
            logger.info(f"'tools/call' to memory (name: create_entities) result: {json.dumps(wrapped_result, indent=2)}")
            error_val_test2 = wrapped_result.get("error")
            if not error_val_test2:
                logger.info("CONCLUSION Test 2: 'tools/call' wrapped call succeeded, as expected for standard MCP servers.")
            else:
                logger.warning(f"CONCLUSION Test 2: 'tools/call' wrapped call failed: {error_val_test2}. This is unexpected if the server is standard.")
        except Exception as e:
            logger.error(f"Exception during 'tools/call' wrapped call to memory (name: create_entities): {e}", exc_info=True)


        # --- Test 3: Filesystem Server ---
        logger.info("\n--- Test 3: Filesystem Server - 'tools/call' Wrapped Style (method: 'tools/call', name: 'list_directory') ---")
        try:
            fs_params = {
                "name": "list_directory", # Corrected from list_files based on discovered capabilities
                "arguments": {"path": "/workspace"} # Example path
            }
            fs_result = mcp_manager.call_tool("filesystem", "tools/call", fs_params)
            logger.info(f"'tools/call' to filesystem (name: list_directory) result: {json.dumps(fs_result, indent=2)}")
            if fs_result and not fs_result.get("error") and fs_result.get("result", {}).get("content") and not fs_result.get("result",{}).get("isError"):
                logger.info("CONCLUSION Test 3: 'tools/call' to filesystem server succeeded, as expected.")
            elif fs_result and fs_result.get("result", {}).get("isError"):
                logger.warning(f"CONCLUSION Test 3: Filesystem server reported an error: {fs_result.get('result').get('content')}")
            else:
                logger.warning(f"CONCLUSION Test 3: 'tools/call' to filesystem server failed or returned unexpected structure: {fs_result}")

        except Exception as e:
            logger.error(f"Exception during 'tools/call' to filesystem (name: list_directory): {e}", exc_info=True)

    finally:
        if mcp_manager:
            logger.info("Shutting down MCPManager...")
            mcp_manager.shutdown()
        remove_temp_config()
        logger.info("Test script finished.")

if __name__ == "__main__":
    # This is a basic way to ensure Python can find modules in 'src'
    # when running from the workspace root.
    # For more robust setups, consider proper packaging or PYTHONPATH adjustments.
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
    # If your utils and mcp_manager are deeper, adjust path e.g.
    # sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__)))) # if mcp_manager is in src/swarmdev/utils
    
    # Add the current directory to sys.path to allow `from src...` if script is in workspace root
    sys.path.insert(0, os.getcwd())


    run_tests() 