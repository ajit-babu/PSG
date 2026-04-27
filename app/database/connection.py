"""
PSG - Professional Safety Guardian
Database Connection Management Module

This module provides a robust database connection manager for SQLite,
with support for connection pooling, backup operations, and thread-safe access.
"""

import logging
import os
import shutil
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Self

from app.config import PSGConfig, get_config
from app.constants import DATABASE_BACKUP_RETENTION_DAYS

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Thread-safe SQLite database connection manager.
    
    This class manages database connections, ensures proper initialization,
    handles backups, and provides a context manager for safe connection access.
    """
    
    _instance: "DatabaseManager | None" = None
    _lock: threading.Lock = threading.Lock()
    
    def __init__(self, db_path: Path | str | None = None, config: PSGConfig | None = None):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file.
            config: Optional configuration object. If not provided, uses default config.
        """
        self._config = config or get_config()
        
        if db_path:
            self._db_path = Path(db_path)
        else:
            self._db_path = self._config.database.get_database_path(
                self._config.get_app_data_dir()
            )
        
        self._local = threading.local()
        self._schema_version: int = 0
        self._initialized: bool = False
        
        # Initialize the database
        self._initialize_database()
    
    def __new__(cls, db_path: Path | str | None = None, config: PSGConfig | None = None) -> Self:
        """Implement singleton pattern for database manager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.__init__(db_path, config)
        return cls._instance
    
    @classmethod
    def get_instance(cls, db_path: Path | str | None = None, config: PSGConfig | None = None) -> "DatabaseManager":
        """Get the singleton instance of the database manager."""
        if cls._instance is None:
            cls._instance = cls(db_path, config)
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.close_all_connections()
                cls._instance = None
    
    @property
    def db_path(self) -> Path:
        """Get the database file path."""
        return self._db_path
    
    @property
    def schema_version(self) -> int:
        """Get the current schema version."""
        return self._schema_version
    
    def _initialize_database(self) -> None:
        """Initialize the database and create tables if they don't exist."""
        try:
            # Ensure parent directory exists
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect and run initialization
            with self.get_connection() as conn:
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Check current schema version
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_info'"
                )
                if cursor.fetchone() is None:
                    # Create schema_info table
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS schema_info (
                            version INTEGER PRIMARY KEY,
                            applied_at TEXT NOT NULL
                        )
                    """)
                    self._schema_version = 0
                else:
                    cursor = conn.execute("SELECT MAX(version) FROM schema_info")
                    result = cursor.fetchone()
                    self._schema_version = result[0] if result and result[0] is not None else 0
                
                # Run migrations
                self._run_migrations(conn)
                
                self._initialized = True
                logger.info(f"Database initialized at {self._db_path} (schema v{self._schema_version})")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _run_migrations(self, conn: sqlite3.Connection) -> None:
        """Run database migrations to create/update schema."""
        migrations = self._get_migrations()
        
        for version, migration_sql in migrations:
            if version > self._schema_version:
                logger.info(f"Applying migration {version}")
                
                try:
                    # Execute migration
                    conn.executescript(migration_sql)
                    
                    # Record migration
                    conn.execute(
                        "INSERT OR REPLACE INTO schema_info (version, applied_at) VALUES (?, ?)",
                        (version, datetime.utcnow().isoformat())
                    )
                    conn.commit()
                    
                    self._schema_version = version
                    
                except sqlite3.Error as e:
                    logger.error(f"Migration {version} failed: {e}")
                    raise
    
    def _get_migrations(self) -> list[tuple[int, str]]:
        """Get list of database migrations."""
        return [
            (1, self._migration_v1_initial_schema()),
            (2, self._migration_v2_add_indexes()),
        ]
    
    def _migration_v1_initial_schema(self) -> str:
        """Migration 1: Initial schema creation."""
        return """
        -- Sync Metadata Table (base fields for all syncable tables)
        CREATE TABLE IF NOT EXISTS sync_metadata (
            id TEXT PRIMARY KEY,
            table_name TEXT NOT NULL,
            record_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_synced INTEGER DEFAULT 0,
            sync_status_code INTEGER DEFAULT 0,
            sync_attempts INTEGER DEFAULT 0,
            last_sync_attempt TEXT,
            remote_id TEXT,
            UNIQUE(table_name, record_id)
        );
        
        -- Employees Table
        CREATE TABLE IF NOT EXISTS employees (
            id TEXT PRIMARY KEY,
            employee_number TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            company TEXT,
            trade TEXT,
            role TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_synced INTEGER DEFAULT 0,
            sync_status_code INTEGER DEFAULT 0
        );
        
        -- Incidents Table (for safety incidents and near-misses)
        CREATE TABLE IF NOT EXISTS incidents (
            id TEXT PRIMARY KEY,
            incident_number TEXT UNIQUE,
            title TEXT NOT NULL,
            description TEXT,
            location_type TEXT NOT NULL,
            location_details TEXT,
            latitude REAL,
            longitude REAL,
            severity_code TEXT NOT NULL,
            incident_datetime TEXT NOT NULL,
            reporter_id TEXT NOT NULL,
            reporter_name TEXT NOT NULL,
            photo_path TEXT,
            witnesses TEXT,
            immediate_actions TEXT,
            root_cause TEXT,
            corrective_actions TEXT,
            status TEXT DEFAULT 'open',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_synced INTEGER DEFAULT 0,
            sync_status_code INTEGER DEFAULT 0,
            FOREIGN KEY (reporter_id) REFERENCES employees(id)
        );
        
        -- Training Logs Table
        CREATE TABLE IF NOT EXISTS training_logs (
            id TEXT PRIMARY KEY,
            employee_id TEXT NOT NULL,
            course_name TEXT NOT NULL,
            course_code TEXT,
            provider TEXT,
            instructor TEXT,
            duration_hours REAL,
            completion_date TEXT,
            expiry_date TEXT,
            score REAL,
            certificate_number TEXT,
            status TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_synced INTEGER DEFAULT 0,
            sync_status_code INTEGER DEFAULT 0,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        );
        
        -- Audit Reports Table
        CREATE TABLE IF NOT EXISTS audit_reports (
            id TEXT PRIMARY KEY,
            audit_number TEXT UNIQUE,
            title TEXT NOT NULL,
            auditor_id TEXT NOT NULL,
            auditor_name TEXT NOT NULL,
            audit_date TEXT NOT NULL,
            location TEXT,
            audit_type TEXT NOT NULL,
            overall_status TEXT NOT NULL,
            overall_score REAL,
            findings TEXT,
            recommendations TEXT,
            follow_up_date TEXT,
            status TEXT DEFAULT 'draft',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_synced INTEGER DEFAULT 0,
            sync_status_code INTEGER DEFAULT 0,
            FOREIGN KEY (auditor_id) REFERENCES employees(id)
        );
        
        -- Audit Check Items Table
        CREATE TABLE IF NOT EXISTS audit_check_items (
            id TEXT PRIMARY KEY,
            audit_id TEXT NOT NULL,
            category_code TEXT NOT NULL,
            item_description TEXT NOT NULL,
            status_code TEXT NOT NULL,
            comments TEXT,
            photo_evidence_path TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_synced INTEGER DEFAULT 0,
            sync_status_code INTEGER DEFAULT 0,
            FOREIGN KEY (audit_id) REFERENCES audit_reports(id) ON DELETE CASCADE
        );
        
        -- Settings Table
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        
        -- Insert default settings
        INSERT OR IGNORE INTO app_settings (key, value, updated_at) VALUES 
            ('last_sync', '', ''),
            ('sync_enabled', 'true', ''),
            ('theme', 'light', '');
        """
    
    def _migration_v2_add_indexes(self) -> str:
        """Migration 2: Add performance indexes."""
        return """
        -- Indexes for sync operations
        CREATE INDEX IF NOT EXISTS idx_sync_metadata_is_synced 
            ON sync_metadata(is_synced);
        CREATE INDEX IF NOT EXISTS idx_sync_metadata_status 
            ON sync_metadata(sync_status_code);
        CREATE INDEX IF NOT EXISTS idx_sync_metadata_table_record 
            ON sync_metadata(table_name, record_id);
        
        -- Indexes for incidents
        CREATE INDEX IF NOT EXISTS idx_incidents_reporter 
            ON incidents(reporter_id);
        CREATE INDEX IF NOT EXISTS idx_incidents_datetime 
            ON incidents(incident_datetime);
        CREATE INDEX IF NOT EXISTS idx_incidents_severity 
            ON incidents(severity_code);
        CREATE INDEX IF NOT EXISTS idx_incidents_sync 
            ON incidents(is_synced);
        
        -- Indexes for training logs
        CREATE INDEX IF NOT EXISTS idx_training_employee 
            ON training_logs(employee_id);
        CREATE INDEX IF NOT EXISTS idx_training_expiry 
            ON training_logs(expiry_date);
        CREATE INDEX IF NOT EXISTS idx_training_sync 
            ON training_logs(is_synced);
        
        -- Indexes for audit reports
        CREATE INDEX IF NOT EXISTS idx_audit_auditor 
            ON audit_reports(auditor_id);
        CREATE INDEX IF NOT EXISTS idx_audit_date 
            ON audit_reports(audit_date);
        CREATE INDEX IF NOT EXISTS idx_audit_sync 
            ON audit_reports(is_synced);
        
        -- Indexes for audit check items
        CREATE INDEX IF NOT EXISTS idx_audit_items_audit 
            ON audit_check_items(audit_id);
        CREATE INDEX IF NOT EXISTS idx_audit_items_sync 
            ON audit_check_items(is_synced);
        
        -- Indexes for employees
        CREATE INDEX IF NOT EXISTS idx_employees_number 
            ON employees(employee_number);
        CREATE INDEX IF NOT EXISTS idx_employees_sync 
            ON employees(is_synced);
        """
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection for the current thread.
        
        Returns:
            sqlite3.Connection: A database connection.
        """
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = self._create_connection()
        return self._local.connection
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimized settings."""
        conn = sqlite3.connect(
            str(self._db_path),
            timeout=self._config.database.connection_timeout,
            isolation_level=None,  # Autocommit mode
            check_same_thread=False,  # We handle thread safety
        )
        
        # Optimize settings
        conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = 10000")  # 10MB cache
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Enable row factory for dict-like access
        conn.row_factory = sqlite3.Row
        
        return conn
    
    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for database transactions.
        
        Usage:
            with db_manager.transaction() as conn:
                conn.execute("INSERT ...")
                # Commits on exit, rolls back on exception
        
        Yields:
            sqlite3.Connection: A database connection.
        """
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
    
    def execute(
        self,
        query: str,
        parameters: tuple[Any, ...] | dict[str, Any] | None = None,
        fetch: bool = False,
        fetch_all: bool = False,
    ) -> list[sqlite3.Row] | sqlite3.Row | None:
        """
        Execute a database query.
        
        Args:
            query: SQL query string.
            parameters: Optional query parameters.
            fetch: If True, fetch one row.
            fetch_all: If True, fetch all rows.
        
        Returns:
            Query results if fetch or fetch_all is True, None otherwise.
        """
        conn = self.get_connection()
        if parameters:
            cursor = conn.execute(query, parameters)
        else:
            cursor = conn.execute(query)
        
        if fetch_all:
            return cursor.fetchall()
        elif fetch:
            return cursor.fetchone()
        return None
    
    def executemany(
        self,
        query: str,
        parameters_list: list[tuple[Any, ...]],
    ) -> None:
        """
        Execute a query with multiple parameter sets.
        
        Args:
            query: SQL query string.
            parameters_list: List of parameter tuples.
        """
        conn = self.get_connection()
        conn.executemany(query, parameters_list)
    
    def create_backup(self) -> Path | None:
        """
        Create a backup of the database.
        
        Returns:
            Path to the backup file, or None if backup failed.
        """
        if not self._config.database.backup_enabled:
            return None
        
        try:
            backup_dir = self._config.get_backup_dir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"psg_backup_{timestamp}.db"
            backup_path = backup_dir / backup_filename
            
            # Ensure WAL is checkpointed before backup
            conn = self.get_connection()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            
            # Copy database file
            shutil.copy2(str(self._db_path), str(backup_path))
            
            logger.info(f"Database backup created: {backup_path}")
            
            # Clean up old backups
            self._cleanup_old_backups(backup_dir)
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            return None
    
    def _cleanup_old_backups(self, backup_dir: Path) -> None:
        """Remove backups older than the retention period."""
        try:
            if not backup_dir.exists():
                return
            
            cutoff_days = self._config.database.backup_retention_days
            cutoff_time = datetime.now().timestamp() - (cutoff_days * 86400)
            
            for file_path in backup_dir.glob("psg_backup_*.db"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    logger.debug(f"Removed old backup: {file_path}")
                    
        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")
    
    def close_all_connections(self) -> None:
        """Close all database connections."""
        if hasattr(self._local, "connection") and self._local.connection is not None:
            try:
                self._local.connection.close()
            except sqlite3.Error:
                pass
            self._local.connection = None
    
    def vacuum(self) -> None:
        """Run VACUUM to reclaim database space."""
        try:
            self.execute("VACUUM")
            logger.info("Database vacuumed successfully")
        except sqlite3.Error as e:
            logger.error(f"Failed to vacuum database: {e}")
    
    def get_stats(self) -> dict[str, Any]:
        """Get database statistics."""
        stats: dict[str, Any] = {}
        
        try:
            # Database size
            if self._db_path.exists():
                stats["size_bytes"] = self._db_path.stat().st_size
                stats["size_mb"] = round(stats["size_bytes"] / (1024 * 1024), 2)
            else:
                stats["size_bytes"] = 0
                stats["size_mb"] = 0
            
            # Table counts
            tables = ["incidents", "training_logs", "audit_reports", "audit_check_items", "employees"]
            for table in tables:
                result = self.execute(
                    f"SELECT COUNT(*) FROM {table}",
                    fetch=True
                )
                stats[f"{table}_count"] = result[0] if result else 0
            
            # Sync stats
            result = self.execute(
                "SELECT COUNT(*) FROM sync_metadata WHERE is_synced = 0",
                fetch=True
            )
            stats["pending_sync"] = result[0] if result else 0
            
            stats["schema_version"] = self._schema_version
            stats["path"] = str(self._db_path)
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get database stats: {e}")
            stats["error"] = str(e)
        
        return stats


# Singleton accessor function
def get_db_manager() -> DatabaseManager:
    """
    Get the database manager singleton.
    
    Returns:
        DatabaseManager: The database manager instance.
    """
    return DatabaseManager.get_instance()