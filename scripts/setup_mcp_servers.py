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

# Determine the project root directory (one level up from the scripts directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


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
        PROJECT_ROOT / "scripts/mcp_build_config.json",
        PROJECT_ROOT / ".swarmdev/mcp_build_config.json", 
        PROJECT_ROOT / "mcp_build_config.json"
    ]
    
    loaded_config = None
    for config_path in config_paths:
        if config_path.exists():
            print(f"Loading build config from: {config_path}")
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
            break
    
    if loaded_config is None:
        print("No build config found, using default configuration")
        loaded_config = get_default_build_config()
        
    return make_paths_absolute_in_config(loaded_config)


def get_default_build_config():
    """Get default build configuration if no config file exists."""
    # Base path for ALL server sources and Dockerfiles if not overridden
    base_server_src_path = PROJECT_ROOT / "src/swarmdev/bundled_mcp/servers"
    # Path for individual server type directories (e.g. .../servers/src/memory)
    direct_src_path = base_server_src_path / "src"

    return {
        "servers": [
            {
                "name": "memory",
                "server_src_path": str(direct_src_path / "memory"),
                # Build context is one level up, so Dockerfile's "COPY src/memory /app" works
                "docker_build_dir": str(base_server_src_path), 
                "dockerfile_path": str(Path("src") / "memory" / "Dockerfile"), # Path relative to new context
                "docker_tag": "ghcr.io/chungoid/memory:latest",
                "build_enabled": True,
                "language": "nodejs"
            },
            {
                "name": "sequential-thinking",
                "server_src_path": str(direct_src_path / "sequentialthinking"),
                "docker_build_dir": str(base_server_src_path),
                "dockerfile_path": str(Path("src") / "sequentialthinking" / "Dockerfile"),
                "docker_tag": "ghcr.io/chungoid/sequentialthinking:latest",
                "build_enabled": True,
                "language": "nodejs"
            },
            {
                "name": "filesystem",
                "server_src_path": str(direct_src_path / "filesystem"),
                "docker_build_dir": str(base_server_src_path),
                "dockerfile_path": str(Path("src") / "filesystem" / "Dockerfile"),
                "docker_tag": "ghcr.io/chungoid/filesystem:latest",
                "build_enabled": True,
                "language": "nodejs"
            },
            { # context7 was building correctly, its Dockerfile likely uses 'COPY . /app'
                "name": "context7",
                "server_src_path": str(direct_src_path / "context7"),
                "docker_build_dir": str(direct_src_path / "context7"), # Its own directory is the context
                "dockerfile_path": "Dockerfile", # Dockerfile is at the root of this context
                "docker_tag": "ghcr.io/chungoid/context7:latest",
                "build_enabled": True,
                "language": "nodejs"
            },
            {
                "name": "everything",
                "server_src_path": str(direct_src_path / "everything"),
                "docker_build_dir": str(base_server_src_path), # Assume similar structure to other failing node ones
                "dockerfile_path": str(Path("src") / "everything" / "Dockerfile"),
                "docker_tag": "ghcr.io/chungoid/everything:latest",
                "build_enabled": True,
                "language": "nodejs"
            },
            { # Python servers were building correctly
                "name": "time",
                "server_src_path": str(direct_src_path / "time"),
                "docker_build_dir": str(direct_src_path / "time"),
                "dockerfile_path": "Dockerfile",
                "docker_tag": "ghcr.io/chungoid/time:latest",
                "build_enabled": True,
                "language": "python"
            },
            {
                "name": "git",
                "server_src_path": str(direct_src_path / "git"),
                "docker_build_dir": str(direct_src_path / "git"),
                "dockerfile_path": "Dockerfile",
                "docker_tag": "ghcr.io/chungoid/git:latest",
                "build_enabled": True,
                "language": "python"
            },
            {
                "name": "fetch",
                "server_src_path": str(direct_src_path / "fetch"),
                "docker_build_dir": str(direct_src_path / "fetch"),
                "dockerfile_path": "Dockerfile",
                "docker_tag": "ghcr.io/chungoid/fetch:latest",
                "build_enabled": True,
                "language": "python"
            }
        ],
        "settings": {
            "skip_existing_images": False
        }
    }


