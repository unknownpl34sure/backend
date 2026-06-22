import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from app import models
from app.schemas import UserCreate, KworkCreate, ReviewCreate, PortfolioCreate, UserUpdate
from app.hashing import get_password_hash, generate_salt

async def create_user(db: AsyncSession, user_data: UserCreate):
    salt = generate_salt()
    hashed_password = get_password_hash(user_data.password, salt)

    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        name=user_data.name,
        phone=user_data.phone,
        description=user_data.description,
        specialization=user_data.specialization,
        password_hash=hashed_password,
        password_salt=salt,
        uuid=str(uuid.uuid4()),
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(
        db: AsyncSession,
        user_id: int,
        user_data: UserUpdate
):
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    update_dict = user_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user

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

async def create_kwork(db: AsyncSession, kwork_data: KworkCreate, user_id: int):
    photo_ids_str = ",".join(kwork_data.photo_ids) if kwork_data.photo_ids else None

    db_kwork = models.Kwork(
        title=kwork_data.title,
        description=kwork_data.description,
        price=kwork_data.price,
        photo_ids=photo_ids_str,
        user_id=user_id,
        status=models.KworkStatus.NOT_COMPLETED
    )
    db.add(db_kwork)
    await db.flush()

    for tag_id in kwork_data.tag_ids:
        tag = await db.get(models.Tag, tag_id)
        if tag:
            db.add(models.kwork_tag(kwork_id=db_kwork.id, tag_id=tag.id))

    await db.commit()
    await db.refresh(db_kwork)
    return db_kwork

async def get_kworks(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(models.Kwork)
        .options(selectinload(models.Kwork.tags))
        .offset(skip)
        .limit(limit)
        .order_by(models.Kwork.created_at.desc())
    )
    return result.scalars().all()

async def get_kwork_by_id(db: AsyncSession, kwork_id: int):
    result = await db.execute(
        select(models.Kwork)
        .options(selectinload(models.Kwork.tags))
        .where(models.Kwork.id == kwork_id)
    )
    return result.scalar_one_or_none()

async def update_kwork_status(
        db: AsyncSession,
        kwork_id: int,
        status: models.KworkStatus,
        client_id: int | None = None
):
    kwork = await get_kwork_by_id(db, kwork_id)
    if not kwork:
        return None

    kwork.status = status
    if client_id is not None:
        kwork.client_id = client_id
        await create_chat(db, kwork.user_id, client_id, kwork_id)

    await db.commit()
    await db.refresh(kwork)
    return kwork

async def create_chat(
        db: AsyncSession,
        initiator_id: int,
        receiver_id: int,
        kwork_id: int | None = None
):
    existing = await db.execute(
        select(models.Chat).where(models.Chat.kwork_id == kwork_id)
    )
    if existing.scalar_one_or_none():
        return existing.scalar_one_or_none()

    chat = models.Chat(
        initiator_id=initiator_id,
        receiver_id=receiver_id,
        kwork_id=kwork_id
    )
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat

async def get_user_chats(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(models.Chat)
        .where(
            (models.Chat.initiator_id == user_id) | (models.Chat.receiver_id == user_id)
        )
        .order_by(desc(models.Chat.created_at))
    )
    return result.scalars().all()

async def get_chat_by_id(db: AsyncSession, chat_id: int):
    result = await db.execute(
        select(models.Chat)
        .options(selectinload(models.Chat.messages))
        .where(models.Chat.id == chat_id)
    )
    return result.scalar_one_or_none()

async def create_message(
    db: AsyncSession,
    chat_id: int,
    sender_id: int,
    text: str
):
    db_message = models.Message(
        chat_id=chat_id,
        sender_id=sender_id,
        text=text
    )
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message

async def get_chat_messages(db: AsyncSession, chat_id: int, limit: int = 50):
    result = await db.execute(
        select(models.Message)
        .where(models.Message.chat_id == chat_id)
        .order_by(desc(models.Message.created_at))
        .limit(limit)
    )
    return result.scalars().all()

