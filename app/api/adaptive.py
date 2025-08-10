"""Adaptive quiz endpoints."""

import structlog
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import DBSession, AuthUser
from app.core.errors import NotFoundError, ValidationError
from app.models.quiz import Quiz
from app.models.submission import Submission
from app.schemas.auth import CurrentUser
from app.schemas.question import NextQuestionRequest, NextQuestionResponse, QuestionResponse
from app.services.adaptive import AdaptiveService

router = APIRouter()
logger = structlog.get_logger()


@router.post("/{quiz_id}/next", response_model=NextQuestionResponse)
async def get_next_question(
    quiz_id: int,
    request: NextQuestionRequest,
    current_user: AuthUser,
    db: DBSession,
) -> NextQuestionResponse:
    """Get the next question based on adaptive difficulty policy."""
    
    # Get quiz and verify it exists and is adaptive
    quiz_query = select(Quiz).options(
        selectinload(Quiz.questions)
    ).where(Quiz.id == quiz_id)
    quiz_result = await db.execute(quiz_query)
    quiz = quiz_result.scalar_one_or_none()
    
    if not quiz:
        raise NotFoundError("Quiz not found")
    
    if not quiz.adaptive:
        raise ValidationError("This quiz is not configured for adaptive mode")
    
    # Get or create active submission for this user
    submission_query = select(Submission).where(
        Submission.user_id == current_user.id,
        Submission.quiz_id == quiz_id,
        Submission.is_completed == False
    ).order_by(Submission.created_at.desc())
    
    submission_result = await db.execute(submission_query)
    submission = submission_result.scalar_one_or_none()
    
    if not submission:
        # Create new submission for adaptive quiz
        submission = Submission(
            user_id=current_user.id,
            quiz_id=quiz_id,
            is_completed=False,
        )
        db.add(submission)
        await db.flush()
        
        logger.info("Created new adaptive submission", submission_id=submission.id, quiz_id=quiz_id)
    
    # Use adaptive service to get next question
    adaptive_service = AdaptiveService()
    next_question_data = await adaptive_service.get_next_question(
        session=db,
        submission=submission,
        quiz_questions=list(quiz.questions)
    )
    
    # Convert question to response format if available
    question_response = None
    if next_question_data["question"]:
        question_response = QuestionResponse.model_validate(next_question_data["question"])
    
    logger.info(
        "Next question determined",
        user_id=current_user.id,
        quiz_id=quiz_id,
        submission_id=submission.id,
        is_complete=next_question_data["is_complete"],
        question_id=next_question_data["question"].id if next_question_data["question"] else None
    )
    
    return NextQuestionResponse(
        question=question_response,
        is_complete=next_question_data["is_complete"],
        progress=next_question_data["progress"]
    )


@router.get("/{quiz_id}/adaptive-status")
async def get_adaptive_status(
    quiz_id: int,
    current_user: AuthUser,
    db: DBSession,
) -> dict[str, Any]:
    """Get current adaptive quiz status for a user."""
    
    # Verify quiz exists and is adaptive
    quiz_query = select(Quiz).where(Quiz.id == quiz_id)
    quiz_result = await db.execute(quiz_query)
    quiz = quiz_result.scalar_one_or_none()
    
    if not quiz:
        raise NotFoundError("Quiz not found")
    
    if not quiz.adaptive:
        raise ValidationError("This quiz is not configured for adaptive mode")
    
    # Get active submission
    submission_query = select(Submission).where(
        Submission.user_id == current_user.id,
        Submission.quiz_id == quiz_id,
        Submission.is_completed == False
    ).order_by(Submission.created_at.desc())
    
    submission_result = await db.execute(submission_query)
    submission = submission_result.scalar_one_or_none()
    
    if not submission:
        return {
            "has_active_session": False,
            "quiz_id": quiz_id,
            "is_adaptive": True,
            "message": "No active adaptive session. Use /next endpoint to start."
        }
    
    # Get progress information
    adaptive_service = AdaptiveService()
    
    # Get all questions for progress calculation
    questions_query = select(quiz.questions)
    questions_result = await db.execute(questions_query)
    all_questions = questions_result.scalars().all()
    
    # Get answered questions
    from app.models.answer import Answer
    answers_query = select(Answer).where(Answer.submission_id == submission.id)
    answers_result = await db.execute(answers_query)
    answered_questions = answers_result.scalars().all()
    
    progress = adaptive_service._calculate_progress(list(all_questions), answered_questions)
    
    return {
        "has_active_session": True,
        "submission_id": submission.id,
        "quiz_id": quiz_id,
        "is_adaptive": True,
        "progress": progress,
        "started_at": submission.started_at.isoformat(),
    }
