# scripts/pull_mcp_images.py
import subprocess
import sys
import os
import platform
import shutil

MCP_IMAGES = [
    "ghcr.io/chungoid/context7:v0.1.1-context7",
    "ghcr.io/chungoid/fetch:v0.3.6",
    "ghcr.io/chungoid/memory:v0.3.6",
    "ghcr.io/chungoid/git:v0.3.6",
    "ghcr.io/chungoid/filesystem:v0.3.6",
    "ghcr.io/chungoid/sequentialthinking:v0.3.6",
    "ghcr.io/chungoid/time:v0.3.6",
]

def detect_os():
    """Detect the operating system and distribution."""
    system = platform.system().lower()
    
    if system == "linux":
        # Try to detect Linux distribution
        try:
            with open('/etc/os-release', 'r') as f:
                os_release = f.read().lower()
                if 'ubuntu' in os_release:
                    return "ubuntu"
                elif 'debian' in os_release:
                    return "debian"
                elif 'fedora' in os_release:
                    return "fedora"
                elif 'centos' in os_release or 'rhel' in os_release:
                    return "centos"
                elif 'arch' in os_release:
                    return "arch"
                else:
                    return "linux"
        except:
            return "linux"
    elif system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    else:
        return "unknown"


def get_docker_install_instructions(os_type):
    """Get Docker installation instructions for the detected OS."""
    instructions = {
        "ubuntu": """
Docker Installation for Ubuntu/Debian:

Option 1 - Quick Install (Recommended for test servers):
  sudo apt update
  sudo apt install docker.io
  sudo systemctl start docker
  sudo systemctl enable docker
  sudo usermod -aG docker $USER
  newgrp docker

Option 2 - Latest Docker CE:
  # Remove old packages
  sudo apt remove docker docker-engine docker.io containerd runc
  
  # Install prerequisites
  sudo apt update
  sudo apt install ca-certificates curl gnupg lsb-release
  
  # Add Docker repository
  sudo mkdir -p /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  
  # Install Docker
  sudo apt update
  sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin
  sudo usermod -aG docker $USER
  newgrp docker
""",
        "debian": """
Docker Installation for Debian:
  sudo apt update
  sudo apt install docker.io
  sudo systemctl start docker
  sudo systemctl enable docker
  sudo usermod -aG docker $USER
  newgrp docker
""",
        "fedora": """
Docker Installation for Fedora:
  sudo dnf install docker
  sudo systemctl start docker
  sudo systemctl enable docker
  sudo usermod -aG docker $USER
  newgrp docker
""",
        "centos": """
Docker Installation for CentOS/RHEL:
  sudo yum install docker
  sudo systemctl start docker
  sudo systemctl enable docker
  sudo usermod -aG docker $USER
  newgrp docker
""",
        "arch": """
Docker Installation for Arch Linux:
  sudo pacman -S docker
  sudo systemctl start docker
  sudo systemctl enable docker
  sudo usermod -aG docker $USER
  newgrp docker
""",
        "macos": """
Docker Installation for macOS:
  1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop
  2. Install the .dmg file
  3. Start Docker Desktop from Applications
""",
        "windows": """
Docker Installation for Windows:
  1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop
  2. Install the installer
  3. Start Docker Desktop
""",
        "linux": """
Docker Installation (Generic Linux):
  Please check your distribution's package manager:
  - For apt-based (Ubuntu/Debian): sudo apt install docker.io
  - For yum-based (CentOS/RHEL): sudo yum install docker
  - For dnf-based (Fedora): sudo dnf install docker
  - For pacman-based (Arch): sudo pacman -S docker
""",
        "unknown": """
Docker Installation:
  Please visit https://docs.docker.com/get-docker/ for installation instructions
  specific to your operating system.
"""
    }
    return instructions.get(os_type, instructions["unknown"])


