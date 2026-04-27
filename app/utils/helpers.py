"""
PSG - Professional Safety Guardian
Helper Functions Module

This module provides utility helper functions for common operations
such as date formatting, ID generation, and data transformation.
"""

import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Any, TypeVar

from app.constants import DATE_FORMAT, DATE_FORMAT_DISPLAY, DATETIME_FORMAT, DATETIME_FORMAT_ISO

T = TypeVar("T")


def format_date(
    date_value: str | datetime,
    output_format: str = DATE_FORMAT_DISPLAY,
    input_format: str | None = None,
) -> str:
    """
    Format a date value to a string.
    
    Args:
        date_value: The date to format (string or datetime).
        output_format: The desired output format.
        input_format: The input format if date_value is a string.
    
    Returns:
        Formatted date string.
    """
    if isinstance(date_value, datetime):
        return date_value.strftime(output_format)
    
    if not date_value:
        return ""
    
    if input_format:
        date_obj = datetime.strptime(date_value, input_format)
    else:
        # Try common formats
        for fmt in [DATETIME_FORMAT_ISO, DATETIME_FORMAT, DATE_FORMAT]:
            try:
                date_obj = datetime.strptime(date_value, fmt)
                break
            except ValueError:
                continue
        else:
            return date_value  # Return as-is if no format matches
    
    return date_obj.strftime(output_format)


def format_datetime(
    datetime_value: str | datetime,
    output_format: str = DATETIME_FORMAT,
    input_format: str | None = None,
) -> str:
    """
    Format a datetime value to a string.
    
    Args:
        datetime_value: The datetime to format (string or datetime).
        output_format: The desired output format.
        input_format: The input format if datetime_value is a string.
    
    Returns:
        Formatted datetime string.
    """
    if isinstance(datetime_value, datetime):
        return datetime_value.strftime(output_format)
    
    if not datetime_value:
        return ""
    
    if input_format:
        dt_obj = datetime.strptime(datetime_value, input_format)
    else:
        # Try common formats
        for fmt in [DATETIME_FORMAT_ISO, DATETIME_FORMAT, DATE_FORMAT]:
            try:
                dt_obj = datetime.strptime(datetime_value, fmt)
                break
            except ValueError:
                continue
        else:
            return datetime_value  # Return as-is if no format matches
    
    return dt_obj.strftime(output_format)


def get_current_timestamp() -> str:
    """
    Get the current timestamp in ISO format.
    
    Returns:
        Current UTC timestamp string.
    """
    return datetime.utcnow().strftime(DATETIME_FORMAT_ISO)


def get_current_date() -> str:
    """
    Get the current date in standard format.
    
    Returns:
        Current date string.
    """
    return datetime.utcnow().strftime(DATE_FORMAT)


def generate_incident_number() -> str:
    """
    Generate a unique incident number.
    
    Format: INC-YYYYMMDD-XXXX where XXXX is a random 4-digit number.
    
    Returns:
        Unique incident number string.
    """
    date_str = datetime.utcnow().strftime("%Y%m%d")
    random_suffix = "".join(random.choices(string.digits, k=4))
    return f"INC-{date_str}-{random_suffix}"


def generate_audit_number() -> str:
    """
    Generate a unique audit number.
    
    Format: AUD-YYYYMMDD-XXXX
    
    Returns:
        Unique audit number string.
    """
    date_str = datetime.utcnow().strftime("%Y%m%d")
    random_suffix = "".join(random.choices(string.digits, k=4))
    return f"AUD-{date_str}-{random_suffix}"


def generate_uuid() -> str:
    """
    Generate a UUID string.
    
    Returns:
        UUID string.
    """
    return str(uuid.uuid4())


def calculate_days_until(date_str: str, from_date: datetime | None = None) -> int:
    """
    Calculate the number of days until a given date.
    
    Args:
        date_str: The target date string.
        from_date: The reference date (defaults to today).
    
    Returns:
        Number of days (negative if date is in the past).
    """
    if from_date is None:
        from_date = datetime.utcnow().date()
    elif isinstance(from_date, datetime):
        from_date = from_date.date()
    
    try:
        target_date = datetime.strptime(date_str, DATE_FORMAT).date()
    except ValueError:
        try:
            target_date = datetime.strptime(date_str, DATETIME_FORMAT_ISO).date()
        except ValueError:
            return 0
    
    return (target_date - from_date).days


def calculate_days_since(date_str: str, from_date: datetime | None = None) -> int:
    """
    Calculate the number of days since a given date.
    
    Args:
        date_str: The past date string.
        from_date: The reference date (defaults to today).
    
    Returns:
        Number of days.
    """
    if from_date is None:
        from_date = datetime.utcnow().date()
    elif isinstance(from_date, datetime):
        from_date = from_date.date()
    
    try:
        past_date = datetime.strptime(date_str, DATE_FORMAT).date()
    except ValueError:
        try:
            past_date = datetime.strptime(date_str, DATETIME_FORMAT_ISO).date()
        except ValueError:
            return 0
    
    return (from_date - past_date).days


def is_date_expired(date_str: str) -> bool:
    """
    Check if a date has passed.
    
    Args:
        date_str: The date to check.
    
    Returns:
        True if the date is in the past, False otherwise.
    """
    return calculate_days_until(date_str) < 0


def is_date_expiring_soon(date_str: str, days_threshold: int = 30) -> bool:
    """
    Check if a date is expiring within a threshold.
    
    Args:
        date_str: The date to check.
        days_threshold: Number of days to consider "soon".
    
    Returns:
        True if expiring within threshold, False otherwise.
    """
    days_until = calculate_days_until(date_str)
    return 0 <= days_until <= days_threshold


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: The text to truncate.
        max_length: Maximum length including suffix.
        suffix: Suffix to add if truncated.
    
    Returns:
        Truncated text.
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def safe_get(data: dict, *keys, default: Any = None) -> Any:
    """
    Safely get a nested value from a dictionary.
    
    Args:
        data: The dictionary to search.
        *keys: Keys to traverse.
        default: Default value if key not found.
    
    Returns:
        The value or default.
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


def merge_dicts(base: dict, override: dict) -> dict:
    """
    Recursively merge two dictionaries.
    
    Args:
        base: The base dictionary.
        override: Values to override/merge.
    
    Returns:
        Merged dictionary.
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def chunk_list(items: list[T], chunk_size: int) -> list[list[T]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        items: The list to split.
        chunk_size: Maximum size of each chunk.
    
    Returns:
        List of chunks.
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def sanitize_html(text: str) -> str:
    """
    Sanitize HTML content by escaping special characters.
    
    Args:
        text: The text to sanitize.
    
    Returns:
        Sanitized text.
    """
    if not text:
        return ""
    
    # Use chr() to avoid quoting issues with special characters
    replacements = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        chr(34): '&quot;',  # double quote
        "'": "&#39;",
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    return text


def format_file_size(size_bytes: int) -> str:
    """
    Format a file size in bytes to human-readable format.
    
    Args:
        size_bytes: Size in bytes.
    
    Returns:
        Human-readable size string.
    """
    if size_bytes < 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.1f} {units[unit_index]}"


def get_relative_time(dt: datetime) -> str:
    """
    Get a relative time string (e.g., "2 hours ago").
    
    Args:
        dt: The datetime to format.
    
    Returns:
        Relative time string.
    """
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "just now"


def parse_bool(value: Any, default: bool = False) -> bool:
    """
    Parse a value to boolean.
    
    Args:
        value: The value to parse.
        default: Default value if parsing fails.
    
    Returns:
        Boolean value.
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1", "on")
    
    if isinstance(value, int):
        return value != 0
    
    return default