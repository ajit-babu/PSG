"""
PSG - Professional Safety Guardian
Repository Pattern Implementation

This module provides a generic repository pattern for database operations,
offering a clean abstraction layer between the database and business logic.
"""

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, TypeVar

from app.database.connection import DatabaseManager, get_db_manager
from app.database.models import (
    AuditCheckItem,
    AuditReport,
    BaseModel,
    Employee,
    Incident,
    SyncMetadata,
    TrainingLog,
)
from app.constants import DATETIME_FORMAT_ISO, SyncStatus

logger = logging.getLogger(__name__)

# Type variable for model types
T = TypeVar("T", bound=BaseModel)


class Repository(ABC, Generic[T]):
    """
    Abstract base repository class implementing common CRUD operations.
    
    This class provides a generic implementation of database operations
    that can be specialized for each model type.
    """
    
    # Class-level cache for table names
    _table_names: dict[type, str] = {}
    
    def __init__(self, db_manager: DatabaseManager | None = None):
        """
        Initialize the repository.
        
        Args:
            db_manager: Optional database manager instance.
        """
        self._db = db_manager or get_db_manager()
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """Return the database table name for this repository."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def model_class(self) -> type[T]:
        """Return the model class for this repository."""
        raise NotImplementedError
    
    def _generate_id(self) -> str:
        """Generate a unique ID for a new record."""
        return str(uuid.uuid4())
    
    def get(self, record_id: str) -> T | None:
        """
        Retrieve a single record by ID.
        
        Args:
            record_id: The unique identifier of the record.
        
        Returns:
            The record if found, None otherwise.
        """
        query = f"SELECT * FROM {self.table_name} WHERE id = ?"
        row = self._db.execute(query, (record_id,), fetch=True)
        
        if row:
            return self.model_class.from_row(row)
        return None
    
    def get_all(
        self,
        where: str | None = None,
        params: tuple[Any, ...] = (),
        order_by: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[T]:
        """
        Retrieve all records matching optional criteria.
        
        Args:
            where: Optional WHERE clause (without 'WHERE' keyword).
            params: Parameters for the WHERE clause.
            order_by: Optional ORDER BY clause.
            limit: Optional result limit.
            offset: Optional result offset.
        
        Returns:
            List of matching records.
        """
        query = f"SELECT * FROM {self.table_name}"
        
        if where:
            query += f" WHERE {where}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" OFFSET {offset}"
        
        rows = self._db.execute(query, params, fetch_all=True)
        return [self.model_class.from_row(row) for row in rows]
    
    def create(self, record: T) -> T:
        """
        Create a new record in the database.
        
        Args:
            record: The record to create.
        
        Returns:
            The created record with ID and timestamps set.
        """
        # Generate ID if not set
        if not record.id:
            record.id = self._generate_id()
        
        # Set timestamps if not set
        now = datetime.utcnow().strftime(DATETIME_FORMAT_ISO)
        if not record.created_at:
            record.created_at = now
        if not record.updated_at:
            record.updated_at = now
        
        # Insert record
        columns, values = self._prepare_insert_data(record)
        placeholders = ", ".join(["?"] * len(values))
        
        query = f"""
            INSERT INTO {self.table_name} ({", ".join(columns)})
            VALUES ({placeholders})
        """
        
        self._db.execute(query, tuple(values))
        
        # Create sync metadata
        self._create_sync_metadata(record)
        
        return record
    
    def update(self, record: T) -> T:
        """
        Update an existing record.
        
        Args:
            record: The record to update.
        
        Returns:
            The updated record.
        """
        # Update timestamp
        record.updated_at = datetime.utcnow().strftime(DATETIME_FORMAT_ISO)
        record.mark_modified()
        
        # Build update query
        set_clause, values = self._prepare_update_data(record)
        values.append(record.id)
        
        query = f"""
            UPDATE {self.table_name}
            SET {set_clause}
            WHERE id = ?
        """
        
        self._db.execute(query, tuple(values))
        
        # Update sync metadata
        self._update_sync_metadata(record)
        
        return record
    
    def delete(self, record_id: str) -> bool:
        """
        Delete a record by ID.
        
        Args:
            record_id: The unique identifier of the record.
        
        Returns:
            True if record was deleted, False if not found.
        """
        # First check if record exists
        record = self.get(record_id)
        if not record:
            return False
        
        # Delete sync metadata first
        self._delete_sync_metadata(record_id)
        
        # Delete the record
        query = f"DELETE FROM {self.table_name} WHERE id = ?"
        self._db.execute(query, (record_id,))
        
        return True
    
    def count(self, where: str | None = None, params: tuple[Any, ...] = ()) -> int:
        """
        Count records matching optional criteria.
        
        Args:
            where: Optional WHERE clause.
            params: Parameters for the WHERE clause.
        
        Returns:
            Number of matching records.
        """
        query = f"SELECT COUNT(*) FROM {self.table_name}"
        
        if where:
            query += f" WHERE {where}"
        
        result = self._db.execute(query, params, fetch=True)
        return result[0] if result else 0
    
    def exists(self, record_id: str) -> bool:
        """Check if a record exists."""
        return self.get(record_id) is not None
    
    # -------------------------------------------------------------------------
    # Sync-related methods
    # -------------------------------------------------------------------------
    
    def get_unsynced(
        self,
        limit: int | None = None,
        status: SyncStatus | None = None,
    ) -> list[T]:
        """
        Get records that haven't been synchronized.
        
        Args:
            limit: Maximum number of records to return.
            status: Optional specific sync status to filter by.
        
        Returns:
            List of unsynced records.
        """
        where = "is_synced = 0"
        params: list[Any] = []
        
        if status is not None:
            where += " AND sync_status_code = ?"
            params.append(status.value if hasattr(status, 'value') else int(status))
        
        order_by = "created_at ASC"
        
        return self.get_all(where=where, params=tuple(params), order_by=order_by, limit=limit)
    
    def mark_as_synced(self, record_id: str, remote_id: str | None = None) -> bool:
        """
        Mark a record as successfully synchronized.
        
        Args:
            record_id: The local record ID.
            remote_id: Optional remote server ID.
        
        Returns:
            True if updated, False if record not found.
        """
        query = f"""
            UPDATE {self.table_name}
            SET is_synced = 1, sync_status_code = ?, updated_at = ?
            WHERE id = ?
        """
        
        now = datetime.utcnow().strftime(DATETIME_FORMAT_ISO)
        result = self._db.execute(query, (SyncStatus.SYNCED, now, record_id))
        
        # Update sync metadata
        if remote_id:
            self._db.execute(
                "UPDATE sync_metadata SET is_synced = 1, sync_status_code = ?, remote_id = ? WHERE record_id = ? AND table_name = ?",
                (SyncStatus.SYNCED, remote_id, record_id, self.table_name)
            )
        else:
            self._db.execute(
                "UPDATE sync_metadata SET is_synced = 1, sync_status_code = ? WHERE record_id = ? AND table_name = ?",
                (SyncStatus.SYNCED, record_id, self.table_name)
            )
        
        return result is not None
    
    def mark_sync_failed(
        self,
        record_id: str,
        status_code: int = SyncStatus.ERROR,
        increment_attempts: bool = True,
    ) -> None:
        """
        Mark a record's sync as failed.
        
        Args:
            record_id: The local record ID.
            status_code: The sync status code to set.
            increment_attempts: Whether to increment the attempt counter.
        """
        now = datetime.utcnow().strftime(DATETIME_FORMAT_ISO)
        
        if increment_attempts:
            self._db.execute(
                f"""UPDATE {self.table_name}
                SET sync_status_code = ?, sync_attempts = sync_attempts + 1, 
                    last_sync_attempt = ?, updated_at = ?
                WHERE id = ?""",
                (status_code, now, now, record_id)
            )
        else:
            self._db.execute(
                f"""UPDATE {self.table_name}
                SET sync_status_code = ?, last_sync_attempt = ?, updated_at = ?
                WHERE id = ?""",
                (status_code, now, now, record_id)
            )
        
        # Update sync metadata
        self._db.execute(
            """UPDATE sync_metadata
            SET sync_status_code = ?, last_sync_attempt = ?
            WHERE record_id = ? AND table_name = ?""",
            (status_code, now, record_id, self.table_name)
        )
    
    # -------------------------------------------------------------------------
    # Sync metadata management
    # -------------------------------------------------------------------------
    
    def _create_sync_metadata(self, record: BaseModel) -> None:
        """Create sync metadata entry for a new record."""
        now = datetime.utcnow().strftime(DATETIME_FORMAT_ISO)
        
        query = """
            INSERT INTO sync_metadata 
            (id, table_name, record_id, created_at, updated_at, is_synced, sync_status_code)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        self._db.execute(query, (
            self._generate_id(),
            self.table_name,
            record.id,
            record.created_at or now,
            record.updated_at or now,
            0,
            SyncStatus.PENDING,
        ))
    
    def _update_sync_metadata(self, record: BaseModel) -> None:
        """Update sync metadata when record is modified."""
        query = """
            UPDATE sync_metadata
            SET updated_at = ?, is_synced = 0, sync_status_code = ?
            WHERE record_id = ? AND table_name = ?
        """
        
        self._db.execute(query, (
            record.updated_at,
            SyncStatus.PENDING,
            record.id,
            self.table_name,
        ))
    
    def _delete_sync_metadata(self, record_id: str) -> None:
        """Delete sync metadata for a record."""
        query = "DELETE FROM sync_metadata WHERE record_id = ? AND table_name = ?"
        self._db.execute(query, (record_id, self.table_name))
    
    def get_sync_metadata(self, record_id: str) -> SyncMetadata | None:
        """Get sync metadata for a record."""
        query = """
            SELECT * FROM sync_metadata
            WHERE record_id = ? AND table_name = ?
        """
        row = self._db.execute(query, (record_id, self.table_name), fetch=True)
        
        if row:
            return SyncMetadata.from_row(row)
        return None
    
    # -------------------------------------------------------------------------
    # Helper methods - to be implemented by subclasses
    # -------------------------------------------------------------------------
    
    @abstractmethod
    def _prepare_insert_data(self, record: T) -> tuple[list[str], list[Any]]:
        """
        Prepare column names and values for INSERT statement.
        
        Returns:
            Tuple of (column_names, values).
        """
        raise NotImplementedError
    
    @abstractmethod
    def _prepare_update_data(self, record: T) -> tuple[str, list[Any]]:
        """
        Prepare SET clause and values for UPDATE statement.
        
        Returns:
            Tuple of (set_clause, values).
        """
        raise NotImplementedError


