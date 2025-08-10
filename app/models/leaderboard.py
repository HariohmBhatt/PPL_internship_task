"""Leaderboard data models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, text
from sqlalchemy.ext.hybrid import hybrid_property

from app.models.base import Base


class LeaderboardEntry(Base):
    """Model for leaderboard entries.
    
    This is a view-like model that aggregates user performance data.
    """
    
    __tablename__ = "leaderboard_entries"
    
    # User information
    user_id = Column(Integer, nullable=False, index=True)
    username = Column(String(100), nullable=False)
    
    # Quiz metadata
    subject = Column(String(100), nullable=False, index=True)
    grade_level = Column(String(10), nullable=False, index=True)
    
    # Performance metrics
    best_score = Column(Float, nullable=False, default=0.0)
    best_percentage = Column(Float, nullable=False, default=0.0)
    total_quizzes = Column(Integer, nullable=False, default=0)
    average_score = Column(Float, nullable=False, default=0.0)
    total_questions_answered = Column(Integer, nullable=False, default=0)
    total_correct_answers = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    first_quiz_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_quiz_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_updated = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    
    @hybrid_property
    def accuracy_percentage(self) -> float:
        """Calculate accuracy percentage."""
        if self.total_questions_answered == 0:
            return 0.0
        return (self.total_correct_answers / self.total_questions_answered) * 100
    
    @hybrid_property
    def activity_score(self) -> float:
        """Calculate activity score based on total quizzes and recency."""
        # Base score from quiz count
        base_score = min(self.total_quizzes * 10, 100)
        
        # Recency bonus (more recent activity gets higher score)
        days_since_last = (datetime.utcnow() - self.last_quiz_date).days
        recency_multiplier = max(0.5, 1.0 - (days_since_last / 30))  # Decay over 30 days
        
        return base_score * recency_multiplier
    
    def __repr__(self) -> str:
        return (
            f"<LeaderboardEntry(user_id={self.user_id}, "
            f"subject='{self.subject}', grade='{self.grade_level}', "
            f"best_percentage={self.best_percentage:.1f}%)>"
        )
