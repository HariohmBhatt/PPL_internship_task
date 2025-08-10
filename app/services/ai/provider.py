"""AI provider interface and factory."""

from abc import ABC, abstractmethod
from typing import Any

from app.core.config import get_settings


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
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
        """Generate quiz questions based on parameters."""
        pass
    
    @abstractmethod
    async def grade_short_answer(
        self,
        question: str,
        correct_answer: str,
        student_answer: str,
        max_points: float = 1.0,
    ) -> dict[str, Any]:
        """Grade a short answer question."""
        pass
    
    @abstractmethod
    async def hint(
        self,
        question: str,
        question_type: str,
        difficulty: str,
        topic: str,
    ) -> str:
        """Generate a hint for a question."""
        pass
    
    @abstractmethod
    async def suggest_improvements(
        self,
        quiz_results: dict[str, Any],
        student_performance: dict[str, Any],
    ) -> list[str]:
        """Suggest improvements based on quiz performance."""
        pass


def get_ai_provider() -> AIProvider:
    """Factory function to get the appropriate AI provider.
    
    Priority: OpenAI → Gemini → Mock
    """
    import structlog
    logger = structlog.get_logger()
    
    settings = get_settings()
    
    # Skip AI providers in testing mode
    if settings.is_testing:
        logger.info("Using MockProvider for testing")
        from app.services.ai.mock import MockProvider
        return MockProvider()
    
    # Try OpenAI first only if it's likely to work
    if settings.openai_api_key and settings.openai_api_key.strip() and len(settings.openai_api_key.strip()) > 20:
        try:
            logger.info("Attempting to use OpenAI provider")
            from app.services.ai.openai_provider import OpenAIProvider
            provider = OpenAIProvider()
            logger.info("OpenAI provider initialized successfully")
            return provider
        except Exception as e:
            logger.warning("OpenAI provider failed to initialize", error=str(e))
    
    # Try Gemini second
    if settings.gemini_api_key and settings.gemini_api_key.strip():
        try:
            logger.info("Attempting to use Gemini provider")
            from app.services.ai.gemini_provider import GeminiProvider
            provider = GeminiProvider(settings.gemini_api_key)
            logger.info("Gemini provider initialized successfully")
            return provider
        except Exception as e:
            logger.warning("Gemini provider failed to initialize", error=str(e))
    
    # Fallback to Mock provider
    logger.info("Using MockProvider as fallback (no API keys available)")
    from app.services.ai.mock import MockProvider
    return MockProvider()
