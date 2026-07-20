import datetime
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.enum import UserRole
from app.schemas.group import ShowGroup


class RegisterUser(BaseModel):
    name: str
    surname: str
    email: EmailStr
    password: str
    dob: datetime.date
    role: UserRole


class ShowUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    surname: str
    email: EmailStr
    dob: datetime.date
    role: UserRole
    createdAt: datetime.datetime
    updatedAt: datetime.datetime
    groups: list[ShowGroup] = Field(default_factory=list)


class UpdateUser(BaseModel):
    name: str | None
    surname: str | None
    dob: datetime.date | None
    role: UserRole | None
    groups: list[uuid.UUID] | None = Field(default_factory=list)

