from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.auth import LoginUser, PasswordResetConfirm, PasswordResetRequest
from app.services.auth_service import (
    confirm_password_reset,
    login_user,
    logout_user,
    refresh_user_token,
    request_password_reset,
)


router = APIRouter()


@router.post("/login")
async def login(
    data: LoginUser,
    session: AsyncSession = Depends(get_session),
):
    return await login_user(data, session)


@router.post("/refresh")
async def refresh(
    refresh_token: str,
    session: AsyncSession = Depends(get_session),
):
    return await refresh_user_token(refresh_token, session)


@router.post("/password-reset")
async def password_reset_request(
    data: PasswordResetRequest,
    session: AsyncSession = Depends(get_session),
):
    return await request_password_reset(data, session)


@router.post("/password-reset/confirm")
async def password_reset_confirm(
    data: PasswordResetConfirm,
    session: AsyncSession = Depends(get_session),
):
    return await confirm_password_reset(data, session)


@router.post("/logout")
async def logout(
    refresh_token: str,
    session: AsyncSession = Depends(get_session),
):
    return await logout_user(refresh_token, session)
