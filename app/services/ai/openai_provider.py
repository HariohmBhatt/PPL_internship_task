"""OpenAI provider implementation."""

import json
from typing import Any

import httpx
import structlog

from app.core.config import get_settings
from app.core.errors import AIServiceError
from app.services.ai.provider import AIProvider

logger = structlog.get_logger()


class OpenAIProvider(AIProvider):
    """OpenAI-based AI provider."""
    
    def __init__(self):
        """Initialize OpenAI provider."""
        self.settings = get_settings()
        self.api_key = self.settings.openai_api_key
        self.base_url = "https://api.openai.com/v1"
        
        if not self.api_key:
            raise AIServiceError("OpenAI API key not configured")
    
    async def _make_request(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Make a request to OpenAI API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/{endpoint}",
                    headers=headers,
                    json=payload,
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                logger.error("OpenAI API error", status_code=e.response.status_code, response=e.response.text)
                raise AIServiceError(f"OpenAI API error: {e.response.status_code}")
            
            except httpx.RequestError as e:
                logger.error("OpenAI request error", error=str(e))
                raise AIServiceError("Failed to connect to OpenAI API")
    
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
        """Generate quiz questions using OpenAI."""
        # This is a stub implementation
        # In a real implementation, you would craft proper prompts and parse responses
        
        prompt = f"""
        Generate {num_questions} {difficulty} quiz questions for {grade_level} students about {subject}.
        
        Topics to cover: {', '.join(topics)}
        Question types needed: {', '.join(question_types)}
        {f'Educational standard: {standard}' if standard else ''}
        
        Return questions in JSON format with the following structure for each question:
        {{
            "question_text": "The question text",
            "question_type": "MCQ|TF|short_answer|essay",
            "difficulty": "{difficulty}",
            "topic": "relevant topic",
            "order": 1,
            "points": 1-10,
            "options": ["option1", "option2", ...] (for MCQ/TF only),
            "correct_answer": "correct answer",
            "explanation": "explanation of the answer",
            "hint_text": "helpful hint without giving away the answer"
        }}
        
        Important: Do not include the correct answer in hints. Hints should guide thinking without revealing the solution.
        """
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are an expert educational content creator."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.7,
        }
        
        try:
            response = await self._make_request("chat/completions", payload)
            content = response["choices"][0]["message"]["content"]
            
            # Parse JSON response
            questions_data = json.loads(content)
            
            # Validate and return questions
            if isinstance(questions_data, list):
                return questions_data
            else:
                raise AIServiceError("Invalid response format from OpenAI")
                
        except json.JSONDecodeError:
            logger.error("Failed to parse OpenAI response as JSON")
            raise AIServiceError("Invalid JSON response from OpenAI")
        
        except Exception as e:
            logger.error("OpenAI question generation failed", error=str(e))
            raise AIServiceError("Failed to generate questions")
    
    async def grade_short_answer(
        self,
        question: str,
        correct_answer: str,
        student_answer: str,
        max_points: float = 1.0,
    ) -> dict[str, Any]:
        """Grade a short answer using OpenAI."""
        prompt = f"""
        Grade this student's answer to a quiz question.
        
        Question: {question}
        Expected Answer: {correct_answer}
        Student Answer: {student_answer}
        Maximum Points: {max_points}
        
        Provide grading in this JSON format:
        {{
            "score": 0.0-{max_points},
            "max_points": {max_points},
            "feedback": "specific feedback for the student",
            "confidence": 0.0-1.0
        }}
        
        Consider:
        - Accuracy of information
        - Completeness of answer
        - Understanding demonstrated
        - Clarity of explanation
        """
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are an expert educator grading student responses."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.3,
        }
        
        try:
            response = await self._make_request("chat/completions", payload)
            content = response["choices"][0]["message"]["content"]
            
            return json.loads(content)
            
        except json.JSONDecodeError:
            logger.error("Failed to parse OpenAI grading response")
            raise AIServiceError("Invalid grading response from OpenAI")
        
        except Exception as e:
            logger.error("OpenAI grading failed", error=str(e))
            raise AIServiceError("Failed to grade answer")
    
    async def hint(
        self,
        question: str,
        question_type: str,
        difficulty: str,
        topic: str,
    ) -> str:
        """Generate a hint using OpenAI."""
        prompt = f"""
        Generate a helpful hint for this quiz question without revealing the answer.
        
        Question: {question}
        Type: {question_type}
        Difficulty: {difficulty}
        Topic: {topic}
        
        The hint should:
        - Guide thinking in the right direction
        - Not give away the answer
        - Be appropriate for the difficulty level
        - Help students learn the concept
        
        Return only the hint text, nothing else.
        """
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful tutor providing hints to students."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 150,
            "temperature": 0.5,
        }
        
        try:
            response = await self._make_request("chat/completions", payload)
            return response["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            logger.error("OpenAI hint generation failed", error=str(e))
            raise AIServiceError("Failed to generate hint")
    
    async def suggest_improvements(
        self,
        quiz_results: dict[str, Any],
        student_performance: dict[str, Any],
    ) -> list[str]:
        """Generate improvement suggestions using OpenAI."""
        prompt = f"""
        Analyze this student's quiz performance and provide exactly 2 specific improvement suggestions.
        
        Quiz Results: {json.dumps(quiz_results, indent=2)}
        Performance Data: {json.dumps(student_performance, indent=2)}
        
        Provide exactly 2 actionable suggestions in JSON format:
        ["suggestion 1", "suggestion 2"]
        
        Each suggestion should be:
        - Specific and actionable
        - Based on the performance data
        - Helpful for improvement
        - Encouraging but honest
        """
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are an expert educational advisor."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 300,
            "temperature": 0.4,
        }
        
        try:
            response = await self._make_request("chat/completions", payload)
            content = response["choices"][0]["message"]["content"]
            
            suggestions = json.loads(content)
            
            # Ensure exactly 2 suggestions
            if isinstance(suggestions, list) and len(suggestions) >= 2:
                return suggestions[:2]
            else:
                raise AIServiceError("Invalid suggestions format from OpenAI")
                
        except json.JSONDecodeError:
            logger.error("Failed to parse OpenAI suggestions response")
            raise AIServiceError("Invalid suggestions response from OpenAI")
        
        except Exception as e:
            logger.error("OpenAI suggestions generation failed", error=str(e))
            raise AIServiceError("Failed to generate suggestions")
