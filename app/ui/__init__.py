"""
PSG - Professional Safety Guardian
UI Layer Package

This package provides the PyQt6-based user interface components,
including the main window, dialogs, widgets, and styling.
"""

from app.ui.main_window import MainWindow
from app.ui.styles import StyleSheet

__all__ = [
    "MainWindow",
    "StyleSheet",
]