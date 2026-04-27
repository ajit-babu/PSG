"""
PSG - Professional Safety Guardian
CSV Import Module

This module handles importing CSV files into the application,
providing data validation and batch processing capabilities.
"""

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from app.services.csv_validator import CSVValidator, ValidationResult


@dataclass
class ImportConfig:
    """Configuration for CSV import operations."""
    
    encoding: str = "utf-8"
    delimiter: str = ","
    skip_header: bool = True
    batch_size: int = 100
    validate_on_import: bool = True
    skip_invalid_rows: bool = False


@dataclass
class ImportResult:
    """Result of a CSV import operation."""
    
    total_rows: int = 0
    successful_rows: int = 0
    failed_rows: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    imported_data: list[dict[str, Any]] = field(default_factory=list)
    validation_results: list[ValidationResult] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_rows == 0:
            return 0.0
        return (self.successful_rows / self.total_rows) * 100


class CSVImporter:
    """
    CSV file importer with validation support.
    
    This class handles reading CSV files, validating the data,
    and preparing it for import into the database.
    """
    
    def __init__(self, config: ImportConfig | None = None):
        self.config = config or ImportConfig()
        self.validator = CSVValidator()
    
    def import_file(
        self,
        file_path: str | Path,
        field_mapping: dict[str, str] | None = None,
        custom_validator: Callable[[dict[str, Any]], ValidationResult] | None = None,
    ) -> ImportResult:
        """
        Import data from a CSV file.
        
        Args:
            file_path: Path to the CSV file
            field_mapping: Optional mapping from CSV columns to internal fields
            custom_validator: Optional custom validation function
            
        Returns:
            ImportResult with import statistics and data
        """
        result = ImportResult()
        file_path = Path(file_path)
        
        # Validate file exists
        if not file_path.exists():
            result.errors.append(f"File not found: {file_path}")
            return result
        
        # Validate file extension
        if file_path.suffix.lower() != ".csv":
            result.errors.append(f"Invalid file type: {file_path.suffix}. Expected .csv")
            return result
        
        try:
            with open(
                file_path,
                "r",
                encoding=self.config.encoding,
                newline="",
            ) as csvfile:
                reader = csv.DictReader(
                    csvfile,
                    delimiter=self.config.delimiter,
                )
                
                rows = list(reader)
                result.total_rows = len(rows)
                
                for idx, row in enumerate(rows):
                    try:
                        # Apply field mapping if provided
                        mapped_row = self._map_fields(row, field_mapping)
                        
                        # Validate row if enabled
                        if self.config.validate_on_import:
                            validation = self.validator.validate_row(mapped_row)
                            
                            if custom_validator:
                                custom_validation = custom_validator(mapped_row)
                                validation.merge(custom_validation)
                            
                            result.validation_results.append(validation)
                            
                            if not validation.is_valid:
                                result.failed_rows += 1
                                if not self.config.skip_invalid_rows:
                                    result.errors.append(
                                        f"Row {idx + 1}: {validation.error_message}"
                                    )
                                continue
                        
                        result.successful_rows += 1
                        result.imported_data.append(mapped_row)
                        
                    except Exception as e:
                        result.failed_rows += 1
                        result.errors.append(f"Row {idx + 1}: {str(e)}")
        
        except UnicodeDecodeError:
            result.errors.append(
                f"Encoding error: Could not read file with {self.config.encoding} encoding. "
                "Try UTF-8 or ISO-8859-1."
            )
        except Exception as e:
            result.errors.append(f"Failed to read CSV file: {str(e)}")
        
        return result
    
    def _map_fields(
        self,
        row: dict[str, Any],
        field_mapping: dict[str, str] | None,
    ) -> dict[str, Any]:
        """Map CSV columns to internal field names."""
        if not field_mapping:
            return row
        
        mapped = {}
        for csv_column, internal_field in field_mapping.items():
            if csv_column in row:
                mapped[internal_field] = row[csv_column]
        
        return mapped
    
    def get_column_names(self, file_path: str | Path) -> list[str]:
        """Get column names from a CSV file without reading all data."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return []
        
        try:
            with open(
                file_path,
                "r",
                encoding=self.config.encoding,
                newline="",
            ) as csvfile:
                reader = csv.DictReader(
                    csvfile,
                    delimiter=self.config.delimiter,
                )
                return reader.fieldnames or []
        except Exception:
            return []
    
    def preview_file(
        self,
        file_path: str | Path,
        max_rows: int = 10,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """
        Preview a CSV file without fully importing it.
        
        Returns:
            Tuple of (column_names, sample_rows)
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return [], []
        
        try:
            with open(
                file_path,
                "r",
                encoding=self.config.encoding,
                newline="",
            ) as csvfile:
                reader = csv.DictReader(
                    csvfile,
                    delimiter=self.config.delimiter,
                )
                
                columns = reader.fieldnames or []
                rows = []
                
                for idx, row in enumerate(reader):
                    if idx >= max_rows:
                        break
                    rows.append(row)
                
                return columns, rows
        except Exception:
            return [], []


def create_importer(
    encoding: str = "utf-8",
    delimiter: str = ",",
    skip_header: bool = True,
    batch_size: int = 100,
    validate_on_import: bool = True,
    skip_invalid_rows: bool = False,
) -> CSVImporter:
    """
    Factory function to create a CSVImporter with custom configuration.
    
    Args:
        encoding: File encoding (default: utf-8)
        delimiter: CSV delimiter character (default: ,)
        skip_header: Whether to skip the header row (default: True)
        batch_size: Number of rows to process in a batch (default: 100)
        validate_on_import: Whether to validate data on import (default: True)
        skip_invalid_rows: Whether to skip invalid rows instead of failing (default: False)
        
    Returns:
        Configured CSVImporter instance
    """
    config = ImportConfig(
        encoding=encoding,
        delimiter=delimiter,
        skip_header=skip_header,
        batch_size=batch_size,
        validate_on_import=validate_on_import,
        skip_invalid_rows=skip_invalid_rows,
    )
    return CSVImporter(config)