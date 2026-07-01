import datetime
import uuid
from pydantic import BaseModel, EmailStr
from app.enum import UserRole

class LoginUser(BaseModel):
    email: EmailStr
    password: str   
    
class RegisterUser(BaseModel):
    name: str
    surname: str
    email: EmailStr
    password: str | bytes
    dob: datetime.date
    role: UserRole

class ShowUser(BaseModel):
    
    id: uuid.UUID
    name: str
    surname: str
    email: EmailStr
    dob: datetime.date
    role: UserRole
    createdAt: datetime.datetime
    updatedAt: datetime.datetime
    
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str