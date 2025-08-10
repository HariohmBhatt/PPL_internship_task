"""Retry model for quiz retakes."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.quiz import Quiz


class Retry(Base):
    """Retry model for tracking quiz retakes."""
    
    __tablename__ = "retries"
    
    # Relationships
    original_quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"), nullable=False)
    retried_quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"), nullable=False)
    
    original_quiz: Mapped["Quiz"] = relationship(
        foreign_keys=[original_quiz_id],
        back_populates="retries"
    )
    retried_quiz: Mapped["Quiz"] = relationship(
        foreign_keys=[retried_quiz_id]
    )
    
    # Retry metadata
    retry_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3, etc.
    reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # Optional reason for retry
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_retry_original_quiz", "original_quiz_id"),
        Index("idx_retry_retried_quiz", "retried_quiz_id"),
        Index("idx_retry_number", "retry_number"),
    )
    
    def __repr__(self) -> str:
        return f"<Retry(id={self.id}, original_quiz_id={self.original_quiz_id}, retry_number={self.retry_number})>"