# =============================================================================
# Concrete Repository Implementations
# =============================================================================

class IncidentRepository(Repository[Incident]):
    """Repository for Incident records."""
    
    @property
    def table_name(self) -> str:
        return "incidents"
    
    @property
    def model_class(self) -> type[Incident]:
        return Incident
    
    def _prepare_insert_data(self, record: Incident) -> tuple[list[str], list[Any]]:
        columns = [
            "id", "incident_number", "title", "description",
            "location_type", "location_details", "latitude", "longitude",
            "severity_code", "incident_datetime", "reporter_id", "reporter_name",
            "photo_path", "witnesses", "immediate_actions", "root_cause",
            "corrective_actions", "status",
            "created_at", "updated_at", "is_synced", "sync_status_code"
        ]
        values = [
            record.id, record.incident_number, record.title, record.description,
            record.location_type, record.location_details, record.latitude, record.longitude,
            record.severity_code, record.incident_datetime, record.reporter_id, record.reporter_name,
            record.photo_path, record.witnesses, record.immediate_actions, record.root_cause,
            record.corrective_actions, record.status,
            record.created_at, record.updated_at,
            0 if not record.is_synced else 1, record.sync_status_code
        ]
        return columns, values
    
    def _prepare_update_data(self, record: Incident) -> tuple[str, list[Any]]:
        set_parts = [
            "incident_number = ?", "title = ?", "description = ?",
            "location_type = ?", "location_details = ?", "latitude = ?", "longitude = ?",
            "severity_code = ?", "incident_datetime = ?", "reporter_id = ?", "reporter_name = ?",
            "photo_path = ?", "witnesses = ?", "immediate_actions = ?", "root_cause = ?",
            "corrective_actions = ?", "status = ?",
            "updated_at = ?", "is_synced = ?", "sync_status_code = ?"
        ]
        values = [
            record.incident_number, record.title, record.description,
            record.location_type, record.location_details, record.latitude, record.longitude,
            record.severity_code, record.incident_datetime, record.reporter_id, record.reporter_name,
            record.photo_path, record.witnesses, record.immediate_actions, record.root_cause,
            record.corrective_actions, record.status,
            record.updated_at,
            0 if not record.is_synced else 1, record.sync_status_code
        ]
        return ", ".join(set_parts), values
    
    def get_by_reporter(self, reporter_id: str) -> list[Incident]:
        """Get all incidents reported by a specific user."""
        return self.get_all(where="reporter_id = ?", params=(reporter_id,))
    
    def get_by_severity(self, severity_code: str) -> list[Incident]:
        """Get all incidents with a specific severity level."""
        return self.get_all(where="severity_code = ?", params=(severity_code,))
    
    def get_recent(self, days: int = 30) -> list[Incident]:
        """Get incidents from the last N days."""
        where = f"incident_datetime >= datetime('now', '-{days} days')"
        return self.get_all(where=where, order_by="incident_datetime DESC")


