#!/usr/bin/env python3
"""
PSG - Professional Safety Guardian
Setup Script

This script provides installation and build capabilities for the PSG
desktop application.

Usage:
    pip install -e .          # Install in development mode
    python setup.py sdist     # Create source distribution
    python setup.py bdist     # Create binary distribution
"""

from setuptools import setup, find_packages

# Read README for long description
try:
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "PSG - Professional Safety Guardian Desktop Application"

setup(
    name="psg-safety",
    version="1.0.0",
    description="Professional Safety Guardian - Desktop Application for MEP Construction Safety Management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="PSG Development Team",
    author_email="dev@psg-safety.com",
    url="https://github.com/psg-safety/psg-desktop",
    license="Proprietary",
    
    # Package discovery
    packages=find_packages(include=["app", "app.*"]),
    
    # Package data (non-Python files)
    package_data={
        "app": [
            "ui/resources/*.qss",
            "ui/resources/*.png",
            "ui/resources/*.ico",
            "ui/resources/*.svg",
        ],
    },
    
    # Python version requirement
    python_requires=">=3.12",
    
    # Dependencies
    install_requires=[
        "PyQt6>=6.6.0",
        "PyQt6-Qt6>=6.6.0",
        "requests>=2.31.0",
        "typing-extensions>=4.9.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "colorlog>=6.8.0",
        "python-dateutil>=2.8.2",
    ],
    
    # Optional dependencies
    extras_require={
        "dev": [
            "pyinstaller>=6.3.0",
            "pytest>=7.4.4",
            "pytest-qt>=4.2.0",
            "black>=23.12.0",
            "ruff>=0.1.8",
            "mypy>=1.8.0",
        ],
    },
    
    # Entry points
    entry_points={
        "gui_scripts": [
            "psg=app.main:main",
        ],
        "console_scripts": [
            "psg-cli=app.main:cli_entry",
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Office/Business",
        "Topic :: Security",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
    
    # Keywords
    keywords=[
        "safety",
        "construction",
        "MEP",
        "desktop",
        "offline-first",
        "PyQt6",
        "UAE",
        "incident-reporting",
        "compliance",
        "training",
        "audit",
    ],
)