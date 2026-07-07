import datetime
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.enum import UserRole

# Схема для регистрации пользователя  
class RegisterUser(BaseModel):
    name: str
    surname: str
    email: EmailStr
    password: str
    dob: datetime.date
    role: UserRole

# Схема для входа пользователя
class LoginUser(BaseModel):
    email: EmailStr
    password: str   

# Схема для отображения информации о пользователе
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
    groups: list["ShowGroup"] = Field(default_factory=list)

# Схема для обновления информации о пользователя
class UpdateUser(BaseModel):
    name: str | None
    surname: str | None
    dob: datetime.date | None
    role: UserRole | None
    groups: list[uuid.UUID] | None = Field(default_factory=list)

# Схема для сброса пароля
class PasswordResetRequest(BaseModel):
    email: EmailStr

# Схема для подтверждения сброса пароля
class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

# Схема для создания группы
class CreateGroup(BaseModel):
    name_group: str

# Схема для отображения информации о группе
class ShowGroup(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name_group: str
    createdAt: datetime.datetime
    updatedAt: datetime.datetime

# Схема для создания группы
class UpdateGroup(BaseModel):
    name_group: str
