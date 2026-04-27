"""
PSG - Professional Safety Guardian
CSV Validator Module

This module provides validation functionality for CSV data,
ensuring data integrity before import into the database.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    
    is_valid: bool = True
    field_name: str = ""
    error_message: str = ""
    warning_message: str = ""
    error_code: str | None = None
    
    def merge(self, other: "ValidationResult") -> None:
        """Merge another validation result into this one."""
        if not other.is_valid:
            self.is_valid = False
            if other.error_message:
                self.error_message = (
                    f"{self.error_message}; {other.error_message}"
                ).strip("; ")
        if other.warning_message:
            self.warning_message = (
                f"{self.warning_message}; {other.warning_message}"
            ).strip("; ")


@dataclass
class FieldValidator:
    """Validator for a specific field type."""
    
    name: str
    required: bool = False
    field_type: str = "string"  # string, number, date, email, phone, enum
    min_length: int | None = None
    max_length: int | None = None
    min_value: float | None = None
    max_value: float | None = None
    pattern: str | None = None
    allowed_values: list[str] | None = None
    custom_validator: Any = None


class CSVValidator:
    """
    CSV data validator with configurable field rules.
    
    This class validates CSV data against defined field rules,
    supporting various data types and validation constraints.
    """
    
    def __init__(self):
        self.field_validators: dict[str, FieldValidator] = {}
        self._setup_default_validators()
    
    def _setup_default_validators(self) -> None:
        """Set up default field validators."""
        # Common incident fields
        self.add_field_validator(FieldValidator(
            name="incident_id",
            required=True,
            field_type="string",
            min_length=1,
            max_length=50,
        ))
        
        self.add_field_validator(FieldValidator(
            name="date",
            required=True,
            field_type="date",
        ))
        
        self.add_field_validator(FieldValidator(
            name="time",
            required=False,
            field_type="string",
            pattern=r"^\d{2}:\d{2}(:\d{2})?$",
        ))
        
        self.add_field_validator(FieldValidator(
            name="location",
            required=True,
            field_type="string",
            min_length=1,
            max_length=200,
        ))
        
        self.add_field_validator(FieldValidator(
            name="severity",
            required=True,
            field_type="enum",
            allowed_values=["near_miss", "minor", "moderate", "major", "critical", "fatal"],
        ))
        
        self.add_field_validator(FieldValidator(
            name="description",
            required=True,
            field_type="string",
            min_length=1,
            max_length=1000,
        ))
        
        self.add_field_validator(FieldValidator(
            name="reported_by",
            required=True,
            field_type="string",
            min_length=1,
            max_length=100,
        ))
        
        self.add_field_validator(FieldValidator(
            name="email",
            required=False,
            field_type="email",
        ))
        
        self.add_field_validator(FieldValidator(
            name="phone",
            required=False,
            field_type="phone",
            pattern=r"^\+?[\d\s\-()]{7,20}$",
        ))
    
    def add_field_validator(self, validator: FieldValidator) -> None:
        """Add or update a field validator."""
        self.field_validators[validator.name] = validator
    
    def remove_field_validator(self, field_name: str) -> None:
        """Remove a field validator."""
        self.field_validators.pop(field_name, None)
    
    def validate_row(self, row: dict[str, Any]) -> ValidationResult:
        """
        Validate a single row of data.
        
        Args:
            row: Dictionary of field names to values
            
        Returns:
            ValidationResult indicating if the row is valid
        """
        result = ValidationResult()
        
        for field_name, validator in self.field_validators.items():
            field_result = self._validate_field(field_name, row.get(field_name), validator)
            
            if not field_result.is_valid:
                result.is_valid = False
                result.error_message = (
                    f"{result.error_message}; {field_result.error_message}"
                ).strip("; ")
            
            if field_result.warning_message:
                result.warning_message = (
                    f"{result.warning_message}; {field_result.warning_message}"
                ).strip("; ")
        
        return result
    
    def _validate_field(
        self,
        field_name: str,
        value: Any,
        validator: FieldValidator,
    ) -> ValidationResult:
        """Validate a single field value."""
        result = ValidationResult(field_name=field_name)
        
        # Check required
        if value is None or (isinstance(value, str) and not value.strip()):
            if validator.required:
                result.is_valid = False
                result.error_message = f"Required field '{field_name}' is missing"
                result.error_code = "REQUIRED_FIELD_MISSING"
            return result
        
        # Skip further validation if empty and not required
        if not value:
            return result
        
        value_str = str(value).strip() if value else ""
        
        # Type-specific validation
        if validator.field_type == "number":
            type_result = self._validate_number(field_name, value_str, validator)
        elif validator.field_type == "date":
            type_result = self._validate_date(field_name, value_str, validator)
        elif validator.field_type == "email":
            type_result = self._validate_email(field_name, value_str, validator)
        elif validator.field_type == "phone":
            type_result = self._validate_phone(field_name, value_str, validator)
        elif validator.field_type == "enum":
            type_result = self._validate_enum(field_name, value_str, validator)
        else:
            type_result = self._validate_string(field_name, value_str, validator)
        
        return type_result
    
    def _validate_string(
        self,
        field_name: str,
        value: str,
        validator: FieldValidator,
    ) -> ValidationResult:
        """Validate a string field."""
        result = ValidationResult(field_name=field_name)
        
        # Length validation
        if validator.min_length is not None and len(value) < validator.min_length:
            result.is_valid = False
            result.error_message = (
                f"Field '{field_name}' must be at least {validator.min_length} characters"
            )
            result.error_code = "STRING_TOO_SHORT"
        
        if validator.max_length is not None and len(value) > validator.max_length:
            result.is_valid = False
            result.error_message = (
                f"Field '{field_name}' must be at most {validator.max_length} characters"
            )
            result.error_code = "STRING_TOO_LONG"
        
        # Pattern validation
        if validator.pattern and not re.match(validator.pattern, value):
            result.is_valid = False
            result.error_message = (
                f"Field '{field_name}' has invalid format"
            )
            result.error_code = "INVALID_FORMAT"
        
        return result
    
    def _validate_number(
        self,
        field_name: str,
        value: str,
        validator: FieldValidator,
    ) -> ValidationResult:
        """Validate a numeric field."""
        result = ValidationResult(field_name=field_name)
        
        try:
            num_value = float(value)
        except ValueError:
            result.is_valid = False
            result.error_message = f"Field '{field_name}' must be a valid number"
            result.error_code = "INVALID_NUMBER"
            return result
        
        if validator.min_value is not None and num_value < validator.min_value:
            result.is_valid = False
            result.error_message = (
                f"Field '{field_name}' must be at least {validator.min_value}"
            )
            result.error_code = "VALUE_TOO_LOW"
        
        if validator.max_value is not None and num_value > validator.max_value:
            result.is_valid = False
            result.error_message = (
                f"Field '{field_name}' must be at most {validator.max_value}"
            )
            result.error_code = "VALUE_TOO_HIGH"
        
        return result
    
    def _validate_date(
        self,
        field_name: str,
        value: str,
        validator: FieldValidator,
    ) -> ValidationResult:
        """Validate a date field."""
        result = ValidationResult(field_name=field_name)
        
        date_formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%Y-%m-%d %H:%M:%S",
        ]
        
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
        
        if parsed_date is None:
            result.is_valid = False
            result.error_message = (
                f"Field '{field_name}' must be a valid date (supported: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY)"
            )
            result.error_code = "INVALID_DATE"
        
        return result
    
    def _validate_email(self, field_name: str, value: str, validator: FieldValidator) -> ValidationResult:
        """Validate an email field."""
        result = ValidationResult(field_name=field_name)
        
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, value):
            result.is_valid = False
            result.error_message = f"Field '{field_name}' must be a valid email address"
            result.error_code = "INVALID_EMAIL"
        
        return result
    
    def _validate_phone(self, field_name: str, value: str, validator: FieldValidator) -> ValidationResult:
        """Validate a phone number field."""
        result = ValidationResult(field_name=field_name)
        
        if validator.pattern and not re.match(validator.pattern, value):
            result.is_valid = False
            result.error_message = f"Field '{field_name}' has invalid phone number format"
            result.error_code = "INVALID_PHONE"
        
        return result
    
    def _validate_enum(
        self,
        field_name: str,
        value: str,
        validator: FieldValidator,
    ) -> ValidationResult:
        """Validate an enum/select field."""
        result = ValidationResult(field_name=field_name)
        
        if validator.allowed_values and value.lower() not in validator.allowed_values:
            result.is_valid = False
            result.error_message = (
                f"Field '{field_name}' must be one of: {', '.join(validator.allowed_values)}"
            )
            result.error_code = "INVALID_ENUM_VALUE"
        
        return result
    
    def validate_batch(self, rows: list[dict[str, Any]]) -> list[ValidationResult]:
        """
        Validate multiple rows at once.
        
        Args:
            rows: List of row dictionaries
            
        Returns:
            List of ValidationResult objects
        """
        return [self.validate_row(row) for row in rows]
    
    def get_validation_summary(
        self,
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Get a summary of validation results for a batch of rows.
        
        Args:
            rows: List of row dictionaries
            
        Returns:
            Dictionary with validation summary statistics
        """
        results = self.validate_batch(rows)
        
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = len(results) - valid_count
        
        return {
            "total_rows": len(rows),
            "valid_rows": valid_count,
            "invalid_rows": invalid_count,
            "success_rate": (valid_count / len(rows) * 100) if rows else 0,
            "results": results,
        }


def create_validator(
    field_rules: list[dict[str, Any]],
) -> CSVValidator:
    """
    Factory function to create a CSVValidator with custom field rules.
    
    Args:
        field_rules: List of field rule dictionaries
        
    Returns:
        Configured CSVValidator instance
    """
    validator = CSVValidator()
    
    for rule in field_rules:
        validator.add_field_validator(FieldValidator(**rule))
    
    return validator