class EmployeeRepository(Repository[Employee]):
    """Repository for Employee records."""
    
    @property
    def table_name(self) -> str:
        return "employees"
    
    @property
    def model_class(self) -> type[Employee]:
        return Employee
    
    def _prepare_insert_data(self, record: Employee) -> tuple[list[str], list[Any]]:
        columns = [
            "id", "employee_number", "first_name", "last_name",
            "email", "phone", "company", "trade", "role", "is_active",
            "created_at", "updated_at", "is_synced", "sync_status_code"
        ]
        values = [
            record.id, record.employee_number, record.first_name, record.last_name,
            record.email, record.phone, record.company, record.trade, record.role,
            1 if record.is_active else 0,
            record.created_at, record.updated_at,
            0 if not record.is_synced else 1, record.sync_status_code
        ]
        return columns, values
    
    def _prepare_update_data(self, record: Employee) -> tuple[str, list[Any]]:
        set_parts = [
            "employee_number = ?", "first_name = ?", "last_name = ?",
            "email = ?", "phone = ?", "company = ?", "trade = ?", "role = ?",
            "is_active = ?", "updated_at = ?", "is_synced = ?", "sync_status_code = ?"
        ]
        values = [
            record.employee_number, record.first_name, record.last_name,
            record.email, record.phone, record.company, record.trade, record.role,
            1 if record.is_active else 0,
            record.updated_at,
            0 if not record.is_synced else 1, record.sync_status_code
        ]
        return ", ".join(set_parts), values
    
    def get_by_number(self, employee_number: str) -> Employee | None:
        """Get employee by employee number."""
        row = self._db.execute(
            f"SELECT * FROM {self.table_name} WHERE employee_number = ?",
            (employee_number,),
            fetch=True
        )
        if row:
            return Employee.from_row(row)
        return None
    
    def get_active(self) -> list[Employee]:
        """Get all active employees."""
        return self.get_all(where="is_active = 1", order_by="last_name, first_name")
    
    def search(self, query: str) -> list[Employee]:
        """Search employees by name or number."""
        search_term = f"%{query}%"
        return self.get_all(
            where="(first_name LIKE ? OR last_name LIKE ? OR employee_number LIKE ?)",
            params=(search_term, search_term, search_term),
            order_by="last_name, first_name"
        )


