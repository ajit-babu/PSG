#!/usr/bin/env python3
"""
PSG - Professional Safety Guardian
Application Entry Point

This script is the main entry point for running the PSG desktop application.
It can be executed directly or installed as a console/gui script.

Usage:
    python run.py              # Run the application
    python run.py --debug      # Run with debug logging
    python run.py --version    # Show version information
"""

import sys


def main():
    """Main entry point for the application."""
    # Import and run the main application
    from app.main import main as app_main
    sys.exit(app_main())


if __name__ == "__main__":
    main()