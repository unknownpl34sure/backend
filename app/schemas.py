from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from app.models import KworkStatus, ReviewStatus

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

class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str

class KworkCreate(BaseModel):
    title: str
    description: str | None = None
    price: int
    tag_ids: list[int] = []
    photo_ids: list[str] = []

class KworkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    price: int
    status: KworkStatus
    user_id: int
    client_id: int | None = None
    photo_ids: str | None = None
    tags: list[TagOut] = []
    created_at: datetime

class KworkCreatedResponse(BaseModel):
    id: int

class KworkStatusUpdate(BaseModel):
    status: KworkStatus
    client_id: int | None = None

class ChatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    initiator_id: int
    receiver_id: int
    kwork_id: int | None
    created_at: datetime
    messages: list["MessageOut"] = []

class ChatListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    initiator_id: int
    receiver_id: int
    kwork_id: int | None
    created_at: datetime
    last_message: str | None


class MessageCreate(BaseModel):
    text: str

class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chat_id: int
    sender_id: int
    text: str
    created_at: datetime

class ReviewCreate(BaseModel):
    target_id: int
    text: str
    status: ReviewStatus

class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: int
    target_id: int
    text: str
    status: ReviewStatus
    created_at: datetime

class SkillCreate(BaseModel):
    name: str

class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str

class UserSkillAdd(BaseModel):
    skill_ids: list[int]

class PortfolioCreate(BaseModel):
    title: str
    description: str | None = None
    photo_id: str | None = None

class PortfolioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    photo_id: str | None
    user_id: int
