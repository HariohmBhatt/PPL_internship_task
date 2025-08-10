"""Application-specific error classes."""

from typing import Optional


class AppError(Exception):
    """Base application error."""
    
    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 400,
        field: Optional[str] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.field = field
        super().__init__(message)


class ValidationError(AppError):
    """Validation error."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            field=field,
        )


class AuthenticationError(AppError):
    """Authentication error."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
        )


class AuthorizationError(AppError):
    """Authorization error."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
        )


class NotFoundError(AppError):
    """Resource not found error."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
        )


class ConflictError(AppError):
    """Resource conflict error."""
    
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
        )


class RateLimitError(AppError):
    """Rate limit exceeded error."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
        )


class AIServiceError(AppError):
    """AI service error."""
    
    def __init__(self, message: str = "AI service unavailable"):
        super().__init__(
            message=message,
            code="AI_SERVICE_ERROR",
            status_code=503,
        )
