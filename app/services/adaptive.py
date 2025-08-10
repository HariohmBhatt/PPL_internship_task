"""Adaptive quiz service for dynamic difficulty adjustment."""

from typing import Dict, List, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.answer import Answer
from app.models.question import Question
from app.models.submission import Submission

logger = structlog.get_logger()


class AdaptiveService:
    """Service for adaptive quiz behavior."""
    
    def __init__(self):
        self.window_size = 3  # Look at last 3 answers for adaptation
    
    async def get_next_question(
        self, 
        session: AsyncSession, 
        submission: Submission,
        quiz_questions: List[Question]
    ) -> Dict[str, any]:
        """Get the next question based on adaptive policy."""
        
        # Get answered questions
        answered_query = select(Answer).where(Answer.submission_id == submission.id)
        result = await session.execute(answered_query)
        answered_questions = result.scalars().all()
        
        answered_question_ids = {answer.question_id for answer in answered_questions}
        
        # Find unanswered questions
        unanswered_questions = [
            q for q in quiz_questions 
            if q.id not in answered_question_ids
        ]
        
        if not unanswered_questions:
            return {
                "question": None,
                "is_complete": True,
                "progress": self._calculate_progress(quiz_questions, answered_questions),
            }
        
        # Determine next difficulty based on recent performance
        target_difficulty = await self._determine_next_difficulty(
            session, answered_questions, quiz_questions
        )
        
        # Select best question for target difficulty
        next_question = self._select_question(unanswered_questions, target_difficulty)
        
        return {
            "question": next_question,
            "is_complete": False,
            "progress": self._calculate_progress(quiz_questions, answered_questions),
        }
    
    async def _determine_next_difficulty(
        self, 
        session: AsyncSession, 
        answered_questions: List[Answer],
        all_questions: List[Question]
    ) -> str:
        """Determine the next question difficulty based on recent performance."""
        
        if len(answered_questions) < self.window_size:
            # Not enough data, start with easy
            return "easy"
        
        # Get the last N answers (rolling window)
        recent_answers = sorted(
            answered_questions, 
            key=lambda a: a.created_at
        )[-self.window_size:]
        
        # Calculate performance in the window
        correct_count = sum(1 for answer in recent_answers if answer.is_correct)
        performance_ratio = correct_count / len(recent_answers)
        
        # Get current difficulty context
        question_map = {q.id: q for q in all_questions}
        recent_difficulties = [
            question_map[answer.question_id].difficulty 
            for answer in recent_answers
            if answer.question_id in question_map
        ]
        
        current_difficulty = self._get_current_difficulty_level(recent_difficulties)
        
        # Adaptive logic: step up/down/hold based on performance
        if performance_ratio >= 0.8:  # 80% or better - step up
            return self._step_up_difficulty(current_difficulty)
        elif performance_ratio <= 0.4:  # 40% or worse - step down
            return self._step_down_difficulty(current_difficulty)
        else:  # 41-79% - hold current level
            return current_difficulty
    
    def _get_current_difficulty_level(self, recent_difficulties: List[str]) -> str:
        """Get the current difficulty level from recent questions."""
        if not recent_difficulties:
            return "easy"
        
        # Use the most common difficulty in recent questions
        difficulty_counts = {}
        for diff in recent_difficulties:
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
        
        return max(difficulty_counts.items(), key=lambda x: x[1])[0]
    
    def _step_up_difficulty(self, current_difficulty: str) -> str:
        """Step up the difficulty level."""
        difficulty_order = ["easy", "medium", "hard"]
        try:
            current_index = difficulty_order.index(current_difficulty)
            next_index = min(current_index + 1, len(difficulty_order) - 1)
            return difficulty_order[next_index]
        except ValueError:
            return "medium"  # Fallback
    
    def _step_down_difficulty(self, current_difficulty: str) -> str:
        """Step down the difficulty level."""
        difficulty_order = ["easy", "medium", "hard"]
        try:
            current_index = difficulty_order.index(current_difficulty)
            next_index = max(current_index - 1, 0)
            return difficulty_order[next_index]
        except ValueError:
            return "easy"  # Fallback
    
    def _select_question(
        self, 
        available_questions: List[Question], 
        target_difficulty: str
    ) -> Optional[Question]:
        """Select the best question for the target difficulty."""
        
        # First, try to find a question with exact difficulty match
        exact_matches = [
            q for q in available_questions 
            if q.difficulty == target_difficulty
        ]
        
        if exact_matches:
            # Return the first question in order
            return min(exact_matches, key=lambda q: q.order)
        
        # If no exact match, find closest difficulty
        difficulty_priority = {
            "easy": ["medium", "hard"],
            "medium": ["easy", "hard"],
            "hard": ["medium", "easy"],
        }
        
        for fallback_difficulty in difficulty_priority.get(target_difficulty, []):
            fallback_matches = [
                q for q in available_questions 
                if q.difficulty == fallback_difficulty
            ]
            if fallback_matches:
                return min(fallback_matches, key=lambda q: q.order)
        
        # Last resort: return any available question
        if available_questions:
            return min(available_questions, key=lambda q: q.order)
        
        return None
    
    def _calculate_progress(
        self, 
        all_questions: List[Question], 
        answered_questions: List[Answer]
    ) -> Dict[str, int]:
        """Calculate quiz progress information."""
        total_questions = len(all_questions)
        answered_count = len(answered_questions)
        remaining_count = total_questions - answered_count
        
        correct_count = sum(1 for answer in answered_questions if answer.is_correct)
        incorrect_count = answered_count - correct_count
        
        return {
            "total_questions": total_questions,
            "answered": answered_count,
            "remaining": remaining_count,
            "correct": correct_count,
            "incorrect": incorrect_count,
            "percentage_complete": round((answered_count / total_questions) * 100, 1) if total_questions > 0 else 0,
        }
