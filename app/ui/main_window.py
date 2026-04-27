"""
PSG - Professional Safety Guardian
Main Application Window Module

This module provides the main application window for the PSG desktop
application, including the navigation, toolbar, status bar, and
central widget area.
"""

import logging
from datetime import datetime
from typing import Any

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSlot
from PyQt6.QtGui import QAction, QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QSystemTrayIcon,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app import __version__
from app.config import get_config
from app.constants import (
    APP_NAME,
    ConnectivityStatus,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
)
from app.services.connectivity import get_connectivity_monitor
from app.services.notification import get_notification_service
from app.services.sync_service import get_sync_service
from app.services.workers.sync_worker import SyncWorker
from app.ui.styles import StyleSheet, Theme

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window for PSG Desktop.
    
    This window provides the primary user interface for the application,
    including navigation, data views, and sync status indicators.
    """
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Configuration
        self._config = get_config()
        
        # Services
        self._sync_service = get_sync_service()
        self._connectivity = get_connectivity_monitor()
        self._notifications = get_notification_service()
        
        # UI Components
        self._central_widget: QWidget | None = None
        self._stacked_widget: QStackedWidget | None = None
        self._navigation: QTreeWidget | None = None
        self._status_bar: QStatusBar | None = None
        self._toolbar: QToolBar | None = None
        self._sync_progress: QProgressBar | None = None
        self._connectivity_label: QLabel | None = None
        self._sync_label: QLabel | None = None
        
        # Workers
        self._sync_worker: SyncWorker | None = None
        
        # System tray
        self._tray_icon: QSystemTrayIcon | None = None
        
        # Initialize UI
        self._setup_ui()
        self._setup_toolbar()
        self._setup_status_bar()
        self._setup_navigation()
        self._setup_central_widget()
        self._setup_system_tray()
        
        # Apply stylesheet
        self._apply_theme()
        
        # Setup connections
        self._setup_connections()
        
        # Start background services
        self._start_services()
        
        logger.info("Main window initialized")
    
    def _setup_ui(self) -> None:
        """Setup the basic UI structure."""
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        
        # Set window icon (would use actual icon file in production)
        # self.setWindowIcon(QIcon(":/icons/app_icon.png"))
    
    def _setup_toolbar(self) -> None:
        """Setup the main toolbar."""
        from PyQt6.QtCore import QSize
        
        self._toolbar = QToolBar("Main Toolbar")
        self._toolbar.setMovable(False)
        icon_size = self._config.ui.font_size * 2
        self._toolbar.setIconSize(QSize(icon_size, icon_size))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self._toolbar)
        
        # Sync button
        self._sync_action = QAction("Sync Now", self)
        self._sync_action.setToolTip("Synchronize data with server")
        self._sync_action.triggered.connect(self._trigger_sync)
        self._toolbar.addAction(self._sync_action)
        
        self._toolbar.addSeparator()
        
        # New Incident button
        self._new_incident_action = QAction("New Incident", self)
        self._new_incident_action.setToolTip("Report a new safety incident")
        self._new_incident_action.triggered.connect(self._show_new_incident)
        self._toolbar.addAction(self._new_incident_action)
        
        # New Audit button
        self._new_audit_action = QAction("New Audit", self)
        self._new_audit_action.setToolTip("Create a new audit report")
        self._new_audit_action.triggered.connect(self._show_new_audit)
        self._toolbar.addAction(self._new_audit_action)
        
        self._toolbar.addSeparator()
        
        # Settings button
        self._settings_action = QAction("Settings", self)
        self._settings_action.setToolTip("Application settings")
        self._settings_action.triggered.connect(self._show_settings)
        self._toolbar.addAction(self._settings_action)
        
        # Help button
        self._help_action = QAction("Help", self)
        self._help_action.setToolTip("Help and documentation")
        self._help_action.triggered.connect(self._show_help)
        self._toolbar.addAction(self._help_action)
    
    def _setup_status_bar(self) -> None:
        """Setup the status bar with sync and connectivity indicators."""
        self._status_bar = self.statusBar()
        
        # Connectivity status label
        self._connectivity_label = QLabel("Checking...")
        self._connectivity_label.setObjectName("statusLabel")
        self._status_bar.addPermanentWidget(self._connectivity_label)
        
        # Sync status label
        self._sync_label = QLabel("Ready")
        self._sync_label.setObjectName("statusLabel")
        self._status_bar.addPermanentWidget(self._sync_label)
        
        # Sync progress bar
        self._sync_progress = QProgressBar()
        self._sync_progress.setMaximumWidth(150)
        self._sync_progress.setVisible(False)
        self._status_bar.addPermanentWidget(self._sync_progress)
        
        # Notification count
        self._notification_label = QLabel("🔔 0")
        self._notification_label.setObjectName("statusLabel")
        self._status_bar.addPermanentWidget(self._notification_label)
    
    def _setup_navigation(self) -> None:
        """Setup the left navigation panel."""
        navigation_frame = QFrame()
        navigation_frame.setMaximumWidth(250)
        navigation_frame.setMinimumWidth(200)
        navigation_layout = QVBoxLayout(navigation_frame)
        navigation_layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigation tree
        self._navigation = QTreeWidget()
        self._navigation.setHeaderHidden(True)
        self._navigation.setIndentation(20)
        self._navigation.currentItemChanged.connect(self._on_navigation_changed)
        
        # Add navigation items
        self._populate_navigation()
        
        navigation_layout.addWidget(self._navigation)
        
        # Store navigation frame for later use
        self._navigation_frame = navigation_frame
    
    def _populate_navigation(self) -> None:
        """Populate the navigation tree with items."""
        items = [
            ("Dashboard", "dashboard", []),
            ("Incidents", "incidents", [
                ("All Incidents", "all_incidents"),
                ("Near Misses", "near_misses"),
                ("My Reports", "my_reports"),
            ]),
            ("Training", "training", [
                ("Training Logs", "training_logs"),
                ("Expiring Soon", "expiring_training"),
                ("Expired", "expired_training"),
            ]),
            ("Audits", "audits", [
                ("All Audits", "all_audits"),
                ("Pending", "pending_audits"),
                ("Follow-ups", "follow_ups"),
            ]),
            ("Employees", "employees", []),
            ("Reports", "reports", [
                ("Safety Summary", "safety_summary"),
                ("Compliance Report", "compliance_report"),
                ("Export Data", "export_data"),
                ("CSV Import", "csv_import"),
            ]),
            ("Settings", "settings", []),
        ]
        
        for item_data in items:
            item = QTreeWidgetItem(self._navigation)
            item.setText(0, item_data[0])
            item.setData(0, Qt.ItemDataRole.UserRole, item_data[1])
            
            for child_data in item_data[2]:
                child = QTreeWidgetItem(item)
                child.setText(0, child_data[0])
                child.setData(0, Qt.ItemDataRole.UserRole, child_data[1])
        
        self._navigation.expandAll()
    
    def _setup_central_widget(self) -> None:
        """Setup the central widget area."""
        # Central widget with horizontal layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add navigation
        layout.addWidget(self._navigation_frame)
        
        # Stacked widget for different views
        self._stacked_widget = QStackedWidget()
        self._stacked_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Add placeholder pages (would be actual view widgets in production)
        self._pages: dict[str, QWidget] = {}
        page_names = [
            "dashboard", "all_incidents", "near_misses", "my_reports",
            "training_logs", "expiring_training", "expired_training",
            "all_audits", "pending_audits", "follow_ups",
            "employees", "safety_summary", "compliance_report", "export_data",
            "csv_import",
            "settings"
        ]
        
        for page_name in page_names:
            page = self._create_placeholder_page(page_name)
            self._pages[page_name] = page
            self._stacked_widget.addWidget(page)
        
        layout.addWidget(self._stacked_widget)
        
        self._central_widget = central_widget
    
    def _create_placeholder_page(self, name: str) -> QWidget:
        """Create a page widget - actual view for specific pages, placeholder for others."""
        # Import the actual view for csv_import
        if name == "csv_import":
            from app.ui.csv_import_view import CSVImportView
            return CSVImportView()
        
        # For all other pages, create placeholder
        page = QWidget()
        layout = QVBoxLayout(page)
        
        label = QLabel(f"{name.replace('_', ' ').title()}")
        label.setObjectName("titleLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        # Add some placeholder content
        info_label = QLabel("Content coming soon...")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #757575; font-size: 14px;")
        layout.addWidget(info_label)
        
        return page
    
    def _setup_system_tray(self) -> None:
        """Setup system tray icon and menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        self._tray_icon = QSystemTrayIcon(self)
        # self._tray_icon.setIcon(QIcon(":/icons/app_icon.png"))
        self._tray_icon.setToolTip(APP_NAME)
        
        # Tray menu
        tray_menu = self._create_tray_menu()
        self._tray_icon.setContextMenu(tray_menu)
        
        # Double-click to show window
        self._tray_icon.activated.connect(self._on_tray_activated)
        
        self._tray_icon.show()
    
    def _create_tray_menu(self) -> None:
        """Create the system tray menu."""
        from PyQt6.QtWidgets import QMenu
        
        menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        menu.addAction(show_action)
        
        sync_action = QAction("Sync Now", self)
        sync_action.triggered.connect(self._trigger_sync)
        menu.addAction(sync_action)
        
        menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)
        
        return menu
    
    def _setup_connections(self) -> None:
        """Setup signal/slot connections."""
        # Sync worker signals
        # (Will be connected when worker is created)
        
        # Connectivity changes
        self._connectivity.on_status_changed(self._on_connectivity_changed)
        
        # Notification updates
        self._notifications.on_notification(self._on_notification_received)
        
        # Periodic status update
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(5000)  # Update every 5 seconds
    
    def _start_services(self) -> None:
        """Start background services."""
        # Start connectivity monitoring
        self._connectivity.start_monitoring(30)
        
        # Start notification background checks
        self._notifications.start_background_checks()
        
        # Start auto-sync if enabled
        if self._config.sync.auto_sync:
            self._sync_service.start_auto_sync()
    
    def _apply_theme(self) -> None:
        """Apply the application theme."""
        theme = Theme.DARK if self._config.ui.theme == "dark" else Theme.LIGHT
        self._stylesheet = StyleSheet(theme)
        self.setStyleSheet(self._stylesheet.get_stylesheet())
    
    # -------------------------------------------------------------------------
    # Event Handlers
    # -------------------------------------------------------------------------
    
    def _on_navigation_changed(self, current: QTreeWidgetItem, previous: QTreeWidgetItem) -> None:
        """Handle navigation item selection change."""
        if current is None:
            return
        
        page_id = current.data(0, Qt.ItemDataRole.UserRole)
        
        if page_id in self._pages:
            self._stacked_widget.setCurrentWidget(self._pages[page_id])
    
    @pyqtSlot()
    def _trigger_sync(self) -> None:
        """Trigger a manual sync operation."""
        if self._sync_service.is_syncing:
            QMessageBox.information(self, "Sync", "Synchronization is already in progress.")
            return
        
        # Create and start sync worker
        self._sync_worker = SyncWorker()
        self._sync_worker.started.connect(self._on_sync_started)
        self._sync_worker.progress.connect(self._on_sync_progress)
        self._sync_worker.completed.connect(self._on_sync_completed)
        self._sync_worker.error.connect(self._on_sync_error)
        self._sync_worker.start()
    
    @pyqtSlot()
    def _on_sync_started(self) -> None:
        """Handle sync start."""
        self._sync_label.setText("Syncing...")
        self._sync_progress.setVisible(True)
        self._sync_progress.setValue(0)
        self._sync_action.setEnabled(False)
        
        logger.info("Sync started")
    
    @pyqtSlot(dict)
    def _on_sync_progress(self, data: dict[str, Any]) -> None:
        """Handle sync progress update."""
        status = data.get("status", "")
        
        if status == "syncing":
            records = data.get("records_synced", 0)
            remaining = data.get("records_remaining", 0)
            total = records + remaining
            progress = int((records / total) * 100) if total > 0 else 0
            self._sync_progress.setValue(progress)
            self._sync_label.setText(f"Syncing... {records}/{total}")
    
    @pyqtSlot(dict)
    def _on_sync_completed(self, result: dict[str, Any]) -> None:
        """Handle sync completion."""
        self._sync_progress.setVisible(False)
        self._sync_action.setEnabled(True)
        
        if result.get("success", False):
            synced = result.get("records_synced", 0)
            self._sync_label.setText(f"Synced: {synced} records")
            self._notifications.notify_sync_status(True, synced, 0)
        else:
            reason = result.get("reason", "unknown")
            if reason == "offline":
                self._sync_label.setText("Offline - sync pending")
                self._notifications.notify_sync_offline()
            else:
                self._sync_label.setText("Sync failed")
        
        logger.info(f"Sync completed: {result}")
    
    @pyqtSlot(str, str)
    def _on_sync_error(self, error_type: str, message: str) -> None:
        """Handle sync error."""
        self._sync_progress.setVisible(False)
        self._sync_action.setEnabled(True)
        self._sync_label.setText("Sync error")
        
        QMessageBox.warning(self, "Sync Error", f"An error occurred during sync:\n{message}")
        
        logger.error(f"Sync error ({error_type}): {message}")
    
    @pyqtSlot(ConnectivityStatus)
    def _on_connectivity_changed(self, status: ConnectivityStatus) -> None:
        """Handle connectivity status change."""
        if status == ConnectivityStatus.ONLINE:
            self._connectivity_label.setText("🟢 Online")
            self._connectivity_label.setObjectName("syncStatusOnline")
        elif status == ConnectivityStatus.OFFLINE:
            self._connectivity_label.setText("🔴 Offline")
            self._connectivity_label.setObjectName("syncStatusOffline")
        else:
            self._connectivity_label.setText("🟡 Unknown")
            self._connectivity_label.setObjectName("syncStatusPending")
        
        # Re-apply stylesheet to update color
        self._connectivity_label.style().unpolish(self._connectivity_label)
        self._connectivity_label.style().polish(self._connectivity_label)
    
    @pyqtSlot(object)
    def _on_notification_received(self, notification) -> None:
        """Handle new notification."""
        count = self._notifications.unread_count
        self._notification_label.setText(f"🔔 {count}")
        
        # Show tray notification for important alerts
        if notification.persistent and self._tray_icon:
            self._tray_icon.showMessage(
                notification.title,
                notification.message,
                QSystemTrayIcon.MessageIcon.Information,
                5000,
            )
    
    def _update_status(self) -> None:
        """Periodic status update."""
        # Update notification count
        count = self._notifications.unread_count
        self._notification_label.setText(f"🔔 {count}")
        
        # Update sync queue info
        queue_status = self._sync_service.get_sync_queue_status()
        pending = queue_status.get("total_pending", 0)
        if pending > 0 and not self._sync_service.is_syncing:
            self._sync_label.setText(f"Pending: {pending} records")
    
    # -------------------------------------------------------------------------
    # Action Handlers
    # -------------------------------------------------------------------------
    
    def _show_new_incident(self) -> None:
        """Show the new incident form."""
        # Navigate to incidents page
        self._navigate_to("all_incidents")
        QMessageBox.information(self, "New Incident", "Incident form would open here.")
    
    def _show_new_audit(self) -> None:
        """Show the new audit form."""
        self._navigate_to("all_audits")
        QMessageBox.information(self, "New Audit", "Audit form would open here.")
    
    def _show_settings(self) -> None:
        """Show the settings dialog."""
        self._navigate_to("settings")
    
    def _show_help(self) -> None:
        """Show the help dialog."""
        QMessageBox.about(
            self,
            "About PSG",
            f"<h2>{APP_NAME}</h2>"
            f"<p>Version: {__version__}</p>"
            f"<p>A professional desktop application for MEP construction safety management.</p>"
            f"<p>Designed for offline-first operation with intelligent synchronization.</p>"
            f"<p>&copy; 2024 PSG Safety Solutions</p>"
        )
    
    def _navigate_to(self, page_id: str) -> None:
        """Navigate to a specific page."""
        if page_id in self._pages:
            self._stacked_widget.setCurrentWidget(self._pages[page_id])
    
    # -------------------------------------------------------------------------
    # Window Events
    # -------------------------------------------------------------------------
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Stop background services
        self._sync_service.stop()
        self._connectivity.stop_monitoring()
        self._notifications.stop()
        
        if self._sync_worker and self._sync_worker.isRunning():
            self._sync_worker.stop()
        
        # Save window geometry if configured
        if self._config.ui.remember_window_geometry:
            # Would save geometry to config
            pass
        
        logger.info("Application closing")
        event.accept()
    
    def changeEvent(self, event) -> None:
        """Handle window state change."""
        if event.type() == event.Type.WindowStateChange:
            # Minimize to tray if configured
            if self.isMinimized() and self._tray_icon:
                # Would minimize to tray
                pass
        
        super().changeEvent(event)
    
    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
            self.activateWindow()