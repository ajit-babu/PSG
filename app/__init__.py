"""
PSG - Professional Safety Guardian
Desktop Application for MEP Construction Safety Management

Copyright (c) 2024 PSG Development Team. All rights reserved.
"""

__version__ = "1.0.0"
__author__ = "PSG Development Team"
__email__ = "dev@psg-safety.com"

# Application metadata
APP_NAME = "PSG - Professional Safety Guardian"
APP_DISPLAY_NAME = "PSG Safety"
ORGANIZATION_NAME = "PSG Safety Solutions"
ORGANIZATION_DOMAIN = "psg-safety.com"

# Import main application class for easy access
from app.main import PSGApplication

__all__ = ["PSGApplication", "__version__"]