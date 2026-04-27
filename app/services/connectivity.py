"""
PSG - Professional Safety Guardian
Network Connectivity Monitor Module

This module provides network connectivity detection and monitoring,
allowing the application to respond to changes in network availability.
"""

import logging
import socket
import threading
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable

import requests

from app.config import get_config
from app.constants import ConnectivityStatus

logger = logging.getLogger(__name__)


class ConnectivityMonitor:
    """
    Network connectivity monitor for detecting online/offline status.
    
    This class provides methods to check network connectivity and emits
    signals when the connectivity status changes. It uses a combination
    of socket connections and HTTP requests to determine connectivity.
    """
    
    _instance: "ConnectivityMonitor | None" = None
    _lock: threading.Lock = threading.Lock()
    
    def __init__(self, config: Any | None = None):
        """
        Initialize the connectivity monitor.
        
        Args:
            config: Optional configuration object.
        """
        self._config = config or get_config()
        
        # Connectivity state
        self._status: ConnectivityStatus = ConnectivityStatus.UNKNOWN
        self._last_check: datetime | None = None
        self._last_online: datetime | None = None
        self._consecutive_failures: int = 0
        
        # Monitoring
        self._monitoring: bool = False
        self._monitor_thread: threading.Thread | None = None
        self._check_interval: float = 30.0  # seconds
        
        # Callbacks for status changes
        self._status_callbacks: list[Callable[[ConnectivityStatus], None]] = []
        
        # Test endpoints (multiple for redundancy)
        self._test_endpoints: list[str] = [
            "https://api.psg-safety.com/health",
            "https://httpbin.org/status/200",
            "8.8.8.8",  # Google DNS (for socket test)
        ]
    
    def __new__(cls, config: Any | None = None) -> "ConnectivityMonitor":
        """Implement singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.__init__(config)
        return cls._instance
    
    @classmethod
    def get_instance(cls, config: Any | None = None) -> "ConnectivityMonitor":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.stop_monitoring()
                cls._instance = None
    
    @property
    def status(self) -> ConnectivityStatus:
        """Get the current connectivity status."""
        return self._status
    
    @property
    def is_online(self) -> bool:
        """Check if the system is currently online."""
        return self._status == ConnectivityStatus.ONLINE
    
    @property
    def is_offline(self) -> bool:
        """Check if the system is currently offline."""
        return self._status == ConnectivityStatus.OFFLINE
    
    @property
    def last_check(self) -> datetime | None:
        """Get the timestamp of the last connectivity check."""
        return self._last_check
    
    @property
    def last_online(self) -> datetime | None:
        """Get the timestamp when the system was last online."""
        return self._last_online
    
    def check_connectivity(self) -> ConnectivityStatus:
        """
        Perform a connectivity check.
        
        This method attempts to verify internet connectivity using
        multiple methods for reliability.
        
        Returns:
            ConnectivityStatus: The determined connectivity status.
        """
        self._last_check = datetime.utcnow()
        
        # Try each test endpoint
        for endpoint in self._test_endpoints:
            try:
                if endpoint.startswith("http"):
                    # HTTP/HTTPS connectivity test
                    if self._test_http_connection(endpoint):
                        self._set_status(ConnectivityStatus.ONLINE)
                        return ConnectivityStatus.ONLINE
                else:
                    # Socket connectivity test (for IP addresses)
                    if self._test_socket_connection(endpoint, 53):
                        self._set_status(ConnectivityStatus.ONLINE)
                        return ConnectivityStatus.ONLINE
                        
            except Exception as e:
                logger.debug(f"Connectivity test failed for {endpoint}: {e}")
                continue
        
        # All tests failed
        self._set_status(ConnectivityStatus.OFFLINE)
        return ConnectivityStatus.OFFLINE
    
    def _test_http_connection(self, url: str) -> bool:
        """
        Test HTTP connectivity to a URL.
        
        Args:
            url: The URL to test.
        
        Returns:
            True if connection successful, False otherwise.
        """
        try:
            response = requests.get(
                url,
                timeout=self._config.api.timeout if hasattr(self._config, 'api') else 10,
                allow_redirects=True,
            )
            # Consider any response (even 4xx, 5xx) as connectivity
            return response.status_code < 500
            
        except requests.exceptions.Timeout:
            return False
        except requests.exceptions.ConnectionError:
            return False
        except requests.exceptions.RequestException:
            return False
    
    def _test_socket_connection(self, host: str, port: int) -> bool:
        """
        Test socket connectivity to a host:port.
        
        Args:
            host: The hostname or IP to connect to.
            port: The port number.
        
        Returns:
            True if connection successful, False otherwise.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
            
        except socket.error:
            return False
    
    def _set_status(self, status: ConnectivityStatus) -> None:
        """
        Set the connectivity status and notify callbacks.
        
        Args:
            status: The new connectivity status.
        """
        old_status = self._status
        self._status = status
        
        if status == ConnectivityStatus.ONLINE:
            self._last_online = datetime.utcnow()
            self._consecutive_failures = 0
        
        # Only trigger callbacks on status change
        if old_status != status:
            logger.info(f"Connectivity status changed: {old_status.value} -> {status.value}")
            self._notify_status_changed(status)
    
    def _notify_status_changed(self, status: ConnectivityStatus) -> None:
        """
        Notify all registered callbacks of a status change.
        
        Args:
            status: The new connectivity status.
        """
        for callback in self._status_callbacks:
            try:
                callback(status)
            except Exception as e:
                logger.error(f"Error in connectivity callback: {e}")
    
    def on_status_changed(self, callback: Callable[[ConnectivityStatus], None]) -> None:
        """
        Register a callback for connectivity status changes.
        
        Args:
            callback: Function to call when status changes.
        """
        self._status_callbacks.append(callback)
    
    def remove_status_callback(self, callback: Callable[[ConnectivityStatus], None]) -> None:
        """
        Remove a status change callback.
        
        Args:
            callback: The callback to remove.
        """
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)
    
    def start_monitoring(self, interval: float | None = None) -> None:
        """
        Start background connectivity monitoring.
        
        Args:
            interval: Check interval in seconds. If None, uses default.
        """
        if self._monitoring:
            return
        
        if interval is not None:
            self._check_interval = interval
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="ConnectivityMonitor",
            daemon=True,
        )
        self._monitor_thread.start()
        
        logger.info(f"Started connectivity monitoring (interval: {self._check_interval}s)")
    
    def stop_monitoring(self) -> None:
        """Stop background connectivity monitoring."""
        self._monitoring = False
        
        if self._monitor_thread is not None:
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None
        
        logger.info("Stopped connectivity monitoring")
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self._monitoring:
            try:
                self.check_connectivity()
            except Exception as e:
                logger.error(f"Error during connectivity check: {e}")
            
            # Sleep in small intervals to allow quick shutdown
            for _ in range(int(self._check_interval)):
                if not self._monitoring:
                    break
                time.sleep(1.0)
    
    def wait_for_connection(self, timeout: float | None = None) -> bool:
        """
        Wait for an internet connection to become available.
        
        Args:
            timeout: Maximum time to wait in seconds. None for indefinite.
        
        Returns:
            True if connection established, False if timeout.
        """
        start_time = time.time()
        
        while True:
            if self.check_connectivity() == ConnectivityStatus.ONLINE:
                return True
            
            if timeout is not None and (time.time() - start_time) >= timeout:
                return False
            
            time.sleep(2.0)
    
    def get_connection_quality(self) -> dict[str, Any]:
        """
        Get detailed connection quality metrics.
        
        Returns:
            Dictionary with connection quality information.
        """
        metrics: dict[str, Any] = {
            "status": self._status.value,
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "last_online": self._last_online.isoformat() if self._last_online else None,
            "consecutive_failures": self._consecutive_failures,
        }
        
        # Test latency if online
        if self.is_online:
            try:
                start = time.time()
                requests.get(self._test_endpoints[0], timeout=5)
                metrics["latency_ms"] = round((time.time() - start) * 1000, 2)
            except Exception:
                metrics["latency_ms"] = None
        
        return metrics


# Singleton accessor function
def get_connectivity_monitor() -> ConnectivityMonitor:
    """
    Get the connectivity monitor singleton.
    
    Returns:
        ConnectivityMonitor: The connectivity monitor instance.
    """
    return ConnectivityMonitor.get_instance()