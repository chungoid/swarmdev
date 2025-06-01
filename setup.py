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


def read_requirements():
    """Read requirements from requirements.txt file."""
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]


def run_mcp_setup():
    """Run MCP server setup after installation."""
    try:
        setup_script = os.path.join(os.path.dirname(__file__), 'scripts', 'setup_mcp_servers.py')
        if os.path.exists(setup_script):
            print("\n" + "="*50)
            print("Setting up MCP servers...")
            print("="*50)
            subprocess.run([sys.executable, setup_script], check=False)
            print("="*50)
        else:
            print("Warning: MCP setup script not found")
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


# Get bundled MCP server files
def get_package_data():
    """Get package data including bundled MCP servers."""
    package_data = {}
    
    # Include bundled MCP server files
    mcp_files = []
    bundled_mcp_dir = "src/swarmdev/bundled_mcp"
    
    if os.path.exists(bundled_mcp_dir):
        for root, dirs, files in os.walk(bundled_mcp_dir):
            for file in files:
                file_path = os.path.relpath(os.path.join(root, file), "src/swarmdev")
                mcp_files.append(file_path)
    
    if mcp_files:
        package_data['swarmdev'] = mcp_files
    
    return package_data


# Read long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="swarmdev",
    version="0.1.0",
    author="SwarmDev Team",
    author_email="team@swarmdev.ai",
    description="A multi-agent swarm platform for autonomous project development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/swarmdev/swarmdev",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data=get_package_data(),
    include_package_data=True,
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
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "mcp": [
            "mcp-server-git>=0.1.0",
            "mcp-server-time>=0.1.0", 
            "mcp-server-fetch>=0.1.0",
        ],
        "full": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "mcp-server-git>=0.1.0",
            "mcp-server-time>=0.1.0",
            "mcp-server-fetch>=0.1.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "swarmdev=swarmdev.cli:main",
        ],
    },
    cmdclass={
        'install': PostInstallCommand,
        'develop': PostDevelopCommand,
    },
    scripts=["swarmdev_cli.py"],
    keywords="ai, swarm, agents, development, automation, llm, mcp",
    project_urls={
        "Bug Reports": "https://github.com/swarmdev/swarmdev/issues",
        "Source": "https://github.com/swarmdev/swarmdev/",
        "Documentation": "https://docs.swarmdev.ai/",
    },
)
