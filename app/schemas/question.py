"""Question schemas."""

from typing import Optional

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema


class QuestionCreate(BaseSchema):
    """Schema for creating a question."""
    
    question_text: str = Field(..., min_length=1, description="Question text")
    question_type: str = Field(..., description="Question type")
    difficulty: str = Field(..., description="Question difficulty")
    topic: str = Field(..., min_length=1, max_length=100, description="Question topic")
    points: int = Field(default=1, ge=1, description="Points for correct answer")
    options: Optional[list[str]] = Field(None, description="Options for MCQ")
    correct_answer: Optional[str] = Field(None, description="Correct answer")
    explanation: Optional[str] = Field(None, description="Explanation of the answer")
    hint_text: Optional[str] = Field(None, description="Hint for the question")
    
    @field_validator("question_type")
    @classmethod
    def validate_question_type(cls, v: str) -> str:
        valid_types = ["MCQ", "TF", "short_answer", "essay"]
        if v not in valid_types:
            raise ValueError(f"Question type must be one of: {valid_types}")
        return v
    
    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        valid_difficulties = ["easy", "medium", "hard"]
        if v not in valid_difficulties:
            raise ValueError(f"Difficulty must be one of: {valid_difficulties}")
        return v


class QuestionResponse(BaseSchema):
    """Schema for question response (without answers)."""
    
    id: int
    question_text: str
    question_type: str
    difficulty: str
    topic: str
    order: int
    points: int
    options: Optional[list[str]]
    hint_text: Optional[str]
    # Note: correct_answer and explanation are excluded for security


class QuestionWithAnswer(QuestionResponse):
    """Schema for question with answer (for admin/review)."""
    
    correct_answer: Optional[str]
    explanation: Optional[str]


class HintRequest(BaseSchema):
    """Schema for hint request."""
    
    pass  # No additional fields needed


class HintResponse(BaseSchema):
    """Schema for hint response."""
    
    hint: str = Field(..., description="AI-generated hint")
    hints_used: int = Field(..., description="Total hints used for this question")
    remaining_hints: int = Field(..., description="Remaining hints allowed")


class NextQuestionRequest(BaseSchema):
    """Schema for adaptive next question request."""
    
    pass  # The system determines next question based on performance


class NextQuestionResponse(BaseSchema):
    """Schema for next question response."""
    
    question: Optional[QuestionResponse] = Field(None, description="Next question or null if quiz complete")
    is_complete: bool = Field(..., description="Whether the quiz is complete")
    progress: dict[str, int] = Field(..., description="Quiz progress information")
