"""Common Pydantic schemas and utilities."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
    )


class TimestampMixin(BaseModel):
    """Mixin for models with timestamps."""
    
    created_at: datetime
    updated_at: datetime


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    limit: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper."""
    
    items: list[Any]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_prev: bool


class ErrorResponse(BaseSchema):
    """Error response schema."""
    
    error: dict[str, str] = Field(
        description="Error details",
        examples=[{
            "code": "VALIDATION_ERROR",
            "message": "Invalid input data",
            "field": "email"
        }]
    )


class SuccessResponse(BaseSchema):
    """Success response schema."""
    
    message: str
    data: Optional[dict[str, Any]] = None
