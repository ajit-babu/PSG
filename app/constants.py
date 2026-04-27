"""
PSG - Professional Safety Guardian
Application Constants and Enumerations

This module defines all application-wide constants, enumerations,
and fixed values used throughout the application.
"""

from enum import Enum, IntEnum
from typing import Final


# =============================================================================
# Application Constants
# =============================================================================

# Application identifiers
APP_ID: Final[str] = "com.psgsafety.desktop"
APP_NAME: Final[str] = "PSG - Professional Safety Guardian"
APP_VERSION: Final[str] = "1.0.0"

# Organization info
ORGANIZATION: Final[str] = "PSG Safety Solutions"
ORG_DOMAIN: Final[str] = "psg-safety.com"
ORGANIZATION_DOMAIN: Final[str] = "psg-safety.com"  # Alias for compatibility

# File paths
DATABASE_FILENAME: Final[str] = "psg.db"
CONFIG_FILENAME: Final[str] = "config.json"
LOG_FILENAME: Final[str] = "psg.log"
BACKUP_DIR: Final[str] = "backups"
PHOTOS_DIR: Final[str] = "photos"
EXPORT_DIR: Final[str] = "exports"

# Database
DATABASE_BACKUP_RETENTION_DAYS: Final[int] = 30
DATABASE_CONNECTION_TIMEOUT: Final[float] = 5.0

# Default API configuration
DEFAULT_API_TIMEOUT: Final[int] = 30
DEFAULT_RETRY_ATTEMPTS: Final[int] = 3
DEFAULT_BACKOFF_FACTOR: Final[int] = 2
DEFAULT_BATCH_SIZE: Final[int] = 50
DEFAULT_SYNC_INTERVAL_MINUTES: Final[int] = 5

# UI Constants
DEFAULT_WINDOW_WIDTH: Final[int] = 1280
DEFAULT_WINDOW_HEIGHT: Final[int] = 800
MIN_WINDOW_WIDTH: Final[int] = 1024
MIN_WINDOW_HEIGHT: Final[int] = 600

# Font sizes
FONT_SIZE_SMALL: Final[int] = 10
FONT_SIZE_NORMAL: Final[int] = 12
FONT_SIZE_LARGE: Final[int] = 14
FONT_SIZE_XLARGE: Final[int] = 18

# Icon sizes
ICON_SIZE_SMALL: Final[int] = 16
ICON_SIZE_NORMAL: Final[int] = 24
ICON_SIZE_LARGE: Final[int] = 32
ICON_SIZE_XLARGE: Final[int] = 48


# =============================================================================
# Severity Levels for Incidents
# =============================================================================

class SeverityLevel(Enum):
    """Incident severity classification levels."""
    
    NEAR_MISS = "near_miss", "Near Miss", "#FFA726"      # Orange
    MINOR = "minor", "Minor", "#66BB6A"                   # Green
    MODERATE = "moderate", "Moderate", "#FFEE58"          # Yellow
    MAJOR = "major", "Major", "#FF8A65"                   # Light Red
    CRITICAL = "critical", "Critical", "#F44336"          # Red
    FATAL = "fatal", "Fatal", "#B71C1C"                   # Dark Red
    
    def __init__(self, code: str, display_name: str, color: str):
        self.code = code
        self.display_name = display_name
        self.color = color
    
    @classmethod
    def from_code(cls, code: str) -> "SeverityLevel":
        """Get severity level from code string."""
        for level in cls:
            if level.code == code:
                return level
        return cls.NEAR_MISS  # Default fallback
    
    @classmethod
    def all_options(cls) -> list[tuple[str, str]]:
        """Get all severity levels as (code, display_name) tuples."""
        return [(level.code, level.display_name) for level in cls]


# =============================================================================
# Sync Status Codes
# =============================================================================

class SyncStatus(IntEnum):
    """Synchronization status codes for tracking record sync state."""
    
    PENDING = 0           # Record created/modified, waiting for sync
    SYNCING = 1           # Currently being synchronized
    SYNCED = 2            # Successfully synchronized
    CONFLICT = 3          # Conflict detected during sync
    ERROR = 4             # Sync failed with error
    RETRY = 5             # Scheduled for retry
    DELETED_REMOTE = 6    # Record deleted on remote
    MERGED = 7            # Conflict resolved via merge


SYNC_STATUS_NAMES: Final[dict[SyncStatus, str]] = {
    SyncStatus.PENDING: "Pending",
    SyncStatus.SYNCING: "Syncing",
    SyncStatus.SYNCED: "Synced",
    SyncStatus.CONFLICT: "Conflict",
    SyncStatus.ERROR: "Error",
    SyncStatus.RETRY: "Retry",
    SyncStatus.DELETED_REMOTE: "Deleted (Remote)",
    SyncStatus.MERGED: "Merged",
}

SYNC_STATUS_COLORS: Final[dict[SyncStatus, str]] = {
    SyncStatus.PENDING: "#FFA726",     # Orange
    SyncStatus.SYNCING: "#42A5F5",     # Blue
    SyncStatus.SYNCED: "#66BB6A",      # Green
    SyncStatus.CONFLICT: "#AB47BC",    # Purple
    SyncStatus.ERROR: "#EF5350",       # Red
    SyncStatus.RETRY: "#FFA726",       # Orange
    SyncStatus.DELETED_REMOTE: "#BDBDBD",  # Gray
    SyncStatus.MERGED: "#26A69A",      # Teal
}


