#!/usr/bin/env python3
"""
Simple test script for the Shell Executor MCP Server

This script tests the basic functionality of our new shell executor to ensure
it can replace the complex tmux-mcp implementation.
"""

import json
import logging
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from swarmdev.utils.mcp_manager import MCPManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_shell_executor():
    """Test the shell executor MCP server functionality."""
    print("=== Testing Shell Executor MCP Server ===\n")
    
    # Create MCP config for testing
    config = {
        "enabled": True,
        "mcpSettings": {
            "defaultTimeout": 30,
            "initializationTimeout": 15,
            "discoveryTimeout": 10
        },
        "mcpServers": {
            "shell": {
                "command": ["python", "-m", "swarmdev.mcp_tools.shell_executor"],
                "timeout": 60,
                "enabled": True,
                "description": "Simple shell command execution with full output capture"
            }
        }
    }
    
    # Initialize MCP Manager
    print("1. Initializing MCP Manager...")
    mcp_manager = MCPManager(config, project_dir=".")
    
    if not mcp_manager.is_enabled():
        print("❌ FAILED: MCP Manager not enabled")
        return False
    
    print("✅ MCP Manager initialized")
    
    # Initialize tools
    print("\n2. Initializing MCP tools...")
    if not mcp_manager.initialize_tools():
        print("❌ FAILED: Tool initialization failed")
        return False
    
    available_tools = mcp_manager.get_available_tools()
    if 'shell' not in available_tools:
        print(f"❌ FAILED: Shell executor not available. Available tools: {available_tools}")
        return False
    
    print(f"✅ Shell executor available. All tools: {available_tools}")
    
    # Test 1: Simple echo command
    print("\n3. Testing simple echo command...")
    try:
        result = mcp_manager.call_tool("shell", "tools/call", {
            "name": "execute_command",
            "arguments": {
                "command": "echo 'Hello from Shell Executor!'",
                "timeout": 10
            }
        })
        
        if result.get("error"):
            print(f"❌ FAILED: Tool call error: {result['error']}")
            return False
        
        # Parse the result
        content = result.get("result", {}).get("content", [])
        if not content:
            print("❌ FAILED: No content in response")
            return False
        
        tool_output = json.loads(content[0]["text"])
        if not tool_output.get("success"):
            print(f"❌ FAILED: Command failed: {tool_output}")
            return False
        
        expected_output = "Hello from Shell Executor!"
        if expected_output not in tool_output.get("stdout", ""):
            print(f"❌ FAILED: Unexpected output: {tool_output.get('stdout')}")
            return False
        
        print(f"✅ Echo command successful: {tool_output['stdout'].strip()}")
        
    except Exception as e:
        print(f"❌ FAILED: Exception during echo test: {e}")
        return False
    
    # Test 2: Command with working directory
    print("\n4. Testing command with working directory...")
    try:
        result = mcp_manager.call_tool("shell", "tools/call", {
            "name": "execute_command",
            "arguments": {
                "command": "pwd",
                "cwd": "/tmp",
                "timeout": 10
            }
        })
        
        content = result.get("result", {}).get("content", [])
        tool_output = json.loads(content[0]["text"])
        
        if not tool_output.get("success"):
            print(f"❌ FAILED: pwd command failed: {tool_output}")
            return False
        
        if "/tmp" not in tool_output.get("stdout", ""):
            print(f"❌ FAILED: Working directory not changed: {tool_output.get('stdout')}")
            return False
        
        print(f"✅ Working directory test successful: {tool_output['stdout'].strip()}")
        
    except Exception as e:
        print(f"❌ FAILED: Exception during working directory test: {e}")
        return False
    
    # Test 3: Error handling (command that fails)
    print("\n5. Testing error handling...")
    try:
        result = mcp_manager.call_tool("shell", "tools/call", {
            "name": "execute_command",
            "arguments": {
                "command": "exit 42",  # Command that fails with exit code 42
                "timeout": 10
            }
        })
        
        content = result.get("result", {}).get("content", [])
        tool_output = json.loads(content[0]["text"])
        
        if tool_output.get("success"):
            print(f"❌ FAILED: Command should have failed but didn't: {tool_output}")
            return False
        
        if tool_output.get("returncode") != 42:
            print(f"❌ FAILED: Expected return code 42, got: {tool_output.get('returncode')}")
            return False
        
        print(f"✅ Error handling test successful: return code = {tool_output['returncode']}")
        
    except Exception as e:
        print(f"❌ FAILED: Exception during error handling test: {e}")
        return False
    
    # Test 4: Script execution
    print("\n6. Testing script execution...")
    try:
        result = mcp_manager.call_tool("shell", "tools/call", {
            "name": "execute_script",
            "arguments": {
                "script_content": "echo 'Script executed successfully'\necho 'Line 2'",
                "script_type": "bash",
                "timeout": 10
            }
        })
        
        content = result.get("result", {}).get("content", [])
        tool_output = json.loads(content[0]["text"])
        
        if not tool_output.get("success"):
            print(f"❌ FAILED: Script execution failed: {tool_output}")
            return False
        
        expected_lines = ["Script executed successfully", "Line 2"]
        stdout = tool_output.get("stdout", "")
        for line in expected_lines:
            if line not in stdout:
                print(f"❌ FAILED: Expected line '{line}' not found in output: {stdout}")
                return False
        
        print(f"✅ Script execution successful")
        
    except Exception as e:
        print(f"❌ FAILED: Exception during script execution test: {e}")
        return False
    
    # Cleanup
    print("\n7. Cleaning up...")
    mcp_manager.shutdown()
    print("✅ Cleanup complete")
    
    print("\n🎉 All tests passed! Shell Executor MCP Server is working correctly.")
    print("\nKey benefits over tmux-mcp:")
    print("  ✅ Simple Python subprocess execution")
    print("  ✅ Complete output capture (stdout, stderr, return code)")
    print("  ✅ No Docker complexity")
    print("  ✅ No socket mounting or port forwarding")
    print("  ✅ Reliable error handling")
    print("  ✅ Perfect for test agents and build automation")
    
    return True

if __name__ == "__main__":
    success = test_shell_executor()
    sys.exit(0 if success else 1) 