"""Evaluation model."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Index, Integer, Float, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.submission import Submission


class Evaluation(Base):
    """Evaluation model for submission analysis and feedback."""
    
    # Relationships
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), nullable=False)
    submission: Mapped["Submission"] = relationship(back_populates="evaluation")
    
    # Overall scores
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    max_possible_score: Mapped[float] = mapped_column(Float, nullable=False)
    percentage: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Performance breakdown
    correct_answers: Mapped[int] = mapped_column(Integer, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Question type performance
    mcq_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tf_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    short_answer_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    essay_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Difficulty performance
    easy_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    medium_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hard_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Topic performance (JSON dict: {topic: score})
    topic_scores: Mapped[Optional[dict[str, float]]] = mapped_column(JSON, nullable=True)
    
    # AI-generated insights
    strengths: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    suggestions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    
    # Additional feedback
    overall_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    improvement_areas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Performance level
    performance_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # excellent, good, fair, poor
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_evaluation_submission", "submission_id"),
        Index("idx_evaluation_percentage", "percentage"),
        Index("idx_evaluation_performance_level", "performance_level"),
    )
    
    def __repr__(self) -> str:
        return f"<Evaluation(id={self.id}, submission_id={self.submission_id}, percentage={self.percentage})>"
