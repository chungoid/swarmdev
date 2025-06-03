# scripts/pull_mcp_images.py
import subprocess
import sys
import os

MCP_IMAGES = [
    "ghcr.io/chungoid/context7:v0.1.1-context7",
    "ghcr.io/chungoid/fetch:v0.3.6",
    "ghcr.io/chungoid/memory:v0.3.6",
    "ghcr.io/chungoid/git:v0.3.6",
    "ghcr.io/chungoid/filesystem:v0.3.6",
    "ghcr.io/chungoid/sequentialthinking:v0.3.6",
    "ghcr.io/chungoid/time:v0.3.6",
]

def check_docker():
    """Checks if Docker is installed and running."""
    try:
        # Use a DEVNULL to prevent 'docker info' from printing to console on success
        with open(os.devnull, 'w') as devnull:
            subprocess.run(["docker", "info"], stdout=devnull, stderr=devnull, check=True)
        print("Docker is installed and seems to be running.")
        return True
    except FileNotFoundError:
        print("Error: Docker command not found. Please install Docker.")
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
                elif "cannot connect to the docker daemon" in result.stderr.lower():
                    print("   Hint: The Docker daemon does not seem to be running.")
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
        print("\\nPlease resolve Docker issues and try again.")
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