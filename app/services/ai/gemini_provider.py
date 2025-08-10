"""Google Gemini AI provider implementation."""

import json
from typing import Any

import httpx
import structlog

from app.services.ai.provider import AIProvider

logger = structlog.get_logger()


class GeminiProvider(AIProvider):
    """Google Gemini AI provider for quiz generation and grading."""
    
    def __init__(self, api_key: str):
        """Initialize Gemini provider with API key."""
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-1.5-flash"
    
    async def generate_questions(
        self,
        subject: str,
        grade_level: str,
        num_questions: int,
        difficulty: str,
        topics: list[str],
        question_types: list[str],
        standard: str | None = None,
    ) -> list[dict[str, Any]]:
        """Generate quiz questions using Gemini."""
        
        # Build prompt
        topics_str = ", ".join(topics) if topics else "general topics"
        types_str = ", ".join(question_types) if question_types else "MCQ"
        standard_str = f" following {standard} standards" if standard else ""
        
        prompt = f"""Generate {num_questions} {difficulty} level quiz questions about {subject} for grade {grade_level}.
Focus on these topics: {topics_str}.
Question types: {types_str}{standard_str}.

For each question, provide:
1. Question text
2. If MCQ/TF: 4 options (for MCQ) or True/False (for TF)
3. Correct answer
4. Explanation
5. Topic and difficulty

Return as JSON array with this exact structure:
[
  {{
    "question": "Question text here?",
    "type": "MCQ" or "TF" or "SHORT",
    "options": ["Option A", "Option B", "Option C", "Option D"] or ["True", "False"] or null,
    "correct_answer": "Option A" or "True" or "correct text answer",
    "explanation": "Why this is correct",
    "topic": "{topics[0] if topics else subject}",
    "difficulty": "{difficulty}",
    "points": 1.0
  }}
]

Make questions educational and appropriate for grade {grade_level}."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                    json={
                        "contents": [{
                            "parts": [{"text": prompt}]
                        }],
                        "generationConfig": {
                            "temperature": 0.7,
                            "maxOutputTokens": 2048,
                        }
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error("Gemini API error", status_code=response.status_code, response=response.text)
                    raise Exception(f"Gemini API error: {response.status_code}")
                
                result = response.json()
                # Log prompt and raw body at debug level (truncated)
                try:
                    logger.debug(
                        "Gemini generate prompt",
                        prompt_preview=prompt[:500] + ("…" if len(prompt) > 500 else ""),
                    )
                except Exception:
                    pass
                
                # Extract text from Gemini response
                if "candidates" in result and result["candidates"]:
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    try:
                        logger.debug(
                            "Gemini raw content",
                            content_preview=content[:2000] + ("…" if len(content) > 2000 else ""),
                        )
                    except Exception:
                        pass
                    
                    # Try to parse JSON from the content
                    # Sometimes Gemini wraps JSON in markdown code blocks
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    
                    questions = json.loads(content.strip())
                    # Log a compact summary for each question at INFO
                    try:
                        for idx, q in enumerate(questions, start=1):
                            qtext = q.get("question") or q.get("question_text") or ""
                            qprev = qtext[:120] + ("…" if len(qtext) > 120 else "")
                            logger.info(
                                "Gemini question parsed",
                                index=idx,
                                type=q.get("type") or q.get("question_type"),
                                topic=q.get("topic"),
                                difficulty=q.get("difficulty"),
                                points=q.get("points"),
                                correct_answer=q.get("correct_answer"),
                                question_preview=qprev,
                            )
                    except Exception:
                        pass
                    logger.info("Generated questions with Gemini", count=len(questions))
                    return questions
                    
                else:
                    logger.error("No candidates in Gemini response", response=result)
                    raise Exception("No content generated by Gemini")
                    
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Gemini JSON response", error=str(e))
            raise Exception(f"Invalid JSON from Gemini: {e}")
        except Exception as e:
            logger.error("Gemini API call failed", error=str(e))
            raise Exception(f"Gemini API failed: {e}")
    
    async def grade_short_answer(
        self,
        question: str,
        correct_answer: str,
        student_answer: str,
        max_points: float = 1.0,
    ) -> dict[str, Any]:
        """Grade a short answer using Gemini."""
        
        prompt = f"""Grade this short answer question:

Question: {question}
Correct Answer: {correct_answer}
Student Answer: {student_answer}
Max Points: {max_points}

Please evaluate:
1. Is the student answer correct? (true/false)
2. How many points should be awarded? (0 to {max_points})
3. Provide feedback explaining the grading
4. Confidence score (0.0 to 1.0)

