"""History and filtering endpoints."""

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import DBSession, AuthUser
from app.models.submission import Submission
from app.models.quiz import Quiz
from app.schemas.auth import CurrentUser
from app.schemas.history import HistoryResponse
from app.schemas.submission import SubmissionSummary
from app.services.datetime import parse_date_range
from typing import Optional

router = APIRouter()
logger = structlog.get_logger()


@router.get("", response_model=HistoryResponse)
async def get_quiz_history(
    current_user: AuthUser,
    db: DBSession,
    grade: Optional[str] = Query(None, description="Filter by grade level"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    min_marks: Optional[float] = Query(None, ge=0, le=100, description="Minimum percentage"),
    max_marks: Optional[float] = Query(None, ge=0, le=100, description="Maximum percentage"),
    from_date: Optional[str] = Query(None, description="Start date (ISO or DD/MM/YYYY)"),
    to_date: Optional[str] = Query(None, description="End date (ISO or DD/MM/YYYY)"),
    completed_date: Optional[str] = Query(None, description="Specific completion date"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> HistoryResponse:
    """Get user's quiz submission history with filtering."""
    
    # Build base query
    query = select(Submission).options(
        selectinload(Submission.quiz)
    ).where(
        Submission.user_id == current_user.id
    )
    
    # Count query for total
    count_query = select(func.count(Submission.id)).where(
        Submission.user_id == current_user.id
    )
    
    filters_applied = {}
    
    # Apply filters
    if grade:
        query = query.where(Submission.quiz.has(Quiz.grade_level == grade))
        count_query = count_query.join(Quiz).where(Quiz.grade_level == grade)
        filters_applied["grade"] = grade
    
    if subject:
        query = query.where(Submission.quiz.has(Quiz.subject == subject))
        if "grade" not in filters_applied:  # Avoid double join
            count_query = count_query.join(Quiz)
        count_query = count_query.where(Quiz.subject == subject)
        filters_applied["subject"] = subject
    
    if min_marks is not None:
        query = query.where(Submission.percentage >= min_marks)
        count_query = count_query.where(Submission.percentage >= min_marks)
        filters_applied["min_marks"] = str(min_marks)
    
    if max_marks is not None:
        query = query.where(Submission.percentage <= max_marks)
        count_query = count_query.where(Submission.percentage <= max_marks)
        filters_applied["max_marks"] = str(max_marks)
    
    # Date filtering
    if from_date:
        try:
            start_date, _ = parse_date_range(from_date)
            query = query.where(Submission.submitted_at >= start_date)
            count_query = count_query.where(Submission.submitted_at >= start_date)
            filters_applied["from_date"] = from_date
        except ValueError as e:
            logger.error("Invalid from_date format", error=str(e))
            # Continue without this filter
    
    if to_date:
        try:
            _, end_date = parse_date_range(to_date)
            query = query.where(Submission.submitted_at <= end_date)
            count_query = count_query.where(Submission.submitted_at <= end_date)
            filters_applied["to_date"] = to_date
        except ValueError as e:
            logger.error("Invalid to_date format", error=str(e))
            # Continue without this filter
    
    if completed_date:
        try:
            start_date, end_date = parse_date_range(completed_date)
            query = query.where(
                and_(
                    Submission.submitted_at >= start_date,
                    Submission.submitted_at <= end_date
                )
            )
            count_query = count_query.where(
                and_(
                    Submission.submitted_at >= start_date,
                    Submission.submitted_at <= end_date
                )
            )
            filters_applied["completed_date"] = completed_date
        except ValueError as e:
            logger.error("Invalid completed_date format", error=str(e))
            # Continue without this filter
    
    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # Apply ordering, pagination
    query = query.order_by(Submission.submitted_at.desc())
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    submissions = result.scalars().all()
    
    # Convert to response format
    submission_summaries = []
    for submission in submissions:
        summary = SubmissionSummary(
            id=submission.id,
            quiz_id=submission.quiz_id,
            quiz_title=submission.quiz.title,
            subject=submission.quiz.subject,
            grade_level=submission.quiz.grade_level,
            total_score=submission.total_score,
            max_possible_score=submission.max_possible_score,
            percentage=submission.percentage,
            is_completed=submission.is_completed,
            submitted_at=submission.submitted_at,
            created_at=submission.created_at,
        )
        submission_summaries.append(summary)
    
    # Calculate pagination
    has_next = offset + limit < total
    has_prev = offset > 0
    
    logger.info(
        "History retrieved", 
        user_id=current_user.id, 
        total=total, 
        limit=limit, 
        offset=offset,
        filters=filters_applied
    )
    
    return HistoryResponse(
        submissions=submission_summaries,
        total=total,
        limit=limit,
        offset=offset,
        has_next=has_next,
        has_prev=has_prev,
        filters_applied=filters_applied,
    )