class TrainingLogRepository(Repository[TrainingLog]):
    """Repository for TrainingLog records."""
    
    @property
    def table_name(self) -> str:
        return "training_logs"
    
    @property
    def model_class(self) -> type[TrainingLog]:
        return TrainingLog
    
    def _prepare_insert_data(self, record: TrainingLog) -> tuple[list[str], list[Any]]:
        columns = [
            "id", "employee_id", "course_name", "course_code",
            "provider", "instructor", "duration_hours", "completion_date",
            "expiry_date", "score", "certificate_number", "status", "notes",
            "created_at", "updated_at", "is_synced", "sync_status_code"
        ]
        values = [
            record.id, record.employee_id, record.course_name, record.course_code,
            record.provider, record.instructor, record.duration_hours, record.completion_date,
            record.expiry_date, record.score, record.certificate_number, record.status, record.notes,
            record.created_at, record.updated_at,
            0 if not record.is_synced else 1, record.sync_status_code
        ]
        return columns, values
    
    def _prepare_update_data(self, record: TrainingLog) -> tuple[str, list[Any]]:
        set_parts = [
            "employee_id = ?", "course_name = ?", "course_code = ?",
            "provider = ?", "instructor = ?", "duration_hours = ?",
            "completion_date = ?", "expiry_date = ?", "score = ?",
            "certificate_number = ?", "status = ?", "notes = ?",
            "updated_at = ?", "is_synced = ?", "sync_status_code = ?"
        ]
        values = [
            record.employee_id, record.course_name, record.course_code,
            record.provider, record.instructor, record.duration_hours,
            record.completion_date, record.expiry_date, record.score,
            record.certificate_number, record.status, record.notes,
            record.updated_at,
            0 if not record.is_synced else 1, record.sync_status_code
        ]
        return ", ".join(set_parts), values
    
    def get_by_employee(self, employee_id: str) -> list[TrainingLog]:
        """Get all training logs for an employee."""
        return self.get_all(where="employee_id = ?", params=(employee_id,))
    
    def get_expiring_soon(self, days: int = 30) -> list[TrainingLog]:
        """Get training records expiring within N days."""
        where = f"""
            expiry_date IS NOT NULL 
            AND expiry_date <= date('now', '+{days} days')
            AND expiry_date >= date('now')
        """
        return self.get_all(where=where, order_by="expiry_date ASC")
    
    def get_expired(self) -> list[TrainingLog]:
        """Get expired training records."""
        return self.get_all(
            where="expiry_date < date('now')",
            order_by="expiry_date ASC"
        )


