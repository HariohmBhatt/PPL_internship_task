"""Question model."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Index, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.quiz import Quiz
    from app.models.answer import Answer


class Question(Base):
    """Question model for quiz questions."""
    
    # Question content
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)  # MCQ, TF, short_answer, essay
    
    # Question metadata
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)  # easy, medium, hard
    topic: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)  # Order within quiz
    
    # Points and scoring
    points: Mapped[int] = mapped_column(Integer, default=1)
    
    # MCQ/TF specific fields
    options: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)  # For MCQ
    correct_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Correct answer
    
    # Additional context
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hint_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"), nullable=False)
    quiz: Mapped["Quiz"] = relationship(back_populates="questions")
    
    answers: Mapped[list["Answer"]] = relationship(
        back_populates="question", 
        cascade="all, delete-orphan"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_question_quiz_order", "quiz_id", "order"),
        Index("idx_question_type", "question_type"),
        Index("idx_question_difficulty", "difficulty"),
        Index("idx_question_topic", "topic"),
    )
    
    def __repr__(self) -> str:
        return f"<Question(id={self.id}, quiz_id={self.quiz_id}, type='{self.question_type}')>"
