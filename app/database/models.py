"""
PSG - Professional Safety Guardian
Data Models Module

This module defines data classes and model helpers for the application's
database entities, providing type-safe data manipulation and serialization.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from app.constants import (
    DATETIME_FORMAT,
    DATETIME_FORMAT_ISO,
    SyncStatus,
)


@dataclass
class SyncMetadata:
    """
    Sync metadata for tracking record synchronization state.
    
    Every syncable table should have a corresponding sync_metadata entry
    that tracks whether the record has been synchronized with the remote server.
    """
    
    id: str
    table_name: str
    record_id: str
    created_at: str
    updated_at: str
    is_synced: bool = False
    sync_status_code: int = SyncStatus.PENDING
    sync_attempts: int = 0
    last_sync_attempt: str | None = None
    remote_id: str | None = None
    
    @property
    def sync_status(self) -> SyncStatus:
        """Get the sync status as an enum."""
        return SyncStatus(self.sync_status_code)
    
    @property
    def needs_sync(self) -> bool:
        """Check if this record needs to be synchronized."""
        return not self.is_synced and self.sync_status_code != SyncStatus.DELETED_REMOTE
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_row(cls, row: Any) -> "SyncMetadata":
        """Create instance from database row."""
        return cls(
            id=row["id"],
            table_name=row["table_name"],
            record_id=row["record_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            is_synced=bool(row["is_synced"]),
            sync_status_code=int(row["sync_status_code"]),
            sync_attempts=int(row.get("sync_attempts", 0)),
            last_sync_attempt=row.get("last_sync_attempt"),
            remote_id=row.get("remote_id"),
        )


@dataclass
class BaseModel:
    """
    Base model class with common fields and methods.
    
    All database entities should inherit from this class to get
    standard sync metadata fields and serialization methods.
    """
    
    id: str = field(default_factory=lambda: "")
    created_at: str = field(default_factory=lambda: "")
    updated_at: str = field(default_factory=lambda: "")
    is_synced: bool = False
    sync_status_code: int = field(default=SyncStatus.PENDING)
    
    def mark_modified(self) -> None:
        """Mark this record as modified and needing sync."""
        self.updated_at = datetime.utcnow().strftime(DATETIME_FORMAT_ISO)
        self.is_synced = False
        self.sync_status_code = SyncStatus.PENDING
    
    def mark_synced(self, remote_id: str | None = None) -> None:
        """Mark this record as successfully synchronized."""
        self.is_synced = True
        self.sync_status_code = SyncStatus.SYNCED
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_row(cls, row: Any) -> "BaseModel":
        """Create instance from database row. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement from_row()")


@dataclass
class Employee(BaseModel):
    """Employee record model."""
    
    employee_number: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    trade: str | None = None
    role: str | None = None
    is_active: bool = True
    
    @property
    def full_name(self) -> str:
        """Get the employee's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @classmethod
    def from_row(cls, row: Any) -> "Employee":
        """Create Employee instance from database row."""
        return cls(
            id=row["id"],
            employee_number=row["employee_number"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row.get("email"),
            phone=row.get("phone"),
            company=row.get("company"),
            trade=row.get("trade"),
            role=row.get("role"),
            is_active=bool(row.get("is_active", 1)),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            is_synced=bool(row.get("is_synced", 0)),
            sync_status_code=int(row.get("sync_status_code", 0)),
        )


@dataclass
class Incident(BaseModel):
    """
    Safety incident/near-miss report model.
    
    This model stores all information about safety incidents reported
    on construction sites, including location, severity, and follow-up actions.
    """
    
    incident_number: str | None = None
    title: str = ""
    description: str | None = None
    location_type: str = ""
    location_details: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    severity_code: str = ""
    incident_datetime: str = ""
    reporter_id: str = ""
    reporter_name: str = ""
    photo_path: str | None = None
    witnesses: str | None = None
    immediate_actions: str | None = None
    root_cause: str | None = None
    corrective_actions: str | None = None
    status: str = "open"
    
    @classmethod
    def from_row(cls, row: Any) -> "Incident":
        """Create Incident instance from database row."""
        return cls(
            id=row["id"],
            incident_number=row.get("incident_number"),
            title=row["title"],
            description=row.get("description"),
            location_type=row["location_type"],
            location_details=row.get("location_details"),
            latitude=row.get("latitude"),
            longitude=row.get("longitude"),
            severity_code=row["severity_code"],
            incident_datetime=row["incident_datetime"],
            reporter_id=row["reporter_id"],
            reporter_name=row["reporter_name"],
            photo_path=row.get("photo_path"),
            witnesses=row.get("witnesses"),
            immediate_actions=row.get("immediate_actions"),
            root_cause=row.get("root_cause"),
            corrective_actions=row.get("corrective_actions"),
            status=row.get("status", "open"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            is_synced=bool(row.get("is_synced", 0)),
            sync_status_code=int(row.get("sync_status_code", 0)),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization."""
        data = super().to_dict()
        data.update({
            "incident_number": self.incident_number,
            "title": self.title,
            "description": self.description,
            "location_type": self.location_type,
            "location_details": self.location_details,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "severity_code": self.severity_code,
            "incident_datetime": self.incident_datetime,
            "reporter_id": self.reporter_id,
            "reporter_name": self.reporter_name,
            "photo_path": self.photo_path,
            "witnesses": self.witnesses,
            "immediate_actions": self.immediate_actions,
            "root_cause": self.root_cause,
            "corrective_actions": self.corrective_actions,
            "status": self.status,
        })
        return data


