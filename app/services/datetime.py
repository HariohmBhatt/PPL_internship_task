"""DateTime utilities for the application."""

from datetime import datetime, timezone
from typing import Tuple

from app.core.errors import ValidationError


def parse_date_filter(date_str: str) -> datetime:
    """Parse date string in ISO format or DD/MM/YYYY format to UTC datetime."""
    if not date_str:
        raise ValidationError("Date string cannot be empty")
    
    # Try ISO format first (with or without timezone)
    try:
        # Handle various ISO formats
        if date_str.endswith('Z'):
            date_str = date_str[:-1] + '+00:00'
        
        parsed_date = datetime.fromisoformat(date_str)
        
        # If no timezone info, assume UTC
        if parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(tzinfo=timezone.utc)
        
        # Convert to UTC
        return parsed_date.astimezone(timezone.utc)
        
    except ValueError:
        pass
    
    # Try DD/MM/YYYY format
    try:
        parsed_date = datetime.strptime(date_str, "%d/%m/%Y")
        # Return start of day in UTC
        return parsed_date.replace(tzinfo=timezone.utc)
        
    except ValueError:
        pass
    
    # Try other common formats
    formats_to_try = [
        "%Y-%m-%d",  # YYYY-MM-DD
        "%d-%m-%Y",  # DD-MM-YYYY
        "%m/%d/%Y",  # MM/DD/YYYY
        "%Y/%m/%d",  # YYYY/MM/DD
    ]
    
    for fmt in formats_to_try:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    
    raise ValidationError(
        f"Invalid date format: '{date_str}'. "
        "Use ISO format (YYYY-MM-DDTHH:MM:SS) or DD/MM/YYYY format.",
        field="date"
    )


def parse_date_range(date_str: str) -> Tuple[datetime, datetime]:
    """Parse date string and return start and end of day in UTC."""
    parsed_date = parse_date_filter(date_str)
    
    # If it's just a date (00:00:00 time), return start and end of that day
    if (parsed_date.hour == 0 and parsed_date.minute == 0 and 
        parsed_date.second == 0 and parsed_date.microsecond == 0):
        
        start_of_day = parsed_date
        end_of_day = parsed_date.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        return start_of_day, end_of_day
    
    # If it's a datetime, return as-is for both start and end
    return parsed_date, parsed_date


def get_utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def to_iso_string(dt: datetime) -> str:
    """Convert datetime to ISO string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def normalize_to_utc(dt: datetime) -> datetime:
    """Normalize datetime to UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
