"""User FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_session
from .service import UserService


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserService:
    """Get user service instance."""
    return UserService(session)


# Type alias for clean dependency injection
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