async def create_review(
        db: AsyncSession,
        review_data: ReviewCreate,
        author_id: int
):
    db_review = models.Review(
        author_id=author_id,
        target_id=review_data.target_id,
        text=review_data.text,
        status=review_data.status
    )
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    return db_review

async def get_reviews_for_user(
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100
):
    result = await db.execute(
        select(models.Review)
        .where(models.Review.target_id == user_id)
        .order_by(desc(models.Review.created_at))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_user_reviews(
        db: AsyncSession,
        author_id: int,
        skip: int = 0,
        limit: int = 100
):
    result = await db.execute(
        select(models.Review)
        .where(models.Review.author_id == author_id)
        .order_by(desc(models.Review.created_at))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_review_by_id(db: AsyncSession, review_id: int):
    return await db.get(models.Review, review_id)

async def get_user_rating_stats(db: AsyncSession, user_id: int):
    total_result = await db.execute(
        select(func.count(models.Review.id))
        .where(models.Review.target_id == user_id)
    )
    total = total_result.scalar() or 0

    if total == 0:
        return {"total": 0, "positive": 0, "negative": 0, "rating_percent": 0}

    positive_result = await db.execute(
        select(func.count(models.Review.id))
        .where(models.Review.target_id == user_id)
        .where(models.Review.status == "POSITIVE")
    )
    positive = positive_result.scalar() or 0

    negative = total - positive

    return {
        "total": total,
        "positive": positive,
        "negative": negative,
        "rating_percent": round((positive / total) * 100, 1)
    }

async def create_skill(db: AsyncSession, name: str):
    db_skill = models.Skill(name=name)
    db.add(db_skill)
    await db.commit()
    await db.refresh(db_skill)
    return db_skill

async def get_skill_by_name(db: AsyncSession, name: str):
    result = await db.execute(
        select(models.Skill).where(models.Skill.name == name)
    )
    return result.scalar_one_or_none()

async def get_all_skills(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(models.Skill).offset(skip).limit(limit).order_by(models.Skill.name)
    )
    return result.scalars().all()

async def get_user_skills(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(models.Skill)
        .join(models.user_skill, models.Skill.id == models.user_skill.c.skill_id)
        .where(models.user_skill.c.user_id == user_id)
        .order_by(models.Skill.name)
    )
    return result.scalars().all()

async def add_skills_to_user(db: AsyncSession, user_id: int, skill_ids: list[int]):
    for skill_id in skill_ids:
        result = await db.execute(
            models.user_skill.select().where(
                models.user_skill.c.user_id == user_id,
                models.user_skill.c.skill_id == skill_id
            )
        )
        if not result.first():
            await db.execute(
                models.user_skill.insert().values(user_id=user_id, skill_id=skill_id)
            )
    await db.commit()

async def remove_skill_from_user(db: AsyncSession, user_id: int, skill_id: int):
    result = await db.execute(
        models.user_skill.delete().where(
            models.user_skill.c.user_id == user_id,
            models.user_skill.c.skill_id == skill_id
        )
    )
    await db.commit()
    return result.rowcount > 0

async def delete_skill(db: AsyncSession, skill_id: int):
    skill = await db.get(models.Skill, skill_id)
    if not skill:
        return False
    await db.delete(skill)
    await db.commit()
    return True

async def create_portfolio(
    db: AsyncSession,
    portfolio_data: PortfolioCreate,
    user_id: int
):
    db_portfolio = models.Portfolio(
        title=portfolio_data.title,
        photo_id=portfolio_data.photo_id,
        user_id=user_id
    )
    db.add(db_portfolio)
    await db.commit()
    await db.refresh(db_portfolio)
    return db_portfolio

async def get_user_portfolio(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 100
):
    result = await db.execute(
        select(models.Portfolio)
        .where(models.Portfolio.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_portfolio_by_id(db: AsyncSession, portfolio_id: int):
    return await db.get(models.Portfolio, portfolio_id)

async def delete_portfolio(db: AsyncSession, portfolio_id: int):
    portfolio = await get_portfolio_by_id(db, portfolio_id)
    if not portfolio:
        return False
    await db.delete(portfolio)
    await db.commit()
    return True