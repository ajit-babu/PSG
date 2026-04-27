"""
PSG - Professional Safety Guardian
Configuration Management Module

This module handles application configuration using pydantic-settings,
providing type-safe configuration management with environment variable
support and JSON file-based persistence.
"""

import json
import os
from datetime import timedelta
from pathlib import Path
from typing import Any, ClassVar

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.constants import (
    BACKUP_DIR,
    CONFIG_FILENAME,
    DATABASE_FILENAME,
    DEFAULT_API_TIMEOUT,
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_BATCH_SIZE,
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_SYNC_INTERVAL_MINUTES,
    EXPORT_DIR,
    LOG_FILENAME,
    PHOTOS_DIR,
)


class APIConfig(BaseSettings):
    """API connection configuration."""
    
    model_config = SettingsConfigDict(env_prefix="PSG_API_")
    
    base_url: str = Field(
        default="https://api.psg-safety.com/v1",
        description="Base URL for the remote API"
    )
    timeout: int = Field(
        default=DEFAULT_API_TIMEOUT,
        ge=5,
        le=300,
        description="HTTP request timeout in seconds"
    )
    retry_attempts: int = Field(
        default=DEFAULT_RETRY_ATTEMPTS,
        ge=0,
        le=10,
        description="Number of retry attempts for failed requests"
    )
    backoff_factor: int = Field(
        default=DEFAULT_BACKOFF_FACTOR,
        ge=1,
        le=10,
        description="Exponential backoff multiplier"
    )
    api_key: str = Field(default="", description="API authentication key")
    
    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate and normalize the base URL."""
        v = v.rstrip("/")
        if v and not v.startswith(("http://", "https://")):
            v = f"https://{v}"
        return v


class DatabaseConfig(BaseSettings):
    """Database configuration."""
    
    model_config = SettingsConfigDict(env_prefix="PSG_DB_")
    
    path: str = Field(
        default="",
        description="Path to the SQLite database file"
    )
    backup_enabled: bool = Field(
        default=True,
        description="Enable automatic database backups"
    )
    backup_interval_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Interval between automatic backups in hours"
    )
    backup_retention_days: int = Field(
        default=30,
        ge=7,
        le=365,
        description="Number of days to retain backup files"
    )
    connection_timeout: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
        description="Database connection timeout in seconds"
    )
    
    def get_database_path(self, app_data_dir: Path) -> Path:
        """Get the full database path, creating directories as needed."""
        if self.path:
            db_path = Path(self.path)
        else:
            db_path = app_data_dir / DATABASE_FILENAME
        
        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return db_path


class SyncConfig(BaseSettings):
    """Synchronization configuration."""
    
    model_config = SettingsConfigDict(env_prefix="PSG_SYNC_")
    
    interval_minutes: int = Field(
        default=DEFAULT_SYNC_INTERVAL_MINUTES,
        ge=1,
        le=1440,
        description="Sync interval in minutes"
    )
    batch_size: int = Field(
        default=DEFAULT_BATCH_SIZE,
        ge=1,
        le=500,
        description="Number of records to sync per batch"
    )
    auto_sync: bool = Field(
        default=True,
        description="Enable automatic background synchronization"
    )
    max_retries: int = Field(
        default=5,
        ge=0,
        le=20,
        description="Maximum retry attempts for failed syncs"
    )
    conflict_resolution: str = Field(
        default="last_write_wins",
        description="Conflict resolution strategy"
    )
    
    @property
    def interval_timedelta(self) -> timedelta:
        """Get sync interval as timedelta."""
        return timedelta(minutes=self.interval_minutes)


class UIConfig(BaseSettings):
    """User interface configuration."""
    
    model_config = SettingsConfigDict(env_prefix="PSG_UI_")
    
    theme: str = Field(
        default="light",
        description="UI theme (light/dark/system)"
    )
    language: str = Field(
        default="en",
        description="UI language code"
    )
    font_size: int = Field(
        default=12,
        ge=8,
        le=24,
        description="Default font size"
    )
    window_width: int = Field(
        default=1280,
        ge=800,
        le=3840,
        description="Default window width"
    )
    window_height: int = Field(
        default=800,
        ge=600,
        le=2160,
        description="Default window height"
    )
    remember_window_geometry: bool = Field(
        default=True,
        description="Remember window position and size"
    )
    
    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        """Validate theme value."""
        valid_themes = {"light", "dark", "system"}
        if v.lower() not in valid_themes:
            return "light"
        return v.lower()


class PSGConfig(BaseSettings):
    """
    Main application configuration class.
    
    This class aggregates all configuration sections and provides
    methods for loading, saving, and accessing configuration values.
    """
    
    model_config = SettingsConfigDict(
        env_prefix="PSG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Nested configuration sections
    api: APIConfig = Field(default_factory=APIConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    sync: SyncConfig = Field(default_factory=SyncConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    
    # Application settings
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    check_updates: bool = Field(default=True, description="Check for updates on startup")
    
    # Class variables for singleton pattern
    _instance: ClassVar["PSGConfig | None"] = None
    _config_dir: ClassVar[Path | None] = None
    
    @classmethod
    def get_config_dir(cls) -> Path:
        """Get the platform-specific configuration directory."""
        if cls._config_dir is None:
            system = os.name
            
            if system == "nt":  # Windows
                appdata = os.getenv("APPDATA", "")
                if appdata:
                    cls._config_dir = Path(appdata) / "PSG"
                else:
                    cls._config_dir = Path.home() / ".psg"
            elif system == "posix":  # Linux/macOS
                xdg_config = os.getenv("XDG_CONFIG_HOME", "")
                if xdg_config:
                    cls._config_dir = Path(xdg_config) / "PSG"
                else:
                    cls._config_dir = Path.home() / ".config" / "PSG"
            else:
                cls._config_dir = Path.home() / ".psg"
            
            # Ensure directory exists
            cls._config_dir.mkdir(parents=True, exist_ok=True)
        
        return cls._config_dir
    
    @classmethod
    def get_app_data_dir(cls) -> Path:
        """Get the platform-specific application data directory."""
        system = os.name
        
        if system == "nt":  # Windows
            localappdata = os.getenv("LOCALAPPDATA", "")
            if localappdata:
                data_dir = Path(localappdata) / "PSG"
            else:
                data_dir = Path.home() / ".psg" / "data"
        elif system == "posix":
            # Check for snap/flatpak environment
            snap_data = os.getenv("SNAP_USER_DATA", "")
            if snap_data:
                data_dir = Path(snap_data) / ".psg"
            else:
                data_dir = Path.home() / ".local" / "share" / "PSG"
        else:
            data_dir = Path.home() / ".psg" / "data"
        
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    
    @classmethod
    def get_instance(cls) -> "PSGConfig":
        """Get the singleton configuration instance."""
        if cls._instance is None:
            cls._instance = cls.load()
        return cls._instance
    
    @classmethod
    def load(cls, config_path: Path | None = None) -> "PSGConfig":
        """
        Load configuration from file.
        
        Args:
            config_path: Optional path to config file. If not provided,
                        uses the default platform-specific location.
        """
        if config_path is None:
            config_path = cls.get_config_dir() / CONFIG_FILENAME
        
        config_data: dict[str, Any] = {}
        
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                # Log warning but continue with defaults
                print(f"Warning: Could not load config file: {e}")
        
        # Flatten nested config for pydantic-settings
        flat_config: dict[str, Any] = {}
        for section, values in config_data.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    flat_config[f"{section}__{key}"] = value
            else:
                flat_config[section] = values
        
        cls._instance = cls(**flat_config)
        return cls._instance
    
    def save(self, config_path: Path | None = None) -> bool:
        """
        Save configuration to file.
        
        Args:
            config_path: Optional path to config file. If not provided,
                        uses the default platform-specific location.
        
        Returns:
            True if save was successful, False otherwise.
        """
        if config_path is None:
            config_path = self.get_config_dir() / CONFIG_FILENAME
        
        try:
            # Build nested config structure
            config_data = {
                "api": self.api.model_dump(),
                "database": self.database.model_dump(),
                "sync": self.sync.model_dump(),
                "ui": self.ui.model_dump(),
                "debug": self.debug,
                "log_level": self.log_level,
                "check_updates": self.check_updates,
            }
            
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write config file
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
            
            return True
            
        except (IOError, OSError) as e:
            print(f"Error saving config file: {e}")
            return False
    
    def get_log_path(self) -> Path:
        """Get the path to the log file."""
        data_dir = self.get_app_data_dir()
        log_dir = data_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / LOG_FILENAME
    
    def get_photos_dir(self) -> Path:
        """Get the directory for storing incident photos."""
        data_dir = self.get_app_data_dir()
        photos_dir = data_dir / PHOTOS_DIR
        photos_dir.mkdir(parents=True, exist_ok=True)
        return photos_dir
    
    def get_backup_dir(self) -> Path:
        """Get the directory for database backups."""
        data_dir = self.get_app_data_dir()
        backup_dir = data_dir / BACKUP_DIR
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir
    
    def get_export_dir(self) -> Path:
        """Get the directory for exported reports."""
        data_dir = self.get_app_data_dir()
        export_dir = data_dir / EXPORT_DIR
        export_dir.mkdir(parents=True, exist_ok=True)
        return export_dir
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._instance = None
        PSGConfig.__pydantic_fields_set__.clear()


# Convenience function for accessing configuration
def get_config() -> PSGConfig:
    """Get the application configuration singleton."""
    return PSGConfig.get_instance()