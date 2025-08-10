"""Submission model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.quiz import Quiz
    from app.models.answer import Answer
    from app.models.evaluation import Evaluation


class Submission(Base):
    """Submission model for quiz attempts."""
    
    # Relationships
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"), nullable=False)
    
    user: Mapped["User"] = relationship(back_populates="submissions")
    quiz: Mapped["Quiz"] = relationship(back_populates="submissions")
    
    # Submission status
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Scoring
    total_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_possible_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Time tracking
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False,
        default=lambda: datetime.now()
    )
    time_taken_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    answers: Mapped[list["Answer"]] = relationship(
        back_populates="submission", 
        cascade="all, delete-orphan"
    )
    evaluation: Mapped[Optional["Evaluation"]] = relationship(
        back_populates="submission", 
        cascade="all, delete-orphan",
        uselist=False
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_submission_user_quiz", "user_id", "quiz_id"),
        Index("idx_submission_completed", "is_completed"),
        Index("idx_submission_submitted_at", "submitted_at"),
        Index("idx_submission_user_submitted", "user_id", "submitted_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Submission(id={self.id}, user_id={self.user_id}, quiz_id={self.quiz_id})>"
