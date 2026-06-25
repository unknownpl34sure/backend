# Studwork — бэкенд

REST + WebSocket API для биржи фриланса для студентов. Написан на **FastAPI**
(async), с PostgreSQL в качестве БД и MinIO (S3-совместимое хранилище) для
файлов. Фронтенд лежит в папке [`../frontend`](../frontend).

## Стек

- **Python 3.10** + **FastAPI** / **Starlette**
- **SQLAlchemy 2.0** (async, `asyncpg`) — ORM, таблицы создаются автоматически
- **PostgreSQL 16**
- **MinIO** (S3) через `aioboto3` / `boto3` — хранение картинок
- **python-jose** + **bcrypt/passlib** — JWT-аутентификация и хеширование паролей
- **WebSocket** — живой чат
- **Docker Compose** — сборка всего окружения

## Быстрый старт (Docker)

Это рекомендуемый способ — поднимает API, PostgreSQL и MinIO одной командой.

```bash
cp .env.example .env   # при необходимости поправьте секреты/пароли
docker compose up --build
```

После запуска доступны:

- API — `http://localhost:8000`
- Swagger UI (документация) — `http://localhost:8000/docs`
- ReDoc — `http://localhost:8000/redoc`
- MinIO консоль — `http://localhost:9001` (логин/пароль из `.env`)

Таблицы в БД и бакет в MinIO создаются автоматически при старте приложения
(см. `lifespan` в `app/main.py`).

### Тестовые данные

Скрипт `seed.py` наполняет базу пользователями, навыками, объявлениями,
портфолио, отзывами и чатами:

```bash
docker compose exec server python seed.py
```

Все тестовые пользователи создаются с паролем `password123`.

## Локальный запуск (без Docker)

Нужны запущенные PostgreSQL и MinIO (или другой S3), а `DATABASE_URL` /
`S3_*` в `.env` должны указывать на них.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Переменные окружения

Все настройки берутся из `.env` (см. `.env.example`):

| Переменная                     | Назначение                                   |
| ------------------------------ | -------------------------------------------- |
| `POSTGRES_USER` / `_PASSWORD` / `_DB` | Параметры контейнера PostgreSQL       |
| `DATABASE_URL`                 | Строка подключения (`postgresql+asyncpg://`) |
| `SECRET_KEY`                   | Секрет для подписи JWT                        |
| `ALGORITHM`                    | Алгоритм JWT (по умолчанию `HS256`)          |
| `ACCESS_TOKEN_EXPIRE_MINUTES`  | Время жизни токена                            |
| `S3_ENDPOINT_URL`              | Адрес MinIO/S3                                |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | Доступы к S3                               |
| `S3_BUCKET_NAME`               | Имя бакета                                    |
| `S3_PUBLIC_URL`                | Базовый публичный URL для отдачи файлов       |

## Структура проекта

```
backend/
  app/
    main.py        Точка входа, подключение роутеров, CORS, lifespan
    database.py    Async-движок SQLAlchemy и сессии
    models.py      ORM-модели (User, Kwork, Chat, Message, Review, ...)
    schemas.py     Pydantic-схемы запросов/ответов
    crud.py        Операции с БД
    auth.py        JWT, получение текущего пользователя
    hashing.py     Хеширование паролей (соль + bcrypt)
    s3.py          Загрузка/удаление/URL файлов в MinIO
    ws_manager.py  Менеджер WebSocket-подключений по чатам
  routers/         Эндпоинты, сгруппированные по доменам
  seed.py          Наполнение базы тестовыми данными
  Dockerfile
  docker-compose.yaml
  requirements.txt
```

## Модель данных (кратко)

- **User** — пользователь (профиль, баланс, аватар/баннер, навыки, портфолио).
- **Kwork** — объявление/заказ (автор `user_id`, заказчик `client_id`, цена,
  статус `not_completed` / `in_process` / `completed`, фото, теги).
- **Skill** / **Tag** — навыки пользователей и теги объявлений (many-to-many).
- **Portfolio** — работы в портфолио пользователя.
- **Review** — отзывы (positive / negative) между пользователями.
- **Chat** / **Message** — переписка (опционально привязана к объявлению).
- **Transaction** — операции по балансу (пополнение, оплата, зачисление).

## API

