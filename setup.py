#!/usr/bin/env python3
"""
Setup script for SwarmDev - Multi-Agent Swarm Platform
"""

import os
import sys
import subprocess
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop


def run_mcp_setup():
    """Run MCP server setup after installation.
    This script will be responsible for ensuring Docker images for MCP servers
    are pulled and that MCPManager is configured to use them.
    """
    try:
        setup_script = os.path.join(os.path.dirname(__file__), 'scripts', 'setup_mcp_servers.py')
        if os.path.exists(setup_script):
            print("\n" + "="*50)
            print("Configuring MCP servers (using pre-built Docker images)...")
            print("="*50)
            # This script will be rewritten to pull images and configure based on a manifest
            subprocess.run([sys.executable, setup_script], check=False)
            print("="*50)
        else:
            print("Warning: MCP setup script not found (scripts/setup_mcp_servers.py)")
    except Exception as e:
        print(f"Warning: MCP setup failed: {e}")
        print("You can run it manually later with: python scripts/setup_mcp_servers.py")


class PostInstallCommand(install):
    """Post-installation command to set up MCP servers."""
    def run(self):
        install.run(self)
        if not os.environ.get('SWARMDEV_SKIP_MCP_SETUP'):
            run_mcp_setup()


class PostDevelopCommand(develop):
    """Post-development command to set up MCP servers."""
    def run(self):
        develop.run(self)
        if not os.environ.get('SWARMDEV_SKIP_MCP_SETUP'):
            run_mcp_setup()


# Read long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="swarmdev",
    version="0.1.0", # Consider updating version for this significant change
    author="SwarmDev Team",
    author_email="team@swarmdev.ai",
    description="A multi-agent swarm platform for autonomous project development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/swarmdev/swarmdev",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    # package_data no longer includes the bundled MCP source.
    # It now needs to include the MCP image manifest file.
    package_data={
        'swarmdev': ['mcp_image_manifest.json'], # Assuming manifest is in src/swarmdev/
    },
    include_package_data=True, # Ensure manifest and other package data are included
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        # Consider if Python 3.12+ support is feasible once MCP images are external
    ],
    python_requires=">=3.8", # This can be re-evaluated once MCP servers are fully externalized
    install_requires=[], # Dependencies are now defined in pyproject.toml
    extras_require={ # These should ideally mirror pyproject.toml's optional-dependencies
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "ipython", # Added from pyproject.toml
            "ipywidgets", # Added from pyproject.toml
            "freezegun", # Added from pyproject.toml
        ],
        "mcp": [
            "mcp-server-git>=0.1.0", # These would likely be removed if MCP servers are only Docker images
            "mcp-server-time>=0.1.0", 
            "mcp-server-fetch>=0.1.0",
        ],
        "docs": [ # Added from pyproject.toml
            "Sphinx>=8.2.3",
            "docutils>=0.21.2", # Assuming docutils is mainly for Sphinx
        ],
        "full": [ # Adjusted to refer to current extras
            "swarmdev[dev]",
            "swarmdev[docs]",
            # "swarmdev[mcp]", # Re-evaluate if 'mcp' extra is still needed in this form
        ]
    },
    entry_points={
        "console_scripts": [
            "swarmdev=swarmdev.cli:main", # Ensure this matches pyproject.toml
        ],
    },
    cmdclass={
        'install': PostInstallCommand,
        'develop': PostDevelopCommand,
    },
    # scripts=["swarmdev_cli.py"], # entry_points is preferred
    keywords="ai, swarm, agents, development, automation, llm, mcp",
    project_urls={
        "Bug Reports": "https://github.com/swarmdev/swarmdev/issues",
        "Source": "https://github.com/swarmdev/swarmdev/",
        "Documentation": "https://docs.swarmdev.ai/",
    },
)
