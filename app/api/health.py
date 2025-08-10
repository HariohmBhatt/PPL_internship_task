"""Health check endpoints."""

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.deps import DBSession
from app.schemas.common import SuccessResponse

router = APIRouter()
logger = structlog.get_logger()


@router.get("/healthz", response_model=dict[str, str])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "ai-quiz-microservice"}


@router.get("/readyz", response_model=dict[str, str])
async def readiness_check(db: DBSession) -> dict[str, str]:
    """Readiness check with database connectivity."""
    try:
        # Test database connection
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        
        return {"status": "ready", "database": "connected"}
    
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        return {"status": "not ready", "database": "disconnected", "error": str(e)}
