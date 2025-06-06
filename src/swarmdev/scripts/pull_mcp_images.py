# scripts/pull_mcp_images.py
import subprocess
import sys
import os
import platform
import shutil

MCP_IMAGES = [
    "ghcr.io/chungoid/everything:latest",
    "ghcr.io/chungoid/fetch:latest",
    "ghcr.io/chungoid/filesystem:latest",
    "ghcr.io/chungoid/git:latest",
    "ghcr.io/chungoid/memory:latest",
    "ghcr.io/chungoid/sequentialthinking:latest",
    "ghcr.io/chungoid/time:latest",

]

def get_real_username():
    """Get the actual login user, not the effective user (which might be root if using sudo)."""
    import getpass
    import os
    
    # Try multiple methods to get the real user
    username = (
        os.environ.get('SUDO_USER') or  # User who ran sudo
        os.environ.get('USER') or       # Current user 
        getpass.getuser()               # Fallback
    )
    return username


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
        
        # Create docker group if it doesn't exist (do this FIRST)
        print("Ensuring docker group exists...")
        try:
            result = subprocess.run(["sudo", "groupadd", "docker"], 
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                print("Docker group created")
            else:
                print("Docker group already exists (this is normal)")
        except Exception as e:
            print(f"Note: Could not create docker group: {e}")
        
        # Add user to docker group BEFORE starting Docker service
        username = get_real_username()
        print(f"Adding user '{username}' to docker group...")
        
        import getpass
        print(f"  User detected: {username}")
        
        try:
            cmd = ["sudo", "usermod", "-aG", "docker", username]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("User added to docker group successfully")
            
            # Verify the user was actually added
            verify_result = subprocess.run(["groups", username], capture_output=True, text=True)
            if verify_result.returncode == 0:
                groups_output = verify_result.stdout.strip()
                if "docker" in groups_output:
                    print(f"✓ Verified: User is now in docker group")
                else:
                    print(f"⚠ Warning: User not showing in docker group after adding")
            
            # Double-check with getent
            getent_result = subprocess.run(["getent", "group", "docker"], capture_output=True, text=True)
            if getent_result.returncode == 0 and username in getent_result.stdout:
                print(f"✓ Confirmed: User found in system docker group")
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to add user to docker group: {e}")
            print(f"  DEBUG: Command failed with return code: {e.returncode}")
            if e.stdout:
                print(f"  DEBUG: Command stdout: '{e.stdout.strip()}'")
            if e.stderr:
                print(f"  DEBUG: Command stderr: '{e.stderr.strip()}'")
            raise e
        
        # Start and enable docker service AFTER adding user to group
        print("Starting Docker service...")
        subprocess.run(["sudo", "systemctl", "start", "docker"], 
                      capture_output=True, text=True, check=True)
        subprocess.run(["sudo", "systemctl", "enable", "docker"], 
                      capture_output=True, text=True, check=True)
        print("Docker service started and enabled")
        
        print("\nDocker installation completed successfully!")
        print("=" * 50)
        
        # Final verification that everything is set up correctly
        print("\nFinal verification:")
        print(f"  DEBUG: Final verification for user '{username}'")
        try:
            # Check Docker service status
            print(f"  DEBUG: Checking Docker service status...")
            service_result = subprocess.run(["sudo", "systemctl", "is-active", "docker"], capture_output=True, text=True)
            print(f"  DEBUG: Docker service check returned code {service_result.returncode}")
            print(f"  DEBUG: Docker service output: '{service_result.stdout.strip()}'")
            if service_result.returncode == 0 and service_result.stdout.strip() == "active":
                print("✓ Docker service is running")
            else:
                print("✗ Docker service is not running")
                
            # Check Docker group exists
            print(f"  DEBUG: Checking if docker group exists...")
            group_check = subprocess.run(["getent", "group", "docker"], capture_output=True, text=True)
            print(f"  DEBUG: getent group docker returned code {group_check.returncode}")
            if group_check.returncode == 0:
                print("✓ Docker group exists")
                # Show group members
                group_info = group_check.stdout.strip()
                print(f"  Group info: {group_info}")
                print(f"  DEBUG: Parsing group members from: '{group_info}'")
                # Parse group info format: groupname:x:gid:member1,member2,member3
                if ':' in group_info:
                    parts = group_info.split(':')
                    if len(parts) >= 4:
                        members = parts[3].strip()
                        print(f"  DEBUG: Group members string: '{members}'")
                        if members:
                            member_list = [m.strip() for m in members.split(',')]
                            print(f"  DEBUG: Group members list: {member_list}")
                            if username in member_list:
                                print(f"  DEBUG: ✓ '{username}' found in parsed member list")
                            else:
                                print(f"  DEBUG: ✗ '{username}' NOT found in parsed member list")
                        else:
                            print(f"  DEBUG: No members in docker group")
            else:
                print("✗ Docker group does not exist")
                print(f"  DEBUG: getent error: '{group_check.stderr.strip()}'")
                
            # Final user group check using multiple methods
            print(f"  DEBUG: Final user group verification...")
            
            # Method 1: groups username
            print(f"  DEBUG: Running 'groups {username}'...")
            final_groups = subprocess.run(["groups", username], capture_output=True, text=True)
            print(f"  DEBUG: 'groups {username}' returned code {final_groups.returncode}")
            if final_groups.returncode == 0:
                groups_list = final_groups.stdout.strip()
                print(f"  DEBUG: 'groups {username}' output: '{groups_list}'")
                if "docker" in groups_list:
                    print(f"✓ User '{username}' is in docker group (via groups command)")
                else:
                    print(f"✗ User '{username}' is NOT in docker group (via groups command)")
                print(f"  All groups: {groups_list}")
            else:
                print(f"  DEBUG: 'groups {username}' failed: '{final_groups.stderr.strip()}'")
            
            # Method 2: id command
            print(f"  DEBUG: Running 'id {username}'...")
            id_result = subprocess.run(["id", username], capture_output=True, text=True)
            print(f"  DEBUG: 'id {username}' returned code {id_result.returncode}")
            if id_result.returncode == 0:
                id_output = id_result.stdout.strip()
                print(f"  DEBUG: 'id {username}' output: '{id_output}'")
                if "docker" in id_output:
                    print(f"  DEBUG: ✓ 'docker' found in id output")
                else:
                    print(f"  DEBUG: ✗ 'docker' NOT found in id output")
            else:
                print(f"  DEBUG: 'id {username}' failed: '{id_result.stderr.strip()}'")
                
        except Exception as e:
            print(f"Could not perform final verification: {e}")
            print(f"  DEBUG: Final verification exception: {type(e).__name__}: {e}")
            import traceback
            print(f"  DEBUG: Traceback: {traceback.format_exc()}")
        
        print("\nIMPORTANT: Group membership changes require a new login session.")
        print("Options to activate Docker group membership:")
        print("  1. Log out and log back in")
        print("  2. Start a new terminal/SSH session")  
        print("  3. Use 'newgrp docker' command")
        print("  4. The script will try 'sg docker' to work around this")
        print("\nFor the most seamless experience, the script can automatically")
        print("activate your docker group membership and continue...")
        
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


def activate_docker_group_and_continue():
    """Provide safe docker group activation guidance for users."""
    username = get_real_username()
    print(f"\nDocker group activation needed for user '{username}'")
    print("=" * 60)
    
    print("Your user was successfully added to the docker group, but your current")
    print("session needs to be refreshed to use the new group membership.")
    print()
    print("REQUIRED: Start a new session with docker group active")
    print("=" * 60)
    print()
    print("SOLUTION: Run this command manually:")
    print(f"   su - {username}")
    print("   swarmdev pull-images")
    print()
    print("This avoids complex session switching and ensures reliable operation.")
    print()
    print("Alternative approaches:")
    print("   • newgrp docker && swarmdev pull-images   (current session)")
    print("   • exit && ssh back in                     (restart terminal)")
    print("   • logout and login                        (console restart)")
    print()
    
    print("Docker installation completed successfully!")
    print("Please manually run one of the options above to download MCP images.")
    
    return False  # Always return False to force manual activation


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
    print("Checking Docker installation and access...")
    
    try:
        # First check if docker command exists
        docker_version_result = subprocess.run(["docker", "--version"], capture_output=True, text=True, check=True)
        print(f"Docker command found: {docker_version_result.stdout.strip()}")
        
        # Then check if we can access Docker daemon
        docker_info_result = subprocess.run(["docker", "info"], capture_output=True, text=True, check=True)
        print("Docker daemon is accessible and running.")
        return True
    except FileNotFoundError:
        print("Error: Docker command not found. Docker needs to be installed.")
        
        # Detect OS and provide installation guidance
        os_type = detect_os()
        print(f"\nDetected OS: {os_type}")
        
        # Ask user if they want automatic installation (only for supported systems)
        if os_type in ["ubuntu", "debian"]:
            print(f"\nAutomatic Docker installation is available for {os_type}.")
            try:
                response = input("Would you like to attempt automatic Docker installation? (Y/n): ").strip().lower()
                # Default to 'yes' if user just presses enter
                if response in ['y', 'yes', '']:
                    print("Starting automatic Docker installation...")
                    if attempt_docker_install(os_type):
                        # Test Docker with new group membership
                        username = get_real_username()
                        
                        print("\nTesting Docker access with group membership...")
                        group_status = test_docker_with_group(username)
                        
                        if group_status:
                            print("Docker is working with group membership!")
                            print("\nProceeding to pull MCP images automatically...")
                            return "docker_installed_continue"  # Special return value
                        else:
                            print("Group membership not yet active in this session.")
                            print("The script can automatically activate docker group and continue.")
                            
                            try:
                                response = input("\nAutomatically activate docker group and continue? (Y/n): ").strip().lower()
                                if response in ['y', 'yes', '']:
                                    return "docker_installed_activate_and_continue"
                                else:
                                    print("Docker is installed but you may need to log out/in for full access.")
                                    print("Trying to continue anyway...")
                                    return "docker_installed_limited"
                            except:
                                print("Could not get user input. Trying to continue with workarounds...")
                                return "docker_installed_limited"
                    else:
                        print("\nAutomatic installation failed. Please install manually.")
                        return False
                else:
                    print("Skipping automatic installation.")
            except KeyboardInterrupt:
                print("\nInstallation cancelled.")
                return False
            except Exception as e:
                print(f"\nCould not get user input: {e}. Attempting automatic installation...")
                # If we can't get input, try to install automatically
                if attempt_docker_install(os_type):
                    return "docker_installed_continue"
                else:
                    print("Automatic installation failed.")
        
        # Show manual installation instructions
        instructions = get_docker_install_instructions(os_type)
        print(instructions)
        
        return False
    except subprocess.CalledProcessError as e:
        print("Error: Docker command found, but Docker daemon might not be running or accessible.")
        print("   Please ensure Docker is started and you have permissions to access it.")
        
        # Check if it's a group membership issue
        username = get_real_username()
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
    
    # Check if image already exists locally
    try:
        if use_group_command:
            username = get_real_username()
            check_result = run_docker_command_with_group(["images", "-q", image_uri], username)
            image_exists = check_result.returncode == 0 and check_result.stdout.strip()
        else:
            check_result = subprocess.run(["docker", "images", "-q", image_uri], 
                                        capture_output=True, text=True, timeout=10)
            image_exists = check_result.returncode == 0 and check_result.stdout.strip()
        
        if image_exists:
            print(f"Image {image_uri} already exists locally - skipping download")
            return True
    except Exception as e:
        print(f"Could not check if image exists (proceeding with pull): {e}")
    
    try:
        if use_group_command:
            # Try with group command first
            username = get_real_username()
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
    elif docker_status == "docker_installed_continue":
        print("Docker was just installed. Continuing with image downloads...")
    elif docker_status == "docker_installed_limited":
        print("Docker was just installed. Continuing with image downloads...")
    elif docker_status == "docker_installed_activate_and_continue":
        print("Docker was just installed. Group activation required...")
        activate_docker_group_and_continue()
        # Always exit after installation to prevent double execution
        sys.exit(0)
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
    use_group = docker_status in ["docker_installed_limited"]
    
    # If we activated the group successfully, docker should work normally
    if docker_status == "docker_installed_activate_and_continue":
        # Test if docker works directly now
        try:
            test_result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
            if test_result.returncode == 0:
                print("✓ Docker is now working directly (no workarounds needed)")
                use_group = False
            else:
                print("⚠ Docker still needs group workarounds")
                use_group = True
        except:
            print("⚠ Could not test docker directly, using group workarounds")
            use_group = True
    
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