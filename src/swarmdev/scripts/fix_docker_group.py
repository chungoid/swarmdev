#!/usr/bin/env python3
"""
fix_docker_group.py - Fix Docker group membership issues

This script helps fix common Docker group membership problems that prevent
MCP containers from running properly.
"""

import subprocess
import sys
import os
import getpass


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


def check_current_groups():
    """Check current user's group membership."""
    username = get_real_username()
    print(f"Checking groups for user: {username}")
    
    try:
        # Check CURRENT session groups vs file groups
        current_session_result = subprocess.run(["groups"], capture_output=True, text=True)
        file_result = subprocess.run(["groups", username], capture_output=True, text=True)
        
        if current_session_result.returncode == 0 and file_result.returncode == 0:
            current_groups = current_session_result.stdout.strip()
            file_groups = file_result.stdout.strip()
            
            print(f"Current session groups: {current_groups}")
            print(f"File system groups: {file_groups}")
            
            session_has_docker = "docker" in current_groups
            file_has_docker = "docker" in file_groups
            
            if session_has_docker:
                print("✓ User is in docker group (current session)")
                return True
            elif file_has_docker and not session_has_docker:
                print("⚠ User is in docker group in /etc/group but NOT in current session")
                print("  Group membership hasn't taken effect in this session yet")
                return "file_only"  # Special return value
            else:
                print("✗ User is NOT in docker group")
                return False
        else:
            print(f"Failed to check groups")
            return False
    except Exception as e:
        print(f"Error checking groups: {e}")
        return False


def test_docker_access():
    """Test if Docker is accessible."""
    print("\nTesting Docker access...")
    
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ Docker is accessible")
            return True
        else:
            print("✗ Docker is not accessible")
            if "permission denied" in result.stderr.lower():
                print("  → Permission denied error detected")
            elif "cannot connect" in result.stderr.lower():
                print("  → Cannot connect to Docker daemon")
            return False
    except subprocess.TimeoutExpired:
        print("✗ Docker command timed out")
        return False
    except Exception as e:
        print(f"✗ Error testing Docker: {e}")
        return False


def fix_docker_group():
    """Add user to docker group."""
    username = get_real_username()
    print(f"\nAdding user '{username}' to docker group...")
    
    try:
        # Add user to docker group
        result = subprocess.run(
            ["sudo", "usermod", "-aG", "docker", username],
            capture_output=True, text=True, check=True
        )
        print("✓ User added to docker group successfully")
        
        # Create docker group if it doesn't exist (shouldn't be needed, but just in case)
        subprocess.run(["sudo", "groupadd", "docker"], 
                      capture_output=True, text=True, check=False)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to add user to docker group: {e}")
        if e.stderr:
            print(f"  Error: {e.stderr.strip()}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_group_workarounds():
    """Test workarounds for group membership in current session."""
    print("\nTesting group membership workarounds...")
    
    approaches = [
        (["sg", "docker", "-c", "docker info >/dev/null 2>&1"], "sg (switch group)"),
        (["sudo", "-g", "docker", "docker", "info"], "sudo -g docker"),
        (["bash", "-c", "newgrp docker && docker info >/dev/null 2>&1"], "newgrp")
    ]
    
    working_method = None
    for cmd, method in approaches:
        try:
            print(f"  Testing {method}...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"  ✓ {method} works!")
                working_method = method
                break
            else:
                print(f"  ✗ {method} failed (code: {result.returncode})")
        except Exception as e:
            print(f"  ✗ {method} error: {e}")
    
    return working_method


def main():
    print("Docker Group Membership Fix Tool")
    print("=" * 40)
    
    # Step 1: Check current group membership
    group_status = check_current_groups()
    
    # Step 2: Test Docker access
    docker_works = test_docker_access()
    
    if docker_works:
        print("\n✓ Docker is working properly!")
        print("No fix needed.")
        return
    
    if group_status == "file_only":
        print(f"\nProblem identified: User is in docker group but session not updated")
        print(f"No need to add to group - just need to refresh session")
        working_method = test_group_workarounds()
        
        if working_method:
            print(f"\n✓ Found working method: {working_method}")
            print(f"SwarmDev should be able to use Docker now.")
        else:
            print(f"\n✗ No workarounds successful in current session.")
            print(f"\nTo fully activate docker group membership:")
            print(f"  1. Log out and log back in")
            print(f"  2. Or start a new terminal/SSH session")
            print(f"  3. Or run: newgrp docker")
            print(f"\nThen try: swarmdev pull-images")
        return
        
    if not group_status:
        print(f"\nProblem identified: User is not in docker group")
        
        try:
            response = input("\nWould you like to add the user to docker group? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                if fix_docker_group():
                    print("\n✓ User added to docker group!")
                    group_status = True
                else:
                    print("\n✗ Failed to add user to docker group")
                    print("You may need to run this manually:")
                    print(f"  sudo usermod -aG docker {get_real_username()}")
                    sys.exit(1)
            else:
                print("Skipping group addition.")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(1)
    
    # Step 3: Test workarounds for current session
    if group_status:
        print(f"\nUser is now in docker group, but group membership")
        print(f"changes don't take effect until a new login session.")
        
        working_method = test_group_workarounds()
        
        if working_method:
            print(f"\n✓ Found working method: {working_method}")
            print(f"SwarmDev should be able to use Docker now.")
        else:
            print(f"\n✗ No workarounds successful in current session.")
            print(f"\nTo fully activate docker group membership:")
            print(f"  1. Log out and log back in")
            print(f"  2. Or start a new terminal/SSH session")
            print(f"  3. Or run: newgrp docker")
            print(f"\nThen try: swarmdev pull-images")
    
    print(f"\nFix attempt completed!")


if __name__ == "__main__":
    main() 