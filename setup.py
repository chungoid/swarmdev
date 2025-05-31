from setuptools import setup, find_packages

setup(
    name="swarmdev",
    version="0.1.0",
    description="Multi-Agent Swarm Platform for Autonomous Project Development",
    author="SwarmDev Contributors",
    author_email="support@swarmdev.ai",
    url="https://github.com/swarmdev/swarmdev",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "swarms>=0.1.0",
        "openai>=1.0.0",
        "anthropic>=0.5.0",
        "chromadb>=0.4.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "docker>=6.0.0",
        "requests>=2.0.0",
        "numpy>=1.0.0",
        "pandas>=2.0.0",
        "scikit-learn>=1.0.0",
        "tqdm>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "swarmdev=swarmdev.cli:main",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
