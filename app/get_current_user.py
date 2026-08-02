import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models.UsersModel import User
from app.utillits import verify_access_token

bearer = HTTPBearer(auto_error=True)
TokenDep = Annotated[HTTPAuthorizationCredentials, Depends(bearer)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_id(token: TokenDep) -> uuid.UUID:
    return await verify_access_token(token.credentials)


UserIdDep = Annotated[uuid.UUID, Depends(get_current_id)]


async def get_current_user(
    user_id: UserIdDep,
    session: SessionDep,
) -> User:
    user = await session.scalar(
        select(User).options(selectinload(User.groups)).where(User.id == user_id)
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if hasattr(user, "is_active") and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return user

