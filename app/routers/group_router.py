import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.get_current_user import get_current_user
from app.models.UsersModel import User
from app.schemas.group import CreateGroup, ShowGroup, UpdateGroup
from app.schemas.user import ShowUser
from app.services.group_service import (
    add_user_to_group as add_user_to_group_service,
    create_group as create_group_service,
    delete_group as delete_group_service,
    get_group as get_group_service,
    get_group_users as get_group_users_service,
    get_groups as get_groups_service,
    get_user_groups as get_user_groups_service,
    remove_user_from_group as remove_user_from_group_service,
    update_group_name as update_group_name_service,
)


router = APIRouter()


@router.post("/groups/create", response_model=ShowGroup)
async def create_group(
    data: CreateGroup,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await create_group_service(data, current_user, session)


@router.get("/groups/{group_id}", response_model=ShowGroup)
async def get_group(
    group_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    return await get_group_service(group_id, session)


@router.get("/groups")
async def get_groups(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await get_groups_service(current_user, session)


@router.put("/groups/{group_id}")
async def update_group_name(
    group_id: uuid.UUID,
    data: UpdateGroup,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await update_group_name_service(group_id, data, current_user, session)


@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await delete_group_service(group_id, current_user, session)


@router.post("/groups/{group_id}/add_user/{user_id}")
async def add_user_to_group(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await add_user_to_group_service(group_id, user_id, current_user, session)


@router.get("/users/{user_id}/groups", response_model=list[ShowGroup])
async def get_user_groups(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await get_user_groups_service(current_user, session)


@router.get("/groups/{group_id}/users", response_model=list[ShowUser])
async def get_group_users(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await get_group_users_service(group_id, current_user, session)


@router.delete("/groups/{group_id}/remove_user/{user_id}")
async def remove_user_from_group(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await remove_user_from_group_service(group_id, user_id, current_user, session)
