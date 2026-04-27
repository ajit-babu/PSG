"""
PSG - Professional Safety Guardian
Database Layer Package

This package provides the data access layer for the application,
including database connection management, models, and repository pattern.
"""

from app.database.connection import DatabaseManager, get_db_manager
from app.database.models import (
    BaseModel,
    Incident,
    TrainingLog,
    AuditReport,
    AuditCheckItem,
    Employee,
    SyncMetadata,
)
from app.database.repository import Repository

__all__ = [
    # Connection
    "DatabaseManager",
    "get_db_manager",
    # Models
    "BaseModel",
    "Incident",
    "TrainingLog",
    "AuditReport",
    "AuditCheckItem",
    "Employee",
    "SyncMetadata",
    # Repository
    "Repository",
]