def build_server(server_config):
    """Build a single server based on its configuration."""
    name = server_config["name"]
    server_src_path_str = server_config["server_src_path"] # Use new key
    build_commands = server_config.get("build_commands", []) # Keep for now
    docker_tag = server_config["docker_tag"]
    
    # New explicit Docker build paths
    docker_build_dir_str = server_config["docker_build_dir"]
    dockerfile_relative_path_str = server_config["dockerfile_path"] # Path relative to docker_build_dir
    language = server_config.get("language", "unknown")

    print(f"\n=== Building {name} ({language}) ===")
    
    # Ensure server_src_path is an absolute path
    abs_server_src_path = Path(server_src_path_str)
    if not abs_server_src_path.is_absolute():
        abs_server_src_path = PROJECT_ROOT / server_src_path_str
    
    if not abs_server_src_path.exists():
        print(f"FAILED: Server source directory not found: {abs_server_src_path}")
        return False

    # Ensure docker_build_dir is an absolute path
    abs_docker_build_dir = Path(docker_build_dir_str)
    if not abs_docker_build_dir.is_absolute():
        abs_docker_build_dir = PROJECT_ROOT / docker_build_dir_str

    if not abs_docker_build_dir.exists():
        print(f"FAILED: Docker build directory not found: {abs_docker_build_dir}")
        return False

    # The Dockerfile path is relative to the abs_docker_build_dir
    abs_dockerfile_path = abs_docker_build_dir / dockerfile_relative_path_str

    if not abs_dockerfile_path.exists():
        print(f"FAILED: Dockerfile not found: {abs_dockerfile_path} (expected relative path '{dockerfile_relative_path_str}' in '{abs_docker_build_dir}')")
        return False
    
    # Temporarily disable workspace for TypeScript/Node.js servers to avoid prepare script conflicts
    # This logic might still be needed if build_commands (like npm install) are run outside Docker
    workspace_pkg = PROJECT_ROOT / "src/swarmdev/bundled_mcp/servers/package.json"
    workspace_backup = str(workspace_pkg) + ".tmp"
    workspace_disabled = False
    
    # Only run pre-build commands if specified and for nodejs language
    if build_commands and language == "nodejs":
        if workspace_pkg.exists():
            print(f"Temporarily disabling workspace for {name} pre-build steps")
            os.rename(workspace_pkg, workspace_backup)
            workspace_disabled = True
    
    try:
        # Run pre-build commands (like npm install, npm run build) if they exist
        # These are run in the server's source directory (abs_server_src_path)
        if build_commands and language == "nodejs": # Only run for nodejs if specified
            print(f"Running pre-build commands for {name} in {abs_server_src_path}...")
            for cmd_list in build_commands: # Expecting a list of lists
                if not run_command(cmd_list, cwd=str(abs_server_src_path)):
                    print(f"FAILED: Pre-build command {' '.join(cmd_list)} failed for {name}")
                    return False
        
        # Docker build
        # The context is abs_docker_build_dir
        # The Dockerfile is dockerfile_relative_path_str (relative to context)
        print(f"Attempting Docker build for {name}...")
        print(f"  Context: {abs_docker_build_dir}")
        print(f"  Dockerfile: {dockerfile_relative_path_str} (relative to context)")
        print(f"  Tag: {docker_tag}")

        # Try BuildKit first
        env_buildkit = os.environ.copy()
        env_buildkit["DOCKER_BUILDKIT"] = "1"
        
        docker_cmd = ["docker", "build", "-f", dockerfile_relative_path_str, "-t", docker_tag, str(abs_docker_build_dir)]
        
        print(f"  Command: {' '.join(docker_cmd)}")
        if run_command(docker_cmd, cwd=str(abs_docker_build_dir), env=env_buildkit): # cwd is context dir
            print(f"SUCCESS: Successfully built {name} -> {docker_tag} (BuildKit)")
            return True
        
        # BuildKit failed, try legacy build
        print(f"BuildKit failed, trying legacy build for {name}...")
        env_legacy = os.environ.copy()
        env_legacy["DOCKER_BUILDKIT"] = "0" # Explicitly disable if needed, though default might be 0 if BuildKit fails
        
        if run_command(docker_cmd, cwd=str(abs_docker_build_dir), env=env_legacy): # cwd is context dir
            print(f"SUCCESS: Successfully built {name} -> {docker_tag} (Legacy)")
            return True
        
        print(f"FAILED: Both BuildKit and legacy Docker builds failed for {name}")
        return False
        
    finally:
        # Restore workspace if it was disabled
        if workspace_disabled and Path(workspace_backup).exists():
            print(f"Restoring workspace package.json after {name} build process")
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
    """Create MCP configuration for MCP Manager."""
    print("\n=== Creating MCP Configuration ===")
    
    mcp_servers = {}
    
    for server_config in server_configs:
        server_name = server_config["name"]
        server_docker_tag = server_config["docker_tag"]
        language = server_config.get("language", "unknown") # Get language
        
        server_command_list = []

        # Use simple docker run commands, relying on image's default entrypoint.
        server_command_list = ["docker", "run", "-i", "--rm"]

        if server_name == "git":
            # Git server needs project root mounted
            server_command_list.extend(["-v", f"{PROJECT_ROOT.resolve()}:/workspace"])
            server_command_list.append(server_docker_tag)
            print(f"  Configuring '{server_name}' (Python) with volume mount and default image entrypoint.")
        
        elif language == "python": # For other python servers like time, fetch
            server_command_list.append(server_docker_tag)
            print(f"  Configuring '{server_name}' (Python) with default image entrypoint.")
        
        elif server_name == "filesystem":
            server_command_list.extend([
                "-v", f"{PROJECT_ROOT.resolve()}:/workspace", 
                server_docker_tag,
                "/workspace" # Argument to the filesystem server
            ])
            print(f"  Configuring '{server_name}' with volume mount: {PROJECT_ROOT.resolve()}:/workspace and arg /workspace")
        
        elif server_name == "context7":
            server_command_list.extend([
                "-e", "MCP_TRANSPORT=stdio",
                server_docker_tag
            ])
            print(f"  Configuring '{server_name}' with MCP_TRANSPORT=stdio")
            
        else: # Default for other Node.js servers (memory, sequential-thinking, everything)
            server_command_list.append(server_docker_tag)
            print(f"  Configuring '{server_name}' ({language}) with basic docker run command using image default entrypoint.")

        mcp_servers[server_name] = {
            "command": server_command_list,
            "timeout": 60 if server_name == "sequential-thinking" else 30,
            "enabled": True,
            "description": f"{language.capitalize()} MCP server for {server_name}"
        }

    # Default settings for MCP Manager
    mcp_settings = {
        "defaultTimeout": 40, # Increased default slightly
        "persistentConnections": True,
        "autoDiscovery": True, # Enable capability discovery
        "retryCount": 2,
        "retryDelay": 1.5
    }
    
    config = {
        "mcpSettings": mcp_settings,
        "mcpServers": mcp_servers
    }
    
    # Ensure the .swarmdev directory exists in the user's home
    swarmdev_home_dir = Path.home() / ".swarmdev"
    swarmdev_home_dir.mkdir(exist_ok=True)
    
    config_file_path = swarmdev_home_dir / "mcp_config.json"
    
    try:
        with open(config_file_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"SUCCESS: MCP configuration written to {config_file_path}")
        return True
    except Exception as e:
        print(f"FAILED: Could not write MCP config to {config_file_path}: {e}")
        return False


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


# Helper function to ensure paths are absolute from project root
def ensure_absolute_path(path_str):
    path_obj = Path(path_str)
    if not path_obj.is_absolute():
        return str(PROJECT_ROOT / path_obj)
    return str(path_obj)

# Update server configurations to use absolute paths
def make_paths_absolute_in_config(config):
    for server in config.get("servers", []):
        if "directory" in server:
            server["directory"] = ensure_absolute_path(server["directory"])
        if "docker_build_dir" in server:
            server["docker_build_dir"] = ensure_absolute_path(server["docker_build_dir"])
    return config


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 