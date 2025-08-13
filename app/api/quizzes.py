"""Quiz management endpoints."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import DBSession, AuthUser
from app.core.errors import NotFoundError, ValidationError, AppError
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.submission import Submission
from app.models.answer import Answer
from app.models.evaluation import Evaluation
from app.models.retry import Retry
from app.models.user import User
from app.schemas.auth import CurrentUser
from app.schemas.quiz import QuizCreate, QuizResponse, QuizSummary, QuizRetryRequest, QuizRetryResponse
from app.schemas.question import QuestionResponse
from app.schemas.submission import QuizSubmission, SubmissionEvaluation
from app.services.ai.provider import get_ai_provider
from app.services.grading import GradingService
from app.services.datetime import get_utc_now
from app.services.cache import get_cache, CacheService
from app.services.notifications import notification_service
from app.services.leaderboard import get_leaderboard_service

router = APIRouter()
logger = structlog.get_logger()


@router.post("", response_model=QuizResponse)
async def create_quiz(
    quiz_data: QuizCreate,
    current_user: AuthUser,
    db: DBSession,
    cache: CacheService = Depends(get_cache),
) -> QuizResponse:
    """Create a new quiz with AI-generated questions."""
    
    ai_provider = get_ai_provider()
    
    try:
        # Generate questions using AI
        logger.info("Generating questions", subject=quiz_data.subject, num_questions=quiz_data.num_questions)
        
        questions_data = await ai_provider.generate_questions(
            subject=quiz_data.subject,
            grade_level=quiz_data.grade_level,
            num_questions=quiz_data.num_questions,
            difficulty=quiz_data.difficulty,
            topics=quiz_data.topics,
            question_types=quiz_data.question_types,
            standard=quiz_data.standard,
        )
        
        # Create quiz
        quiz_title = f"{quiz_data.subject} - {quiz_data.grade_level} Quiz"
        quiz = Quiz(
            title=quiz_title,
            subject=quiz_data.subject,
            grade_level=quiz_data.grade_level,
            num_questions=quiz_data.num_questions,
            difficulty=quiz_data.difficulty,
            adaptive=quiz_data.adaptive,
            topics=quiz_data.topics,
            question_types=quiz_data.question_types,
            standard=quiz_data.standard,
            creator_id=current_user.id,
            is_published=True,
        )
        
        db.add(quiz)
        await db.flush()  # Get quiz ID
        
        # Create questions
        for index, question_data in enumerate(questions_data):
            # Transform AI provider data to match our database schema
            question = Question(
                quiz_id=quiz.id,
                question_text=question_data.get("question", question_data.get("question_text", "")),
                question_type=question_data.get("type", question_data.get("question_type", "MCQ")),
                difficulty=question_data.get("difficulty", quiz_data.difficulty),
                topic=question_data.get("topic", quiz_data.topics[0] if quiz_data.topics else quiz_data.subject),
                order=question_data.get("order", index + 1),
                points=question_data.get("points", 1.0),
                options=question_data.get("options"),
                correct_answer=question_data.get("correct_answer"),
                explanation=question_data.get("explanation"),
                hint_text=question_data.get("hint_text"),
            )
            db.add(question)
        
        await db.commit()
        await db.refresh(quiz)
        
        # Cache the quiz data
        quiz_response = QuizResponse.model_validate(quiz)
        await cache.set(
            cache.get_quiz_cache_key(quiz.id),
            quiz_response.model_dump(),
            ttl=3600
        )
        
        logger.info("Quiz created", quiz_id=quiz.id, num_questions=len(questions_data))
        
        return quiz_response
    
    except Exception as e:
        logger.error("Failed to create quiz", error=str(e), traceback=str(e.__traceback__))
        await db.rollback()
        
        # More specific error handling
        if "generate_questions" in str(e):
            detail = f"AI provider failed: {str(e)}"
        elif "JSON" in str(e) or "json" in str(e):
            detail = f"Invalid AI response format: {str(e)}"
        else:
            detail = f"Database error: {str(e)}"
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: int,
    current_user: AuthUser,
    db: DBSession,
) -> QuizResponse:
    """Get quiz details (without revealing answers)."""
    
    query = select(Quiz).where(Quiz.id == quiz_id)
    result = await db.execute(query)
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise NotFoundError("Quiz not found")
    
    return QuizResponse.model_validate(quiz)


@router.get("/{quiz_id}/questions", response_model=list[QuestionResponse])
async def get_quiz_questions(
    quiz_id: int,
    current_user: AuthUser,
    db: DBSession,
    cache: CacheService = Depends(get_cache),
) -> list[QuestionResponse]:
    """Get quiz questions (without revealing answers)."""
    
    # Try to get from cache first
    cache_key = cache.get_quiz_questions_cache_key(quiz_id)
    cached_questions = await cache.get(cache_key)
    
    if cached_questions:
        logger.info("Quiz questions served from cache", quiz_id=quiz_id)
        return [QuestionResponse(**q) for q in cached_questions]
    
    # Verify quiz exists
    quiz_query = select(Quiz).where(Quiz.id == quiz_id)
    quiz_result = await db.execute(quiz_query)
    quiz = quiz_result.scalar_one_or_none()
    
    if not quiz:
        raise NotFoundError("Quiz not found")
    
    # Get questions
    questions_query = select(Question).where(Question.quiz_id == quiz_id).order_by(Question.order)
    questions_result = await db.execute(questions_query)
    questions = questions_result.scalars().all()
    
    questions_response = [QuestionResponse.model_validate(q) for q in questions]
    
    # Cache the questions
    await cache.set(
        cache_key,
        [q.model_dump() for q in questions_response],
        ttl=3600
    )
    
    logger.info("Quiz questions loaded and cached", quiz_id=quiz_id, count=len(questions_response))
    
    return questions_response


@router.post("/{quiz_id}/submit", response_model=SubmissionEvaluation)
async def submit_quiz(
    quiz_id: int,
    submission_data: QuizSubmission,
    current_user: AuthUser,
    db: DBSession,
    cache: CacheService = Depends(get_cache),
) -> SubmissionEvaluation:
    """Submit quiz answers and get evaluation."""
    
    # Verify quiz exists
    quiz_query = select(Quiz).options(selectinload(Quiz.questions)).where(Quiz.id == quiz_id)
    quiz_result = await db.execute(quiz_query)
    quiz = quiz_result.scalar_one_or_none()
    
    if not quiz:
        raise NotFoundError("Quiz not found")
    
    # Create submission
    submission = Submission(
        user_id=current_user.id,
        quiz_id=quiz_id,
        started_at=get_utc_now(),
        time_taken_minutes=submission_data.time_taken_minutes,
        is_completed=True,
        submitted_at=get_utc_now(),
    )
    
    db.add(submission)
    await db.flush()  # Get submission ID
    
    # Create answers
    answers = []
    question_map = {q.id: q for q in quiz.questions}
    
    for answer_data in submission_data.answers:
        if answer_data.question_id not in question_map:
            raise ValidationError(f"Invalid question ID: {answer_data.question_id}")
        
        answer = Answer(
            submission_id=submission.id,
            question_id=answer_data.question_id,
            answer_text=(answer_data.answer_text or None),
            selected_option=(answer_data.selected_option or None),
            time_spent_seconds=answer_data.time_spent_seconds,
        )
        answers.append(answer)
        db.add(answer)
    
    await db.flush()
    
    # Grade the submission
    grading_service = GradingService()
    evaluation_data = await grading_service.grade_submission(
        submission=submission,
        questions=list(quiz.questions),
        answers=answers,
    )
    
    # Update submission with scores
    submission.total_score = evaluation_data["total_score"]
    submission.max_possible_score = evaluation_data["max_possible_score"]
    submission.percentage = evaluation_data["percentage"]
    
    # Update individual answers with grades
    for answer, graded_answer in zip(answers, evaluation_data["answers"]):
        answer.is_correct = graded_answer["is_correct"]
        answer.points_earned = graded_answer["points_earned"]
        answer.max_points = graded_answer["max_points"]
        answer.ai_feedback = graded_answer["ai_feedback"]
        answer.confidence_score = graded_answer["confidence_score"]
    
    # Create evaluation record
    evaluation = Evaluation(
        submission_id=submission.id,
        total_score=evaluation_data["total_score"],
        max_possible_score=evaluation_data["max_possible_score"],
        percentage=evaluation_data["percentage"],
        correct_answers=evaluation_data["correct_answers"],
        total_questions=evaluation_data["total_questions"],
        mcq_score=evaluation_data["mcq_score"],
        tf_score=evaluation_data["tf_score"],
        short_answer_score=evaluation_data["short_answer_score"],
        easy_score=evaluation_data["easy_score"],
        medium_score=evaluation_data["medium_score"],
        hard_score=evaluation_data["hard_score"],
        topic_scores=evaluation_data["topic_scores"],
        strengths=evaluation_data["strengths"],
        weaknesses=evaluation_data["weaknesses"],
        suggestions=evaluation_data["suggestions"],
        performance_level=evaluation_data["performance_level"],
    )
    
    db.add(evaluation)
    await db.commit()
    
    # Update leaderboard
    try:
        leaderboard_service = get_leaderboard_service(cache)
        await leaderboard_service.update_leaderboard_entry(
            db=db,
            user_id=current_user.id,
            quiz_id=quiz_id,
            submission_data=evaluation_data
        )
    except Exception as e:
        logger.error("Failed to update leaderboard", error=str(e), quiz_id=quiz_id, user_id=current_user.id)
    
    # Send email notification and enrich response metadata
    notification_attempted = False
    notification_sent = False
    notification_to_email = ""
    try:
        # Get user email from database
        user_query = select(User).where(User.id == current_user.id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        user_email = user.email if user else ""

        notification_attempted = True
        notification_sent = await notification_service.send_quiz_result_email(
            user_email=user_email,
            user_name=current_user.username,
            quiz_title=quiz.title,
            score_percentage=evaluation_data["percentage"],
            total_score=evaluation_data["total_score"],
            max_possible_score=evaluation_data["max_possible_score"],
            correct_answers=evaluation_data["correct_answers"],
            total_questions=evaluation_data["total_questions"],
            performance_level=evaluation_data["performance_level"],
            suggestions=evaluation_data.get("suggestions"),
            strengths=evaluation_data.get("strengths"),
            weaknesses=evaluation_data.get("weaknesses")
        )
        notification_to_email = user_email
    except Exception as e:
        logger.error("Failed to send notification email", error=str(e), user_id=current_user.id)
    
    logger.info(
        "Quiz submitted and graded", 
        quiz_id=quiz_id, 
        submission_id=submission.id,
        score=evaluation_data["percentage"]
    )
    
    # Attach notification metadata for frontend visibility
    evaluation_data["notification_attempted"] = notification_attempted
    from app.core.config import get_settings
    settings = get_settings()
    evaluation_data["notification_enabled"] = settings.notification_enabled
    evaluation_data["notification_sent"] = notification_sent
    evaluation_data["notification_to_email"] = notification_to_email

    return SubmissionEvaluation.model_validate(evaluation_data)


@router.post("/{quiz_id}/retry", response_model=QuizRetryResponse)
async def retry_quiz(
    quiz_id: int,
    retry_data: QuizRetryRequest,
    current_user: AuthUser,
    db: DBSession,
) -> QuizRetryResponse:
    """Create a retry of an existing quiz."""
    
    # Get original quiz
    quiz_query = select(Quiz).options(selectinload(Quiz.questions)).where(Quiz.id == quiz_id)
    quiz_result = await db.execute(quiz_query)
    original_quiz = quiz_result.scalar_one_or_none()
    
    if not original_quiz:
        raise NotFoundError("Quiz not found")
    
    # Count existing retries
    retry_query = select(Retry).where(Retry.original_quiz_id == quiz_id)
    retry_result = await db.execute(retry_query)
    existing_retries = retry_result.scalars().all()
    retry_number = len(existing_retries) + 1
    
    # Create new quiz (copy of original)
    new_quiz = Quiz(
        title=f"{original_quiz.title} (Retry {retry_number})",
        subject=original_quiz.subject,
        grade_level=original_quiz.grade_level,
        num_questions=original_quiz.num_questions,
        difficulty=original_quiz.difficulty,
        adaptive=original_quiz.adaptive,
        topics=original_quiz.topics,
        question_types=original_quiz.question_types,
        standard=original_quiz.standard,
        creator_id=current_user.id,
        is_published=True,
    )
    
    db.add(new_quiz)
    await db.flush()
    
    # Copy questions (potentially with different order/selection for retries)
    for question in original_quiz.questions:
        new_question = Question(
            quiz_id=new_quiz.id,
            question_text=question.question_text,
            question_type=question.question_type,
            difficulty=question.difficulty,
            topic=question.topic,
            order=question.order,
            points=question.points,
            options=question.options,
            correct_answer=question.correct_answer,
            explanation=question.explanation,
            hint_text=question.hint_text,
        )
        db.add(new_question)
    
    # Create retry record
    retry_record = Retry(
        original_quiz_id=quiz_id,
        retried_quiz_id=new_quiz.id,
        retry_number=retry_number,
        reason=retry_data.reason,
    )
    
    db.add(retry_record)
    await db.commit()
    
    logger.info("Quiz retry created", original_quiz_id=quiz_id, new_quiz_id=new_quiz.id, retry_number=retry_number)
    
    return QuizRetryResponse(
        new_quiz_id=new_quiz.id,
        retry_number=retry_number,
        message=f"Retry {retry_number} created successfully",
    )


@router.delete("/{quiz_id}")
async def delete_quiz(
    quiz_id: int,
    current_user: AuthUser,
    db: DBSession,
    cache: CacheService = Depends(get_cache),
):
    """Delete a quiz and all its associated data.

    Requires authentication. Only the quiz creator can delete their quiz.
    This removes the quiz, its questions, submissions, answers, evaluations,
    and retry records, and invalidates relevant caches.
    """

    # Load quiz
    quiz_query = select(Quiz).where(Quiz.id == quiz_id)
    quiz_result = await db.execute(quiz_query)
    quiz = quiz_result.scalar_one_or_none()

    if not quiz:
        raise NotFoundError("Quiz not found")

    # Authorization: only creator can delete
    if quiz.creator_id != current_user.id:
        from app.core.errors import AuthorizationError

        raise AuthorizationError("You are not allowed to delete this quiz")

    # Keep subject/grade for cache invalidation before deletion
    subject = quiz.subject
    grade_level = quiz.grade_level

    try:
        # Explicitly delete Retry rows that reference this quiz either as original or retried
        retry_delete_stmt = delete(Retry).where(
            or_(
                Retry.original_quiz_id == quiz_id,
                Retry.retried_quiz_id == quiz_id,
            )
        )
        await db.execute(retry_delete_stmt)

        # Delete the quiz (cascades to questions, submissions, answers, evaluations)
        await db.delete(quiz)
        await db.commit()

        # Invalidate caches
        try:
            await cache.delete(cache.get_quiz_cache_key(quiz_id))
            await cache.delete(cache.get_quiz_questions_cache_key(quiz_id))

            # Invalidate leaderboard cache for this subject/grade
            leaderboard_service = get_leaderboard_service(cache)
            await leaderboard_service.invalidate_leaderboard_cache(subject, grade_level)
        except Exception:
            # Cache failures should not break deletion semantics
            pass

        logger.info("Quiz deleted", quiz_id=quiz_id, user_id=current_user.id)
        return {"message": "Quiz deleted successfully", "id": quiz_id}

    except AppError:
        # Re-raise known app errors untouched
        raise
    except Exception as e:
        logger.error("Failed to delete quiz", error=str(e), quiz_id=quiz_id)
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete quiz")