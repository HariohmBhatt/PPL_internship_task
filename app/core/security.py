"""Security utilities for JWT authentication."""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
import bcrypt

from app.core.config import get_settings
from app.core.errors import AuthenticationError

# Simple bcrypt implementation
def _hash_password_bcrypt(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def _verify_password_bcrypt(password: str, hashed: str) -> bool:
    """Verify password using bcrypt."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(data: dict[str, Any]) -> str:
    """Create a JWT access token."""
    settings = get_settings()
    
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret, 
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> dict[str, Any]:
    """Verify and decode a JWT token."""
    settings = get_settings()
    
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret, 
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return _hash_password_bcrypt(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return _verify_password_bcrypt(plain_password, hashed_password)


def extract_bearer_token(authorization: str) -> str:
    """Extract token from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization header format")
    
    return authorization.split(" ", 1)[1]
