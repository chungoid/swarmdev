#!/usr/bin/env python3
"""
SwarmDev CLI wrapper.
 
This script is a simple wrapper that calls the main CLI module.
For the full CLI functionality, use the 'swarmdev' command or import swarmdev.cli directly.
"""

import sys
import os

# Ensure the package is in the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    try:
        from swarmdev.cli import main
        main()
    except ImportError as e:
        print(f"Error: Could not import SwarmDev CLI module: {e}")
        print("Make sure you've installed the package with 'pip install -e .'")
        print("Or try running from the project root with proper Python path.")
        sys.exit(1)