Return as JSON:
{{
  "is_correct": boolean,
  "points_earned": number,
  "max_points": {max_points},
  "feedback": "explanation text",
  "confidence_score": number
}}"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                    json={
                        "contents": [{
                            "parts": [{"text": prompt}]
                        }],
                        "generationConfig": {
                            "temperature": 0.3,
                            "maxOutputTokens": 512,
                        }
                    },
                    timeout=15.0
                )
                
                if response.status_code != 200:
                    logger.error("Gemini grading API error", status_code=response.status_code)
                    raise Exception(f"Gemini API error: {response.status_code}")
                
                result = response.json()
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                
                # Parse JSON response
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                    
                grading_result = json.loads(content.strip())
                try:
                    logger.debug(
                        "Gemini grade raw",
                        question_preview=question[:120] + ("…" if len(question) > 120 else ""),
                        correct_answer_preview=(correct_answer or "")[:120],
                        student_answer_preview=(student_answer or "")[:200],
                        result=grading_result,
                    )
                except Exception:
                    pass
                logger.info("Graded short answer with Gemini", points=grading_result.get("points_earned"))
                return grading_result
                
        except Exception as e:
            logger.error("Gemini grading failed", error=str(e))
            # Fallback to simple grading
            is_correct = correct_answer.lower().strip() in student_answer.lower().strip()
            return {
                "is_correct": is_correct,
                "points_earned": max_points if is_correct else 0.0,
                "max_points": max_points,
                "feedback": f"Auto-graded: {'Correct' if is_correct else 'Incorrect'} (Gemini unavailable)",
                "confidence_score": 0.5
            }
    
    async def hint(
        self,
        question: str,
        question_type: str,
        difficulty: str,
        topic: str,
    ) -> str:
        """Generate a helpful hint using Gemini."""
        
        prompt = f"""Provide a helpful hint for this {difficulty} level {question_type} question about {topic}:

Question: {question}

Generate a hint that:
1. Guides the student without giving away the answer
2. Explains key concepts or approaches
3. Is encouraging and educational
4. Is appropriate for the difficulty level

Provide ONLY the hint text, no additional formatting."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                    json={
                        "contents": [{
                            "parts": [{"text": prompt}]
                        }],
                        "generationConfig": {
                            "temperature": 0.8,
                            "maxOutputTokens": 256,
                        }
                    },
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Gemini API error: {response.status_code}")
                
                result = response.json()
                hint_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                
                logger.info("Generated hint with Gemini")
                return hint_text
                
        except Exception as e:
            logger.error("Gemini hint generation failed", error=str(e))
            return f"Think about the key concepts related to {topic}. Consider the {difficulty} level approach to this problem."
    
    async def suggest_improvements(
        self,
        quiz_results: dict[str, Any],
        student_performance: dict[str, Any],
    ) -> list[str]:
        """Generate improvement suggestions using Gemini."""
        
        performance_summary = f"""
Student Performance Summary:
- Score: {student_performance.get('percentage', 0)}%
- Correct: {student_performance.get('correct_answers', 0)}/{student_performance.get('total_questions', 0)}
- Strengths: {', '.join(student_performance.get('strengths', []))}
- Weaknesses: {', '.join(student_performance.get('weaknesses', []))}
- MCQ Score: {student_performance.get('mcq_score', 0)}%
- True/False Score: {student_performance.get('tf_score', 0)}%
- Short Answer Score: {student_performance.get('short_answer_score', 0)}%
"""

        prompt = f"""{performance_summary}

Based on this quiz performance, provide 3-5 specific, actionable improvement suggestions.
Focus on:
1. Weak areas that need attention
2. Study strategies for improvement
3. Specific topics to review
4. Learning techniques for better retention

Return suggestions as a JSON array of strings:
["suggestion 1", "suggestion 2", "suggestion 3"]"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                    json={
                        "contents": [{
                            "parts": [{"text": prompt}]
                        }],
                        "generationConfig": {
                            "temperature": 0.7,
                            "maxOutputTokens": 512,
                        }
                    },
                    timeout=15.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Gemini API error: {response.status_code}")
                
                result = response.json()
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                
                # Parse JSON response
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                    
                suggestions = json.loads(content.strip())
                
                logger.info("Generated improvement suggestions with Gemini", count=len(suggestions))
                return suggestions
                
        except Exception as e:
            logger.error("Gemini suggestions failed", error=str(e))
            # Fallback suggestions
            fallback_suggestions = [
                "Review the topics where you scored lower",
                "Practice more questions of the types you found challenging",
                "Focus on understanding concepts rather than memorizing",
                "Try explaining concepts in your own words to reinforce learning"
            ]
            
            if student_performance.get('percentage', 0) < 60:
                fallback_suggestions.append("Consider seeking additional help or tutoring")
            
            return fallback_suggestions[:3]