Базовый префикс — `/api`. Защищённые эндпоинты требуют заголовок
`Authorization: Bearer <token>`. Полная интерактивная документация — `/docs`.

### Users — `/api/users`

| Метод  | Путь                     | Описание                              |
| ------ | ------------------------ | ------------------------------------- |
| POST   | `/register`              | Регистрация                           |
| POST   | `/login`                 | Логин (OAuth2 form), выдаёт JWT       |
| GET    | `/me`                    | Текущий пользователь                  |
| PATCH  | `/me`                    | Обновление профиля                    |
| POST   | `/me/balance/topup`      | Пополнение баланса (заглушка оплаты)  |
| GET    | `/me/transactions`       | История операций по балансу           |
| GET    | `/{user_id}`             | Публичный профиль пользователя        |

### Kworks — `/api/kworks`

| Метод  | Путь                  | Описание                                       |
| ------ | --------------------- | ---------------------------------------------- |
| POST   | `/`                   | Создать объявление                             |
| GET    | `/`                   | Список объявлений (`skip`, `limit`)           |
| GET    | `/{id}`               | Объявление по id                               |
| PATCH  | `/{id}/status`        | Сменить статус (только автор)                  |
| POST   | `/{id}/order`         | Взять заказ — создаёт чат, ставит `in_process` |
| POST   | `/{id}/complete`      | Подтвердить выполнение и провести оплату        |
| DELETE | `/{id}`               | Удалить объявление (только автор)              |

### Chats — `/api/chats`

| Метод | Путь        | Описание                |
| ----- | ----------- | ----------------------- |
| GET   | `/my`       | Мои чаты с превью        |
| GET   | `/{id}`     | Чат по id (участники)    |

### Messages — `/api/messages`

| Метод | Путь            | Описание                                   |
| ----- | --------------- | ------------------------------------------ |
| WS    | `/ws/{chat_id}` | WebSocket живого чата (`?token=<jwt>`)      |
| POST  | `/{chat_id}`    | Отправить сообщение (текст и/или картинка)  |
| GET   | `/{chat_id}`    | История сообщений чата                      |

### Reviews — `/api/reviews`

| Метод | Путь                    | Описание                          |
| ----- | ----------------------- | --------------------------------- |
| POST  | `/`                     | Оставить отзыв                    |
| GET   | `/my`                   | Мои написанные отзывы             |
| GET   | `/user/{id}`            | Отзывы о пользователе             |
| GET   | `/user/{id}/rating`     | Рейтинг пользователя (% позитива) |

### Skills — `/api/skills`

| Метод  | Путь            | Описание                       |
| ------ | --------------- | ------------------------------ |
| POST   | `/`             | Создать навык                  |
| GET    | `/`             | Все навыки                     |
| GET    | `/my`           | Мои навыки                     |
| POST   | `/my`           | Добавить навыки себе           |
| DELETE | `/my/{id}`      | Убрать навык                   |
| GET    | `/user/{id}`    | Навыки пользователя            |

### Portfolio — `/api/portfolio`

| Метод  | Путь            | Описание                      |
| ------ | --------------- | ----------------------------- |
| POST   | `/`             | Добавить работу               |
| GET    | `/my`           | Моё портфолио                 |
| GET    | `/user/{id}`    | Портфолио пользователя        |
| GET    | `/{id}`         | Работа по id                  |
| DELETE | `/{id}`         | Удалить работу (только автор) |

### Files — `/api/files`

Загрузка картинок в MinIO (макс. 5–10 МБ, форматы JPEG/PNG/GIF/WEBP):

| Метод | Путь                       | Описание                       |
| ----- | -------------------------- | ------------------------------ |
| POST  | `/upload/avatar`           | Аватар                         |
| POST  | `/upload/banner`           | Баннер профиля                 |
| GET   | `/avatar/{user_id}`        | URL аватара пользователя       |
| POST  | `/upload/portfolio/{id}`   | Картинка работы портфолио      |
| POST  | `/upload/chat/{id}`        | Картинка в чат                 |
| POST  | `/upload/kwork/{id}`       | Картинка к объявлению          |

## Аутентификация

1. `POST /api/users/register` — создать аккаунт.
2. `POST /api/users/login` — получить `access_token` (JWT).
3. Передавать токен в заголовке `Authorization: Bearer <token>`.
   Для WebSocket токен передаётся параметром строки запроса: `?token=<token>`.
