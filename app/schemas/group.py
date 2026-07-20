import datetime
import uuid

from pydantic import BaseModel, ConfigDict


class CreateGroup(BaseModel):
    name_group: str


class ShowGroup(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name_group: str
    user_id: uuid.UUID
    createdAt: datetime.datetime
    updatedAt: datetime.datetime


class UpdateGroup(BaseModel):
    name_group: str

