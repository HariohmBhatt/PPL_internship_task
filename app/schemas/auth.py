"""Authentication schemas."""

from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema


class LoginRequest(BaseSchema):
    """Login request schema."""
    
    username: str = Field(..., min_length=1, max_length=50, description="Username")
    password: str = Field(..., min_length=1, description="Password")


class LoginResponse(BaseSchema):
    """Login response schema."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class CurrentUser(BaseModel):
    """Current authenticated user."""
    
    id: int
    username: str
    
    class Config:
        from_attributes = True


class UserCreate(BaseSchema):
    """User creation schema."""
    
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Password")


class UserResponse(BaseSchema):
    """User response schema."""
    
    id: int
    username: str
    email: str
    created_at: str
