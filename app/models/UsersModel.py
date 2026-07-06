import typing
import datetime
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.db import Base
from app.enum import UserRole
from app.models.GroupModel import Group
from sqlalchemy import ForeignKey, String

if typing.TYPE_CHECKING:
    from app.models.TokenModel import RefreshToken



class Users(Base):
    __tablename__ = "users_table"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), 
                                          primary_key=True, 
                                          default=uuid.uuid4)
    name: Mapped[str]
    surname: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column(String)
    dob: Mapped[datetime.date]
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), 
                                           default=UserRole.TEACHER)

    createdAt: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), 
                                                         server_default=func.now())
    
    updatedAt: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), 
                                                         server_default=func.now(), 
                                                         onupdate=func.now())

    # Связи
    groups: Mapped[list["Group"]] = relationship(secondary="usersgroups", back_populates="users", uselist=True)

    # Refresh токен
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship("RefreshToken", 
                                                                back_populates="user",
                                                                cascade="all, delete-orphan")

User = Users

class UsersGroups(Base):
    __tablename__ = "usersgroups"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users_table.id"),primary_key=True)
    group_id:Mapped[uuid.UUID] = mapped_column(ForeignKey("group_table.id"),primary_key=True)


# Модель токена восстановления
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users_table.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime.datetime]



