#!/usr/bin/env python3
"""
Standalone Shell Execution MCP Server

This MCP server provides reliable shell command execution with complete output capture.
It is designed to be a self-contained script that can be called from any project.

Perfect for test agents, build automation, and any workflow requiring shell commands.
Based on Python subprocess module for reliable, simple execution.

Usage:
    This script is intended to be called by an MCP Manager.

Example MCP Configuration:
    "shell": {
        "command": ["python", "/path/to/this/shell_executor.py"],
        "timeout": 60,
        "enabled": true,
        "description": "Simple shell command execution with full output capture"
    }
"""

import asyncio
import json
import subprocess
import sys
import os
import tempfile
from typing import Optional, Dict, Any, List
from pathlib import Path

# Import MCP SDK
try:
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.server.stdio import stdio_server 
    from mcp.types import TextContent, Tool
    import mcp.server.stdio
    import mcp.types as types
except ImportError:
    print("Error: MCP SDK not found. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Create the MCP server
server = Server("shell-executor")

def validate_command(command: str) -> tuple[bool, str]:
    """Basic command validation for security."""
    # Block obviously dangerous commands
    dangerous_patterns = [
        "rm -rf /",
        "dd if=",
        "mkfs",
        "fdisk", 
        "> /dev/",
        "sudo rm",
        "sudo dd",
        "sudo mkfs"
    ]
    
    command_lower = command.lower()
    for pattern in dangerous_patterns:
        if pattern in command_lower:
            return False, f"Command blocked for safety: contains '{pattern}'"
    
    return True, ""

# Tool implementations
async def execute_command_impl(arguments: dict) -> List[types.TextContent]:
    """
    Execute a shell command and return complete output.
    """
    command = arguments.get("command", "")
    cwd = arguments.get("cwd")
    timeout = arguments.get("timeout", 30)
    capture_output = arguments.get("capture_output", True)
    
    # Validate command for basic security
    is_safe, error_msg = validate_command(command)
    if not is_safe:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "blocked",
                "command": command,
                "error": error_msg,
                "returncode": -1
            }, indent=2)
        )]
    
    # Set working directory
    if cwd:
        work_dir = Path(cwd).resolve()
        if not work_dir.exists():
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "command": command,
                    "error": f"Working directory does not exist: {cwd}",
                    "returncode": -1
                }, indent=2)
            )]
    else:
        work_dir = Path.cwd()
    
    try:
        # Execute the command using subprocess.run for reliability
        process = subprocess.run(
            command,
            shell=True,
            cwd=str(work_dir),
            capture_output=capture_output,
            text=True,
            timeout=timeout
        )
        
        # Return comprehensive results
        result = {
            "status": "success" if process.returncode == 0 else "failed",
            "command": command,
            "returncode": process.returncode,
            "success": process.returncode == 0,
            "cwd": str(work_dir)
        }
        
        if capture_output:
            result["stdout"] = process.stdout or ""
            result["stderr"] = process.stderr or ""
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
        
    except subprocess.TimeoutExpired:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "timeout", 
                "command": command,
                "error": f"Command timed out after {timeout} seconds",
                "returncode": -1,
                "cwd": str(work_dir)
            }, indent=2)
        )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "command": command,
                "error": str(e),
                "returncode": -1,
                "cwd": str(work_dir)
            }, indent=2)
        )]

async def execute_script_impl(arguments: dict) -> List[types.TextContent]:
    """
    Execute a script from content string.
    """
    script_content = arguments.get("script_content", "")
    script_type = arguments.get("script_type", "bash")
    cwd = arguments.get("cwd")
    timeout = arguments.get("timeout", 30)
    
    # Validate script type
    valid_types = ["bash", "sh", "python", "python3", "node", "zsh"]
    if script_type not in valid_types:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "error": f"Unsupported script type: {script_type}. Valid types: {valid_types}",
                "returncode": -1
            }, indent=2)
        )]
    
    # Create temporary script file
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=f'.{script_type}',
            delete=False
        ) as temp_file:
            temp_file.write(script_content)
            temp_script_path = temp_file.name
        
        # Make script executable
        os.chmod(temp_script_path, 0o755)
        
        # Execute the script
        if script_type in ["bash", "sh", "zsh"]:
            command = f"{script_type} {temp_script_path}"
        elif script_type in ["python", "python3"]:
            command = f"{script_type} {temp_script_path}"
        elif script_type == "node":
            command = f"node {temp_script_path}"
        else:
            command = temp_script_path
        
        # Use execute_command to run the script
        result = await execute_command_impl({
            "command": command,
            "cwd": cwd,
            "timeout": timeout,
            "capture_output": True
        })
        
        # Clean up temp file
        try:
            os.unlink(temp_script_path)
        except OSError:
            pass  # Best effort cleanup
        
        return result
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "error": f"Failed to create/execute script: {str(e)}",
                "returncode": -1
            }, indent=2)
        )]

async def execute_with_input_impl(arguments: dict) -> List[types.TextContent]:
    """
    Execute a command with stdin input.
    """
    command = arguments.get("command", "")
    stdin_input = arguments.get("stdin_input", "")
    cwd = arguments.get("cwd")
    timeout = arguments.get("timeout", 30)
    
    # Validate command
    is_safe, error_msg = validate_command(command)
    if not is_safe:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "blocked",
                "command": command,
                "error": error_msg,
                "returncode": -1
            }, indent=2)
        )]
    
    # Set working directory
    if cwd:
        work_dir = Path(cwd).resolve()
        if not work_dir.exists():
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "command": command,
                    "error": f"Working directory does not exist: {cwd}",
                    "returncode": -1
                }, indent=2)
            )]
    else:
        work_dir = Path.cwd()
    
    try:
        # Execute the command with stdin
        process = subprocess.run(
            command,
            shell=True,
            cwd=str(work_dir),
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        result = {
            "status": "success" if process.returncode == 0 else "failed",
            "command": command,
            "returncode": process.returncode,
            "success": process.returncode == 0,
            "stdout": process.stdout or "",
            "stderr": process.stderr or "",
            "cwd": str(work_dir)
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
        
    except subprocess.TimeoutExpired:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "timeout",
                "command": command,
                "error": f"Command timed out after {timeout} seconds",
                "returncode": -1,
                "cwd": str(work_dir)
            }, indent=2)
        )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "command": command,
                "error": str(e),
                "returncode": -1,
                "cwd": str(work_dir)
            }, indent=2)
        )]

# Register tools with the server
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    """
    return [
        types.Tool(
            name="execute_command",
            description="Execute a shell command and return complete output",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute"
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (optional)"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Command timeout in seconds (default: 30)"
                    },
                    "capture_output": {
                        "type": "boolean",
                        "description": "Whether to capture stdout/stderr (default: true)"
                    }
                },
                "required": ["command"]
            }
        ),
        types.Tool(
            name="execute_script",
            description="Execute a script from content string",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_content": {
                        "type": "string",
                        "description": "The script content to execute"
                    },
                    "script_type": {
                        "type": "string",
                        "description": "Script type (bash, python, sh, etc.)",
                        "enum": ["bash", "sh", "python", "python3", "node", "zsh"]
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (optional)"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Script timeout in seconds (default: 30)"
                    }
                },
                "required": ["script_content"]
            }
        ),
        types.Tool(
            name="execute_with_input",
            description="Execute a command with stdin input",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute"
                    },
                    "stdin_input": {
                        "type": "string",
                        "description": "Input to send to command's stdin"
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (optional)"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Command timeout in seconds (default: 30)"
                    }
                },
                "required": ["command", "stdin_input"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """
    Handle tool calls.
    """
    if name == "execute_command":
        return await execute_command_impl(arguments)
    elif name == "execute_script":
        return await execute_script_impl(arguments)
    elif name == "execute_with_input":
        return await execute_with_input_impl(arguments)
    else:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "error": f"Unknown tool: {name}"
            })
        )]

async def main():
    """Main entry point for the shell executor MCP server."""
    try:
        # Start the stdio server
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="shell-executor",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    print("Starting Shell Executor MCP Server...", file=sys.stderr)
    asyncio.run(main()) 