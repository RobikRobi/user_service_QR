import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_response import success_response
from app.celery_app import send_email
from app.config import config
from app.models.TokenModel import RefreshToken
from app.models.UsersModel import PasswordResetToken, User
from app.schemas.auth import LoginUser, PasswordResetConfirm, PasswordResetRequest
from app.utillits import (
    check_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    hash_refresh_token,
)


async def login_user(data: LoginUser, session: AsyncSession) -> dict:
    stmt = select(User).where(User.email == data.email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not await check_password(user.password, data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    refresh_db = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=datetime.utcnow() + timedelta(days=config.auth_data.days),
    )
    session.add(refresh_db)
    await session.commit()

    return success_response(
        "Login successful",
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        },
    )


async def refresh_user_token(refresh_token: str, session: AsyncSession) -> dict:
    payload = decode_refresh_token(refresh_token)
    token_hash = hash_refresh_token(refresh_token)

    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False,
    )
    result = await session.execute(stmt)
    token_db = result.scalar_one_or_none()

    if not token_db:
        raise HTTPException(status_code=401, detail="Token revoked")

    token_db.revoked = True

    user_id = uuid.UUID(payload["sub"])
    new_access = create_access_token(user_id)
    new_refresh = create_refresh_token(user_id)

    session.add(
        RefreshToken(
            user_id=user_id,
            token_hash=hash_refresh_token(new_refresh),
            expires_at=datetime.utcnow() + timedelta(days=config.auth_data.days),
        )
    )

    await session.commit()

    return success_response(
        "Token refreshed",
        {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
        },
    )


async def request_password_reset(data: PasswordResetRequest, session: AsyncSession) -> dict:
    user = await session.scalar(select(User).where(User.email == data.email))

    if not user:
        return success_response("Password reset request accepted")

    token = str(uuid.uuid4())
    reset_token = PasswordResetToken(
        token=token,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(minutes=30),
    )

    session.add(reset_token)
    await session.commit()

    reset_link = f"https://your-frontend/reset-password?token={token}"

    send_email.delay(
        user.email,
        "Восстановление пароля",
        f"Перейдите по ссылке для восстановления пароля:\n{reset_link}",
    )

    return success_response("Password reset request accepted")


async def confirm_password_reset(data: PasswordResetConfirm, session: AsyncSession) -> dict:
    token_obj = await session.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token == data.token)
    )

    if not token_obj or token_obj.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = await session.get(User, token_obj.user_id)
    user.password = await hash_password(data.new_password)

    await session.execute(
        delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
    )
    await session.commit()

    return success_response("Password updated")


async def logout_user(refresh_token: str, session: AsyncSession) -> dict:
    token_hash = hash_refresh_token(refresh_token)

    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False,
    )
    result = await session.execute(stmt)
    token_db = result.scalar_one_or_none()

    if not token_db:
        raise HTTPException(status_code=401, detail="Invalid token")

    token_db.revoked = True
    await session.commit()

    return success_response("Logged out successfully")
