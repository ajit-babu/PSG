"""
PSG - Professional Safety Guardian
Notification Service Module

This module provides a notification system for user alerts,
including sync status notifications, training expiry warnings,
and system messages.
"""

import logging
import threading
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

from app.config import get_config
from app.database.repository import RepositoryFactory

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications."""
    
    INFO = "info", "Information", "#2196F3"
    SUCCESS = "success", "Success", "#4CAF50"
    WARNING = "warning", "Warning", "#FF9800"
    ERROR = "error", "Error", "#F44336"
    SYNC = "sync", "Sync Status", "#9C27B0"
    TRAINING = "training", "Training Alert", "#00BCD4"
    AUDIT = "audit", "Audit Alert", "#795548"
    
    def __init__(self, code: str, display_name: str, color: str):
        self.code = code
        self.display_name = display_name
        self.color = color


class Notification:
    """Represents a single notification."""
    
    def __init__(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: dict[str, Any] | None = None,
        persistent: bool = False,
    ):
        self.id = datetime.utcnow().timestamp()
        self.type = notification_type
        self.title = title
        self.message = message
        self.data = data or {}
        self.persistent = persistent
        self.created_at = datetime.utcnow()
        self.read = False
        self.acknowledged = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "type_code": self.type.code,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "persistent": self.persistent,
            "created_at": self.created_at.isoformat(),
            "read": self.read,
            "acknowledged": self.acknowledged,
        }


class NotificationService:
    """
    Central notification service for the application.
    
    This service manages system notifications, including:
    - Sync status notifications
    - Training expiry warnings
    - Audit follow-up reminders
    - System alerts
    
    It provides a callback system for UI updates and maintains
    a notification history.
    """
    
    _instance: "NotificationService | None" = None
    _lock: threading.Lock = threading.Lock()
    
    def __init__(self, config: Any | None = None):
        """
        Initialize the notification service.
        
        Args:
            config: Optional configuration object.
        """
        import threading
        self._config = config or get_config()
        
        # Notification storage
        self._notifications: list[Notification] = []
        self._max_history: int = 100
        
        # Callbacks
        self._notification_callbacks: list[Callable[[Notification], None]] = []
        
        # Threading for background checks
        self._check_thread: threading.Thread | None = None
        self._running: bool = False
        
        # Check intervals (in seconds)
        self._training_check_interval: int = 3600  # 1 hour
        self._audit_check_interval: int = 3600  # 1 hour
    
    def __new__(cls, config: Any | None = None) -> "NotificationService":
        """Implement singleton pattern."""
        import threading
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.__init__(config)
        return cls._instance
    
    @classmethod
    def get_instance(cls, config: Any | None = None) -> "NotificationService":
        """Get the singleton instance."""
        import threading
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance."""
        import threading
        with cls._lock:
            if cls._instance is not None:
                cls._instance.stop()
                cls._instance = None
    
    @property
    def unread_count(self) -> int:
        """Get count of unread notifications."""
        return sum(1 for n in self._notifications if not n.read)
    
    @property
    def notifications(self) -> list[Notification]:
        """Get all notifications (newest first)."""
        return sorted(self._notifications, key=lambda n: n.created_at, reverse=True)
    
    def get_unread(self) -> list[Notification]:
        """Get all unread notifications."""
        return [n for n in self._notifications if not n.read]
    
    def get_by_type(self, notification_type: NotificationType) -> list[Notification]:
        """Get notifications of a specific type."""
        return [n for n in self._notifications if n.type == notification_type]
    
    def on_notification(self, callback: Callable[[Notification], None]) -> None:
        """
        Register a callback for new notifications.
        
        Args:
            callback: Function to call when notification is created.
        """
        self._notification_callbacks.append(callback)
    
    def remove_notification_callback(self, callback: Callable[[Notification], None]) -> None:
        """Remove a notification callback."""
        if callback in self._notification_callbacks:
            self._notification_callbacks.remove(callback)
    
    def _notify(self, notification: Notification) -> None:
        """
        Process and store a notification.
        
        Args:
            notification: The notification to process.
        """
        # Store notification
        self._notifications.append(notification)
        
        # Trim history if needed
        if len(self._notifications) > self._max_history:
            # Remove old non-persistent notifications
            self._notifications = [
                n for n in self._notifications 
                if n.persistent or n.read
            ][-self._max_history:]
        
        # Notify callbacks
        for callback in self._notification_callbacks:
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"Error in notification callback: {e}")
    
    # -------------------------------------------------------------------------
    # Notification Creation Methods
    # -------------------------------------------------------------------------
    
    def notify_sync_status(
        self,
        success: bool,
        records_synced: int,
        records_failed: int,
        errors: list[str] | None = None,
    ) -> None:
        """
        Notify about sync operation status.
        
        Args:
            success: Whether sync was successful.
            records_synced: Number of records synced.
            records_failed: Number of records that failed.
            errors: Optional list of error messages.
        """
        if success:
            notification = Notification(
                NotificationType.SYNC,
                "Sync Completed",
                f"Successfully synced {records_synced} records.",
                data={
                    "records_synced": records_synced,
                    "records_failed": records_failed,
                },
            )
        else:
            notification = Notification(
                NotificationType.SYNC,
                "Sync Failed",
                f"Sync failed. {records_failed} records could not be synced.",
                data={
                    "records_synced": records_synced,
                    "records_failed": records_failed,
                    "errors": errors or [],
                },
                persistent=True,
            )
        
        self._notify(notification)
    
    def notify_sync_offline(self) -> None:
        """Notify that the system is offline and sync is pending."""
        notification = Notification(
            NotificationType.SYNC,
            "Offline Mode",
            "No internet connection. Data will sync when connection is restored.",
            persistent=False,
        )
        self._notify(notification)
    
    def notify_training_expiring(
        self,
        employee_name: str,
        course_name: str,
        expiry_date: str,
        days_remaining: int,
    ) -> None:
        """
        Notify about expiring training.
        
        Args:
            employee_name: Name of the employee.
            course_name: Name of the training course.
            expiry_date: Training expiry date.
            days_remaining: Days until expiry.
        """
        if days_remaining <= 0:
            severity = NotificationType.ERROR
            title = "Training Expired"
            message = f"{employee_name}'s {course_name} training has expired."
        elif days_remaining <= 7:
            severity = NotificationType.WARNING
            title = "Training Expiring Soon"
            message = f"{employee_name}'s {course_name} expires in {days_remaining} days."
        else:
            severity = NotificationType.TRAINING
            title = "Training Expiry Notice"
            message = f"{employee_name}'s {course_name} expires on {expiry_date}."
        
        notification = Notification(
            severity,
            title,
            message,
            data={
                "employee_name": employee_name,
                "course_name": course_name,
                "expiry_date": expiry_date,
                "days_remaining": days_remaining,
            },
            persistent=True,
        )
        self._notify(notification)
    
    def notify_audit_follow_up(
        self,
        audit_title: str,
        follow_up_date: str,
        days_until: int,
    ) -> None:
        """
        Notify about upcoming audit follow-up.
        
        Args:
            audit_title: Title of the audit.
            follow_up_date: Scheduled follow-up date.
            days_until: Days until follow-up.
        """
        if days_until <= 0:
            severity = NotificationType.AUDIT
            title = "Audit Follow-Up Due"
            message = f"Follow-up for '{audit_title}' is overdue."
        elif days_until <= 3:
            severity = NotificationType.WARNING
            title = "Audit Follow-Up Soon"
            message = f"Follow-up for '{audit_title}' is due in {days_until} days."
        else:
            return  # Not urgent enough to notify
        
        notification = Notification(
            severity,
            title,
            message,
            data={
                "audit_title": audit_title,
                "follow_up_date": follow_up_date,
                "days_until": days_until,
            },
            persistent=True,
        )
        self._notify(notification)
    
    def notify_info(self, title: str, message: str, data: dict[str, Any] | None = None) -> None:
        """Send an informational notification."""
        self._notify(Notification(NotificationType.INFO, title, message, data))
    
    def notify_success(self, title: str, message: str, data: dict[str, Any] | None = None) -> None:
        """Send a success notification."""
        self._notify(Notification(NotificationType.SUCCESS, title, message, data))
    
    def notify_warning(self, title: str, message: str, data: dict[str, Any] | None = None) -> None:
        """Send a warning notification."""
        self._notify(Notification(NotificationType.WARNING, title, message, data, persistent=True))
    
    def notify_error(self, title: str, message: str, data: dict[str, Any] | None = None) -> None:
        """Send an error notification."""
        self._notify(Notification(NotificationType.ERROR, title, message, data, persistent=True))
    
    # -------------------------------------------------------------------------
    # Notification Management
    # -------------------------------------------------------------------------
    
    def mark_as_read(self, notification_id: float) -> None:
        """Mark a notification as read."""
        for notification in self._notifications:
            if notification.id == notification_id:
                notification.read = True
                break
    
    def mark_all_as_read(self) -> None:
        """Mark all notifications as read."""
        for notification in self._notifications:
            notification.read = True
    
    def acknowledge(self, notification_id: float) -> None:
        """Acknowledge a notification."""
        for notification in self._notifications:
            if notification.id == notification_id:
                notification.acknowledged = True
                notification.read = True
                break
    
    def clear(self, keep_types: list[NotificationType] | None = None) -> None:
        """
        Clear notifications.
        
        Args:
            keep_types: Optional list of notification types to keep.
        """
        if keep_types:
            self._notifications = [
                n for n in self._notifications
                if n.type in keep_types or n.persistent
            ]
        else:
            self._notifications = [
                n for n in self._notifications
                if n.persistent
            ]
    
    # -------------------------------------------------------------------------
    # Background Checks
    # -------------------------------------------------------------------------
    
    def start_background_checks(self) -> None:
        """Start background notification checks."""
        if self._running:
            return
        
        self._running = True
        self._check_thread = threading.Thread(
            target=self._check_loop,
            name="NotificationCheck",
            daemon=True,
        )
        self._check_thread.start()
        
        logger.info("Started notification background checks")
    
    def stop(self) -> None:
        """Stop background checks."""
        self._running = False
        
        if self._check_thread is not None:
            self._check_thread.join(timeout=5.0)
            self._check_thread = None
        
        logger.info("Stopped notification background checks")
    
    def _check_loop(self) -> None:
        """Background check loop for training and audit notifications."""
        last_training_check: datetime | None = None
        last_audit_check: datetime | None = None
        
        while self._running:
            try:
                now = datetime.utcnow()
                
                # Check training expirations
                if (last_training_check is None or 
                    (now - last_training_check).total_seconds() >= self._training_check_interval):
                    self._check_training_expirations()
                    last_training_check = now
                
                # Check audit follow-ups
                if (last_audit_check is None or
                    (now - last_audit_check).total_seconds() >= self._audit_check_interval):
                    self._check_audit_follow_ups()
                    last_audit_check = now
                
                # Sleep briefly
                threading.Event().wait(60.0)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in notification check loop: {e}")
    
    def _check_training_expirations(self) -> None:
        """Check for expiring training records."""
        try:
            repo = RepositoryFactory().get_training_repo()
            
            # Check expiring soon (within 30 days)
            expiring = repo.get_expiring_soon(days=30)
            today = datetime.utcnow().date()
            
            for record in expiring:
                if record.expiry_date:
                    expiry = datetime.fromisoformat(record.expiry_date).date()
                    days_remaining = (expiry - today).days
                    
                    # Get employee name
                    employee_repo = RepositoryFactory().get_employee_repo()
                    employee = employee_repo.get(record.employee_id)
                    employee_name = employee.full_name if employee else record.employee_id
                    
                    self.notify_training_expiring(
                        employee_name=employee_name,
                        course_name=record.course_name,
                        expiry_date=record.expiry_date,
                        days_remaining=days_remaining,
                    )
            
            # Check already expired
            expired = repo.get_expired()
            for record in expired:
                employee_repo = RepositoryFactory().get_employee_repo()
                employee = employee_repo.get(record.employee_id)
                employee_name = employee.full_name if employee else record.employee_id
                
                self.notify_training_expiring(
                    employee_name=employee_name,
                    course_name=record.course_name,
                    expiry_date=record.expiry_date or "unknown",
                    days_remaining=0,
                )
                
        except Exception as e:
            logger.error(f"Error checking training expirations: {e}")
    
    def _check_audit_follow_ups(self) -> None:
        """Check for upcoming audit follow-ups."""
        try:
            repo = RepositoryFactory().get_audit_repo()
            today = datetime.utcnow().date()
            
            # Get audits with follow-up dates
            audits = repo.get_all(where="follow_up_date IS NOT NULL")
            
            for audit in audits:
                if audit.follow_up_date:
                    follow_up = datetime.fromisoformat(audit.follow_up_date).date()
                    days_until = (follow_up - today).days
                    
                    if days_until <= 7:  # Notify within 7 days
                        self.notify_audit_follow_up(
                            audit_title=audit.title,
                            follow_up_date=audit.follow_up_date,
                            days_until=days_until,
                        )
                        
        except Exception as e:
            logger.error(f"Error checking audit follow-ups: {e}")
    
    def get_summary(self) -> dict[str, Any]:
        """Get a summary of notification status."""
        return {
            "total": len(self._notifications),
            "unread": self.unread_count,
            "by_type": {
                type_.value: len(self.get_by_type(type_))
                for type_ in NotificationType
            },
            "recent": [n.to_dict() for n in self.notifications[:5]],
        }


# Import threading at module level for singleton
import threading

# Singleton accessor function
def get_notification_service() -> NotificationService:
    """
    Get the notification service singleton.
    
    Returns:
        NotificationService: The notification service instance.
    """
    return NotificationService.get_instance()