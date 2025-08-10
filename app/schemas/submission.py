"""Submission schemas."""

from datetime import datetime
from typing import Optional

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema


class AnswerSubmission(BaseSchema):
    """Schema for individual answer submission."""
    
    question_id: int = Field(..., description="Question ID")
    answer_text: Optional[str] = Field(None, description="Text answer for subjective questions")
    selected_option: Optional[str] = Field(None, description="Selected option for MCQ/TF")
    time_spent_seconds: Optional[int] = Field(None, ge=0, description="Time spent on question")
    
    @field_validator("answer_text", "selected_option")
    @classmethod
    def validate_answer_provided(cls, v: Optional[str], info) -> Optional[str]:
        # At least one answer field should be provided
        values = info.data
        if not v and not values.get("selected_option") and not values.get("answer_text"):
            raise ValueError("Either answer_text or selected_option must be provided")
        return v


class QuizSubmission(BaseSchema):
    """Schema for submitting a complete quiz."""
    
    answers: list[AnswerSubmission] = Field(..., min_length=1, description="List of answers")
    time_taken_minutes: Optional[int] = Field(None, ge=0, description="Total time taken")


class AnswerEvaluation(BaseSchema):
    """Schema for individual answer evaluation."""
    
    question_id: int
    is_correct: Optional[bool]
    points_earned: float
    max_points: float
    ai_feedback: Optional[str] = None
    confidence_score: Optional[float] = None


class SubmissionEvaluation(BaseSchema):
    """Schema for submission evaluation response."""
    
    submission_id: int
    quiz_id: int
    total_score: float
    max_possible_score: float
    percentage: float
    correct_answers: int
    total_questions: int
    performance_level: str
    
    # Per-question breakdown
    answers: list[AnswerEvaluation]
    
    # Performance by type/difficulty
    mcq_score: Optional[float] = None
    tf_score: Optional[float] = None
    short_answer_score: Optional[float] = None
    easy_score: Optional[float] = None
    medium_score: Optional[float] = None
    hard_score: Optional[float] = None
    
    # Topic performance
    topic_scores: Optional[dict[str, float]] = None
    
    # AI-generated feedback
    suggestions: list[str] = Field(..., min_length=1, max_length=10, description="1-10 improvement suggestions")
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    overall_feedback: Optional[str] = None
    
    # Timing
    time_taken_minutes: Optional[int] = None
    submitted_at: datetime


class SubmissionSummary(BaseSchema):
    """Schema for submission summary in history."""
    
    id: int
    quiz_id: int
    quiz_title: str
    subject: str
    grade_level: str
    total_score: Optional[float]
    max_possible_score: Optional[float]
    percentage: Optional[float]
    is_completed: bool
    submitted_at: Optional[datetime]
    created_at: datetime
