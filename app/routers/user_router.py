import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.get_current_user import get_current_user
from app.models.UsersModel import User
from app.schemas.user import RegisterUser, ShowUser, UpdateUser
from app.services.user_service import delete_user as delete_user_service
from app.services.user_service import register_user as register_user_service
from app.services.user_service import update_user as update_user_service


router = APIRouter()


@router.post("/register")
async def register_user(
    data: RegisterUser,
    session: AsyncSession = Depends(get_session),
):
    return await register_user_service(data, session)


@router.get("/me", response_model=ShowUser)
async def me(me=Depends(get_current_user)):
    return me


@router.put("/update", response_model=ShowUser)
async def update_user(
    data: UpdateUser,
    me=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await update_user_service(data, me, session)


@router.delete("/delete/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await delete_user_service(user_id, current_user, session)
