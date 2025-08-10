"""History and filtering schemas."""

from datetime import date, datetime
from typing import Optional

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema, PaginationParams
from app.schemas.submission import SubmissionSummary


class HistoryFilters(BaseSchema):
    """Schema for history filtering parameters."""
    
    grade: Optional[str] = Field(None, description="Filter by grade level")
    subject: Optional[str] = Field(None, description="Filter by subject")
    min_marks: Optional[float] = Field(None, ge=0, le=100, description="Minimum percentage")
    max_marks: Optional[float] = Field(None, ge=0, le=100, description="Maximum percentage")
    from_date: Optional[str] = Field(None, description="Start date (ISO format or DD/MM/YYYY)")
    to_date: Optional[str] = Field(None, description="End date (ISO format or DD/MM/YYYY)")
    completed_date: Optional[str] = Field(None, description="Specific completion date (ISO format or DD/MM/YYYY)")
    
    @field_validator("min_marks", "max_marks")
    @classmethod
    def validate_marks_range(cls, v: Optional[float], info) -> Optional[float]:
        if v is not None:
            values = info.data
            min_marks = values.get("min_marks")
            max_marks = values.get("max_marks")
            
            if min_marks is not None and max_marks is not None and min_marks > max_marks:
                raise ValueError("min_marks cannot be greater than max_marks")
        return v


class HistoryResponse(BaseSchema):
    """Schema for history response."""
    
    submissions: list[SubmissionSummary]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_prev: bool
    filters_applied: dict[str, str]


def parse_date_string(date_str: str) -> datetime:
    """Parse date string in ISO format or DD/MM/YYYY format."""
    # Try ISO format first
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        pass
    
    # Try DD/MM/YYYY format
    try:
        parsed_date = datetime.strptime(date_str, "%d/%m/%Y")
        # Return start of day in UTC
        return parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
    except ValueError:
        raise ValueError(f"Invalid date format. Use ISO format or DD/MM/YYYY. Got: {date_str}")


def parse_date_range(date_str: str) -> tuple[datetime, datetime]:
    """Parse date string and return start and end of day in UTC."""
    parsed_date = parse_date_string(date_str)
    
    # If it's just a date (DD/MM/YYYY), return start and end of that day
    if parsed_date.hour == 0 and parsed_date.minute == 0 and parsed_date.second == 0:
        start_of_day = parsed_date
        end_of_day = parsed_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start_of_day, end_of_day
    
    # If it's a datetime (ISO), return as-is for both start and end
    return parsed_date, parsed_date
