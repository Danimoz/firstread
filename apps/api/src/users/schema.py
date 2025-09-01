import uuid
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserCreate(BaseModel):
  email: EmailStr
  password: str

class UserResponse(BaseModel):
  id: uuid.UUID
  email: EmailStr
  password: str = Field(exclude=True)
  is_active: bool
  created_at: datetime

  class Config:
    from_attributes = True

class Token(BaseModel):
  access_token: str
  token_type: str

class UserRegistrationResponse(BaseModel):
  user: UserResponse
  access_token: str
  token_type: str

class SignoutResponse(BaseModel):
  message: str

class TokenData(BaseModel):
  email: str | None = None