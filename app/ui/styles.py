"""
PSG - Professional Safety Guardian
Application Stylesheet Module

This module provides the Qt stylesheet (QSS) for the application,
defining the visual appearance of all UI components.
"""

from enum import Enum


class Theme(Enum):
    """Available application themes."""
    LIGHT = "light"
    DARK = "dark"


class StyleSheet:
    """
    Central stylesheet manager for the application.
    
    Provides theme-aware stylesheets for PyQt6 components,
    ensuring a consistent and professional appearance.
    """
    
    # Light theme colors
    LIGHT_THEME = {
        # Primary colors
        "primary": "#1976D2",
        "primary-light": "#BBDEFB",
        "primary-dark": "#1565C0",
        
        # Status colors
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336",
        "info": "#2196F3",
        
        # Neutral colors
        "background": "#F5F5F5",
        "surface": "#FFFFFF",
        "border": "#E0E0E0",
        "text-primary": "#212121",
        "text-secondary": "#757575",
        "text-disabled": "#BDBDBD",
        
        # Component colors
        "header-bg": "#1976D2",
        "header-text": "#FFFFFF",
        "sidebar-bg": "#ECEFF1",
        "sidebar-text": "#37474F",
        "button-bg": "#1976D2",
        "button-text": "#FFFFFF",
        "button-hover": "#1565C0",
        "button-disabled": "#BDBDBD",
        
        # Data colors
        "row-alternate": "#FAFAFA",
        "row-hover": "#E3F2FD",
        "selection": "#BBDEFB",
    }
    
    # Dark theme colors
    DARK_THEME = {
        # Primary colors
        "primary": "#42A5F5",
        "primary-light": "#1E88E5",
        "primary-dark": "#0D47A1",
        
        # Status colors
        "success": "#66BB6A",
        "warning": "#FFA726",
        "error": "#EF5350",
        "info": "#42A5F5",
        
        # Neutral colors
        "background": "#121212",
        "surface": "#1E1E1E",
        "border": "#333333",
        "text-primary": "#FFFFFF",
        "text-secondary": "#B0B0B0",
        "text-disabled": "#666666",
        
        # Component colors
        "header-bg": "#1E1E1E",
        "header-text": "#FFFFFF",
        "sidebar-bg": "#252525",
        "sidebar-text": "#E0E0E0",
        "button-bg": "#42A5F5",
        "button-text": "#FFFFFF",
        "button-hover": "#64B5F6",
        "button-disabled": "#444444",
        
        # Data colors
        "row-alternate": "#2A2A2A",
        "row-hover": "#333333",
        "selection": "#1E88E5",
    }
    
    def __init__(self, theme: Theme = Theme.LIGHT):
        """
        Initialize the stylesheet manager.
        
        Args:
            theme: The theme to use (LIGHT or DARK).
        """
        self._theme = theme
        self._colors = self.LIGHT_THEME if theme == Theme.LIGHT else self.DARK_THEME
    
    @property
    def theme(self) -> Theme:
        """Get the current theme."""
        return self._theme
    
    def set_theme(self, theme: Theme) -> None:
        """
        Set the application theme.
        
        Args:
            theme: The new theme to use.
        """
        self._theme = theme
        self._colors = self.LIGHT_THEME if theme == Theme.LIGHT else self.DARK_THEME
    
    def get_stylesheet(self) -> str:
        """
        Get the complete application stylesheet.
        
        Returns:
            The complete QSS stylesheet string.
        """
        c = self._colors
        font_family = "Segoe UI, -apple-system, BlinkMacSystemFont, sans-serif"
        
        return f"""
/* ============================================================
   PSG - Professional Safety Guardian
   Application Stylesheet
   Theme: {self._theme.value}
   ============================================================ */

/* ============================================================
   Global Styles
   ============================================================ */
QWidget {{
    font-family: {font_family};
    font-size: 12px;
    color: {c['text-primary']};
    background-color: {c['background']};
}}

QWidget:disabled {{
    color: {c['text-disabled']};
}}

QMainWindow {{
    background-color: {c['background']};
}}

/* ============================================================
   Header / Toolbar
   ============================================================ */
QToolBar {{
    background-color: {c['header-bg']};
    border: none;
    padding: 4px;
    spacing: 4px;
}}

QToolBar QToolButton {{
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 8px;
    color: {c['header-text']};
}}

QToolBar QToolButton:hover {{
    background-color: {c['primary-light']};
}}

QToolBar QToolButton:pressed {{
    background-color: {c['primary']};
}}

QMenuBar {{
    background-color: {c['header-bg']};
    color: {c['header-text']};
    padding: 4px;
}}

QMenuBar::item {{
    padding: 4px 8px;
    background: transparent;
}}

QMenuBar::item:selected {{
    background-color: {c['primary-light']};
    border-radius: 4px;
}}

QMenu {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px;
}}

QMenu::item:selected {{
    background-color: {c['selection']};
    border-radius: 4px;
}}

/* ============================================================
   Sidebar / Navigation
   ============================================================ */
QTreeWidget {{
    background-color: {c['sidebar-bg']};
    border: none;
    border-right: 1px solid {c['border']};
    color: {c['sidebar-text']};
}}

QTreeWidget::item {{
    padding: 8px;
    border: none;
}}

QTreeWidget::item:hover {{
    background-color: {c['row-hover']};
}}

QTreeWidget::item:selected {{
    background-color: {c['selection']};
    color: {c['text-primary']};
}}

QTabWidget::pane {{
    border: 1px solid {c['border']};
    background-color: {c['surface']};
    border-radius: 4px;
}}

QTabBar::tab {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 8px 16px;
    margin-right: 2px;
    color: {c['text-secondary']};
}}

QTabBar::tab:selected {{
    background-color: {c['surface']};
    color: {c['primary']};
    border-bottom: 2px solid {c['primary']};
}}

QTabBar::tab:hover {{
    background-color: {c['row-hover']};
}}

/* ============================================================
   Buttons
   ============================================================ */
QPushButton {{
    background-color: {c['button-bg']};
    color: {c['button-text']};
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 600;
    min-width: 80px;
}}

QPushButton:hover {{
    background-color: {c['button-hover']};
}}

QPushButton:pressed {{
    background-color: {c['primary-dark']};
}}

QPushButton:disabled {{
    background-color: {c['button-disabled']};
    color: {c['text-disabled']};
}}

QPushButton::menu-indicator {{
    image: none;
}}

/* Button variants */
QPushButton#primaryButton {{
    background-color: {c['primary']};
    font-weight: 600;
}}

QPushButton#successButton {{
    background-color: {c['success']};
}}

QPushButton#successButton:hover {{
    background-color: #43A047;
}}

QPushButton#warningButton {{
    background-color: {c['warning']};
}}

QPushButton#errorButton {{
    background-color: {c['error']};
}}

QPushButton#secondaryButton {{
    background-color: transparent;
    border: 1px solid {c['primary']};
    color: {c['primary']};
}}

QPushButton#secondaryButton:hover {{
    background-color: {c['primary-light']};
}}

/* ============================================================
   Input Fields
   ============================================================ */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 6px 10px;
    color: {c['text-primary']};
    selection-background-color: {c['selection']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {c['primary']};
    border-width: 2px;
}}

QLineEdit:disabled, QTextEdit:disabled {{
    background-color: {c['background']};
    color: {c['text-disabled']};
}}

QLineEdit[readOnly="true"] {{
    background-color: {c['background']};
}}

/* Placeholder text */
QLineEdit {{
    color: {c['text-secondary']};
}}

/* ============================================================
   ComboBox / Dropdown
   ============================================================ */
QComboBox {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 6px 10px;
    color: {c['text-primary']};
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {c['primary']};
}}

QComboBox:focus {{
    border-color: {c['primary']};
    border-width: 2px;
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {c['text-secondary']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    selection-background-color: {c['selection']};
    padding: 4px;
}}

QComboBox QAbstractItemView::item {{
    padding: 6px;
    border-radius: 4px;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: {c['row-hover']};
}}

/* ============================================================
   SpinBox
   ============================================================ */
QSpinBox, QDoubleSpinBox {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 6px 10px;
    color: {c['text-primary']};
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {c['primary']};
    border-width: 2px;
}}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    width: 16px;
    border: none;
    background: transparent;
}}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
    background-color: {c['row-hover']};
}}

/* ============================================================
   Checkboxes & Radio Buttons
   ============================================================ */
QCheckBox, QRadioButton {{
    color: {c['text-primary']};
    spacing: 8px;
    padding: 4px;
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {c['border']};
    border-radius: 4px;
    background-color: {c['surface']};
}}

QCheckBox::indicator:checked {{
    background-color: {c['primary']};
    border-color: {c['primary']};
}}

QCheckBox::indicator:hover {{
    border-color: {c['primary']};
}}

QRadioButton::indicator {{
    border-radius: 9px;
}}

QRadioButton::indicator:checked {{
    background-color: {c['primary']};
    border-color: {c['primary']};
    border-radius: 9px;
}}

/* ============================================================
   Tables / Data Grids
   ============================================================ */
QTableWidget, QTableView {{
    background-color: {c['surface']};
    alternate-background-color: {c['row-alternate']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    gridline-color: {c['border']};
    selection-background-color: {c['selection']};
}}

QTableWidget::item, QTableView::item {{
    padding: 6px 8px;
    border: none;
}}

QTableWidget::item:hover, QTableView::item:hover {{
    background-color: {c['row-hover']};
}}

QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {c['selection']};
    color: {c['text-primary']};
}}

QHeaderView::section {{
    background-color: {c['sidebar-bg']};
    color: {c['sidebar-text']};
    padding: 8px 12px;
    border: none;
    border-bottom: 2px solid {c['border']};
    font-weight: 600;
    text-align: left;
}}

QHeaderView::section:hover {{
    background-color: {c['row-hover']};
}}

QHeaderView::section:pressed {{
    background-color: {c['selection']};
}}

/* ============================================================
   Scrollbars
   ============================================================ */
QScrollBar:vertical {{
    background-color: {c['background']};
    width: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {c['border']};
    border-radius: 6px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {c['text-disabled']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {c['background']};
    height: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {c['border']};
    border-radius: 6px;
    min-width: 20px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {c['text-disabled']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ============================================================
   Progress Bar
   ============================================================ */
QProgressBar {{
    background-color: {c['background']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    text-align: center;
    color: {c['text-primary']};
    height: 20px;
}}

QProgressBar::chunk {{
    background-color: {c['primary']};
    border-radius: 3px;
}}

/* ============================================================
   Group Box
   ============================================================ */
QGroupBox {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 8px;
    color: {c['primary']};
}}

/* ============================================================
   Labels
   ============================================================ */
QLabel {{
    color: {c['text-primary']};
    background: transparent;
}}

QLabel#titleLabel {{
    font-size: 18px;
    font-weight: 700;
    color: {c['text-primary']};
}}

QLabel#sectionLabel {{
    font-size: 14px;
    font-weight: 600;
    color: {c['primary']};
    padding: 4px 0;
}}

QLabel#statusLabel {{
    font-size: 11px;
    color: {c['text-secondary']};
}}

/* ============================================================
   Status Bar
   ============================================================ */
QStatusBar {{
    background-color: {c['sidebar-bg']};
    border-top: 1px solid {c['border']};
    color: {c['sidebar-text']};
    padding: 4px;
}}

QStatusBar::item {{
    border: none;
    padding: 0 8px;
}}

/* ============================================================
   Tool Tips
   ============================================================ */
QToolTip {{
    background-color: {c['surface']};
    color: {c['text-primary']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}}

/* ============================================================
   Splitter
   ============================================================ */
QSplitter::handle {{
    background-color: {c['border']};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

/* ============================================================
   Calendar Widget
   ============================================================ */
QCalendarWidget {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 4px;
}}

QCalendarWidget QMenu {{
    background-color: {c['surface']};
}}

QCalendarWidget QSpinBox {{
    background-color: transparent;
    border: none;
}}

/* ============================================================
   Date/Time Edit
   ============================================================ */
QDateEdit, QTimeEdit, QDateTimeEdit {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 6px 10px;
    color: {c['text-primary']};
    min-width: 120px;
}}

QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {{
    border-color: {c['primary']};
    border-width: 2px;
}}

/* ============================================================
   Slider
   ============================================================ */
QSlider::groove:horizontal {{
    height: 6px;
    background: {c['border']};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    width: 16px;
    height: 16px;
    margin: -5px 0;
    background: {c['primary']};
    border-radius: 8px;
}}

QSlider::handle:horizontal:hover {{
    background: {c['button-hover']};
}}

/* ============================================================
   Status Indicators
   ============================================================ */
QLabel#syncStatusOnline {{
    color: {c['success']};
    font-weight: 600;
}}

QLabel#syncStatusOffline {{
    color: {c['error']};
    font-weight: 600;
}}

QLabel#syncStatusPending {{
    color: {c['warning']};
    font-weight: 600;
}}

/* ============================================================
   Notification Badge
   ============================================================ */
QLabel#notificationBadge {{
    background-color: {c['error']};
    color: white;
    font-size: 10px;
    font-weight: 700;
    border-radius: 8px;
    min-width: 16px;
    min-height: 16px;
    padding: 0 4px;
}}
"""
    
    def get_color(self, name: str) -> str:
        """
        Get a color value by name.
        
        Args:
            name: The color name.
        
        Returns:
            The color hex value.
        """
        return self._colors.get(name, "#000000")