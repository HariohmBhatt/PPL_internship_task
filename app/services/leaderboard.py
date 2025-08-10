"""Leaderboard service for managing quiz rankings."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import structlog
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.leaderboard import LeaderboardEntry
from app.models.quiz import Quiz
from app.models.submission import Submission
from app.models.evaluation import Evaluation
from app.models.user import User
from app.schemas.leaderboard import (
    LeaderboardEntryResponse,
    LeaderboardQuery,
    LeaderboardResponse,
    UserRankResponse,
)
from app.services.cache import CacheService

logger = structlog.get_logger()


class LeaderboardService:
    """Service for managing quiz leaderboards."""
    
    def __init__(self, cache: CacheService):
        self.cache = cache
    
    async def get_leaderboard(
        self,
        db: AsyncSession,
        query: LeaderboardQuery
    ) -> LeaderboardResponse:
        """Get leaderboard for subject and grade."""
        
        # Try to get from cache first
        cache_key = self.cache.get_leaderboard_cache_key(query.subject, query.grade_level)
        cached_data = await self.cache.get(cache_key)
        
        if cached_data:
            logger.info("Leaderboard served from cache", subject=query.subject, grade=query.grade_level)
            return LeaderboardResponse(**cached_data)
        
        # Generate leaderboard from database
        logger.info("Generating fresh leaderboard", subject=query.subject, grade=query.grade_level)
        
        # Get aggregated user performance data
        leaderboard_data = await self._generate_leaderboard_data(db, query)
        
        # Rank the entries
        ranked_entries = self._rank_entries(leaderboard_data, query.ranking_type, query.limit)
        
        # Create response
        response = LeaderboardResponse(
            subject=query.subject,
            grade_level=query.grade_level,
            total_users=len(leaderboard_data),
            entries=ranked_entries,
            generated_at=datetime.utcnow(),
            cache_ttl_seconds=3600
        )
        
        # Cache the result
        await self.cache.set(cache_key, response.model_dump(), ttl=3600)
        
        return response
    
    async def get_user_rank(
        self,
        db: AsyncSession,
        user_id: int,
        subject: str,
        grade_level: str
    ) -> Optional[UserRankResponse]:
        """Get specific user's ranking in leaderboard."""
        
        # Get full leaderboard
        query = LeaderboardQuery(
            subject=subject,
            grade_level=grade_level,
            limit=100,  # Respect schema limit and fetch enough entries for ranking
            ranking_type="best_percentage"
        )
        
        leaderboard = await self.get_leaderboard(db, query)
        
        # Find user in leaderboard
        user_entry = None
        user_rank = None
        
        for i, entry in enumerate(leaderboard.entries):
            if entry.user_id == user_id:
                user_entry = entry
                user_rank = entry.rank
                break
        
        if not user_entry:
            return None
        
        # Calculate percentile
        percentile = None
        if leaderboard.total_users > 0:
            percentile = ((leaderboard.total_users - user_rank + 1) / leaderboard.total_users) * 100
        
        # Calculate gap to leader
        score_gap_to_leader = None
        if leaderboard.entries and user_rank > 1:
            leader_score = leaderboard.entries[0].best_percentage
            score_gap_to_leader = leader_score - user_entry.best_percentage
        
        return UserRankResponse(
            user_id=user_id,
            username=user_entry.username,
            current_rank=user_rank,
            total_participants=leaderboard.total_users,
            percentile=percentile,
            best_percentage=user_entry.best_percentage,
            average_score=user_entry.average_score,
            total_quizzes=user_entry.total_quizzes,
            score_gap_to_leader=score_gap_to_leader,
            rank_change_trend="stable"  # Could be enhanced with historical data
        )
    
    async def update_leaderboard_entry(
        self,
        db: AsyncSession,
        user_id: int,
        quiz_id: int,
        submission_data: Dict
    ) -> None:
        """Update leaderboard entry after quiz submission."""
        
        try:
            # Get quiz and user information
            quiz_stmt = select(Quiz).where(Quiz.id == quiz_id)
            quiz_result = await db.execute(quiz_stmt)
            quiz = quiz_result.scalar_one_or_none()
            
            user_stmt = select(User).where(User.id == user_id)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not quiz or not user:
                logger.warning("Quiz or user not found for leaderboard update", quiz_id=quiz_id, user_id=user_id)
                return
            
            # Check if leaderboard entry exists
            entry_stmt = select(LeaderboardEntry).where(
                and_(
                    LeaderboardEntry.user_id == user_id,
                    LeaderboardEntry.subject == quiz.subject,
                    LeaderboardEntry.grade_level == quiz.grade_level
                )
            )
            entry_result = await db.execute(entry_stmt)
            entry = entry_result.scalar_one_or_none()
            
            # Calculate new metrics
            score = submission_data.get("total_score", 0)
            percentage = submission_data.get("percentage", 0.0)
            correct_answers = submission_data.get("correct_answers", 0)
            total_questions = submission_data.get("total_questions", 1)
            
            if entry:
                # Update existing entry
                entry.total_quizzes += 1
                entry.total_questions_answered += total_questions
                entry.total_correct_answers += correct_answers
                entry.last_quiz_date = datetime.utcnow()
                
                # Update best scores if this is better
                if percentage > entry.best_percentage:
                    entry.best_percentage = percentage
                    entry.best_score = score
                
                # Recalculate average score
                entry.average_score = (entry.average_score * (entry.total_quizzes - 1) + score) / entry.total_quizzes
                
            else:
                # Create new entry
                entry = LeaderboardEntry(
                    user_id=user_id,
                    username=user.username,
                    subject=quiz.subject,
                    grade_level=quiz.grade_level,
                    best_score=score,
                    best_percentage=percentage,
                    total_quizzes=1,
                    average_score=score,
                    total_questions_answered=total_questions,
                    total_correct_answers=correct_answers,
                    first_quiz_date=datetime.utcnow(),
                    last_quiz_date=datetime.utcnow()
                )
                db.add(entry)
            
            await db.commit()
            
            # Invalidate cache for this subject/grade combination
            cache_key = self.cache.get_leaderboard_cache_key(quiz.subject, quiz.grade_level)
            await self.cache.delete(cache_key)
            
            logger.info(
                "Leaderboard entry updated",
                user_id=user_id,
                subject=quiz.subject,
                grade=quiz.grade_level,
                new_score=percentage
            )
            
        except Exception as e:
            logger.error("Failed to update leaderboard entry", error=str(e), user_id=user_id, quiz_id=quiz_id)
            await db.rollback()
    
    async def _generate_leaderboard_data(
        self,
        db: AsyncSession,
        query: LeaderboardQuery
    ) -> List[Dict]:
        """Generate leaderboard data from database."""
        
        # Query to get user performance aggregated data
        stmt = (
            select(
                User.id.label("user_id"),
                User.username,
                func.max(Submission.percentage).label("best_percentage"),
                func.max(Submission.total_score).label("best_score"),
                func.avg(Submission.total_score).label("average_score"),
                func.count(Submission.id).label("total_quizzes"),
                func.sum(Evaluation.total_questions).label("total_questions_answered"),
                func.sum(Evaluation.correct_answers).label("total_correct_answers"),
                func.min(Submission.submitted_at).label("first_quiz_date"),
                func.max(Submission.submitted_at).label("last_quiz_date"),
            )
            .select_from(
                User.__table__
                .join(Submission.__table__, User.id == Submission.user_id)
                .join(Evaluation.__table__, Evaluation.submission_id == Submission.id)
                .join(Quiz.__table__, Submission.quiz_id == Quiz.id)
            )
            .where(
                and_(
                    Quiz.subject == query.subject,
                    Quiz.grade_level == query.grade_level,
                    Submission.is_completed == True
                )
            )
            .group_by(User.id, User.username)
        )
        
        result = await db.execute(stmt)
        rows = result.fetchall()
        
        leaderboard_data = []
        now_utc = datetime.now(timezone.utc)

        def _as_aware(dt: datetime) -> datetime:
            if dt is None:
                return now_utc
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        for row in rows:
            # Calculate derived metrics
            accuracy_percentage = 0.0
            if row.total_questions_answered > 0:
                accuracy_percentage = (row.total_correct_answers / row.total_questions_answered) * 100
            
            # Calculate activity score
            days_since_last = (now_utc - _as_aware(row.last_quiz_date)).days if row.last_quiz_date else 0
            base_score = min(row.total_quizzes * 10, 100)
            recency_multiplier = max(0.5, 1.0 - (days_since_last / 30))
            activity_score = base_score * recency_multiplier
            
            leaderboard_data.append({
                "user_id": row.user_id,
                "username": row.username,
                "best_score": float(row.best_score or 0),
                "best_percentage": float(row.best_percentage or 0),
                "average_score": float(row.average_score or 0),
                "total_quizzes": row.total_quizzes or 0,
                "total_questions_answered": row.total_questions_answered or 0,
                "total_correct_answers": row.total_correct_answers or 0,
                "accuracy_percentage": accuracy_percentage,
                "activity_score": activity_score,
                "first_quiz_date": _as_aware(row.first_quiz_date) if row.first_quiz_date else now_utc,
                "last_quiz_date": _as_aware(row.last_quiz_date) if row.last_quiz_date else now_utc,
            })
        
        return leaderboard_data
    
    def _rank_entries(
        self,
        data: List[Dict],
        ranking_type: str,
        limit: int
    ) -> List[LeaderboardEntryResponse]:
        """Rank and format leaderboard entries."""
        
        # Sort by ranking criteria
        if ranking_type == "best_percentage":
            data.sort(key=lambda x: x["best_percentage"], reverse=True)
        elif ranking_type == "average_score":
            data.sort(key=lambda x: x["average_score"], reverse=True)
        elif ranking_type == "activity_score":
            data.sort(key=lambda x: x["activity_score"], reverse=True)
        elif ranking_type == "total_quizzes":
            data.sort(key=lambda x: x["total_quizzes"], reverse=True)
        else:
            # Default to best percentage
            data.sort(key=lambda x: x["best_percentage"], reverse=True)
        
        # Take top entries and add rank
        ranked_entries = []
        for i, entry_data in enumerate(data[:limit]):
            entry_data["rank"] = i + 1
            ranked_entries.append(LeaderboardEntryResponse(**entry_data))
        
        return ranked_entries
    
    async def invalidate_leaderboard_cache(
        self,
        subject: str,
        grade_level: str
    ) -> None:
        """Invalidate leaderboard cache for specific subject/grade."""
        cache_key = self.cache.get_leaderboard_cache_key(subject, grade_level)
        await self.cache.delete(cache_key)
        
        logger.info("Leaderboard cache invalidated", subject=subject, grade=grade_level)


def get_leaderboard_service(cache: CacheService) -> LeaderboardService:
    """Get leaderboard service instance."""
    return LeaderboardService(cache)
