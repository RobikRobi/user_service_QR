import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import send_email
from app.db import get_session
from app.get_current_user import get_current_user
from app.models.UsersModel import User
from app.shema import RegisterUser, ShowUser, UpdateUser
from app.utillits import create_access_token, hash_password


router = APIRouter()

subject = "Регистрация на сайте QRCard"
text = """
Здравствуйте!

Спасибо, что зарегистрировались на нашем сайте.

Теперь Вы можете создавать интерактивные викторины и тесты.

Надеемся, что наш сервис будет полезен Вам в вашей работе
и поможет сделать обучение более интересным и эффективным.

С уважением, администрация сайта QRCard.
"""


@router.post("/register")
async def register_user(
    data: RegisterUser,
    session: AsyncSession = Depends(get_session)
):
    is_user_exists = await session.scalar(select(User).where(User.email == data.email))

    if is_user_exists:
        raise HTTPException(
            status_code=411,
            detail={"status": 411, "data": "user is exists"}
        )

    data_dict = data.model_dump()
    data_dict["password"] = await hash_password(password=data.password)

    user = User(**data_dict)
    session.add(user)
    await session.flush([user])

    user_id = user.id

    await session.commit()
    send_email.delay(user.email, subject, text)

    user_token = create_access_token(user_id=user_id)
    data_dict["token"] = user_token

    return data_dict


@router.get("/me", response_model=ShowUser)
async def me(me=Depends(get_current_user)):
    return me


@router.put("/update", response_model=ShowUser)
async def update_user(
    data: UpdateUser,
    me=Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    await session.refresh(me)
    if data.name:
        me.name = data.name
    if data.surname:
        me.surname = data.surname
    if data.dob:
        me.dob = data.dob
    if data.role:
        me.role = data.role
    if data.groups:
        me.groups = data.groups

    await session.commit()
    await session.refresh(me)

    return me


@router.delete("/delete/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if current_user.role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не имеете прав на удаление пользователя."
        )

    user = await session.scalar(select(User).where(User.id == user_id))

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await session.delete(user)
    await session.commit()

    return {"message": f"User with ID {user_id} has been deleted"}
