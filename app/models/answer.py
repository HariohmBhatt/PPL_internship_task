"""Answer model."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.submission import Submission
    from app.models.question import Question


class Answer(Base):
    """Answer model for user responses to questions."""
    
    # Relationships
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    
    submission: Mapped["Submission"] = relationship(back_populates="answers")
    question: Mapped["Question"] = relationship(back_populates="answers")
    
    # Answer content
    answer_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # User's answer
    selected_option: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # For MCQ/TF
    
    # Scoring
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    points_earned: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_points: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # AI evaluation (for subjective questions)
    ai_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # AI confidence
    
    # Hint tracking
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    hint_penalty: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    
    # Timing
    time_spent_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_answer_submission_question", "submission_id", "question_id"),
        Index("idx_answer_question", "question_id"),
        Index("idx_answer_is_correct", "is_correct"),
    )
    
    def __repr__(self) -> str:
        return f"<Answer(id={self.id}, submission_id={self.submission_id}, question_id={self.question_id})>"
