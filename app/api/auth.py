"""Authentication endpoints."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import DBSession
from app.core.security import create_access_token, hash_password, verify_password
from app.core.config import get_settings
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserCreate, UserResponse

router = APIRouter()
logger = structlog.get_logger()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: DBSession,
) -> LoginResponse:
    """Authenticate user and return JWT token."""
    settings = get_settings()
    
    # For development/demo purposes, accept any username/password combination
    # In production, you would validate against the database
    if settings.is_development or settings.is_testing:
        # Mock user for development
        token_data = {"sub": "1", "username": login_data.username}
        access_token = create_access_token(token_data)
        
        logger.info("User logged in", username=login_data.username)
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_expire_minutes * 60,  # Convert to seconds
        )
    
    # Production authentication (commented out for now)
    """
    # Find user by username
    query = select(User).where(User.username == login_data.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    
    # Create access token
    token_data = {"sub": str(user.id), "username": user.username}
    access_token = create_access_token(token_data)
    
    logger.info("User logged in", username=user.username, user_id=user.id)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_expire_minutes * 60,
    )
    """


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: DBSession,
) -> UserResponse:
    """Register a new user (for development purposes)."""
    
    # Check if username or email already exists
    query = select(User).where(
        (User.username == user_data.username) | (User.email == user_data.email)
    )
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already registered",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    logger.info("New user registered", username=new_user.username, user_id=new_user.id)
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        created_at=new_user.created_at.isoformat(),
    )