# =============================================================================
# Training Status
# =============================================================================

class TrainingStatus(Enum):
    """Training/compliance status enumeration."""
    
    NOT_STARTED = "not_started", "Not Started", "#BDBDBD"
    IN_PROGRESS = "in_progress", "In Progress", "#42A5F5"
    COMPLETED = "completed", "Completed", "#66BB6A"
    EXPIRING_SOON = "expiring_soon", "Expiring Soon", "#FFA726"  # Within 30 days
    EXPIRED = "expired", "Expired", "#EF5350"
    
    def __init__(self, code: str, display_name: str, color: str):
        self.code = code
        self.display_name = display_name
        self.color = color


# =============================================================================
# Audit/Inspection Status
# =============================================================================

class AuditStatus(Enum):
    """Audit/inspection result status."""
    
    PASS = "pass", "Pass", "#66BB6A"
    FAIL = "fail", "Fail", "#EF5350"
    CONDITIONAL = "conditional", "Conditional Pass", "#FFA726"
    NOT_APPLICABLE = "not_applicable", "N/A", "#BDBDBD"
    PENDING = "pending", "Pending Review", "#42A5F5"
    
    def __init__(self, code: str, display_name: str, color: str):
        self.code = code
        self.display_name = display_name
        self.color = color


# =============================================================================
# User Roles
# =============================================================================

class UserRole(Enum):
    """User role permissions."""
    
    ADMIN = "admin", "Administrator"
    SAFETY_OFFICER = "safety_officer", "Safety Officer"
    SITE_MANAGER = "site_manager", "Site Manager"
    SUPERVISOR = "supervisor", "Supervisor"
    WORKER = "worker", "Worker"
    AUDITOR = "auditor", "Auditor"
    
    def __init__(self, code: str, display_name: str):
        self.code = code
        self.display_name = display_name


# =============================================================================
# Location Types (UAE-specific)
# =============================================================================

class LocationType(Enum):
    """Types of construction site locations."""
    
    MAIN_SITE = "main_site", "Main Construction Site"
    WAREHOUSE = "warehouse", "Warehouse/Storage"
    OFFICE = "office", "Site Office"
    PARKING = "parking", "Parking Area"
    ENTRANCE = "entrance", "Site Entrance"
    MECHANICAL_ROOM = "mechanical_room", "Mechanical Room"
    ELECTRICAL_ROOM = "electrical_room", "Electrical Room"
    HVAC_AREA = "hvac_area", "HVAC Area"
    PLUMBING_AREA = "plumbing_area", "Plumbing Area"
    FIRE_SAFETY = "fire_safety", "Fire Safety Zone"
    OTHER = "other", "Other"
    
    def __init__(self, code: str, display_name: str):
        self.code = code
        self.display_name = display_name


# =============================================================================
# Compliance Check Categories
# =============================================================================

class ComplianceCategory(Enum):
    """Categories for compliance/audit checks."""
    
    PERSONAL_PROTECTIVE_EQUIPMENT = "ppe", "Personal Protective Equipment (PPE)"
    ELECTRICAL_SAFETY = "electrical", "Electrical Safety"
    FIRE_SAFETY = "fire", "Fire Safety"
    WORKING_AT_HEIGHT = "height", "Working at Height"
    CONFINED_SPACE = "confined_space", "Confined Space"
    MACHINERY_EQUIPMENT = "machinery", "Machinery & Equipment"
    HAZARDOUS_MATERIALS = "hazmat", "Hazardous Materials"
    ENVIRONMENTAL = "environmental", "Environmental"
    FIRST_AID = "first_aid", "First Aid"
    SIGNAGE = "signage", "Safety Signage"
    HOUSEKEEPING = "housekeeping", "Housekeeping"
    EMERGENCY_PREPAREDNESS = "emergency", "Emergency Preparedness"
    
    def __init__(self, code: str, display_name: str):
        self.code = code
        self.display_name = display_name


# =============================================================================
# Network/Connectivity
# =============================================================================

class ConnectivityStatus(Enum):
    """Network connectivity status."""
    
    ONLINE = "online", "Online"
    OFFLINE = "offline", "Offline"
    UNKNOWN = "unknown", "Unknown"
    
    def __init__(self, code: str, display_name: str):
        self.code = code
        self.display_name = display_name


# =============================================================================
# Date/Time Formats
# =============================================================================

DATETIME_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
DATETIME_FORMAT_ISO: Final[str] = "%Y-%m-%dT%H:%M:%S.%fZ"
DATE_FORMAT: Final[str] = "%Y-%m-%d"
DATE_FORMAT_DISPLAY: Final[str] = "%d %b %Y"
TIME_FORMAT: Final[str] = "%H:%M:%S"

# UAE Weekend (Friday-Saturday)
UAE_WEEKEND_DAYS: Final[set[int]] = {4, 5}  # Friday=4, Saturday=5 (Python weekday)