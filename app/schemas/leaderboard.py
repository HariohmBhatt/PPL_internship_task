"""Leaderboard Pydantic schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class LeaderboardEntryResponse(BaseModel):
    """Response schema for leaderboard entry."""
    
    model_config = ConfigDict(from_attributes=True)
    
    # Ranking information
    rank: int = Field(..., description="Current rank position")
    
    # User information
    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    
    # Performance metrics
    best_score: float = Field(..., description="Best quiz score achieved")
    best_percentage: float = Field(..., description="Best percentage score")
    average_score: float = Field(..., description="Average score across all quizzes")
    total_quizzes: int = Field(..., description="Total number of quizzes taken")
    total_questions_answered: int = Field(..., description="Total questions answered")
    total_correct_answers: int = Field(..., description="Total correct answers")
    accuracy_percentage: float = Field(..., description="Overall accuracy percentage")
    
    # Activity metrics
    activity_score: float = Field(..., description="Activity score based on engagement")
    first_quiz_date: datetime = Field(..., description="Date of first quiz")
    last_quiz_date: datetime = Field(..., description="Date of most recent quiz")


class LeaderboardResponse(BaseModel):
    """Response schema for leaderboard data."""
    
    subject: str = Field(..., description="Subject filter")
    grade_level: str = Field(..., description="Grade level filter")
    total_users: int = Field(..., description="Total number of users in leaderboard")
    entries: List[LeaderboardEntryResponse] = Field(..., description="Leaderboard entries")
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When leaderboard was generated")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")


class LeaderboardQuery(BaseModel):
    """Query parameters for leaderboard requests."""
    
    subject: str = Field(..., description="Subject to filter by", examples=["Mathematics", "Science"])
    grade_level: str = Field(..., description="Grade level to filter by", examples=["8", "9", "10"])
    limit: int = Field(default=10, ge=1, le=100, description="Number of top entries to return")
    ranking_type: str = Field(
        default="best_percentage", 
        description="Ranking criteria",
        pattern="^(best_percentage|average_score|activity_score|total_quizzes)$"
    )


class UserRankResponse(BaseModel):
    """Response schema for individual user ranking."""
    
    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    current_rank: Optional[int] = Field(None, description="Current rank in leaderboard")
    total_participants: int = Field(..., description="Total number of participants")
    percentile: Optional[float] = Field(None, description="Percentile ranking (0-100)")
    
    # Performance metrics
    best_percentage: float = Field(..., description="Best percentage score")
    average_score: float = Field(..., description="Average score")
    total_quizzes: int = Field(..., description="Total quizzes taken")
    
    # Comparison to leaders
    score_gap_to_leader: Optional[float] = Field(None, description="Gap to #1 position")
    rank_change_trend: Optional[str] = Field(None, description="Recent rank trend", examples=["improving", "declining", "stable"])
