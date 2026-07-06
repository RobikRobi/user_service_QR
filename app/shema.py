import datetime
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.enum import UserRole

class LoginUser(BaseModel):
    email: EmailStr
    password: str   
    
class RegisterUser(BaseModel):
    name: str
    surname: str
    email: EmailStr
    password: str
    dob: datetime.date
    role: UserRole

class ShowGroup(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name_group: str
    createdAt: datetime.datetime
    updatedAt: datetime.datetime

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
    
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
