"""
PSG - Professional Safety Guardian
Input Validation Module

This module provides validation functions for user input,
ensuring data integrity before storage or transmission.
"""

import re
from datetime import datetime
from typing import Any

from app.constants import DATE_FORMAT, DATETIME_FORMAT_ISO


def validate_email(email: str) -> bool:
    """
    Validate an email address.
    
    Args:
        email: The email address to validate.
    
    Returns:
        True if the email is valid, False otherwise.
    """
    if not email:
        return False
    
    # Basic email regex pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_phone(phone: str, country_code: str = "AE") -> bool:
    """
    Validate a phone number.
    
    Args:
        phone: The phone number to validate.
        country_code: The country code (default: AE for UAE).
    
    Returns:
        True if the phone number is valid, False otherwise.
    """
    if not phone:
        return False
    
    # Remove common separators
    cleaned = re.sub(r"[\s\-\(\)\.]", "", phone)
    
    if country_code == "AE":
        # UAE phone numbers: +971 followed by 9 digits, or 0 followed by 9 digits
        pattern = r"^(\+971|00971|0)?[5-9]\d{8}$"
    else:
        # Generic international format
        pattern = r"^\+?[1-9]\d{6,14}$"
    
    return bool(re.match(pattern, cleaned))


def validate_date(
    date_str: str,
    date_format: str = DATE_FORMAT,
    allow_empty: bool = False,
) -> bool:
    """
    Validate a date string.
    
    Args:
        date_str: The date string to validate.
        date_format: The expected date format.
        allow_empty: Whether to allow empty strings.
    
    Returns:
        True if the date is valid, False otherwise.
    """
    if not date_str:
        return allow_empty
    
    try:
        datetime.strptime(date_str, date_format)
        return True
    except ValueError:
        return False


def validate_datetime(
    datetime_str: str,
    date_format: str = DATETIME_FORMAT_ISO,
    allow_empty: bool = False,
) -> bool:
    """
    Validate a datetime string.
    
    Args:
        datetime_str: The datetime string to validate.
        date_format: The expected datetime format.
        allow_empty: Whether to allow empty strings.
    
    Returns:
        True if the datetime is valid, False otherwise.
    """
    if not datetime_str:
        return allow_empty
    
    try:
        datetime.strptime(datetime_str, date_format)
        return True
    except ValueError:
        return False


def validate_required(value: Any, field_name: str = "Field") -> tuple[bool, str]:
    """
    Validate that a required field is not empty.
    
    Args:
        value: The value to check.
        field_name: The name of the field for error messages.
    
    Returns:
        Tuple of (is_valid, error_message).
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return False, f"{field_name} is required"
    return True, ""


def validate_length(
    value: str,
    min_length: int = 0,
    max_length: int = 1000,
    field_name: str = "Field",
) -> tuple[bool, str]:
    """
    Validate string length.
    
    Args:
        value: The string to validate.
        min_length: Minimum allowed length.
        max_length: Maximum allowed length.
        field_name: The name of the field for error messages.
    
    Returns:
        Tuple of (is_valid, error_message).
    """
    if not value:
        return True, ""  # Empty is ok, use validate_required for required fields
    
    if len(value) < min_length:
        return False, f"{field_name} must be at least {min_length} characters"
    
    if len(value) > max_length:
        return False, f"{field_name} must not exceed {max_length} characters"
    
    return True, ""


def validate_number(
    value: Any,
    min_value: float | None = None,
    max_value: float | None = None,
    field_name: str = "Field",
) -> tuple[bool, str]:
    """
    Validate a numeric value.
    
    Args:
        value: The value to validate.
        min_value: Minimum allowed value.
        max_value: Maximum allowed value.
        field_name: The name of the field for error messages.
    
    Returns:
        Tuple of (is_valid, error_message).
    """
    try:
        num_value = float(value)
    except (ValueError, TypeError):
        return False, f"{field_name} must be a number"
    
    if min_value is not None and num_value < min_value:
        return False, f"{field_name} must be at least {min_value}"
    
    if max_value is not None and num_value > max_value:
        return False, f"{field_name} must not exceed {max_value}"
    
    return True, ""


def validate_severity_code(severity_code: str) -> bool:
    """
    Validate an incident severity code.
    
    Args:
        severity_code: The severity code to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    from app.constants import SeverityLevel
    
    valid_codes = {level.code for level in SeverityLevel}
    return severity_code in valid_codes


def validate_location_type(location_type: str) -> bool:
    """
    Validate a location type code.
    
    Args:
        location_type: The location type code to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    from app.constants import LocationType
    
    valid_codes = {lt.code for lt in LocationType}
    return location_type in valid_codes


def validate_training_status(status: str) -> bool:
    """
    Validate a training status code.
    
    Args:
        status: The status code to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    from app.constants import TrainingStatus
    
    valid_codes = {s.code for s in TrainingStatus}
    return status in valid_codes


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field


class Validator:
    """
    Chainable validator for complex validation scenarios.
    
    Usage:
        errors = (Validator()
            .required("title", title)
            .min_length("description", description, 10)
            .email("contact_email", email)
            .validate())
    """
    
    def __init__(self):
        """Initialize the validator."""
        self._errors: dict[str, str] = {}
    
    def required(self, field: str, value: Any) -> "Validator":
        """Validate a required field."""
        is_valid, message = validate_required(value, field)
        if not is_valid:
            self._errors[field] = message
        return self
    
    def min_length(self, field: str, value: str, length: int) -> "Validator":
        """Validate minimum string length."""
        if value and len(value) < length:
            self._errors[field] = f"{field} must be at least {length} characters"
        return self
    
    def max_length(self, field: str, value: str, length: int) -> "Validator":
        """Validate maximum string length."""
        if value and len(value) > length:
            self._errors[field] = f"{field} must not exceed {length} characters"
        return self
    
    def email(self, field: str, value: str) -> "Validator":
        """Validate an email address."""
        if value and not validate_email(value):
            self._errors[field] = f"{field} must be a valid email address"
        return self
    
    def phone(self, field: str, value: str, country_code: str = "AE") -> "Validator":
        """Validate a phone number."""
        if value and not validate_phone(value, country_code):
            self._errors[field] = f"{field} must be a valid phone number"
        return self
    
    def number(
        self,
        field: str,
        value: Any,
        min_value: float | None = None,
        max_value: float | None = None,
    ) -> "Validator":
        """Validate a numeric value."""
        is_valid, message = validate_number(value, min_value, max_value, field)
        if not is_valid:
            self._errors[field] = message
        return self
    
    def date(self, field: str, value: str, date_format: str = DATE_FORMAT) -> "Validator":
        """Validate a date string."""
        if value and not validate_date(value, date_format):
            self._errors[field] = f"{field} must be a valid date ({date_format})"
        return self
    
    def custom(
        self,
        field: str,
        value: Any,
        validation_func: callable,
        error_message: str,
    ) -> "Validator":
        """Run a custom validation function."""
        if value and not validation_func(value):
            self._errors[field] = error_message
        return self
    
    def validate(self) -> dict[str, str]:
        """
        Get all validation errors.
        
        Returns:
            Dictionary of field names to error messages.
        """
        return self._errors
    
    def is_valid(self) -> bool:
        """
        Check if all validations passed.
        
        Returns:
            True if no errors, False otherwise.
        """
        return len(self._errors) == 0
    
    def raise_if_invalid(self) -> None:
        """
        Raise a ValidationError if validation failed.
        
        Raises:
            ValidationError: If any validation failed.
        """
        if self._errors:
            error_messages = "; ".join(self._errors.values())
            raise ValidationError(error_messages)