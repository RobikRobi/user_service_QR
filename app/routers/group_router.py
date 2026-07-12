import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.get_current_user import get_current_user
from app.models.GroupModel import Group
from app.models.UsersModel import User, UsersGroups
from app.shema import CreateGroup, ShowGroup, ShowUser, UpdateGroup


router = APIRouter()


@router.post("/groups/create", response_model=ShowGroup)
async def create_group(
    data: CreateGroup,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if current_user.role.value != "ADMIN" and current_user.role.value != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не имеете прав на создание группы."
        )

    new_group = Group(**data.model_dump(), user_id=current_user.id)
    session.add(new_group)
    await session.commit()
    await session.refresh(new_group)

    return new_group


@router.get("/groups/{group_id}", response_model=ShowGroup)
async def get_group(
    group_id: uuid.UUID,
    session: AsyncSession = Depends(get_session)
):
    group = await session.scalar(select(Group).where(Group.id == group_id))
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    return group


@router.get("/groups")
async def get_groups(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if current_user.role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не имеете прав на просмотр групп."
        )

    profiles = await session.scalars(select(Group))
    return profiles.all()


@router.put("/groups/{group_id}")
async def update_group_name(
    group_id: uuid.UUID,
    data: UpdateGroup,
    session: AsyncSession = Depends(get_session)
):
    group = await session.scalar(select(Group).where(Group.id == group_id))
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group.name_group = data.name_group
    await session.commit()
    await session.refresh(group)

    return {
        "detail": f"Group {group_id} name updated",
        "group": {"id": group.id, "name_group": group.name_group}
    }


@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: uuid.UUID,
    session: AsyncSession = Depends(get_session)
):
    group = await session.scalar(select(Group).where(Group.id == group_id))
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    await session.delete(group)
    await session.commit()

    return {"detail": f"Group {group_id} deleted"}


@router.post("/groups/{group_id}/add_user/{user_id}")
async def add_user_to_group(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if current_user.role.value != "ADMIN" and current_user.role.value != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не имеете прав на добавление пользователя в группу."
        )

    group = await session.scalar(select(Group).where(Group.id == group_id))
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    user = await session.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_user_in_group = await session.scalar(
        select(UsersGroups).where(
            UsersGroups.group_id == group_id,
            UsersGroups.user_id == user_id
        )
    )
    if is_user_in_group:
        raise HTTPException(status_code=409, detail="User already in group")

    session.add(UsersGroups(group_id=group_id, user_id=user_id))
    await session.commit()

    return {"detail": f"User {user_id} added to group {group_id}"}


@router.get("/users/{user_id}/groups", response_model=list[ShowGroup])
async def get_user_groups(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    stmt = select(Group).where(Group.user_id == current_user.id)
    result = await session.execute(stmt)
    groups = result.scalars().all()
    return groups


@router.get("/groups/{group_id}/users", response_model=list[ShowUser])
async def get_group_users(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if current_user.role.value != "ADMIN" and current_user.role.value != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не имеете прав на просмотр пользователей в группе."
        )

    group = await session.scalar(select(Group).where(Group.id == group_id))
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    stmt = (
        select(User)
        .options(selectinload(User.groups))
        .join(UsersGroups)
        .where(UsersGroups.group_id == group_id)
    )
    result = await session.execute(stmt)
    users = result.scalars().all()
    return users


@router.delete("/groups/{group_id}/remove_user/{user_id}")
async def remove_user_from_group(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if current_user.role.value != "ADMIN" and current_user.role.value != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не имеете прав на удаление пользователя из группы."
        )

    group = await session.scalar(select(Group).where(Group.id == group_id))
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    user = await session.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_user_in_group = await session.scalar(
        select(UsersGroups).where(
            UsersGroups.group_id == group_id,
            UsersGroups.user_id == user_id
        )
    )
    if not is_user_in_group:
        raise HTTPException(status_code=404, detail="User not in group")

    await session.delete(is_user_in_group)
    await session.commit()

    return {"detail": f"User {user_id} removed from group {group_id}"}
