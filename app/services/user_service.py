import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_response import success_response
from app.celery_app import send_email
from app.email_templates import REGISTER_SUBJECT, REGISTER_TEXT
from app.models.UsersModel import User
from app.schemas.user import RegisterUser, UpdateUser
from app.utillits import create_access_token, hash_password


async def register_user(data: RegisterUser, session: AsyncSession) -> dict:
    is_user_exists = await session.scalar(select(User).where(User.email == data.email))

    if is_user_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    data_dict = data.model_dump()
    data_dict["password"] = await hash_password(password=data.password)

    user = User(**data_dict)
    session.add(user)
    await session.flush([user])

    user_id = user.id

    await session.commit()
    send_email.delay(user.email, REGISTER_SUBJECT, REGISTER_TEXT)

    user_token = create_access_token(user_id=user_id)

    return success_response(
        "User registered successfully",
        {
            "id": user_id,
            "name": user.name,
            "surname": user.surname,
            "email": user.email,
            "dob": user.dob,
            "role": user.role,
            "token": user_token,
        },
    )


async def update_user(data: UpdateUser, user: User, session: AsyncSession) -> User:
    await session.refresh(user)
    if data.name:
        user.name = data.name
    if data.surname:
        user.surname = data.surname
    if data.dob:
        user.dob = data.dob
    if data.role:
        user.role = data.role
    if data.groups:
        user.groups = data.groups

    await session.commit()
    await session.refresh(user)

    return user


async def delete_user(user_id: uuid.UUID, current_user: User, session: AsyncSession) -> dict:
    if current_user.role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete users.",
        )

    user = await session.scalar(select(User).where(User.id == user_id))

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await session.delete(user)
    await session.commit()

    return success_response("User deleted", {"user_id": user_id})
