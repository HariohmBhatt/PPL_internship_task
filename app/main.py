"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from app.api import adaptive, auth, health, hints, history, quizzes, leaderboard
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import setup_logging
from app.db.session import create_tables

# Setup structured logging
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    setup_logging()
    logger.info("Starting AI Quiz Microservice with bonus features")
    
    # Create database tables
    await create_tables()
    logger.info("Database tables initialized")
    
    # Initialize cache connection
    try:
        from app.services.cache import cache_service
        redis_client = await cache_service.get_redis()
        if redis_client:
            logger.info("Redis cache connection established")
        else:
            logger.warning("Redis cache not available, continuing without caching")
    except Exception as e:
        logger.warning(f"Failed to initialize Redis cache: {e}")
    
    logger.info("AI Quiz Microservice startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Quiz Microservice")
    
    # Close cache connections
    try:
        from app.services.cache import cache_service
        await cache_service.close()
        logger.info("Cache connections closed")
    except Exception as e:
        logger.warning(f"Error closing cache connections: {e}")
    
    logger.info("AI Quiz Microservice shutdown completed")


# Create FastAPI application
settings = get_settings()
app = FastAPI(
    title="AI Quiz Microservice",
    description="AI-powered quiz generation and evaluation service",
    version="0.1.0",
    docs_url="/docs" if settings.env == "dev" else None,
    redoc_url="/redoc" if settings.env == "dev" else None,
    lifespan=lifespan,
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handler to ensure CORS headers are always present
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Custom HTTP exception handler that ensures CORS headers are always present."""
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    
    # Add CORS headers manually for error responses
    origin = request.headers.get("origin")
    if origin and origin in settings.cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    elif "null" in settings.cors_origins:  # Handle file:// protocol
        response.headers["Access-Control-Allow-Origin"] = "null"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response


@app.exception_handler(HTTPException)
async def custom_fastapi_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Custom FastAPI exception handler that ensures CORS headers are always present."""
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    
    # Add CORS headers manually for error responses
    origin = request.headers.get("origin")
    if origin and origin in settings.cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    elif "null" in settings.cors_origins:  # Handle file:// protocol
        response.headers["Access-Control-Allow-Origin"] = "null"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response


@app.exception_handler(ValidationError)
async def custom_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Custom Pydantic validation exception handler that ensures CORS headers are always present."""
    response = JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()}
    )
    
    # Add CORS headers manually for error responses
    origin = request.headers.get("origin")
    if origin and origin in settings.cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    elif "null" in settings.cors_origins:  # Handle file:// protocol
        response.headers["Access-Control-Allow-Origin"] = "null"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response


@app.exception_handler(Exception)
async def custom_general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Custom general exception handler that ensures CORS headers are always present."""
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
    
    # Add CORS headers manually for error responses
    origin = request.headers.get("origin")
    if origin and origin in settings.cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    elif "null" in settings.cors_origins:  # Handle file:// protocol
        response.headers["Access-Control-Allow-Origin"] = "null"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next) -> Response:
    """Add request ID to all requests for tracing."""
    import uuid
    
    request_id = str(uuid.uuid4())
    
    # Add request ID to context for structured logging
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next) -> Response:
    """Log all requests and responses."""
    import time
    
    start_time = time.time()
    
    # Skip logging for health endpoints to reduce noise
    if request.url.path in ["/healthz", "/readyz"]:
        return await call_next(request)
    
    # Log request (redact sensitive data)
    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params),
        client_ip=request.client.host if request.client else "unknown",
    )
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        "Request completed",
        status_code=response.status_code,
        process_time=round(process_time, 4),
    )
    
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle application-specific errors."""
    logger.error(
        "Application error",
        error_code=exc.code,
        error_message=exc.message,
        error_field=exc.field,
        path=request.url.path,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "field": exc.field,
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    logger.error(
        "Unexpected error",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=request.url.path,
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
            }
        },
    )


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(quizzes.router, prefix="/quizzes", tags=["Quizzes"])
app.include_router(hints.router, prefix="/quizzes", tags=["Hints"])
app.include_router(history.router, prefix="/quiz-history", tags=["History"])
app.include_router(adaptive.router, prefix="/quizzes", tags=["Adaptive"])
app.include_router(leaderboard.router, tags=["Leaderboard"])


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "AI Quiz Microservice", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.env == "dev",
        log_config=None,  # Use our custom logging
    )
