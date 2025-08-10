"""Leaderboard API endpoints."""

from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import DBSession, AuthUser
from app.schemas.leaderboard import (
    LeaderboardQuery,
    LeaderboardResponse,
    UserRankResponse,
)
from app.services.cache import get_cache, CacheService
from app.services.leaderboard import get_leaderboard_service, LeaderboardService

logger = structlog.get_logger()

router = APIRouter()


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    current_user: AuthUser,
    db: DBSession,
    subject: str = Query(..., description="Subject to filter by", examples=["Mathematics", "Science"]),
    grade_level: str = Query(..., description="Grade level to filter by", examples=["8", "9", "10"]),
    limit: int = Query(default=10, ge=1, le=100, description="Number of top entries to return"),
    ranking_type: str = Query(
        default="best_percentage",
        description="Ranking criteria",
        regex="^(best_percentage|average_score|activity_score|total_quizzes)$"
    ),
    cache: CacheService = Depends(get_cache),
) -> LeaderboardResponse:
    """
    Get leaderboard for specific subject and grade level.
    
    Returns top performers based on various ranking criteria:
    - **best_percentage**: Highest quiz percentage score
    - **average_score**: Average score across all quizzes  
    - **activity_score**: Score based on quiz count and recency
    - **total_quizzes**: Most quizzes completed
    
    Results are cached for improved performance.
    """
    try:
        leaderboard_service = get_leaderboard_service(cache)
        
        query = LeaderboardQuery(
            subject=subject,
            grade_level=grade_level,
            limit=limit,
            ranking_type=ranking_type
        )
        
        logger.info(
            "Fetching leaderboard",
            subject=subject,
            grade_level=grade_level,
            ranking_type=ranking_type,
            limit=limit,
            user_id=current_user.id
        )
        
        leaderboard = await leaderboard_service.get_leaderboard(db, query)
        
        logger.info(
            "Leaderboard fetched successfully",
            subject=subject,
            grade_level=grade_level,
            total_users=leaderboard.total_users,
            entries_returned=len(leaderboard.entries)
        )
        
        return leaderboard
        
    except Exception as e:
        logger.error(
            "Failed to fetch leaderboard",
            error=str(e),
            subject=subject,
            grade_level=grade_level,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch leaderboard data"
        )


@router.get("/leaderboard/my-rank", response_model=UserRankResponse)
async def get_my_rank(
    current_user: AuthUser,
    db: DBSession,
    subject: str = Query(..., description="Subject to check rank for"),
    grade_level: str = Query(..., description="Grade level to check rank for"),
    cache: CacheService = Depends(get_cache),
) -> UserRankResponse:
    """
    Get current user's ranking in the leaderboard.
    
    Returns detailed ranking information including:
    - Current rank position
    - Percentile ranking
    - Performance metrics
    - Gap to leader
    """
    try:
        leaderboard_service = get_leaderboard_service(cache)
        
        logger.info(
            "Fetching user rank",
            user_id=current_user.id,
            subject=subject,
            grade_level=grade_level
        )
        
        user_rank = await leaderboard_service.get_user_rank(
            db, current_user.id, subject, grade_level
        )
        
        if not user_rank:
            raise HTTPException(
                status_code=404,
                detail="No ranking data found for this user in the specified subject and grade"
            )
        
        logger.info(
            "User rank fetched successfully",
            user_id=current_user.id,
            subject=subject,
            grade_level=grade_level,
            rank=user_rank.current_rank
        )
        
        return user_rank
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to fetch user rank",
            error=str(e),
            user_id=current_user.id,
            subject=subject,
            grade_level=grade_level
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch user ranking data"
        )


@router.get("/leaderboard/subjects", response_model=list[str])
async def get_available_subjects(
    current_user: AuthUser,
    db: DBSession,
) -> list[str]:
    """
    Get list of available subjects in the leaderboard.
    
    Returns subjects that have quiz data available.
    """
    try:
        from sqlalchemy import select, distinct
        from app.models.quiz import Quiz
        
        stmt = select(distinct(Quiz.subject)).where(Quiz.subject.isnot(None))
        result = await db.execute(stmt)
        subjects = [row[0] for row in result.fetchall()]
        
        logger.info(
            "Available subjects fetched",
            subjects=subjects,
            count=len(subjects)
        )
        
        return sorted(subjects)
        
    except Exception as e:
        logger.error("Failed to fetch available subjects", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch available subjects"
        )


@router.get("/leaderboard/grades", response_model=list[str])
async def get_available_grades(
    current_user: AuthUser,
    db: DBSession,
    subject: Optional[str] = Query(None, description="Filter grades by subject"),
) -> list[str]:
    """
    Get list of available grade levels in the leaderboard.
    
    Optionally filter by subject.
    """
    try:
        from sqlalchemy import select, distinct
        from app.models.quiz import Quiz
        
        stmt = select(distinct(Quiz.grade_level)).where(Quiz.grade_level.isnot(None))
        
        if subject:
            stmt = stmt.where(Quiz.subject == subject)
        
        result = await db.execute(stmt)
        grades = [row[0] for row in result.fetchall()]
        
        logger.info(
            "Available grades fetched",
            subject=subject,
            grades=grades,
            count=len(grades)
        )
        
        return sorted(grades)
        
    except Exception as e:
        logger.error("Failed to fetch available grades", error=str(e), subject=subject)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch available grades"
        )
