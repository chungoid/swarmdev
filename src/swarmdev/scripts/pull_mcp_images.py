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
    
    print("Attempting to install Docker automatically...")
    try:
        # Update package list
        subprocess.run(["sudo", "apt", "update"], check=True)
        
        # Install docker.io
        subprocess.run(["sudo", "apt", "install", "-y", "docker.io"], check=True)
        
        # Start and enable docker
        subprocess.run(["sudo", "systemctl", "start", "docker"], check=True)
        subprocess.run(["sudo", "systemctl", "enable", "docker"], check=True)
        
        # Add user to docker group
        import getpass
        username = getpass.getuser()
        subprocess.run(["sudo", "usermod", "-aG", "docker", username], check=True)
        
        print("Docker installed successfully!")
        print("Note: You may need to log out and back in for group changes to take effect.")
        print("For now, trying to continue...")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Docker automatically: {e}")
        return False
    except Exception as e:
        print(f"Error during Docker installation: {e}")
        return False


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
                        # Try Docker check again after installation
                        print("\nRechecking Docker status...")
                        return check_docker()
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


def pull_image(image_uri: str) -> bool:
    """Pulls a single Docker image."""
    print(f"Pulling {image_uri}...")
    try:
        # Stream output for better user experience
        process = subprocess.Popen(["docker", "pull", image_uri], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)
        
        # Print stdout line by line
        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                print(f"   {line.strip()}")
            process.stdout.close()

        return_code = process.wait() # Wait for the process to complete

        if return_code == 0:
            print(f"Successfully pulled {image_uri}")
            return True
        else:
            print(f"Failed to pull {image_uri}. Return code: {return_code}")
            # Stderr would have been mixed if Popen redirected stderr=subprocess.STDOUT
            # If stderr was separate, you could read it here, but for pull it often goes to stdout
            # For simplicity, the live printing above should show errors.
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


    if not check_docker():
        print("\\nDocker setup required. Please follow the instructions above and try again.")
        print("After installing Docker, run: swarmdev pull-images")
        sys.exit(1)

    print(f"\\nFound {len(MCP_IMAGES)} MCP images to pull.")
    all_successful = True
    for image in MCP_IMAGES:
        if not pull_image(image):
            all_successful = False

    if all_successful:
        print("\\nAll MCP Docker images pulled successfully!")
    else:
        print("\\nSome images could not be pulled. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    # Need pathlib for this relative path logic to work if script is called from elsewhere
    # Pathlib is not used in the main script body anymore, so removing the import for now.
    # from pathlib import Path 
    main() 