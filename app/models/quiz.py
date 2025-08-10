"""Quiz model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.question import Question
    from app.models.submission import Submission
    from app.models.retry import Retry


class Quiz(Base):
    """Quiz model containing metadata and configuration."""
    
    __tablename__ = "quizzes"
    
    # Basic information
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    grade_level: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Configuration
    num_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)  # easy, medium, hard, adaptive
    adaptive: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Content specification
    topics: Mapped[list[str]] = mapped_column(JSON, nullable=False)  # List of topic strings
    question_types: Mapped[list[str]] = mapped_column(JSON, nullable=False)  # MCQ, TF, short_answer, etc.
    standard: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_limit_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    creator: Mapped["User"] = relationship(back_populates="quizzes")
    
    questions: Mapped[list["Question"]] = relationship(
        back_populates="quiz", 
        cascade="all, delete-orphan",
        order_by="Question.order"
    )
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="quiz", 
        cascade="all, delete-orphan"
    )
    retries: Mapped[list["Retry"]] = relationship(
        "Retry",
        foreign_keys="Retry.original_quiz_id",
        back_populates="original_quiz", 
        cascade="all, delete-orphan"
    )
    
    # Status tracking
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_quiz_subject_grade", "subject", "grade_level"),
        Index("idx_quiz_creator_created", "creator_id", "created_at"),
        Index("idx_quiz_difficulty", "difficulty"),
        Index("idx_quiz_published", "is_published"),
    )
    
    def __repr__(self) -> str:
        return f"<Quiz(id={self.id}, title='{self.title}', subject='{self.subject}')>"
