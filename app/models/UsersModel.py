import typing
import datetime
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.db import Base
from app.enum import UserRole
from sqlalchemy import ForeignKey

if typing.TYPE_CHECKING:
    from app.models.GroupModel import Group



class Users(Base):
    __tablename__ = "users_table"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), 
                                          primary_key=True, 
                                          default=uuid.uuid4)
    name: Mapped[str]
    surname: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[bytes]
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), 
                                           default=UserRole.TEACHER)

    createdAt: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), 
                                                         server_default=func.now())
    
    updatedAt: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), 
                                                         server_default=func.now(), 
                                                         onupdate=func.now())

    # Связи
    groups: Mapped[list["Group"]] = relationship(secondary="usersgroups", back_populates="users", uselist=True)

class UsersGroups(Base):
    __tablename__ = "usersgroups"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_table.id"),primary_key=True)
    group_id:Mapped[uuid.UUID] = mapped_column(ForeignKey("group_table.id"),primary_key=True)




