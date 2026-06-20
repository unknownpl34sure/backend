import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app import models
from app.schemas import UserCreate
from app.hashing import get_password_hash

async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(
        select(models.User).where(models.User.username == username)
    )
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(
        select(models.User).where(models.User.email == email)
    )
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_data: UserCreate):
    hashed_password = get_password_hash(user_data.password)
    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        name=user_data.name,
        phone=user_data.phone,
        description=user_data.description,
        specialization=user_data.specialization,
        password_hash=hashed_password,
        password_salt="",
        uuid=str(uuid.uuid4()),
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user