def attempt_docker_install(os_type):
    """Attempt to automatically install Docker on supported systems."""
    if os_type not in ["ubuntu", "debian"]:
        return False
    
    print("\nInstalling Docker automatically...")
    print("=" * 50)
    
    try:
        # Update package list
        print("Updating package list...")
        result = subprocess.run(["sudo", "apt", "update"], 
                              capture_output=True, text=True, check=True)
        print("Package list updated successfully")
        
        # Install docker.io
        print("Installing Docker...")
        result = subprocess.run(["sudo", "apt", "install", "-y", "docker.io"], 
                              capture_output=True, text=True, check=True)
        print("Docker installed successfully")
        
        # Start and enable docker
        print("Starting Docker service...")
        subprocess.run(["sudo", "systemctl", "start", "docker"], 
                      capture_output=True, text=True, check=True)
        subprocess.run(["sudo", "systemctl", "enable", "docker"], 
                      capture_output=True, text=True, check=True)
        print("Docker service started and enabled")
        
        # Add user to docker group
        import getpass
        username = getpass.getuser()
        print(f"Adding user '{username}' to docker group...")
        subprocess.run(["sudo", "usermod", "-aG", "docker", username], 
                      capture_output=True, text=True, check=True)
        print("User added to docker group successfully")
        
        # Create docker group if it doesn't exist (edge case)
        try:
            subprocess.run(["sudo", "groupadd", "docker"], 
                          capture_output=True, text=True, check=False)
        except:
            pass  # Group already exists, which is fine
        
        print("\nDocker installation completed successfully!")
        print("=" * 50)
        print("\nIMPORTANT: Group membership changes require a new login session.")
        print("Options to activate Docker group membership:")
        print("  1. Log out and log back in")
        print("  2. Start a new terminal/SSH session")  
        print("  3. Use 'newgrp docker' command")
        print("  4. The script will try 'sg docker' to work around this")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Docker automatically: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr.strip()}")
        return False
    except Exception as e:
        print(f"Error during Docker installation: {e}")
        return False


