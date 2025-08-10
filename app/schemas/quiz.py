"""Quiz schemas."""

from datetime import datetime
from typing import Optional

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema, TimestampMixin


class QuizCreate(BaseSchema):
    """Schema for creating a new quiz."""
    
    subject: str = Field(..., min_length=1, max_length=100, description="Subject area")
    grade_level: str = Field(..., min_length=1, max_length=50, description="Grade level")
    num_questions: int = Field(..., ge=1, le=50, description="Number of questions")
    difficulty: str = Field(..., description="Difficulty level")
    topics: list[str] = Field(..., min_length=1, description="List of topics to cover")
    question_types: list[str] = Field(..., min_length=1, description="Types of questions")
    standard: Optional[str] = Field(None, max_length=100, description="Educational standard")
    adaptive: bool = Field(default=False, description="Enable adaptive difficulty")
    
    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        valid_difficulties = ["easy", "medium", "hard", "adaptive"]
        if v not in valid_difficulties:
            raise ValueError(f"Difficulty must be one of: {valid_difficulties}")
        return v
    
    @field_validator("question_types")
    @classmethod
    def validate_question_types(cls, v: list[str]) -> list[str]:
        valid_types = ["MCQ", "TF", "short_answer", "essay"]
        for qt in v:
            if qt not in valid_types:
                raise ValueError(f"Question type '{qt}' must be one of: {valid_types}")
        return v


class QuizResponse(BaseSchema, TimestampMixin):
    """Schema for quiz response."""
    
    id: int
    title: str
    subject: str
    grade_level: str
    num_questions: int
    difficulty: str
    adaptive: bool
    topics: list[str]
    question_types: list[str]
    standard: Optional[str]
    description: Optional[str]
    is_published: bool
    creator_id: int


class QuizSummary(BaseSchema):
    """Schema for quiz summary in lists."""
    
    id: int
    title: str
    subject: str
    grade_level: str
    num_questions: int
    difficulty: str
    created_at: datetime
    is_published: bool


class QuizRetryRequest(BaseSchema):
    """Schema for quiz retry request."""
    
    reason: Optional[str] = Field(None, max_length=200, description="Reason for retry")


class QuizRetryResponse(BaseSchema):
    """Schema for quiz retry response."""
    
    new_quiz_id: int
    retry_number: int
    message: str
