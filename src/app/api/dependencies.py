"""API dependencies for dependency injection."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User
from app.services.file import FileService
from app.services.session import SessionService
from app.services.user import UserService

# Database dependency
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]


# Service dependencies
def get_user_service(db: DatabaseDep) -> UserService:
    """Get user service instance.

    Args:
        db: Database session

    Returns:
        UserService instance
    """
    return UserService(db)


def get_session_service(db: DatabaseDep) -> SessionService:
    """Get session service instance.

    Args:
        db: Database session

    Returns:
        SessionService instance
    """
    return SessionService(db)


def get_file_service(db: DatabaseDep) -> FileService:
    """Get file service instance.

    Args:
        db: Database session

    Returns:
        FileService instance
    """
    return FileService(db)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
SessionServiceDep = Annotated[SessionService, Depends(get_session_service)]
FileServiceDep = Annotated[FileService, Depends(get_file_service)]


# Authentication dependencies
async def get_current_user(
    authorization: str | None = Header(None),
    user_service: UserServiceDep = None,
) -> User:
    """Get current authenticated user from JWT token.

    Args:
        authorization: Authorization header with Bearer token
        user_service: User service instance

    Returns:
        Current user

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Extract token from "Bearer <token>"
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")

        # Decode token
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Get user from database
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        user = await user_service.get_user(int(user_id))
        return user

    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed") from e


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Get current active user.

    Args:
        current_user: Current user from token

    Returns:
        Current active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """Get current superuser.

    Args:
        current_user: Current active user

    Returns:
        Current superuser

    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user


# Optional authentication (for endpoints that work with or without auth)
async def get_current_user_optional(
    authorization: str | None = Header(None),
    user_service: UserServiceDep = None,
) -> User | None:
    """Get current user if authenticated, None otherwise.

    Args:
        authorization: Authorization header with Bearer token
        user_service: User service instance

    Returns:
        Current user or None
    """
    if not authorization:
        return None

    try:
        return await get_current_user(authorization, user_service)
    except HTTPException:
        return None


CurrentUserDep = Annotated[User, Depends(get_current_active_user)]
CurrentSuperuserDep = Annotated[User, Depends(get_current_superuser)]
CurrentUserOptionalDep = Annotated[User | None, Depends(get_current_user_optional)]
