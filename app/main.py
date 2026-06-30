from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from app.database import engine, Base
import uvicorn
from app import models
from routers import users, kworks, chats, messages, reviews, skills, portfolio, files
from app.s3 import create_bucket_if_not_exists


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Запуск сервера...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Лёгкая миграция: добавляем колонку вложения, если её ещё нет,
        # и разрешаем пустой текст (сообщение может быть только с картинкой)
        await conn.execute(
            text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS image_id VARCHAR(255)")
        )
        await conn.execute(
            text("ALTER TABLE messages ALTER COLUMN text DROP NOT NULL")
        )
        await conn.execute(
            text("ALTER TABLE users ADD COLUMN IF NOT EXISTS banner_id VARCHAR(255)")
        )
        await conn.execute(
            text("ALTER TABLE users ADD COLUMN IF NOT EXISTS balance INTEGER NOT NULL DEFAULT 0")
        )

    await create_bucket_if_not_exists()

    print("Таблицы созданы (или уже существуют)")
    yield
    print("Остановка сервера...")
    await engine.dispose()
    print("Подключение к БД закрыто")

app = FastAPI(
    title="Freelance Exchange API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://frontend-production-fe5d.up.railway.app",  # ← Добавьте домен Railway
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|.*\.up\.railway\.app):\d*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Freelance Exchange API is running!"}

app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(kworks.router, prefix="/api/kworks", tags=["Kworks"])
app.include_router(chats.router, prefix="/api/chats", tags=["Chats"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["Reviews"])
app.include_router(skills.router, prefix="/api/skills", tags=["Skills"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )