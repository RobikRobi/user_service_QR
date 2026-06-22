import datetime
import typing
import uuid

from app.db import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID


if typing.TYPE_CHECKING:
    from app.models.UsersModel import Users, UsersGroups




class Group(Base):
    __tablename__ = "group_table"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), 
                                          primary_key=True, 
                                          default=uuid.uuid4)

    name_group: Mapped[str]
    createdAt: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), 
                                                         server_default=func.now())
    
    updatedAt: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), 
                                                         server_default=func.now(), 
                                                         onupdate=func.now())

    # Связи
    users: Mapped[list["Users"]] = relationship(secondary="usersgroups", back_populates="groups", uselist=True)