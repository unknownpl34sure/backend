from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import engine, Base
import uvicorn
from app import models
from routers import users, kworks, chats, messages, reviews, skills, portfolio


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Запуск сервера...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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

@app.get("/")
async def root():
    return {"message": "Freelance Exchange API is running!"}

@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "pong"}

app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(kworks.router, prefix="/api/kworks", tags=["Kworks"])
app.include_router(chats.router, prefix="/api/chats", tags=["Chats"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["Reviews"])
app.include_router(skills.router, prefix="/api/skills", tags=["Skills"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )