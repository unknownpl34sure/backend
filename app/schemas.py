from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, model_validator
from app.models import KworkStatus, ReviewStatus
from app.s3 import get_file_url
import json


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
    avatar_url: str | None = None
    uuid: str
    created_at: datetime

    @model_validator(mode='after')
    def add_avatar_url(self):
        if self.avatar_id:
            self.avatar_url = get_file_url(self.avatar_id)
        return self

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
    photos: list[str] = []
    tags: list[TagOut] = []
    created_at: datetime

    @model_validator(mode='after')
    def add_photos(self):
        if self.photo_ids:
            try:
                photo_ids = json.loads(self.photo_ids) if isinstance(self.photo_ids, str) else self.photo_ids
                self.photos = [get_file_url(pid) for pid in photo_ids]

            except:
                pass
        return self

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

class PortfolioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    photo_id: str | None
    photo_url: str | None = None
    user_id: int

    @model_validator(mode='after')
    def add_photo_url(self):
        if self.photo_id:
            self.photo_url = get_file_url(self.photo_id)
        return self
