"""Grading service for quiz evaluation."""

from typing import Any, Dict, List
import re

import structlog

from app.models.answer import Answer
from app.models.question import Question
from app.models.submission import Submission
from app.services.ai.provider import get_ai_provider

logger = structlog.get_logger()


class GradingService:
    """Service for grading quiz submissions."""
    
    def __init__(self):
        self.ai_provider = get_ai_provider()
    
    async def grade_submission(
        self, 
        submission: Submission, 
        questions: List[Question], 
        answers: List[Answer]
    ) -> Dict[str, Any]:
        """Grade a complete submission and return detailed results."""
        total_score = 0.0
        max_possible_score = 0.0
        correct_answers = 0
        total_questions = len(questions)
        
        # Performance tracking by type and difficulty
        type_scores = {"MCQ": [], "TF": [], "short_answer": [], "essay": []}
        difficulty_scores = {"easy": [], "medium": [], "hard": []}
        topic_scores = {}
        
        # Grade each answer
        graded_answers = []
        for answer in answers:
            question = next((q for q in questions if q.id == answer.question_id), None)
            if not question:
                continue
            
            graded_answer = await self._grade_answer(answer, question)
            graded_answers.append(graded_answer)
            
            # Update totals
            points_earned = graded_answer["points_earned"]
            max_points = graded_answer["max_points"]
            
            total_score += points_earned
            max_possible_score += max_points
            
            if graded_answer["is_correct"]:
                correct_answers += 1
            
            # Track by type
            question_type = question.question_type
            if question_type in type_scores:
                type_scores[question_type].append(points_earned / max_points)
            
            # Track by difficulty
            difficulty = question.difficulty
            if difficulty in difficulty_scores:
                difficulty_scores[difficulty].append(points_earned / max_points)
            
            # Track by topic
            topic = question.topic
            if topic not in topic_scores:
                topic_scores[topic] = []
            topic_scores[topic].append(points_earned / max_points)
        
        # Calculate percentage
        percentage = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
        
        # Calculate performance by category
        def avg_score(scores: List[float]) -> float | None:
            return sum(scores) / len(scores) * 100 if scores else None
        
        mcq_score = avg_score(type_scores["MCQ"])
        tf_score = avg_score(type_scores["TF"])
        short_answer_score = avg_score(type_scores["short_answer"])
        essay_score = avg_score(type_scores["essay"])
        
        easy_score = avg_score(difficulty_scores["easy"])
        medium_score = avg_score(difficulty_scores["medium"])
        hard_score = avg_score(difficulty_scores["hard"])
        
        topic_averages = {
            topic: avg_score(scores) for topic, scores in topic_scores.items()
        }
        
        # Determine performance level
        performance_level = self._get_performance_level(percentage)
        
        # Generate AI suggestions
        quiz_results = {
            "total_score": total_score,
            "max_possible_score": max_possible_score,
            "percentage": percentage,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
        }
        
        student_performance = {
            "percentage": percentage,
            "weak_topics": [topic for topic, score in topic_averages.items() if score and score < 60],
            "question_types": {
                "MCQ": mcq_score or 0,
                "TF": tf_score or 0,
                "short_answer": short_answer_score or 0,
                "essay": essay_score or 0,
            }
        }
        
        suggestions = await self.ai_provider.suggest_improvements(
            quiz_results, student_performance
        )
        
        return {
            "submission_id": submission.id,
            "quiz_id": submission.quiz_id,
            "total_score": total_score,
            "max_possible_score": max_possible_score,
            "percentage": percentage,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "performance_level": performance_level,
            "answers": graded_answers,
            "mcq_score": mcq_score,
            "tf_score": tf_score,
            "short_answer_score": short_answer_score,
            "essay_score": essay_score,
            "easy_score": easy_score,
            "medium_score": medium_score,
            "hard_score": hard_score,
            "topic_scores": topic_averages,
            "suggestions": suggestions,
            "strengths": self._identify_strengths(type_scores, difficulty_scores),
            "weaknesses": self._identify_weaknesses(type_scores, difficulty_scores),
            "time_taken_minutes": submission.time_taken_minutes,
            "submitted_at": submission.submitted_at,
        }
    
    async def _grade_answer(self, answer: Answer, question: Question) -> Dict[str, Any]:
        """Grade an individual answer."""
        max_points = float(question.points)
        
        def normalize_text(text: str) -> str:
            return re.sub(r"\s+", " ", text or "").strip().lower()

        def extract_numbers(text: str) -> List[float]:
            if not text:
                return []
            nums = []
            for match in re.findall(r"-?\d*\.?\d+", text):
                try:
                    nums.append(float(match))
                except ValueError:
                    continue
            return nums

        def boolean_equivalent(a: str, b: str) -> bool:
            truthy = {"true", "t", "yes", "y", "1"}
            falsy = {"false", "f", "no", "n", "0"}
            na = normalize_text(a)
            nb = normalize_text(b)
            return (na in truthy and nb in truthy) or (na in falsy and nb in falsy)

        def obviously_correct(student: str, correct: str) -> bool:
            if not student or not correct:
                return False
            ns = normalize_text(student)
            nc = normalize_text(correct)
            if ns == nc:
                return True
            if boolean_equivalent(ns, nc):
                return True
            # Numeric tolerance match (order-insensitive, units ignored)
            snums = extract_numbers(ns)
            cnums = extract_numbers(nc)
            if snums and cnums and len(snums) == len(cnums):
                tol = 1e-6
                return all(abs(s - c) <= tol for s, c in zip(snums, cnums))
            return False

        if question.question_type in ["MCQ", "TF"]:
            # Rule-based grading for objective questions
            # Be robust to case/whitespace and boolean synonyms
            selected = answer.selected_option or ""
            correct = question.correct_answer or ""
            is_correct = (
                normalize_text(selected) == normalize_text(correct)
                or boolean_equivalent(selected, correct)
            )
            points_earned = max_points if is_correct else 0.0
            ai_feedback = None
            confidence_score = 1.0
            
        else:
            # AI-based grading for subjective questions
            if not answer.answer_text or answer.answer_text.strip() == "":
                points_earned = 0.0
                is_correct = False
                ai_feedback = "No answer provided."
                confidence_score = 1.0
            else:
                # Short-circuit: if student's text obviously matches expected, award full credit
                if obviously_correct(answer.answer_text, question.correct_answer or ""):
                    points_earned = max_points
                    is_correct = True
                    ai_feedback = "Matched expected answer."
                    confidence_score = 1.0
                else:
                    try:
                        grading_result = await self.ai_provider.grade_short_answer(
                            question=question.question_text,
                            correct_answer=question.correct_answer or "",
                            student_answer=answer.answer_text,
                            max_points=max_points,
                        )
                        
                        points_earned = grading_result["score"]
                        is_correct = points_earned >= (max_points * 0.6)  # 60% threshold
                        ai_feedback = grading_result["feedback"]
                        confidence_score = grading_result["confidence"]
                        
                    except Exception as e:
                        logger.error("AI grading failed", error=str(e), question_id=question.id)
                        # Fallback grading
                        points_earned = max_points * 0.5  # Give 50% credit
                        is_correct = False
                        ai_feedback = "Automatic grading unavailable. Manual review may be needed."
                        confidence_score = 0.5
        
        # Apply hint penalty if hints were used
        hint_penalty = answer.hints_used * 0.1 * max_points  # 10% penalty per hint
        points_earned = max(0.0, points_earned - hint_penalty)
        
        return {
            "question_id": question.id,
            "is_correct": is_correct,
            "points_earned": round(points_earned, 2),
            "max_points": max_points,
            "ai_feedback": ai_feedback,
            "confidence_score": confidence_score,
        }
    
    def _get_performance_level(self, percentage: float) -> str:
        """Determine performance level based on percentage."""
        if percentage >= 90:
            return "excellent"
        elif percentage >= 75:
            return "good"
        elif percentage >= 60:
            return "fair"
        else:
            return "poor"
    
    def _identify_strengths(
        self, 
        type_scores: Dict[str, List[float]], 
        difficulty_scores: Dict[str, List[float]]
    ) -> List[str]:
        """Identify student strengths."""
        strengths = []
        
        # Check question type strengths
        for qtype, scores in type_scores.items():
            if scores and sum(scores) / len(scores) >= 0.8:  # 80% or better
                strengths.append(f"Strong performance on {qtype} questions")
        
        # Check difficulty strengths
        for difficulty, scores in difficulty_scores.items():
            if scores and sum(scores) / len(scores) >= 0.8:  # 80% or better
                strengths.append(f"Excellent handling of {difficulty} questions")
        
        if not strengths:
            strengths.append("Shows effort and engagement with the material")
        
        return strengths[:3]  # Limit to 3 strengths
    
    def _identify_weaknesses(
        self, 
        type_scores: Dict[str, List[float]], 
        difficulty_scores: Dict[str, List[float]]
    ) -> List[str]:
        """Identify areas for improvement."""
        weaknesses = []
        
        # Check question type weaknesses
        for qtype, scores in type_scores.items():
            if scores and sum(scores) / len(scores) < 0.6:  # Below 60%
                weaknesses.append(f"Needs improvement on {qtype} questions")
        
        # Check difficulty weaknesses
        for difficulty, scores in difficulty_scores.items():
            if scores and sum(scores) / len(scores) < 0.6:  # Below 60%
                weaknesses.append(f"Struggles with {difficulty} questions")
        
        if not weaknesses:
            weaknesses.append("Overall performance is good with room for minor improvements")
        
        return weaknesses[:3]  # Limit to 3 weaknesses
