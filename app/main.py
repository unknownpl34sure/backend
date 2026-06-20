from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import engine, Base
import uvicorn
from app import models
from routers import users


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

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )