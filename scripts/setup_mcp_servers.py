#!/usr/bin/env python3
"""
Generic MCP Server Setup Script - No hardcoded server logic.

This script builds MCP servers based purely on configuration, without any hardcoded knowledge
of specific server types, technologies, or build processes.
"""

import os
import subprocess
import json
import sys
from pathlib import Path


def run_command(cmd, cwd=None, env=None):
    """Run a command and return success status."""
    try:
        print(f"Running: {' '.join(cmd)}")
        if cwd:
            print(f"  Working directory: {cwd}")
        
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            env=env,
            capture_output=True, 
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"SUCCESS: Command succeeded")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"FAILED: Command failed with return code {result.returncode}")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"FAILED: Command timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"FAILED: Exception running command: {e}")
        return False


def load_build_config():
    """Load build configuration from file."""
    config_paths = [
        "scripts/mcp_build_config.json",
        ".swarmdev/mcp_build_config.json", 
        "mcp_build_config.json"
    ]
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            print(f"Loading build config from: {config_path}")
            with open(config_path, 'r') as f:
                return json.load(f)
    
    print("No build config found, using default configuration")
    return get_default_build_config()


def get_default_build_config():
    """Get default build configuration if no config file exists."""
    return {
        "servers": [
            {
                "name": "memory",
                "directory": "src/swarmdev/bundled_mcp/servers/src/memory",
                "build_commands": [
                    ["npm", "install", "--no-fund"],
                    ["npm", "run", "build"]
                ],
                "docker_tag": "mcp/memory",
                "docker_build_dir": "src/swarmdev/bundled_mcp/servers",
                "dockerfile_path": "src/memory/Dockerfile"
            },
            {
                "name": "sequential-thinking", 
                "directory": "src/swarmdev/bundled_mcp/servers/src/sequentialthinking",
                "build_commands": [
                    ["npm", "install", "--no-fund"],
                    ["npm", "run", "build"]
                ],
                "docker_tag": "mcp/sequentialthinking",
                "docker_build_dir": "src/swarmdev/bundled_mcp/servers",
                "dockerfile_path": "src/sequentialthinking/Dockerfile"
            },
            {
                "name": "context7",
                "directory": "src/swarmdev/bundled_mcp/servers/src/context7",
                "build_commands": [
                    ["npm", "install", "--no-fund"],
                    ["npm", "run", "build"]
                ],
                "docker_tag": "context7-mcp"
            },
            {
                "name": "git",
                "directory": "src/swarmdev/bundled_mcp/servers/src/git",
                "build_commands": [],
                "docker_tag": "mcp/git"
            },
            {
                "name": "time",
                "directory": "src/swarmdev/bundled_mcp/servers/src/time", 
                "build_commands": [],
                "docker_tag": "mcp/time"
            },
            {
                "name": "fetch",
                "directory": "src/swarmdev/bundled_mcp/servers/src/fetch",
                "build_commands": [],
                "docker_tag": "mcp/fetch"
            },
            {
                "name": "filesystem",
                "directory": "src/swarmdev/bundled_mcp/servers/src/filesystem",
                "build_commands": [
                    ["npm", "install", "--no-fund"],
                    ["npm", "run", "build"]
                ],
                "docker_tag": "mcp/filesystem",
                "docker_build_dir": "src/swarmdev/bundled_mcp/servers",
                "dockerfile_path": "src/filesystem/Dockerfile"
            }
        ]
    }


def build_server(server_config):
    """Build a single server based on its configuration."""
    name = server_config["name"]
    directory = server_config["directory"]
    build_commands = server_config.get("build_commands", [])
    docker_tag = server_config["docker_tag"]
    dockerfile_dir = server_config.get("dockerfile_dir", ".")
    
    print(f"\n=== Building {name} ===")
    
    # Check if directory exists
    if not os.path.exists(directory):
        print(f"FAILED: Directory not found: {directory}")
        return False
    
    # Temporarily disable workspace for TypeScript servers to avoid prepare script conflicts
    workspace_pkg = "src/swarmdev/bundled_mcp/servers/package.json"
    workspace_backup = workspace_pkg + ".tmp"
    workspace_disabled = False
    
    if build_commands and name in ["memory", "sequential-thinking", "filesystem"]:
        if os.path.exists(workspace_pkg):
            print(f"Temporarily disabling workspace for {name} build")
            os.rename(workspace_pkg, workspace_backup)
            workspace_disabled = True
    
    try:
        # Run pre-build commands (like npm install, npm run build)
        for cmd in build_commands:
            if not run_command(cmd, cwd=directory):
                print(f"FAILED: Pre-build command failed for {name}")
                return False
        
        # Determine Docker context directory and dockerfile path
        docker_build_dir = server_config.get("docker_build_dir")
        dockerfile_path = server_config.get("dockerfile_path")
        
        if docker_build_dir and dockerfile_path:
            # Build from workspace root with specific dockerfile
            docker_context_dir = docker_build_dir
            dockerfile_full_path = os.path.join(docker_build_dir, dockerfile_path)
        else:
            # Build from server directory
            docker_context_dir = os.path.join(directory, dockerfile_dir) if dockerfile_dir != "." else directory
            dockerfile_full_path = os.path.join(docker_context_dir, "Dockerfile")
        
        # Check if Dockerfile exists
        if not os.path.exists(dockerfile_full_path):
            print(f"FAILED: Dockerfile not found: {dockerfile_full_path}")
            return False
        
        # Try BuildKit first, then legacy mode
        print(f"Attempting BuildKit build for {name}...")
        env = os.environ.copy()
        env["DOCKER_BUILDKIT"] = "1"
        
        if dockerfile_path:
            # Use specific dockerfile
            docker_cmd = ["docker", "build", "-f", dockerfile_path, "-t", docker_tag, "."]
        else:
            # Use default Dockerfile
            docker_cmd = ["docker", "build", "-t", docker_tag, "."]
        
        if run_command(docker_cmd, cwd=docker_context_dir, env=env):
            print(f"SUCCESS: Successfully built {name} -> {docker_tag} (BuildKit)")
            return True
        
        print(f"BuildKit failed, trying legacy build for {name}...")
        env["DOCKER_BUILDKIT"] = "0"
        
        if run_command(docker_cmd, cwd=docker_context_dir, env=env):
            print(f"SUCCESS: Successfully built {name} -> {docker_tag} (Legacy)")
            return True
        
        print(f"FAILED: Both BuildKit and legacy builds failed for {name}")
        return False
        
    finally:
        # Restore workspace if it was disabled
        if workspace_disabled and os.path.exists(workspace_backup):
            print(f"Restoring workspace for {name}")
            os.rename(workspace_backup, workspace_pkg)


def verify_docker_images(server_configs):
    """Verify that all Docker images were built successfully."""
    print("\n=== Verifying Docker Images ===")
    
    for server_config in server_configs:
        docker_tag = server_config["docker_tag"]
        cmd = ["docker", "images", "--format", "table {{.Repository}}:{{.Tag}}", "--filter", f"reference={docker_tag}"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and docker_tag in result.stdout:
                print(f"VERIFIED: {docker_tag}")
            else:
                print(f"MISSING: {docker_tag} - Image not found")
        except Exception as e:
            print(f"ERROR: {docker_tag} - Verification failed: {e}")


def create_mcp_config(server_configs):
    """Create MCP configuration based on built servers."""
    print("\n=== Creating MCP Configuration ===")
    
    config = {
        "enabled": True,
        "mcpSettings": {
            "defaultTimeout": 30,
            "initializationTimeout": 15,
            "discoveryTimeout": 10,
            "persistentConnections": True,
            "autoDiscovery": True,
            "retryCount": 3,
            "retryDelay": 1.0
        },
        "mcpServers": {}
    }
    
    # Add each server to config
    for server_config in server_configs:
        name = server_config["name"]
        docker_tag = server_config["docker_tag"]
        description = server_config.get("description", f"{name} MCP server")
        
        config["mcpServers"][name] = {
            "command": ["docker", "run", "-i", "--rm", docker_tag],
            "description": description,
            "timeout": server_config.get("timeout", 30)
        }
    
    # Create config directory
    config_dir = os.path.expanduser("~/.swarmdev")
    os.makedirs(config_dir, exist_ok=True)
    
    # Write config file
    config_file = os.path.join(config_dir, "mcp_config.json")
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"SUCCESS: MCP configuration written to: {config_file}")
    print(f"   Configured {len(config['mcpServers'])} servers")


def run_mcp_tests():
    """Run the comprehensive MCP installation test suite."""
    try:
        # Find the test script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        test_script = os.path.join(script_dir, "test_mcp_installation.py")
        
        if not os.path.exists(test_script):
            print(f"FAILED: Test script not found: {test_script}")
            return False
        
        # Run the test script
        print(f"Running: python {test_script}")
        result = subprocess.run(
            [sys.executable, test_script],
            cwd=os.path.dirname(script_dir),  # Run from swarmdev root
            timeout=300  # 5 minute timeout
        )
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"FAILED: MCP tests timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"FAILED: Failed to run MCP tests: {e}")
        return False


def main():
    """Main setup function."""
    print("=== Generic MCP Server Setup ===")
    print("Building MCP servers based on configuration...")
    
    # Load build configuration
    build_config = load_build_config()
    server_configs = build_config.get("servers", [])
    
    if not server_configs:
        print("FAILED: No servers configured for building")
        return False
    
    print(f"Found {len(server_configs)} servers to build")
    
    # Build each server
    success_count = 0
    for server_config in server_configs:
        if build_server(server_config):
            success_count += 1
    
    print(f"\n=== Build Summary ===")
    print(f"Successfully built: {success_count}/{len(server_configs)} servers")
    
    if success_count == 0:
        print("FAILED: No servers built successfully")
        return False
    
    # Verify built images
    verify_docker_images(server_configs)
    
    # Create MCP configuration for successfully built servers
    successful_configs = []
    for server_config in server_configs:
        # Quick check if image exists
        docker_tag = server_config["docker_tag"]
        try:
            result = subprocess.run(
                ["docker", "images", "-q", docker_tag], 
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                successful_configs.append(server_config)
        except:
            pass
    
    if successful_configs:
        create_mcp_config(successful_configs)
        print(f"\nSUCCESS: Setup complete! {len(successful_configs)} MCP servers ready to use.")
        
        # Run comprehensive MCP installation test
        print(f"\nRunning MCP Installation Test Suite...")
        test_success = run_mcp_tests()
        
        if test_success:
            print(f"\nAll done! Your SwarmDev MCP installation is ready to use.")
        else:
            print(f"\nSetup completed but some tests failed. Check output above.")
            
        return test_success
    else:
        print("\nFAILED: No servers available for configuration")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 