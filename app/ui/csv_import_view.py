"""
PSG - Professional Safety Guardian
CSV Import View Module

This module provides the CSV import view widget for importing data from CSV files
into the application database.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database.repository import RepositoryFactory
from app.services.csv_importer import CSVImporter, ImportConfig, ImportResult
from app.services.csv_validator import CSVValidator, ValidationResult

logger = logging.getLogger(__name__)


class CSVImportView(QWidget):
    """
    CSV Import View Widget
    
    This widget provides a user interface for importing CSV data into the application.
    It supports file selection, field mapping, validation, and database import.
    """
    
    def __init__(self):
        """Initialize the CSV import view."""
        super().__init__()
        
        # Services
        self._csv_importer = CSVImporter()
        self._csv_validator = CSVValidator()
        
        # State
        self._selected_file: Path | None = None
        self._column_names: List[str] = []
        self._preview_data: List[Dict[str, Any]] = []
        self._import_result: ImportResult | None = None
        
        # UI Components
        self._file_path_edit: QLineEdit | None = None
        self._browse_button: QPushButton | None = None
        self._preview_table: QTableWidget | None = None
        self._field_mapping_group: QGroupBox | None = None
        self._import_button: QPushButton | None = None
        self._results_text: QTextEdit | None = None
        
        # Initialize UI
        self._setup_ui()
        
        logger.info("CSV Import view initialized")
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("CSV Data Import")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # File selection group
        file_group = QGroupBox("File Selection")
        file_layout = QHBoxLayout(file_group)
        
        self._file_path_edit = QLineEdit()
        self._file_path_edit.setPlaceholderText("Select a CSV file...")
        self._file_path_edit.setReadOnly(True)
        file_layout.addWidget(self._file_path_edit)
        
        self._browse_button = QPushButton("Browse...")
        self._browse_button.clicked.connect(self._browse_file)
        file_layout.addWidget(self._browse_button)
        
        layout.addWidget(file_group)
        
        # Preview group
        preview_group = QGroupBox("Data Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self._preview_table = QTableWidget()
        self._preview_table.setAlternatingRowColors(True)
        self._preview_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        preview_layout.addWidget(self._preview_table)
        
        layout.addWidget(preview_group)
        
        # Field mapping group
        self._field_mapping_group = QGroupBox("Field Mapping")
        self._field_mapping_layout = QFormLayout(self._field_mapping_group)
        layout.addWidget(self._field_mapping_group)
        
        # Import options
        options_group = QGroupBox("Import Options")
        options_layout = QVBoxLayout(options_group)
        
        self._validate_checkbox = QCheckBox("Validate data on import")
        self._validate_checkbox.setChecked(True)
        options_layout.addWidget(self._validate_checkbox)
        
        self._skip_invalid_checkbox = QCheckBox("Skip invalid rows")
        options_layout.addWidget(self._skip_invalid_checkbox)
        
        layout.addWidget(options_group)
        
        # Import button
        self._import_button = QPushButton("Import Data")
        self._import_button.clicked.connect(self._import_data)
        self._import_button.setEnabled(False)
        layout.addWidget(self._import_button)
        
        # Results group
        results_group = QGroupBox("Import Results")
        results_layout = QVBoxLayout(results_group)
        
        self._results_text = QTextEdit()
        self._results_text.setReadOnly(True)
        self._results_text.setMaximumHeight(150)
        results_layout.addWidget(self._results_text)
        
        layout.addWidget(results_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def _browse_file(self) -> None:
        """Open file dialog to select a CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self._selected_file = Path(file_path)
            self._file_path_edit.setText(str(file_path))
            self._load_file_preview()
    
    def _load_file_preview(self) -> None:
        """Load and display preview of the selected CSV file."""
        if not self._selected_file:
            return
        
        try:
            # Get column names
            self._column_names = self._csv_importer.get_column_names(self._selected_file)
            
            # Get preview data
            self._column_names, self._preview_data = self._csv_importer.preview_file(
                self._selected_file, max_rows=10
            )
            
            # Update preview table
            self._update_preview_table()
            
            # Enable import button
            self._import_button.setEnabled(True)
            
            # Clear field mapping
            self._clear_field_mapping()
            
            logger.info(f"Loaded preview for {self._selected_file}")
            
        except Exception as e:
            logger.error(f"Error loading file preview: {e}")
            QMessageBox.warning(
                self,
                "Preview Error",
                f"Failed to load file preview:\n{str(e)}"
            )
    
    def _update_preview_table(self) -> None:
        """Update the preview table with current data."""
        if not self._preview_table or not self._column_names:
            return
        
        # Set table dimensions
        self._preview_table.setRowCount(len(self._preview_data))
        self._preview_table.setColumnCount(len(self._column_names))
        self._preview_table.setHorizontalHeaderLabels(self._column_names)
        
        # Populate table data
        for row_idx, row_data in enumerate(self._preview_data):
            for col_idx, column_name in enumerate(self._column_names):
                value = str(row_data.get(column_name, ""))
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._preview_table.setItem(row_idx, col_idx, item)
        
        # Resize columns to content
        self._preview_table.resizeColumnsToContents()
    
    def _clear_field_mapping(self) -> None:
        """Clear the field mapping controls."""
        if not self._field_mapping_layout:
            return
        
        # Remove all children from the layout
        while self._field_mapping_layout.count():
            child = self._field_mapping_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _setup_field_mapping(self) -> None:
        """Setup field mapping controls based on column names."""
        if not self._column_names:
            return
        
        self._clear_field_mapping()
        
        # Add mapping controls for each column
        self._mapping_edits: Dict[str, QLineEdit] = {}
        
        for column_name in self._column_names:
            label = QLabel(f"{column_name}:")
            edit = QLineEdit()
            edit.setPlaceholderText("Internal field name (optional)")
            self._mapping_edits[column_name] = edit
            
            self._field_mapping_layout.addRow(label, edit)
    
    @pyqtSlot()
    def _import_data(self) -> None:
        """Handle the import button click."""
        if not self._selected_file:
            QMessageBox.warning(self, "Import Error", "No file selected.")
            return
        
        try:
            # Get field mapping
            field_mapping = self._get_field_mapping()
            
            # Update importer configuration
            config = ImportConfig(
                validate_on_import=self._validate_checkbox.isChecked(),
                skip_invalid_rows=self._skip_invalid_checkbox.isChecked(),
            )
            self._csv_importer.config = config
            
            # Perform import
            logger.info(f"Starting import of {self._selected_file}")
            self._import_result = self._csv_importer.import_file(
                self._selected_file,
                field_mapping=field_mapping if field_mapping else None
            )
            
            # Display results
            self._display_import_results()
            
            # Import to database if validation passed and we have data
            db_import_success = False
            if self._import_result.successful_rows > 0:
                db_import_success = self._import_to_database()
            
            # Show appropriate message
            if self._import_result.successful_rows > 0 and db_import_success:
                QMessageBox.information(
                    self,
                    "Import Successful",
                    f"Successfully imported {self._import_result.successful_rows} rows to the database."
                )
            elif self._import_result.successful_rows > 0 and not db_import_success:
                QMessageBox.warning(
                    self,
                    "Partial Success",
                    f"Imported {self._import_result.successful_rows} rows but failed to save to database.\n"
                    "See logs for details."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Import Failed",
                    "No rows were successfully imported."
                )
            
        except Exception as e:
            logger.error(f"Error during import: {e}")
            QMessageBox.critical(
                self,
                "Import Error",
                f"An error occurred during import:\n{str(e)}"
            )
    
    def _get_field_mapping(self) -> Dict[str, str]:
        """Get the current field mapping from UI controls."""
        if not hasattr(self, '_mapping_edits') or not self._mapping_edits:
            return {}
        
        mapping = {}
        for column_name, edit in self._mapping_edits.items():
            internal_field = edit.text().strip()
            if internal_field:
                mapping[column_name] = internal_field
        
        return mapping
    
    def _display_import_results(self) -> None:
        """Display the import results in the results text area."""
        if not self._import_result or not self._results_text:
            return
        
        result = self._import_result
        
        text = f"""
Import Results:
===============
Total Rows: {result.total_rows}
Successful: {result.successful_rows}
Failed: {result.failed_rows}
Success Rate: {result.success_rate:.1f}%

"""
        
        if result.warnings:
            text += "Warnings:\n"
            for warning in result.warnings:
                text += f"  - {warning}\n"
            text += "\n"
        
        if result.errors:
            text += "Errors:\n"
            for error in result.errors:
                text += f"  - {error}\n"
            text += "\n"
        
        if result.imported_data:
            text += f"Imported Data Sample (first {min(3, len(result.imported_data))} rows):\n"
            for i, row in enumerate(result.imported_data[:3]):
                text += f"  Row {i+1}: {row}\n"
        
        self._results_text.setPlainText(text.strip())
    
    def _import_to_database(self) -> bool:
        """Import the validated data into the database."""
        if not self._import_result or not self._import_result.imported_data:
            logger.warning("No data to import to database")
            return False
        
        try:
            # Determine what type of data we're importing based on field names
            # For now, we'll assume incident data since that's what our sample is
            # In a real implementation, this would be configurable
            
            # Get the incident repository
            incident_repo = RepositoryFactory.get_incident_repo()
            
            imported_count = 0
            for row_data in self._import_result.imported_data:
                try:
                    # Convert the row data to an Incident object
                    # Map CSV fields to Incident model fields
                    incident = self._create_incident_from_row(row_data)
                    if incident:
                        incident_repo.create(incident)
                        imported_count += 1
                except Exception as e:
                    logger.error(f"Error creating incident from row {row_data}: {e}")
                    continue
            
            logger.info(f"Successfully imported {imported_count} incidents to database")
            return imported_count > 0
            
        except Exception as e:
            logger.error(f"Error importing data to database: {e}")
            return False
    
    def _create_incident_from_row(self, row_data: Dict[str, Any]) -> Any:
        """Create an Incident object from a row of CSV data."""
        from app.database.models import Incident
        
        try:
            # Map CSV column names to Incident model fields
            # This mapping should match what's expected by the CSV importer
            incident = Incident(
                id="",  # Will be generated by repository
                incident_number=row_data.get('incident_id', ''),
                title=row_data.get('description', '')[:100],  # Truncate to reasonable length
                description=row_data.get('description', ''),
                location_type=row_data.get('location', ''),
                location_details=None,
                latitude=None,
                longitude=None,
                severity_code=row_data.get('severity', ''),
                incident_datetime=f"{row_data.get('date', '')} {row_data.get('time', '00:00')}".strip(),
                reporter_id="",  # Would need to look up or create employee
                reporter_name=row_data.get('reported_by', ''),
                photo_path=None,
                witnesses=None,
                immediate_actions=None,
                root_cause=None,
                corrective_actions=None,
                status="open",
                created_at="",  # Will be set by repository
                updated_at="",  # Will be set by repository
                is_synced=False,
                sync_status_code=0
            )
            
            # Validate required fields
            if not incident.incident_number:
                logger.warning("Skipping row with missing incident number")
                return None
                
            if not incident.title:
                logger.warning("Skipping row with missing title/description")
                return None
                
            return incident
            
        except Exception as e:
            logger.error(f"Error creating incident from row data: {e}")
            return None
    
    def refresh(self) -> None:
        """Refresh the view (called when navigating to this tab)."""
        # Reload file preview if a file was previously selected
        if self._selected_file and self._selected_file.exists():
            self._load_file_preview()