"""
PSG - Professional Safety Guardian
Logging Configuration Module

This module provides centralized logging configuration for the application,
with support for file and console output, colored logs, and log rotation.
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from app.config import get_config

# Module-level logger instance
_logger: Optional[logging.Logger] = None


def setup_logging(
    log_level: str | None = None,
    log_file: Path | None = None,
    console_output: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Setup the application logging system.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Path to the log file. If None, uses config default.
        console_output: Whether to output logs to console.
        max_bytes: Maximum size of log file before rotation.
        backup_count: Number of backup log files to keep.
    
    Returns:
        The configured logger instance.
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    # Get configuration
    config = get_config()
    
    if log_level is None:
        log_level = config.log_level
    
    if log_file is None:
        log_file = config.get_log_path()
    
    # Create logger
    _logger = logging.getLogger("psg")
    _logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear any existing handlers
    _logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console handler with color support
    if console_output:
        console_handler = _create_console_handler(log_level)
        console_handler.setFormatter(formatter)
        _logger.addHandler(console_handler)
    
    # File handler with rotation
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)
    except (OSError, IOError) as e:
        if console_output:
            print(f"Warning: Could not setup log file: {e}")
    
    # Log startup
    _logger.info(f"Logging initialized (level: {log_level})")
    
    return _logger


def _create_console_handler(log_level: str) -> logging.Handler:
    """
    Create a console handler with optional color output.
    
    Args:
        log_level: The logging level for the handler.
    
    Returns:
        Configured StreamHandler.
    """
    try:
        # Try to use colorlog for colored output
        import colorlog
        
        handler = colorlog.StreamHandler()
        handler.setFormatter(colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        ))
    except ImportError:
        # Fallback to standard handler
        handler = logging.StreamHandler(sys.stdout)
    
    handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    return handler


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Optional logger name for creating a child logger.
    
    Returns:
        Logger instance.
    """
    if _logger is None:
        setup_logging()
    
    if name:
        return _logger.getChild(name)
    
    return _logger


def get_log_level_name(level: int) -> str:
    """
    Get the name of a logging level.
    
    Args:
        level: The logging level number.
    
    Returns:
        The level name as a string.
    """
    return logging.getLevelName(level)


class LoggingContext:
    """
    Context manager for temporary logging configuration.
    
    Usage:
        with LoggingContext("DEBUG"):
            # Code here runs with DEBUG logging
    """
    
    def __init__(self, level: str):
        """
        Initialize the logging context.
        
        Args:
            level: The logging level to use within the context.
        """
        self.level = level
        self.original_level: int | None = None
    
    def __enter__(self) -> "LoggingContext":
        """Enter the context and set the new logging level."""
        logger = get_logger()
        self.original_level = logger.level
        logger.setLevel(getattr(logging, self.level.upper(), logging.INFO))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context and restore the original logging level."""
        if self.original_level is not None:
            get_logger().setLevel(self.original_level)