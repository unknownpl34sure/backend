from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    username: str
    phone: str | None
    email: str
    description: str | None
    specialization: str | None
    avatar_id: str | None
    uuid: str
    created_at: datetime
    #skills: list[SkillOut] = []


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    name: str
    phone: str | None = None
    description: str | None = None
    specialization: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    description: str | None = None
    specialization: str | None = None
    avatar_id: str | None = None


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None