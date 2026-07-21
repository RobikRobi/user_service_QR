import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api_response import success_response
from app.models.GroupModel import Group
from app.models.UsersModel import User, UsersGroups
from app.schemas.group import CreateGroup, UpdateGroup


def _ensure_admin(user: User, detail: str) -> None:
    if user.role.value != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _ensure_admin_or_teacher(user: User, detail: str) -> None:
    if user.role.value != "ADMIN" and user.role.value != "TEACHER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _ensure_group_owner_or_admin(user: User, group: Group, detail: str) -> None:
    if user.role.value != "ADMIN" and group.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


async def create_group(data: CreateGroup, current_user: User, session: AsyncSession) -> Group:
    _ensure_admin_or_teacher(
        current_user,
        "You do not have permission to create a group.",
    )

    new_group = Group(**data.model_dump(), user_id=current_user.id)
    session.add(new_group)
    await session.commit()
    await session.refresh(new_group)

    return new_group


async def get_group(group_id: uuid.UUID, session: AsyncSession) -> Group:
    group = await session.scalar(select(Group).where(Group.id == group_id))
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    return group


async def get_groups(current_user: User, session: AsyncSession) -> list[Group]:
    _ensure_admin(
        current_user,
        "You do not have permission to view groups.",
    )

    groups = await session.scalars(select(Group))
    return list(groups.all())


async def update_group_name(
    group_id: uuid.UUID,
    data: UpdateGroup,
    current_user: User,
    session: AsyncSession,
) -> dict:
    group = await get_group(group_id, session)
    _ensure_group_owner_or_admin(
        current_user,
        group,
        "You do not have permission to update this group.",
    )

    group.name_group = data.name_group
    await session.commit()
    await session.refresh(group)

    return success_response(
        "Group updated",
        {"group": {"id": group.id, "name_group": group.name_group}},
    )


async def delete_group(group_id: uuid.UUID, current_user: User, session: AsyncSession) -> dict:
    group = await get_group(group_id, session)
    _ensure_group_owner_or_admin(
        current_user,
        group,
        "You do not have permission to delete this group.",
    )

    await session.delete(group)
    await session.commit()

    return success_response("Group deleted", {"group_id": group_id})


async def add_user_to_group(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User,
    session: AsyncSession,
) -> dict:
    _ensure_admin_or_teacher(
        current_user,
        "You do not have permission to add users to this group.",
    )

    await _get_user_and_group(group_id, user_id, session)

    is_user_in_group = await session.scalar(
        select(UsersGroups).where(
            UsersGroups.group_id == group_id,
            UsersGroups.user_id == user_id,
        )
    )
    if is_user_in_group:
        raise HTTPException(status_code=409, detail="User already in group")

    session.add(UsersGroups(group_id=group_id, user_id=user_id))
    await session.commit()

    return success_response(
        "User added to group",
        {"group_id": group_id, "user_id": user_id},
    )


async def get_user_groups(current_user: User, session: AsyncSession) -> list[Group]:
    stmt = select(Group).where(Group.user_id == current_user.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_group_users(group_id: uuid.UUID, current_user: User, session: AsyncSession) -> list[User]:
    _ensure_admin_or_teacher(
        current_user,
        "You do not have permission to view users in this group.",
    )

    await get_group(group_id, session)

    stmt = (
        select(User)
        .options(selectinload(User.groups))
        .join(UsersGroups)
        .where(UsersGroups.group_id == group_id)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def remove_user_from_group(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User,
    session: AsyncSession,
) -> dict:
    _ensure_admin_or_teacher(
        current_user,
        "You do not have permission to remove users from this group.",
    )

    await _get_user_and_group(group_id, user_id, session)

    is_user_in_group = await session.scalar(
        select(UsersGroups).where(
            UsersGroups.group_id == group_id,
            UsersGroups.user_id == user_id,
        )
    )
    if not is_user_in_group:
        raise HTTPException(status_code=404, detail="User not in group")

    await session.delete(is_user_in_group)
    await session.commit()

    return success_response(
        "User removed from group",
        {"group_id": group_id, "user_id": user_id},
    )


async def _get_user_and_group(group_id: uuid.UUID, user_id: uuid.UUID, session: AsyncSession) -> tuple[Group, User]:
    group = await session.scalar(select(Group).where(Group.id == group_id))
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    user = await session.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return group, user
