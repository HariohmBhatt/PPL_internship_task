"""Hint endpoints for quiz questions."""

from collections import defaultdict
from typing import Dict

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import DBSession, AuthUser
from app.core.errors import NotFoundError, RateLimitError
from app.core.config import get_settings
from app.models.question import Question
from app.models.answer import Answer
from app.schemas.auth import CurrentUser
from app.schemas.question import HintRequest, HintResponse
from app.services.ai.provider import get_ai_provider

router = APIRouter()
logger = structlog.get_logger()

# In-memory rate limiting (in production, use Redis or database)
hint_usage: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))


@router.post("/{quiz_id}/questions/{question_id}/hint", response_model=HintResponse)
async def get_hint(
    quiz_id: int,
    question_id: int,
    hint_request: HintRequest,
    current_user: AuthUser,
    db: DBSession,
) -> HintResponse:
    """Get an AI-generated hint for a specific question."""
    
    settings = get_settings()
    
    # Check rate limit
    user_key = f"{current_user.id}"
    current_usage = hint_usage[user_key][question_id]
    
    if current_usage >= settings.hint_rate_limit_per_user_question:
        raise RateLimitError(
            f"Hint limit exceeded for this question. Maximum {settings.hint_rate_limit_per_user_question} hints allowed."
        )
    
    # Get question
    query = select(Question).where(
        Question.id == question_id,
        Question.quiz_id == quiz_id
    )
    result = await db.execute(query)
    question = result.scalar_one_or_none()
    
    if not question:
        raise NotFoundError("Question not found")
    
    # Generate hint using AI
    ai_provider = get_ai_provider()
    
    try:
        hint_text = await ai_provider.hint(
            question=question.question_text,
            question_type=question.question_type,
            difficulty=question.difficulty,
            topic=question.topic,
        )
        
        # Update rate limit counter
        hint_usage[user_key][question_id] += 1
        hints_used = hint_usage[user_key][question_id]
        remaining_hints = settings.hint_rate_limit_per_user_question - hints_used
        
        # Update hint usage in any existing answer
        answer_query = select(Answer).where(
            Answer.question_id == question_id,
            Answer.submission_id.in_(
                # Get submissions for this user and quiz
                select(Answer.submission_id)
                .join(Answer.submission)
                .where(Answer.submission.has(user_id=current_user.id))
            )
        )
        answer_result = await db.execute(answer_query)
        existing_answer = answer_result.scalar_one_or_none()
        
        if existing_answer:
            existing_answer.hints_used = hints_used
            await db.commit()
        
        logger.info(
            "Hint provided", 
            user_id=current_user.id, 
            question_id=question_id,
            hints_used=hints_used
        )
        
        return HintResponse(
            hint=hint_text,
            hints_used=hints_used,
            remaining_hints=remaining_hints,
        )
    
    except Exception as e:
        logger.error("Failed to generate hint", error=str(e), question_id=question_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate hint"
        )


@router.delete("/{quiz_id}/questions/{question_id}/hint-usage")
async def reset_hint_usage(
    quiz_id: int,
    question_id: int,
    current_user: AuthUser,
    db: DBSession,
) -> dict[str, str]:
    """Reset hint usage for a question (admin/testing function)."""
    
    settings = get_settings()
    
    # Only allow in development mode
    if not settings.is_development:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development mode"
        )
    
    user_key = f"{current_user.id}"
    if question_id in hint_usage[user_key]:
        del hint_usage[user_key][question_id]
    
    logger.info("Hint usage reset", user_id=current_user.id, question_id=question_id)
    
    return {"message": "Hint usage reset successfully"}
