"""FastAPI dependency providers."""

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AuthenticationError
from app.core.security import extract_bearer_token, verify_token
from app.db.session import get_db_session
from app.schemas.auth import CurrentUser


async def get_current_user(
    authorization: Annotated[str, Header()],
) -> CurrentUser:
    """Get current authenticated user from JWT token."""
    try:
        token = extract_bearer_token(authorization)
        payload = verify_token(token)
        
        user_id = payload.get("sub")
        username = payload.get("username")
        
        if not user_id or not username:
            raise AuthenticationError("Invalid token payload")
        
        return CurrentUser(id=int(user_id), username=username)
    
    except (ValueError, KeyError) as e:
        raise AuthenticationError("Invalid token") from e


# Type annotations for common dependencies
DBSession = Annotated[AsyncSession, Depends(get_db_session)]
AuthUser = Annotated[CurrentUser, Depends(get_current_user)]
