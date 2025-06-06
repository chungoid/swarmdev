import json
import logging
import os
import time
import uuid
import subprocess

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
    "mcpSettings": {
        "defaultTimeout": 45,        # Increased default timeout for potentially slow operations
        "initializationTimeout": 60, # Increased for servers that might be slow to start
        "discoveryTimeout": 30,
        "logLevel": "DEBUG"          # Ensure MCPManager logs verbosely
    },
    "mcpServers": {
        "filesystem": {
            "enabled": True,
            "command": ["docker", "run", "-i", "--rm", "-v", "$(pwd):/workspace", 
                       "ghcr.io/chungoid/filesystem:latest", "/workspace"],
            "timeout": 30,
            "description": "Filesystem access server"
        },
        "memory": {
            "enabled": True,
            "command": ["docker", "run", "-i", "--rm", "mcp/memory"],
            "timeout": 30,
            "description": "MCP Memory Server (built via scripts/setup_mcp_servers.py)"
        },
        "tmux-mcp": {
            "command": [
                "docker", "run", "-i", "--rm",
                "-v", "$(pwd):/workspace",
                "-v", "/tmp/tmux-1000:/tmp/tmux-1000",
                "-e", "TMUX_TMPDIR=/tmp/tmux-1000",
                "-p", "127.0.0.1:13008:3000",
                "ghcr.io/chungoid/tmux-mcp:debug-v4"
            ],
            "timeout": 45,
            "init_delay": 1.0,
            "enabled": True,
            "description": "TMUX MCP Server (debug-v4)"
        },
        "everything": {
            "enabled": True,
            "command": ["docker", "run", "-i", "--rm", "ghcr.io/chungoid/everything:latest"],
            "timeout": 30,
            "description": "A server that has every possible MCP feature for testing purposes."
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

            # Log discovered capabilities for the everything server
            everything_caps = mcp_manager.get_server_capabilities("everything")
            logger.info(f"Discovered capabilities for 'everything' server: {json.dumps(everything_caps, indent=2)}")

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

        # --- Test 4: tmux-mcp Server - Full Command Execution Flow ---
        logger.info("\n--- Test 4: tmux-mcp Server - Full Command Execution Flow ---")
        
        # Step 0: Verify the correct debug-v4 image is running
        logger.info("Attempting to call tmux-mcp.debug_v4_check_version")
        try:
            debug_check_params = {"name": "debug_v4_check_version", "arguments": {}}
            debug_check_result = mcp_manager.call_tool("tmux-mcp", "tools/call", debug_check_params)
            logger.info(f"tmux-mcp.debug_v4_check_version result: {json.dumps(debug_check_result, indent=2)}")
            if debug_check_result and debug_check_result.get("result", {}).get("content", [{}])[0].get("text") == "tmux-mcp-debug-v4-active":
                logger.info("SUCCESS: tmux-mcp.debug_v4_check_version returned 'tmux-mcp-debug-v4-active'. Correct image is running.")
            else:
                logger.error("FAILURE: tmux-mcp.debug_v4_check_version did NOT return 'tmux-mcp-debug-v4-active'. WRONG IMAGE OR TOOL ISSUE.")
                # Optionally, we could raise an exception here to stop further tmux-mcp tests if the version is wrong.
        except Exception as e_debug_check:
            logger.error(f"EXCEPTION during tmux-mcp.debug_v4_check_version: {e_debug_check}", exc_info=True)
            # Again, could raise to stop if this check is critical for subsequent steps

        test_session_name = f"mcp_test_session_{uuid.uuid4().hex[:6]}"
        created_session_id = None
        created_window_id = None
        created_pane_id = None

        try:
            # Step 1: Create a new session
            logger.info(f"Attempting to create tmux session: {test_session_name}")
            create_session_params = {"name": "create-session", "arguments": {"name": test_session_name}}
            create_session_result = mcp_manager.call_tool("tmux-mcp", "tools/call", create_session_params)
            logger.info(f"Create session result: {json.dumps(create_session_result, indent=2)}")

            if create_session_result and not create_session_result.get("error") and create_session_result.get("result", {}).get("content") and not create_session_result.get("result",{}).get("isError"):
                session_text = create_session_result["result"]["content"][0]["text"]
                if "Session created:" in session_text:
                    session_json_str = session_text.split("Session created:", 1)[1].strip()
                    created_session_info = json.loads(session_json_str)
                    created_session_id = created_session_info.get("id")
                    logger.info(f"Successfully created session '{test_session_name}', ID: {created_session_id}")
                else:
                    # Attempt to parse as just the session JSON if "Session created:" prefix is missing
                    try:
                        created_session_info = json.loads(session_text)
                        created_session_id = created_session_info.get("id")
                        if created_session_id:
                             logger.info(f"Successfully parsed session from direct JSON '{test_session_name}', ID: {created_session_id}")
                        else:
                            raise Exception(f"Failed to parse created session info (no ID found): {session_text}")
                    except json.JSONDecodeError:
                        raise Exception(f"Failed to parse created session info (not plain JSON either): {session_text}")
            else:
                error_detail = create_session_result.get("error") if create_session_result else "No result"
                is_app_error = create_session_result.get("result",{}).get("isError") if create_session_result and not error_detail else False
                app_error_content = create_session_result.get("result",{}).get("content") if is_app_error else "N/A"
                raise Exception(f"Failed to create session. JSON-RPC error: {error_detail}. App error: {is_app_error}. App content: {app_error_content}. Full response: {create_session_result}")

            if not created_session_id:
                raise Exception("Could not obtain session ID after creation step.")

            # Step 2: List windows in the new session (should be one default window)
            logger.info(f"Attempting to list windows for session ID: {created_session_id}")
            list_windows_params = {"name": "list-windows", "arguments": {"sessionId": created_session_id}}
            list_windows_result = mcp_manager.call_tool("tmux-mcp", "tools/call", list_windows_params)
            logger.info(f"List windows result: {json.dumps(list_windows_result, indent=2)}")
            
            if list_windows_result and not list_windows_result.get("error") and list_windows_result.get("result", {}).get("content") and not list_windows_result.get("result",{}).get("isError"):
                windows_list_json = json.loads(list_windows_result["result"]["content"][0]["text"])
                if windows_list_json and isinstance(windows_list_json, list) and len(windows_list_json) > 0:
                    created_window_id = windows_list_json[0].get("id")
                    logger.info(f"Successfully listed windows, using first window ID: {created_window_id}")
                else:
                    raise Exception(f"No windows found in new session or bad format: {windows_list_json}")
            else:
                error_detail_lw = list_windows_result.get("error") if list_windows_result else "No result"
                raise Exception(f"Failed to list windows. JSON-RPC error: {error_detail_lw}. Full response: {list_windows_result}")

            if not created_window_id:
                raise Exception("Could not obtain window ID.")

            # Step 3: List panes in the new window (should be one default pane)
            logger.info(f"Attempting to list panes for window ID: {created_window_id}")
            list_panes_params = {"name": "list-panes", "arguments": {"windowId": created_window_id}}
            list_panes_result = mcp_manager.call_tool("tmux-mcp", "tools/call", list_panes_params)
            logger.info(f"List panes result: {json.dumps(list_panes_result, indent=2)}")

            if list_panes_result and not list_panes_result.get("error") and list_panes_result.get("result", {}).get("content") and not list_panes_result.get("result",{}).get("isError"):
                panes_list_json = json.loads(list_panes_result["result"]["content"][0]["text"])
                if panes_list_json and isinstance(panes_list_json, list) and len(panes_list_json) > 0:
                    created_pane_id = panes_list_json[0].get("id")
                    logger.info(f"Successfully listed panes, using first pane ID: {created_pane_id}")
                else:
                    raise Exception(f"No panes found in new window or bad format: {panes_list_json}")
            else:
                error_detail_lp = list_panes_result.get("error") if list_panes_result else "No result"
                raise Exception(f"Failed to list panes. JSON-RPC error: {error_detail_lp}. Full response: {list_panes_result}")
            
            if not created_pane_id:
                raise Exception("Could not obtain pane ID.")

            # Step 4: Execute a command in the identified pane
            # Change to /workspace first, then echo.
            command_to_run = f"cd /workspace && echo hello_tmux_cd_test_{uuid.uuid4().hex[:6]} > tmux_pane_output.txt"
            output_file_name = "tmux_pane_output.txt"
            
            logger.info(f"Attempting to execute command '{command_to_run}' in pane ID: {created_pane_id}")
            exec_command_params = {
                "name": "execute-command", 
                "arguments": {"paneId": created_pane_id, "command": command_to_run}
            }
            exec_command_result = mcp_manager.call_tool("tmux-mcp", "tools/call", exec_command_params)
            logger.info(f"Execute command result: {json.dumps(exec_command_result, indent=2)}")

            if exec_command_result and not exec_command_result.get("error") and exec_command_result.get("result", {}).get("content") and not exec_command_result.get("result",{}).get("isError"):
                exec_text = exec_command_result["result"]["content"][0]["text"]
                if "Command execution started" in exec_text and "tmux://command/" in exec_text:
                    logger.info(f"CONCLUSION Test 4: 'execute-command' on tmux-mcp server started successfully. Output: {exec_text}")
                    
                    logger.info(f"Waiting 5 seconds for command to complete and file '{output_file_name}' to be written...")
                    time.sleep(5) # Give command more time to execute and write file
                    
                    if os.path.exists(output_file_name):
                        logger.info(f"Command output file {output_file_name} created successfully.")
                        with open(output_file_name, "r") as f_out:
                            file_content = f_out.read().strip()
                            logger.info(f"Content of {output_file_name}: {file_content}")
                            if "hello_tmux_cd_test" in file_content:
                                logger.info("Command output file content verified.")
                            else:
                                logger.warning("Command output file content MISMATCH.")
                        os.remove(output_file_name) # Clean up test file
                    else:
                        logger.warning(f"Command output file {output_file_name} NOT found in {os.getcwd()}. Checking /workspace mapping.")
                        # For debugging, let's also try to list /workspace content from another MCP if possible, or just note this.
                        # This path is relative to where test_mcp_interaction.py is run.
                else:
                    logger.warning(f"CONCLUSION Test 4: 'execute-command' response from tmux-mcp had unexpected content: {exec_text}")
            elif exec_command_result and exec_command_result.get("error"):
                logger.warning(f"CONCLUSION Test 4: 'execute-command' call failed with JSON-RPC error: {exec_command_result.get('error')}")
            else:
                logger.warning(f"CONCLUSION Test 4: 'execute-command' call failed at a low level, result: {exec_command_result}")

        except Exception as e:
            logger.error(f"Exception during tmux-mcp full command execution flow: {e}", exc_info=True)
        finally:
            if created_session_id:
                try:
                    logger.info(f"Attempting to clean up (kill) test session: {created_session_id} ({test_session_name})")
                    cleanup_command = f"tmux kill-session -t {created_session_id}"
                    logger.info(f"Executing cleanup: {cleanup_command}")
                    # Use subprocess for more control and to avoid shell=True risks if session_id could be manipulated
                    # For this test, os.system is simpler but less secure if test_session_name was from untrusted source
                    process = subprocess.Popen(cleanup_command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = process.communicate(timeout=5)
                    if process.returncode != 0:
                        logger.warning(f"tmux kill-session for {created_session_id} exited with {process.returncode}. Stderr: {stderr.decode()}")
                    else:
                        logger.info(f"Successfully killed session {created_session_id}.")
                except subprocess.TimeoutExpired:
                    logger.error(f"Timeout during tmux session cleanup for {created_session_id}. Process might still be running.")
                    if process: process.kill()
                except Exception as e_cleanup:
                    logger.error(f"Error during tmux session cleanup for {created_session_id}: {e_cleanup}")

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