def test_docker_with_group(username):
    """Test if Docker works with the user's group membership."""
    # Check ACTUAL current session group membership (not just /etc/group file)
    try:
        # Use 'groups' without username to get CURRENT session groups
        current_session_result = subprocess.run(["groups"], capture_output=True, text=True)
        # Also check what /etc/group says
        file_result = subprocess.run(["groups", username], capture_output=True, text=True)
        
        current_session_groups = current_session_result.stdout.strip() if current_session_result.returncode == 0 else ""
        file_groups = file_result.stdout.strip() if file_result.returncode == 0 else ""
        
        print(f"Checking group membership for user: {username}")
        print(f"  Current session groups: {current_session_groups}")
        print(f"  File system groups: {file_groups}")
        
        # Check if docker group is in current session (what matters for Docker access)
        session_has_docker = "docker" in current_session_groups
        file_has_docker = "docker" in file_groups
        
        if session_has_docker:
            print(f"✓ User '{username}' has docker group in current session")
            return True
        elif file_has_docker and not session_has_docker:
            print(f"⚠ User '{username}' is in docker group in /etc/group but NOT in current session")
            print(f"  This means group membership hasn't taken effect yet")
            print(f"  Need to log out/in or use 'newgrp docker' or 'sg docker'")
            return False
        else:
            print(f"✗ User '{username}' is NOT in docker group")
            return False
    except Exception as e:
        print(f"Could not check group membership: {e}")
        return False
    
    # Test different approaches to run docker
    approaches = [
        # Method 1: Use sg to switch to docker group
        (["sg", "docker", "-c", "docker info >/dev/null 2>&1"], "sg (switch group)"),
        # Method 2: Use newgrp in a subshell  
        (["bash", "-c", "newgrp docker && docker info >/dev/null 2>&1"], "newgrp"),
        # Method 3: Direct docker command (might work if already in group)
        (["docker", "info"], "direct")
    ]
    
    for cmd, method in approaches:
        try:
            print(f"  Testing Docker access with {method}...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"  ✓ Docker working with {method}")
                return True
            else:
                print(f"  ✗ Docker failed with {method} (code: {result.returncode})")
                if result.stderr and "permission denied" in result.stderr.lower():
                    print(f"    Permission denied error detected")
        except subprocess.TimeoutExpired:
            print(f"  ✗ Docker command timed out with {method}")
        except Exception as e:
            print(f"  ✗ Exception with {method}: {e}")
    
    return False


def run_docker_command_with_group(cmd_args, username):
    """Run a docker command with proper group context."""
    # Try multiple approaches in order of preference
    approaches = [
        # Method 1: sg (switch group) - most reliable
        (["sg", "docker", "-c", " ".join(["docker"] + cmd_args)], "sg"),
        # Method 2: sudo with group specification
        (["sudo", "-g", "docker", "docker"] + cmd_args, "sudo -g"),
        # Method 3: Direct docker (fallback)
        (["docker"] + cmd_args, "direct")
    ]
    
    for cmd, method in approaches:
        try:
            print(f"  Trying {method} method...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"  ✓ Success with {method}")
                return result
            else:
                print(f"  ✗ Failed with {method} (code: {result.returncode})")
                if result.stderr:
                    print(f"    Error: {result.stderr.strip()[:100]}...")
        except Exception as e:
            print(f"  ✗ Exception with {method}: {e}")
    
    # All methods failed
    print("  All Docker execution methods failed!")
    print("  You may need to:")
    print("    1. Log out and log back in to refresh group membership")
    print("    2. Or run: newgrp docker")
    print("    3. Or restart your terminal/SSH session")
    
    # Return the last result for error reporting
    return result


def check_docker():
    """Checks if Docker is installed and running, with installation guidance."""
    try:
        # Use a DEVNULL to prevent 'docker info' from printing to console on success
        with open(os.devnull, 'w') as devnull:
            subprocess.run(["docker", "info"], stdout=devnull, stderr=devnull, check=True)
        print("Docker is installed and seems to be running.")
        return True
    except FileNotFoundError:
        print("Error: Docker command not found. Docker needs to be installed.")
        
        # Detect OS and provide installation guidance
        os_type = detect_os()
        print(f"\nDetected OS: {os_type}")
        
        # Ask user if they want automatic installation (only for supported systems)
        if os_type in ["ubuntu", "debian"]:
            try:
                response = input("\nWould you like to attempt automatic Docker installation? (y/N): ").strip().lower()
                if response in ['y', 'yes']:
                    if attempt_docker_install(os_type):
                        # Test Docker with new group membership
                        import getpass
                        username = getpass.getuser()
                        
                        print("\nTesting Docker access with group membership...")
                        if test_docker_with_group(username):
                            print("Docker is working with group membership!")
                            print("\nProceeding to pull MCP images automatically...")
                            return "docker_installed_continue"  # Special return value
                        else:
                            print("Group membership not yet active in this session.")
                            print("Docker is installed but you may need to log out/in for full access.")
                            print("Trying to continue anyway...")
                            return "docker_installed_limited"  # Try to continue with limited access
                    else:
                        print("\nAutomatic installation failed. Please install manually.")
            except KeyboardInterrupt:
                print("\nInstallation cancelled.")
            except:
                print("\nCould not get user input. Showing manual instructions.")
        
        # Show manual installation instructions
        instructions = get_docker_install_instructions(os_type)
        print(instructions)
        
        return False
    except subprocess.CalledProcessError as e:
        print("Error: Docker command found, but Docker daemon might not be running or accessible.")
        print("   Please ensure Docker is started and you have permissions to access it.")
        
        # Check if it's a group membership issue
        import getpass
        username = getpass.getuser()
        try:
            # Check CURRENT session groups vs file groups
            current_session_result = subprocess.run(["groups"], capture_output=True, text=True)
            file_result = subprocess.run(["groups", username], capture_output=True, text=True)
            
            if current_session_result.returncode == 0 and file_result.returncode == 0:
                current_groups = current_session_result.stdout.strip()
                file_groups = file_result.stdout.strip()
                
                session_has_docker = "docker" in current_groups
                file_has_docker = "docker" in file_groups
                
                if not session_has_docker and not file_has_docker:
                    print(f"\n   DETECTED ISSUE: User '{username}' is not in 'docker' group.")
                    print(f"   Current session groups: {current_groups}")
                    print(f"   File system groups: {file_groups}")
                    print("\n   TO FIX THIS:")
                    print("   1. Add user to docker group: sudo usermod -aG docker $USER")
                    print("   2. Then either:")
                    print("      - Log out and log back in")
                    print("      - Run: newgrp docker")
                    print("      - Start a new terminal session")
                    print("   3. Then re-run: swarmdev pull-images")
                    return "group_fix_needed"
                elif file_has_docker and not session_has_docker:
                    print(f"\n   DETECTED ISSUE: User '{username}' is in docker group but session not updated.")
                    print(f"   Current session groups: {current_groups}")
                    print(f"   File system groups: {file_groups}")
                    print("\n   TO FIX THIS:")
                    print("   1. The user is already in docker group, but current session needs refresh")
                    print("   2. Either:")
                    print("      - Log out and log back in")
                    print("      - Run: newgrp docker")
                    print("      - Start a new terminal session")
                    print("   3. Then re-run: swarmdev pull-images")
                    return "group_fix_needed"
                else:
                    print(f"   User '{username}' is in docker group (session): {current_groups}")
                    print(f"   But Docker daemon seems inaccessible - check if Docker is running")
        except:
            pass
        
        # Attempt to get more specific error from docker info if possible, without printing full output
        try:
            result = subprocess.run(["docker", "info"], capture_output=True, text=True, check=False)
            if result.stderr:
                # Try to find common error messages
                if "permission denied" in result.stderr.lower():
                    print("   Hint: You might need to run Docker commands with sudo or add your user to the 'docker' group.")
                    print("   Try: sudo usermod -aG docker $USER && newgrp docker")
                elif "cannot connect to the docker daemon" in result.stderr.lower():
                    print("   Hint: The Docker daemon does not seem to be running.")
                    print("   Try: sudo systemctl start docker")
                else:
                    # Print a snippet if not a common known one, to avoid too much spam
                    error_snippet = result.stderr.strip().split('\\n')[0]
                    print(f"   Docker info error snippet: {error_snippet}")
        except Exception:
            pass # Ignore if we can't get more details
        return False
    except Exception as e:
        print(f"An unexpected error occurred while checking Docker status: {e}")
        return False


def pull_image(image_uri: str, use_group_command: bool = False) -> bool:
    """Pulls a single Docker image."""
    print(f"Pulling {image_uri}...")
    try:
        if use_group_command:
            # Try with group command first
            import getpass
            username = getpass.getuser()
            result = run_docker_command_with_group(["pull", image_uri], username)
            
            if result.returncode == 0:
                print(f"Successfully pulled {image_uri}")
                return True
            else:
                print(f"Failed to pull {image_uri} with group command. Return code: {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr.strip()}")
                return False
        else:
            # Stream output for better user experience
            process = subprocess.Popen(["docker", "pull", image_uri], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)
            
            # Print stdout line by line
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    if line.strip():  # Only print non-empty lines
                        print(f"  {line.strip()}")
                process.stdout.close()

            return_code = process.wait() # Wait for the process to complete

            if return_code == 0:
                print(f"Successfully pulled {image_uri}")
                return True
            else:
                print(f"Failed to pull {image_uri}. Return code: {return_code}")
                return False
            
    except FileNotFoundError:
        print("Error: Docker command not found during pull. This should not happen if check_docker passed.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while pulling {image_uri}: {e}")
        return False

def main():
    print("--- MCP Docker Image Setup ---")
    
    # This script is now in src/swarmdev/scripts/
    # To get to the swarmdev_root (project root), we need to go up two levels.
    script_file_path = os.path.abspath(__file__) # <workspace>/src/swarmdev/scripts/pull_mcp_images.py
    scripts_dir = os.path.dirname(script_file_path)   # <workspace>/src/swarmdev/scripts
    src_swarmdev_dir = os.path.dirname(scripts_dir) # <workspace>/src/swarmdev
    swarmdev_root = os.path.dirname(src_swarmdev_dir) # <workspace>
    
    # It's generally better for scripts invoked by a CLI at the project root
    # to operate relative to the CWD set by the CLI, or to be explicit.
    # The pull_mcp_images.py script itself doesn't need to change CWD if invoked correctly.
    # However, the original `os.chdir` was to `scripts_dir.parent`, which if `scripts_dir` was root `scripts/`,
    # it would `chdir` to the project root.
    # Let's remove the chdir from this script, assuming it's called with CWD at project root.
    # print(f"Current working directory: {os.getcwd()}")


    docker_status = check_docker()
    if docker_status == True:
        print("Docker is ready.")
    elif docker_status in ["docker_installed_continue", "docker_installed_limited"]:
        print("Docker was just installed. Continuing with image downloads...")
    elif docker_status == "group_fix_needed":
        print("\nDocker group membership issue detected.")
        print("Please follow the fix instructions above and then re-run: swarmdev pull-images")
        sys.exit(1)
    else:
        print("\nDocker setup required. Please follow the instructions above and try again.")
        print("After installing Docker, run: swarmdev pull-images")
        sys.exit(1)

    print(f"\nFound {len(MCP_IMAGES)} MCP images to pull.")
    
    # Determine if we should use group commands
    use_group = docker_status in ["docker_installed_continue", "docker_installed_limited"]
    
    all_successful = True
    for i, image in enumerate(MCP_IMAGES, 1):
        print(f"\n[{i}/{len(MCP_IMAGES)}] {image}")
        if not pull_image(image, use_group_command=use_group):
            all_successful = False

    if all_successful:
        print("\nAll MCP Docker images pulled successfully!")
        print("Setup complete! You can now use SwarmDev with MCP tools.")
    else:
        print("\nSome images could not be pulled. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    # Need pathlib for this relative path logic to work if script is called from elsewhere
    # Pathlib is not used in the main script body anymore, so removing the import for now.
    # from pathlib import Path 
    main() 