@dataclass
class TrainingLog(BaseModel):
    """
    Training and compliance log model.
    
    Tracks employee training records, certifications, and expiry dates
    for compliance monitoring.
    """
    
    employee_id: str = ""
    course_name: str = ""
    course_code: str | None = None
    provider: str | None = None
    instructor: str | None = None
    duration_hours: float | None = None
    completion_date: str | None = None
    expiry_date: str | None = None
    score: float | None = None
    certificate_number: str | None = None
    status: str = ""
    notes: str | None = None
    
    @classmethod
    def from_row(cls, row: Any) -> "TrainingLog":
        """Create TrainingLog instance from database row."""
        return cls(
            id=row["id"],
            employee_id=row["employee_id"],
            course_name=row["course_name"],
            course_code=row.get("course_code"),
            provider=row.get("provider"),
            instructor=row.get("instructor"),
            duration_hours=row.get("duration_hours"),
            completion_date=row.get("completion_date"),
            expiry_date=row.get("expiry_date"),
            score=row.get("score"),
            certificate_number=row.get("certificate_number"),
            status=row["status"],
            notes=row.get("notes"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            is_synced=bool(row.get("is_synced", 0)),
            sync_status_code=int(row.get("sync_status_code", 0)),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization."""
        data = super().to_dict()
        data.update({
            "employee_id": self.employee_id,
            "course_name": self.course_name,
            "course_code": self.course_code,
            "provider": self.provider,
            "instructor": self.instructor,
            "duration_hours": self.duration_hours,
            "completion_date": self.completion_date,
            "expiry_date": self.expiry_date,
            "score": self.score,
            "certificate_number": self.certificate_number,
            "status": self.status,
            "notes": self.notes,
        })
        return data


@dataclass
class AuditCheckItem(BaseModel):
    """
    Individual check item within an audit report.
    
    Each audit report contains multiple check items, each evaluating
    a specific compliance requirement.
    """
    
    audit_id: str = ""
    category_code: str = ""
    item_description: str = ""
    status_code: str = ""
    comments: str | None = None
    photo_evidence_path: str | None = None
    
    @classmethod
    def from_row(cls, row: Any) -> "AuditCheckItem":
        """Create AuditCheckItem instance from database row."""
        return cls(
            id=row["id"],
            audit_id=row["audit_id"],
            category_code=row["category_code"],
            item_description=row["item_description"],
            status_code=row["status_code"],
            comments=row.get("comments"),
            photo_evidence_path=row.get("photo_evidence_path"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            is_synced=bool(row.get("is_synced", 0)),
            sync_status_code=int(row.get("sync_status_code", 0)),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization."""
        data = super().to_dict()
        data.update({
            "audit_id": self.audit_id,
            "category_code": self.category_code,
            "item_description": self.item_description,
            "status_code": self.status_code,
            "comments": self.comments,
            "photo_evidence_path": self.photo_evidence_path,
        })
        return data


@dataclass
class AuditReport(BaseModel):
    """
    Audit/inspection report model.
    
    Comprehensive audit reports containing multiple check items,
    overall assessment, and recommendations.
    """
    
    audit_number: str | None = None
    title: str = ""
    auditor_id: str = ""
    auditor_name: str = ""
    audit_date: str = ""
    location: str | None = None
    audit_type: str = ""
    overall_status: str = ""
    overall_score: float | None = None
    findings: str | None = None
    recommendations: str | None = None
    follow_up_date: str | None = None
    status: str = "draft"
    
    # Related check items (not stored in this table)
    check_items: list[AuditCheckItem] = field(default_factory=list)
    
    @classmethod
    def from_row(cls, row: Any) -> "AuditReport":
        """Create AuditReport instance from database row."""
        return cls(
            id=row["id"],
            audit_number=row.get("audit_number"),
            title=row["title"],
            auditor_id=row["auditor_id"],
            auditor_name=row["auditor_name"],
            audit_date=row["audit_date"],
            location=row.get("location"),
            audit_type=row["audit_type"],
            overall_status=row["overall_status"],
            overall_score=row.get("overall_score"),
            findings=row.get("findings"),
            recommendations=row.get("recommendations"),
            follow_up_date=row.get("follow_up_date"),
            status=row.get("status", "draft"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            is_synced=bool(row.get("is_synced", 0)),
            sync_status_code=int(row.get("sync_status_code", 0)),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization."""
        data = super().to_dict()
        data.update({
            "audit_number": self.audit_number,
            "title": self.title,
            "auditor_id": self.auditor_id,
            "auditor_name": self.auditor_name,
            "audit_date": self.audit_date,
            "location": self.location,
            "audit_type": self.audit_type,
            "overall_status": self.overall_status,
            "overall_score": self.overall_score,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "follow_up_date": self.follow_up_date,
            "status": self.status,
        })
        return data


# =============================================================================
# Model Factory Functions
# =============================================================================

def create_incident(
    title: str,
    location_type: str,
    severity_code: str,
    incident_datetime: str,
    reporter_id: str,
    reporter_name: str,
    description: str | None = None,
    location_details: str | None = None,
    photo_path: str | None = None,
) -> Incident:
    """
    Factory function to create a new incident record.
    
    Args:
        title: Brief title for the incident.
        location_type: Type of location where incident occurred.
        severity_code: Severity level code.
        incident_datetime: When the incident occurred.
        reporter_id: ID of the person reporting.
        reporter_name: Name of the person reporting.
        description: Optional detailed description.
        location_details: Optional specific location details.
        photo_path: Optional path to incident photo.
    
    Returns:
        Incident: A new incident instance.
    """
    now = datetime.utcnow().strftime(DATETIME_FORMAT_ISO)
    return Incident(
        id="",  # Will be set by repository
        title=title,
        location_type=location_type,
        severity_code=severity_code,
        incident_datetime=incident_datetime,
        reporter_id=reporter_id,
        reporter_name=reporter_name,
        description=description,
        location_details=location_details,
        photo_path=photo_path,
        status="open",
        created_at=now,
        updated_at=now,
        is_synced=False,
        sync_status_code=SyncStatus.PENDING,
    )


def create_training_log(
    employee_id: str,
    course_name: str,
    status: str,
    completion_date: str | None = None,
    expiry_date: str | None = None,
    score: float | None = None,
    course_code: str | None = None,
    provider: str | None = None,
    instructor: str | None = None,
    duration_hours: float | None = None,
    certificate_number: str | None = None,
    notes: str | None = None,
) -> TrainingLog:
    """
    Factory function to create a new training log entry.
    
    Returns:
        TrainingLog: A new training log instance.
    """
    now = datetime.utcnow().strftime(DATETIME_FORMAT_ISO)
    return TrainingLog(
        id="",  # Will be set by repository
        employee_id=employee_id,
        course_name=course_name,
        status=status,
        completion_date=completion_date,
        expiry_date=expiry_date,
        score=score,
        course_code=course_code,
        provider=provider,
        instructor=instructor,
        duration_hours=duration_hours,
        certificate_number=certificate_number,
        notes=notes,
        created_at=now,
        updated_at=now,
        is_synced=False,
        sync_status_code=SyncStatus.PENDING,
    )


def create_audit_report(
    title: str,
    auditor_id: str,
    auditor_name: str,
    audit_date: str,
    audit_type: str,
    overall_status: str,
    location: str | None = None,
    findings: str | None = None,
    recommendations: str | None = None,
    follow_up_date: str | None = None,
) -> AuditReport:
    """
    Factory function to create a new audit report.
    
    Returns:
        AuditReport: A new audit report instance.
    """
    now = datetime.utcnow().strftime(DATETIME_FORMAT_ISO)
    return AuditReport(
        id="",  # Will be set by repository
        title=title,
        auditor_id=auditor_id,
        auditor_name=auditor_name,
        audit_date=audit_date,
        audit_type=audit_type,
        overall_status=overall_status,
        location=location,
        findings=findings,
        recommendations=recommendations,
        follow_up_date=follow_up_date,
        status="draft",
        created_at=now,
        updated_at=now,
        is_synced=False,
        sync_status_code=SyncStatus.PENDING,
    )


def create_audit_check_item(
    audit_id: str,
    category_code: str,
    item_description: str,
    status_code: str,
    comments: str | None = None,
    photo_evidence_path: str | None = None,
) -> AuditCheckItem:
    """
    Factory function to create a new audit check item.
    
    Returns:
        AuditCheckItem: A new audit check item instance.
    """
    now = datetime.utcnow().strftime(DATETIME_FORMAT_ISO)
    return AuditCheckItem(
        id="",  # Will be set by repository
        audit_id=audit_id,
        category_code=category_code,
        item_description=item_description,
        status_code=status_code,
        comments=comments,
        photo_evidence_path=photo_evidence_path,
        created_at=now,
        updated_at=now,
        is_synced=False,
        sync_status_code=SyncStatus.PENDING,
    )