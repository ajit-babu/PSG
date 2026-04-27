"""
PSG - Professional Safety Guardian
Sync Worker Module

This module provides a QThread-based worker for running
synchronization operations in the background without blocking
the PyQt6 UI.
"""

import logging
from typing import Any

from PyQt6.QtCore import QThread, pyqtSignal

from app.services.sync_service import SyncService, get_sync_service
from app.services.connectivity import ConnectivityMonitor, get_connectivity_monitor
from app.constants import ConnectivityStatus

logger = logging.getLogger(__name__)


class SyncWorker(QThread):
    """
    QThread-based worker for background synchronization.
    
    This worker runs synchronization operations in a separate thread,
    emitting signals to update the UI about progress and completion.
    This ensures the desktop GUI remains responsive during sync operations.
    
    Signals:
        started: Emitted when sync starts
        progress: Emitted with progress data (dict)
        record_synced: Emitted when a record is successfully synced
        batch_complete: Emitted when a batch is complete
        completed: Emitted when sync finishes with result data
        error: Emitted when an error occurs
        finished: Emitted when the worker is done (Qt standard)
    """
    
    # Signals for UI updates
    started = pyqtSignal()
    progress = pyqtSignal(dict)
    record_synced = pyqtSignal(str, str)  # table_name, record_id
    batch_complete = pyqtSignal(dict)  # batch results
    completed = pyqtSignal(dict)  # final results
    error = pyqtSignal(str, str)  # error_type, message
    connectivity_changed = pyqtSignal(str)  # status
    
    def __init__(
        self,
        sync_service: SyncService | None = None,
        connectivity_monitor: ConnectivityMonitor | None = None,
        parent: QThread | None = None,
    ):
        """
        Initialize the sync worker.
        
        Args:
            sync_service: Optional sync service instance.
            connectivity_monitor: Optional connectivity monitor instance.
            parent: Optional parent thread.
        """
        super().__init__(parent)
        
        self._sync_service = sync_service or get_sync_service()
        self._connectivity = connectivity_monitor or get_connectivity_monitor()
        
        # Worker state
        self._running = False
        self._paused = False
        
        # Connect internal callbacks
        self._sync_service.on_progress(self._on_sync_progress)
        self._connectivity.on_status_changed(self._on_connectivity_changed)
    
    def run(self) -> None:
        """
        Run the sync worker thread.
        
        This method is called when the thread starts and runs the
        synchronization process.
        """
        self._running = True
        logger.info("SyncWorker started")
        
        try:
            self.started.emit()
            
            # Check connectivity first
            connectivity_status = self._connectivity.check_connectivity()
            
            if connectivity_status != ConnectivityStatus.ONLINE:
                self.progress.emit({
                    "status": "offline",
                    "message": "No internet connection available",
                })
                self.completed.emit({
                    "success": False,
                    "reason": "offline",
                    "message": "No internet connection available",
                })
                return
            
            # Run synchronization
            self._sync_service.sync_now(blocking=True)
            
            # Emit completion
            self.completed.emit(self._sync_service.statistics)
            
        except Exception as e:
            logger.error(f"SyncWorker error: {e}")
            self.error.emit("sync_error", str(e))
        
        finally:
            self._running = False
    
    def _on_sync_progress(self, data: dict[str, Any]) -> None:
        """
        Handle sync progress updates.
        
        Args:
            data: Progress data from sync service.
        """
        # Forward to UI via signal
        self.progress.emit(data)
    
    def _on_connectivity_changed(self, status: ConnectivityStatus) -> None:
        """
        Handle connectivity status changes.
        
        Args:
            status: New connectivity status.
        """
        self.connectivity_changed.emit(status.value)
        
        # Auto-trigger sync when coming online
        if status == ConnectivityStatus.ONLINE and self._running:
            self.progress.emit({
                "status": "online",
                "message": "Connection restored, starting sync...",
            })
    
    def stop(self) -> None:
        """Stop the worker gracefully."""
        self._running = False
        self._sync_service.stop()
        
        # Wait for thread to finish
        if self.isRunning():
            self.wait(5000)  # 5 second timeout
    
    def pause(self) -> None:
        """Pause the worker."""
        self._paused = True
    
    def resume(self) -> None:
        """Resume the worker."""
        self._paused = False
    
    @property
    def is_running(self) -> bool:
        """Check if the worker is currently running."""
        return self._running and super().isRunning()
    
    @property
    def is_paused(self) -> bool:
        """Check if the worker is paused."""
        return self._paused


class AutoSyncWorker(QThread):
    """
    Background worker for automatic periodic synchronization.
    
    This worker runs continuously, checking for connectivity and
    triggering syncs at configured intervals.
    """
    
    # Signals
    sync_triggered = pyqtSignal()
    sync_complete = pyqtSignal(dict)
    connectivity_status = pyqtSignal(str)
    error = pyqtSignal(str, str)
    
    def __init__(
        self,
        sync_service: SyncService | None = None,
        connectivity_monitor: ConnectivityMonitor | None = None,
        parent: QThread | None = None,
    ):
        """
        Initialize the auto-sync worker.
        
        Args:
            sync_service: Optional sync service instance.
            connectivity_monitor: Optional connectivity monitor instance.
            parent: Optional parent thread.
        """
        super().__init__(parent)
        
        self._sync_service = sync_service or get_sync_service()
        self._connectivity = connectivity_monitor or get_connectivity_monitor()
        
        # Configuration
        self._check_interval: int = 30  # seconds
        self._sync_interval: int = 300  # 5 minutes default
        
        # State
        self._running = False
        self._last_sync: float = 0
    
    def run(self) -> None:
        """Run the auto-sync worker loop."""
        import time
        
        self._running = True
        self._last_sync = time.time()
        
        logger.info("AutoSyncWorker started")
        
        # Start connectivity monitoring
        self._connectivity.start_monitoring(self._check_interval)
        
        while self._running:
            try:
                import time as time_module
                
                # Check if it's time to sync
                current_time = time_module.time()
                time_since_sync = current_time - self._last_sync
                
                if (time_since_sync >= self._sync_interval and 
                    self._connectivity.is_online and
                    not self._sync_service.is_syncing):
                    
                    # Trigger sync
                    self.sync_triggered.emit()
                    self._sync_service.sync_now(blocking=True)
                    self._last_sync = time_module.time()
                    
                    # Emit completion
                    self.sync_complete.emit(self._sync_service.statistics)
                
                # Sleep briefly
                time_module.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"AutoSyncWorker error: {e}")
                self.error.emit("auto_sync_error", str(e))
                time.sleep(5)
        
        # Cleanup
        self._connectivity.stop_monitoring()
        logger.info("AutoSyncWorker stopped")
    
    def stop(self) -> None:
        """Stop the worker gracefully."""
        self._running = False
        
        if self.isRunning():
            self.wait(5000)  # 5 second timeout
    
    def set_sync_interval(self, interval_seconds: int) -> None:
        """
        Set the sync interval.
        
        Args:
            interval_seconds: Interval between syncs in seconds.
        """
        self._sync_interval = interval_seconds
    
    def set_check_interval(self, interval_seconds: int) -> None:
        """
        Set the connectivity check interval.
        
        Args:
            interval_seconds: Interval between connectivity checks in seconds.
        """
        self._check_interval = interval_seconds