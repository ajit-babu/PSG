"""
PSG - Professional Safety Guardian
Main Application Module

This module provides the main application class and entry point
for the PSG desktop application.
"""

import sys
import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from app import __version__
from app.config import get_config, PSGConfig
from app.constants import APP_NAME, ORGANIZATION, ORGANIZATION_DOMAIN
from app.utils.logger import setup_logging, get_logger
from app.ui.main_window import MainWindow

logger = logging.getLogger(__name__)


class PSGApplication:
    """
    Main application class for PSG Desktop.
    
    This class manages the application lifecycle, including initialization,
    running the event loop, and cleanup.
    """
    
    def __init__(self, args: list[str] | None = None):
        """
        Initialize the application.
        
        Args:
            args: Command line arguments.
        """
        self._args = args or sys.argv
        self._app: Optional[QApplication] = None
        self._main_window: Optional[MainWindow] = None
        
        # Initialize configuration
        self._config = get_config()
        
        # Setup logging
        setup_logging()
        logger.info(f"Starting {APP_NAME} v{__version__}")
    
    def run(self) -> int:
        """
        Run the application.
        
        Returns:
            Exit code.
        """
        try:
            # Create Qt application
            self._create_application()
            
            # Create and show main window
            self._create_main_window()
            
            # Run event loop
            logger.info("Starting application event loop")
            return self._app.exec()
            
        except Exception as e:
            logger.critical(f"Application error: {e}", exc_info=True)
            self._show_error_dialog(e)
            return 1
        
        finally:
            self._cleanup()
    
    def _create_application(self) -> None:
        """Create the Qt application instance."""
        # Set application metadata
        QApplication.setApplicationName(APP_NAME)
        QApplication.setApplicationDisplayName(APP_NAME)
        QApplication.setApplicationVersion(__version__)
        QApplication.setOrganizationName(ORGANIZATION)
        QApplication.setOrganizationDomain(ORGANIZATION_DOMAIN)
        
        # Enable high DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        # Create application
        self._app = QApplication(self._args)
        
        # Set application font (optional - for consistency across platforms)
        # font = QFont("Segoe UI", 10)
        # self._app.setFont(font)
    
    def _create_main_window(self) -> None:
        """Create and show the main window."""
        self._main_window = MainWindow()
        self._main_window.show()
        
        logger.info("Main window created and shown")
    
    def _show_error_dialog(self, error: Exception) -> None:
        """
        Show an error dialog to the user.
        
        Args:
            error: The exception that occurred.
        """
        from PyQt6.QtWidgets import QMessageBox
        
        QMessageBox.critical(
            None,
            "Application Error",
            f"An unexpected error occurred:\n\n{str(error)}\n\n"
            f"The application will now close. Please check the log file for details."
        )
    
    def _cleanup(self) -> None:
        """Clean up application resources."""
        logger.info("Cleaning up application resources")
        
        # Close database connections
        try:
            from app.database.connection import DatabaseManager
            DatabaseManager.reset_instance()
        except Exception:
            pass
        
        # Reset services
        try:
            from app.services.sync_service import SyncService
            SyncService.reset_instance()
        except Exception:
            pass
        
        try:
            from app.services.connectivity import ConnectivityMonitor
            ConnectivityMonitor.reset_instance()
        except Exception:
            pass
        
        try:
            from app.services.notification import NotificationService
            NotificationService.reset_instance()
        except Exception:
            pass
        
        logger.info("Application cleanup complete")


def main() -> int:
    """
    Main entry point for the application.
    
    Returns:
        Exit code.
    """
    app = PSGApplication()
    return app.run()


def cli_entry() -> None:
    """Entry point for CLI commands."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="PSG - Professional Safety Guardian",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    
    args = parser.parse_args()
    
    # Override config if specified
    if args.config:
        from pathlib import Path
        PSGConfig.load(Path(args.config))
    
    if args.debug:
        import os
        os.environ["PSG_DEBUG"] = "true"
        os.environ["PSG_LOG_LEVEL"] = "DEBUG"
    
    sys.exit(main())


if __name__ == "__main__":
    sys.exit(main())