#!/usr/bin/env python3
"""
SwarmDev MCP Server Setup Script

Automatically installs and configures official MCP servers for enhanced agent capabilities.
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path


def install_pip_servers():
    """Install pip-installable MCP servers."""
    servers = [
        "mcp-server-git",
        "mcp-server-time", 
        "mcp-server-fetch"
    ]
    
    print("Installing official MCP servers...")
    for server in servers:
        try:
            print(f"  Installing {server}...")
            subprocess.run([sys.executable, "-m", "pip", "install", server], 
                         check=True, capture_output=True)
            print(f"  SUCCESS: {server} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"  ERROR: Failed to install {server}: {e}")


def build_docker_servers():
    """Build Docker images for TypeScript MCP servers."""
    bundled_servers = [
        "sequential-thinking",
        "memory",
        "context7"
    ]
    
    print("Building Docker images for bundled MCP servers...")
    
    # Get the SwarmDev package directory
    package_dir = Path(__file__).parent.parent / "src" / "swarmdev" / "bundled_mcp"
    
    for server in bundled_servers:
        server_dir = package_dir / server
        
        if not server_dir.exists():
            print(f"  ERROR: Server directory not found: {server_dir}")
            continue
            
        print(f"  Building Docker image for {server}...")
        
        try:
            # Build the Docker image - use context7-mcp for context7, swarmdev-mcp-* for others
            if server == "context7":
                image_name = "context7-mcp:latest"
            else:
                image_name = f"swarmdev-mcp-{server}:latest"
            
            subprocess.run([
                "docker", "build", 
                "-t", image_name,
                str(server_dir)
            ], check=True, capture_output=True, text=True)
            
            print(f"  SUCCESS: Built Docker image {image_name}")
            
        except subprocess.CalledProcessError as e:
            print(f"  ERROR: Failed to build {server} Docker image")
            print(f"         stdout: {e.stdout if e.stdout else 'None'}")
            print(f"         stderr: {e.stderr if e.stderr else 'None'}")
        except FileNotFoundError:
            print(f"  ERROR: Docker not found. Please install Docker to use bundled servers.")
            return False
    
    return True


def create_enhanced_config():
    """Create enhanced MCP configuration with all servers."""
    config_template = {
        "mcpServers": {
            "git": {
                "command": "python",
                "args": ["-m", "mcp_server_git"],
                "capabilities": ["git_operations", "repository_analysis"],
                "description": "Git repository operations and analysis"
            },
            "time": {
                "command": "python",
                "args": ["-m", "mcp_server_time"],
                "capabilities": ["time_operations", "scheduling"],
                "description": "System time and scheduling operations"
            },
            "fetch": {
                "command": "python",
                "args": ["-m", "mcp_server_fetch"],
                "capabilities": ["web_requests", "documentation_lookup"],
                "description": "Web requests and online research"
            },
            "sequential-thinking": {
                "command": "docker",
                "args": ["run", "--rm", "-i", "swarmdev-mcp-sequential-thinking:latest"],
                "capabilities": ["reasoning", "problem_solving"],
                "description": "Advanced reasoning and sequential thinking"
            },
            "memory": {
                "command": "docker",
                "args": ["run", "--rm", "-i", "swarmdev-mcp-memory:latest"],
                "capabilities": ["memory", "context_persistence"],
                "description": "Persistent agent memory and context"
            },
            "context7": {
                "command": "docker",
                "args": ["run", "--rm", "-i", "context7-mcp:latest"],
                "capabilities": ["documentation", "library_docs", "api_reference"],
                "description": "Up-to-date documentation for libraries and frameworks"
            }
        },
        "settings": {
            "auto_install_pip_servers": True,
            "enable_official_servers": True,
            "docker_build_bundled": True,
            "default_timeout": 30,
            "retry_attempts": 3
        }
    }
    
    # Create both user and project configs
    configs_to_create = [
        (Path.home() / ".swarmdev" / "mcp_config.json", "Global user config"),
        (Path("./examples/mcp_config_complete.json"), "Project template config")
    ]
    
    for config_path, description in configs_to_create:
        config_path.parent.mkdir(exist_ok=True, parents=True)
        
        if not config_path.exists():
            print(f"Creating {description.lower()}...")
            with open(config_path, "w") as f:
                json.dump(config_template, f, indent=2)
            print(f"  SUCCESS: Config created at {config_path}")
        else:
            print(f"  INFO: Config already exists at {config_path}")


def verify_installation():
    """Verify that all components are properly installed."""
    print("Verifying installation...")
    
    # Check pip servers
    pip_servers = ["mcp-server-git", "mcp-server-time", "mcp-server-fetch"]
    for server in pip_servers:
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "show", server], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  SUCCESS: {server} is installed")
            else:
                print(f"  WARNING: {server} not found")
        except Exception as e:
            print(f"  ERROR: Could not verify {server}: {e}")
    
    # Check Docker images
    docker_images = ["swarmdev-mcp-sequential-thinking:latest", "swarmdev-mcp-memory:latest", "context7-mcp:latest"]
    for image in docker_images:
        try:
            result = subprocess.run(["docker", "images", "-q", image], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                print(f"  SUCCESS: Docker image {image} is available")
            else:
                print(f"  WARNING: Docker image {image} not found")
        except Exception as e:
            print(f"  ERROR: Could not verify Docker image {image}: {e}")


def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")
    
    missing_deps = []
    
    # Check for python (should always be available since we're running this script)
    if shutil.which("python") or shutil.which("python3"):
        print("  SUCCESS: Python found")
    else:
        print("  WARNING: Python not found")
        missing_deps.append("python")
    
    # Check for docker
    if not shutil.which("docker"):
        print("  WARNING: Docker not found. Please install Docker for bundled servers.")
        missing_deps.append("docker")
    else:
        print("  SUCCESS: Docker found")
        
        # Check if Docker daemon is running
        try:
            subprocess.run(["docker", "info"], capture_output=True, check=True)
            print("  SUCCESS: Docker daemon is running")
        except subprocess.CalledProcessError:
            print("  WARNING: Docker daemon is not running")
            missing_deps.append("docker-daemon")
    
    return len(missing_deps) == 0, missing_deps


def main():
    """Main setup function."""
    print("SwarmDev MCP Server Setup")
    print("=" * 40)
    
    # Check dependencies
    deps_ok, missing_deps = check_dependencies()
    if not deps_ok:
        print(f"WARNING: Missing dependencies: {', '.join(missing_deps)}")
        print("Some features may not work properly.")
        print()
    
    try:
        # Install pip servers
        install_pip_servers()
        print()
        
        # Build Docker servers (if Docker is available)
        if "docker" not in missing_deps and "docker-daemon" not in missing_deps:
            docker_success = build_docker_servers()
            print()
        else:
            print("Skipping Docker server builds due to missing Docker")
            docker_success = False
            print()
        
        # Create enhanced configuration
        create_enhanced_config()
        print()
        
        # Verify installation
        verify_installation()
        print()
        
        print("Setup complete!")
        print("\nSwarmDev MCP servers available:")
        print("  • git - Repository analysis and operations")
        print("  • time - System time and scheduling")
        print("  • fetch - Web requests and research")
        
        if docker_success:
            print("  • sequential-thinking - Advanced reasoning (Docker)")
            print("  • memory - Persistent context (Docker)")
            print("  • context7 - Up-to-date library documentation (Docker)")
        else:
            print("  • sequential-thinking - NOT AVAILABLE (Docker required)")
            print("  • memory - NOT AVAILABLE (Docker required)")
            print("  • context7 - NOT AVAILABLE (Docker required)")
        
        print("\nNext steps:")
        print("  1. Configure your project with enhanced MCP capabilities")
        print("  2. The agents will automatically use these enhanced capabilities!")
        print("  3. Check examples/mcp_config_complete.json for full configuration")
        
        if not deps_ok:
            print(f"\nNOTE: Install missing dependencies for full functionality:")
            for dep in missing_deps:
                if dep == "python":
                    print(f"  Install Python from https://python.org")
                elif dep == "docker":
                    print(f"  Install Docker from https://docker.com")
                elif dep == "docker-daemon":
                    print(f"  Start Docker daemon")
        
        return 0
        
    except Exception as e:
        print(f"ERROR: Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 