class AuditReportRepository(Repository[AuditReport]):
    """Repository for AuditReport records."""
    
    def __init__(self, db_manager: DatabaseManager | None = None):
        super().__init__(db_manager)
        self._check_item_repo = AuditCheckItemRepository(db_manager)
    
    @property
    def table_name(self) -> str:
        return "audit_reports"
    
    @property
    def model_class(self) -> type[AuditReport]:
        return AuditReport
    
    def _prepare_insert_data(self, record: AuditReport) -> tuple[list[str], list[Any]]:
        columns = [
            "id", "audit_number", "title", "auditor_id", "auditor_name",
            "audit_date", "location", "audit_type", "overall_status",
            "overall_score", "findings", "recommendations", "follow_up_date",
            "status", "created_at", "updated_at", "is_synced", "sync_status_code"
        ]
        values = [
            record.id, record.audit_number, record.title, record.auditor_id, record.auditor_name,
            record.audit_date, record.location, record.audit_type, record.overall_status,
            record.overall_score, record.findings, record.recommendations, record.follow_up_date,
            record.status,
            record.created_at, record.updated_at,
            0 if not record.is_synced else 1, record.sync_status_code
        ]
        return columns, values
    
    def _prepare_update_data(self, record: AuditReport) -> tuple[str, list[Any]]:
        set_parts = [
            "audit_number = ?", "title = ?", "auditor_id = ?", "auditor_name = ?",
            "audit_date = ?", "location = ?", "audit_type = ?", "overall_status = ?",
            "overall_score = ?", "findings = ?", "recommendations = ?",
            "follow_up_date = ?", "status = ?",
            "updated_at = ?", "is_synced = ?", "sync_status_code = ?"
        ]
        values = [
            record.audit_number, record.title, record.auditor_id, record.auditor_name,
            record.audit_date, record.location, record.audit_type, record.overall_status,
            record.overall_score, record.findings, record.recommendations,
            record.follow_up_date, record.status,
            record.updated_at,
            0 if not record.is_synced else 1, record.sync_status_code
        ]
        return ", ".join(set_parts), values
    
    def get_with_items(self, audit_id: str) -> AuditReport | None:
        """Get an audit report with all its check items."""
        report = self.get(audit_id)
        if report:
            report.check_items = self._check_item_repo.get_by_audit(audit_id)
        return report
    
    def get_by_auditor(self, auditor_id: str) -> list[AuditReport]:
        """Get all audit reports by a specific auditor."""
        return self.get_all(where="auditor_id = ?", params=(auditor_id,))
    
    def get_by_status(self, status: str) -> list[AuditReport]:
        """Get audit reports with a specific status."""
        return self.get_all(where="status = ?", params=(status,))


