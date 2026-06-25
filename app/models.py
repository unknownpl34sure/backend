import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    Integer,
    Enum,
    DateTime,
    Table,
    Column,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ReviewStatus(PyEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"

class KworkStatus(PyEnum):
    NOT_COMPLETED = "not_completed"
    IN_PROCESS = "in_process"
    COMPLETED = "completed"

class TransactionType(PyEnum):
    TOPUP = "topup"       # пополнение баланса (заглушка оплаты)
    PAYMENT = "payment"   # списание у заказчика за выполненный заказ
    EARNING = "earning"   # зачисление исполнителю за выполненную работу

user_skill = Table(
    "user_skill",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

kwork_tag = Table(
    "kwork_tag",
    Base.metadata,
    Column("kwork_id", ForeignKey("kwork.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    specialization: Mapped[str] = mapped_column(String(150), nullable=True)
    avatar_id: Mapped[str] = mapped_column(String(255), nullable=True)
    banner_id: Mapped[str] = mapped_column(String(255), nullable=True)
    balance: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    password_hash: Mapped[str] = mapped_column(String(255))
    password_salt: Mapped[str] = mapped_column(String(255))
    uuid: Mapped[str] = mapped_column(
        String(36), unique=True, default=lambda: str(uuid.uuid4())
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    skills: Mapped[list["Skill"]] = relationship(
        secondary=user_skill, back_populates="users"
    )

    portfolio: Mapped[list["Portfolio"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    kworks_as_performer: Mapped[list["Kwork"]] = relationship(
        back_populates="performer",
        foreign_keys="Kwork.user_id",
    )

    kworks_as_client: Mapped[list["Kwork"]] = relationship(
        back_populates="client",
        foreign_keys="Kwork.client_id",
    )

    reviews_written: Mapped[list["Review"]] = relationship(
        back_populates="author",
        foreign_keys="Review.author_id",
    )

    reviews_received: Mapped[list["Review"]] = relationship(
        back_populates="target",
        foreign_keys="Review.target_id",
    )

    chats_initiated: Mapped[list["Chat"]] = relationship(
        back_populates="initiator",
        foreign_keys="Chat.initiator_id",
    )

    chats_received: Mapped[list["Chat"]] = relationship(
        back_populates="receiver",
        foreign_keys="Chat.receiver_id",
    )

    messages_sent: Mapped[list["Message"]] = relationship(back_populates="sender")

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"

class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    users: Mapped[list["User"]] = relationship(
        secondary=user_skill, back_populates="skills"
    )

    def __repr__(self) -> str:
        return f"<Skill id={self.id} name={self.name!r}>"

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    target_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, native_enum=False)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    author: Mapped["User"] = relationship(
        back_populates="reviews_written", foreign_keys=[author_id]
    )
    target: Mapped["User"] = relationship(
        back_populates="reviews_received", foreign_keys=[target_id]
    )

    def __repr__(self) -> str:
        return f"<Review id={self.id} {self.author_id}->{self.target_id}>"

class Portfolio(Base):
    __tablename__ = "portfolio"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    photo_id: Mapped[str] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(back_populates="portfolio")

    def __repr__(self) -> str:
        return f"<Portfolio id={self.id} title={self.title!r}>"

class Kwork(Base):
    __tablename__ = "kwork"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    photo_ids: Mapped[str] = mapped_column(Text, nullable=True)  # JSON-encoded list
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, default=None
    )
    price: Mapped[int] = mapped_column(Integer)
    status: Mapped[KworkStatus] = mapped_column(
        Enum(KworkStatus, native_enum=False), default=KworkStatus.NOT_COMPLETED
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    performer: Mapped["User"] = relationship(
        back_populates="kworks_as_performer", foreign_keys=[user_id]
    )
    client: Mapped["User | None"] = relationship(
        back_populates="kworks_as_client", foreign_keys=[client_id]
    )

    tags: Mapped[list["Tag"]] = relationship(
        secondary=kwork_tag, back_populates="kworks"
    )

    chats: Mapped[list["Chat"]] = relationship(back_populates="kwork")

    def __repr__(self) -> str:
        return f"<Kwork id={self.id} title={self.title!r} status={self.status}>"

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    kworks: Mapped[list["Kwork"]] = relationship(
        secondary=kwork_tag, back_populates="tags"
    )

    def __repr__(self) -> str:
        return f"<Tag id={self.id} name={self.name!r}>"

class Chat(Base):
    __tablename__ = "chat"

    id: Mapped[int] = mapped_column(primary_key=True)
    initiator_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kwork_id: Mapped[int | None] = mapped_column(
        ForeignKey("kwork.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    initiator: Mapped["User"] = relationship(
        back_populates="chats_initiated", foreign_keys=[initiator_id]
    )
    receiver: Mapped["User"] = relationship(
        back_populates="chats_received", foreign_keys=[receiver_id]
    )
    kwork: Mapped["Kwork | None"] = relationship(back_populates="chats")

    messages: Mapped[list["Message"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Chat id={self.id} {self.initiator_id}<->{self.receiver_id}>"

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chat.id", ondelete="CASCADE"))
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text, nullable=True)
    image_id: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    chat: Mapped["Chat"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship(back_populates="messages_sent")

    @property
    def image_url(self) -> str | None:
        from app.s3 import get_file_url

        return get_file_url(self.image_id) if self.image_id else None

    def __repr__(self) -> str:
        return f"<Message id={self.id} chat_id={self.chat_id}>"

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # Сумма со знаком: > 0 — зачисление, < 0 — списание
    amount: Mapped[int] = mapped_column(Integer)
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, native_enum=False)
    )
    kwork_id: Mapped[int | None] = mapped_column(
        ForeignKey("kwork.id", ondelete="SET NULL"), nullable=True, default=None
    )
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship()
    kwork: Mapped["Kwork | None"] = relationship()

    def __repr__(self) -> str:
        return f"<Transaction id={self.id} user_id={self.user_id} amount={self.amount}>"