class AuditCheckItemRepository(Repository[AuditCheckItem]):
    """Repository for AuditCheckItem records."""
    
    @property
    def table_name(self) -> str:
        return "audit_check_items"
    
    @property
    def model_class(self) -> type[AuditCheckItem]:
        return AuditCheckItem
    
    def _prepare_insert_data(self, record: AuditCheckItem) -> tuple[list[str], list[Any]]:
        columns = [
            "id", "audit_id", "category_code", "item_description",
            "status_code", "comments", "photo_evidence_path",
            "created_at", "updated_at", "is_synced", "sync_status_code"
        ]
        values = [
            record.id, record.audit_id, record.category_code, record.item_description,
            record.status_code, record.comments, record.photo_evidence_path,
            record.created_at, record.updated_at,
            0 if not record.is_synced else 1, record.sync_status_code
        ]
        return columns, values
    
    def _prepare_update_data(self, record: AuditCheckItem) -> tuple[str, list[Any]]:
        set_parts = [
            "audit_id = ?", "category_code = ?", "item_description = ?",
            "status_code = ?", "comments = ?", "photo_evidence_path = ?",
            "updated_at = ?", "is_synced = ?", "sync_status_code = ?"
        ]
        values = [
            record.audit_id, record.category_code, record.item_description,
            record.status_code, record.comments, record.photo_evidence_path,
            record.updated_at,
            0 if not record.is_synced else 1, record.sync_status_code
        ]
        return ", ".join(set_parts), values
    
    def get_by_audit(self, audit_id: str) -> list[AuditCheckItem]:
        """Get all check items for an audit report."""
        return self.get_all(where="audit_id = ?", params=(audit_id,))
    
    def get_by_category(self, category_code: str) -> list[AuditCheckItem]:
        """Get check items by category."""
        return self.get_all(where="category_code = ?", params=(category_code,))
    
    def delete_by_audit(self, audit_id: str) -> int:
        """Delete all check items for an audit report."""
        items = self.get_by_audit(audit_id)
        for item in items:
            self.delete(item.id)
        return len(items)


# =============================================================================
# Repository Factory
# =============================================================================

class RepositoryFactory:
    """Factory for creating repository instances."""
    
    _instances: dict[str, Repository[Any]] = {}
    
    @classmethod
    def get_incident_repo(cls, db_manager: DatabaseManager | None = None) -> IncidentRepository:
        """Get or create an IncidentRepository."""
        key = "incident"
        if key not in cls._instances:
            cls._instances[key] = IncidentRepository(db_manager)
        return cls._instances[key]
    
    @classmethod
    def get_employee_repo(cls, db_manager: DatabaseManager | None = None) -> EmployeeRepository:
        """Get or create an EmployeeRepository."""
        key = "employee"
        if key not in cls._instances:
            cls._instances[key] = EmployeeRepository(db_manager)
        return cls._instances[key]
    
    @classmethod
    def get_training_repo(cls, db_manager: DatabaseManager | None = None) -> TrainingLogRepository:
        """Get or create a TrainingLogRepository."""
        key = "training"
        if key not in cls._instances:
            cls._instances[key] = TrainingLogRepository(db_manager)
        return cls._instances[key]
    
    @classmethod
    def get_audit_repo(cls, db_manager: DatabaseManager | None = None) -> AuditReportRepository:
        """Get or create an AuditReportRepository."""
        key = "audit"
        if key not in cls._instances:
            cls._instances[key] = AuditReportRepository(db_manager)
        return cls._instances[key]
    
    @classmethod
    def get_audit_item_repo(cls, db_manager: DatabaseManager | None = None) -> AuditCheckItemRepository:
        """Get or create an AuditCheckItemRepository."""
        key = "audit_item"
        if key not in cls._instances:
            cls._instances[key] = AuditCheckItemRepository(db_manager)
        return cls._instances[key]
    
    @classmethod
    def reset(cls) -> None:
        """Reset all repository instances (useful for testing)."""
        cls._instances.clear()