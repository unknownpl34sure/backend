"""
Скрипт наполнения базы тестовыми данными: пользователи, навыки, теги,
объявления (kworks), портфолио, отзывы и чаты со случайными фотографиями.

Запуск (внутри контейнера, т.к. DATABASE_URL указывает на host `db`):

    docker compose exec server python seed.py

Локальный запуск возможен, если DATABASE_URL указывает на доступный Postgres.

Фотографии — это внешние случайные изображения (picsum.photos / pravatar.cc),
которые отдаются как есть благодаря passthrough в app.s3.get_file_url.

Все пользователи создаются с паролем: password123
"""

import asyncio
import json
import random

from sqlalchemy import select, func

from app.database import AsyncSessionLocal, engine, Base
from app import models
from app.models import KworkStatus, ReviewStatus
from app.hashing import get_password_hash, generate_salt


DEFAULT_PASSWORD = "password123"

SKILLS = [
    "Figma", "Photoshop", "Illustrator", "React", "Python", "FastAPI",
    "JavaScript", "Копирайтинг", "Рерайтинг", "SMM", "Таргетинг", "SEO",
    "Premiere Pro", "After Effects", "Blender", "Excel", "Перевод", "Вёрстка",
]

TAGS = [
    "дизайн", "разработка", "тексты", "учёба", "маркетинг", "видео",
    "логотип", "сайт", "бот", "курсовая", "реклама", "3d",
]

USERS = [
    {
        "username": "anna_design",
        "name": "Анна Кузнецова",
        "email": "anna@univer.ru",
        "specialization": "UI/UX дизайнер",
        "description": "Создаю чистые и понятные интерфейсы. Студентка 3 курса, дизайню в Figma уже 2 года.",
        "avatar": "https://i.pravatar.cc/300?img=47",
        "skills": ["Figma", "Photoshop", "Illustrator"],
    },
    {
        "username": "ivan_dev",
        "name": "Иван Петров",
        "email": "ivan@univer.ru",
        "specialization": "Веб-разработчик",
        "description": "Фронтенд на React + бэкенд на Node. Беру заказы любой сложности, делаю быстро.",
        "avatar": "https://i.pravatar.cc/300?img=12",
        "skills": ["React", "JavaScript", "Вёрстка"],
    },
    {
        "username": "maria_text",
        "name": "Мария Смирнова",
        "email": "maria@univer.ru",
        "specialization": "Копирайтер",
        "description": "Пишу продающие тексты, статьи и эссе. Филфак, грамотность гарантирую.",
        "avatar": "https://i.pravatar.cc/300?img=5",
        "skills": ["Копирайтинг", "Рерайтинг", "Перевод"],
    },
    {
        "username": "dmitry_code",
        "name": "Дмитрий Соколов",
        "email": "dmitry@univer.ru",
        "specialization": "Python-разработчик",
        "description": "Telegram-боты, парсеры, автоматизация и бэкенд на FastAPI. Помогу с курсовой по программированию.",
        "avatar": "https://i.pravatar.cc/300?img=33",
        "skills": ["Python", "FastAPI", "Excel"],
    },
    {
        "username": "elena_smm",
        "name": "Елена Попова",
        "email": "elena@univer.ru",
        "specialization": "SMM-специалист",
        "description": "Веду соцсети, настраиваю таргет и пишу контент-планы. Подниму охваты вашего проекта.",
        "avatar": "https://i.pravatar.cc/300?img=24",
        "skills": ["SMM", "Таргетинг", "SEO"],
    },
    {
        "username": "pavel_video",
        "name": "Павел Морозов",
        "email": "pavel@univer.ru",
        "specialization": "Видеомонтажёр",
        "description": "Монтирую ролики для YouTube и Reels. Цветокоррекция, субтитры, динамичный монтаж.",
        "avatar": "https://i.pravatar.cc/300?img=15",
        "skills": ["Premiere Pro", "After Effects"],
    },
    {
        "username": "olga_study",
        "name": "Ольга Новикова",
        "email": "olga@univer.ru",
        "specialization": "Помощь с учёбой",
        "description": "Решаю задачи по высшей математике и физике, помогаю с рефератами и презентациями.",
        "avatar": "https://i.pravatar.cc/300?img=44",
        "skills": ["Excel", "Перевод"],
    },
    {
        "username": "sergey_3d",
        "name": "Сергей Волков",
        "email": "sergey@univer.ru",
        "specialization": "3D-дизайнер",
        "description": "Моделирую и визуализирую в Blender. Предметка, персонажи, анимация.",
        "avatar": "https://i.pravatar.cc/300?img=51",
        "skills": ["Blender", "Photoshop"],
    },
]

# author — username автора; tags — список названий тегов
KWORKS = [
    {
        "author": "anna_design",
        "title": "Нарисую современный логотип для вашего проекта",
        "description": "Сделаю 3 варианта логотипа, передам исходники в AI и PNG. Срок — 2 дня. Бесплатные правки до полного утверждения.",
        "price": 2500,
        "tags": ["дизайн", "логотип"],
        "photos": 2,
    },
    {
        "author": "anna_design",
        "title": "Дизайн мобильного приложения в Figma",
        "description": "Спроектирую до 8 экранов с кликабельным прототипом. Современный стиль, удобный UX.",
        "price": 6000,
        "tags": ["дизайн"],
        "photos": 3,
    },
    {
        "author": "ivan_dev",
        "title": "Сверстаю адаптивный лендинг по макету",
        "description": "HTML/CSS/JS или React. Идеальное соответствие макету, адаптив под все устройства, анимации.",
        "price": 4500,
        "tags": ["разработка", "сайт"],
        "photos": 2,
    },
    {
        "author": "ivan_dev",
        "title": "Создам сайт-визитку под ключ",
        "description": "Многостраничный сайт на React, подключу форму обратной связи и аналитику. Выложу на хостинг.",
        "price": 9000,
        "tags": ["разработка", "сайт"],
        "photos": 1,
    },
    {
        "author": "dmitry_code",
        "title": "Напишу Telegram-бота любой сложности",
        "description": "Бот для расписания, магазина или рассылок. Python + aiogram, размещу на сервере.",
        "price": 3500,
        "tags": ["разработка", "бот"],
        "photos": 1,
    },
    {
        "author": "dmitry_code",
        "title": "Помогу с курсовой по программированию",
        "description": "Python, базы данных, алгоритмы. Объясню код, подготовлю к защите. Антиплагиат пройдём.",
        "price": 5000,
        "tags": ["учёба", "курсовая", "разработка"],
        "photos": 1,
    },
    {
        "author": "maria_text",
        "title": "Напишу продающий текст для сайта",
        "description": "Цепляющий текст для главной или о компании. До 4000 знаков, анализ ЦА, SEO-оптимизация.",
        "price": 1500,
        "tags": ["тексты", "маркетинг"],
        "photos": 1,
    },
    {
        "author": "maria_text",
        "title": "Эссе, рефераты и статьи на заказ",
        "description": "Грамотно и в срок. Любая тема гуманитарного цикла, оформление по ГОСТу.",
        "price": 1200,
        "tags": ["тексты", "учёба"],
        "photos": 1,
    },
    {
        "author": "elena_smm",
        "title": "Настрою таргетированную рекламу",
        "description": "ВКонтакте и Telegram Ads. Подберу аудитории, сделаю креативы, запущу и оптимизирую кампанию.",
        "price": 4000,
        "tags": ["маркетинг", "реклама"],
        "photos": 2,
    },
    {
        "author": "elena_smm",
        "title": "Контент-план для соцсетей на месяц",
        "description": "30 идей постов с рубрикатором и временем публикации. Под вашу нишу и tone of voice.",
        "price": 2000,
        "tags": ["маркетинг"],
        "photos": 1,
    },
    {
        "author": "pavel_video",
        "title": "Смонтирую видео для YouTube",
        "description": "Динамичный монтаж, цветокор, звук, субтитры и превью. До 10 минут готового ролика.",
        "price": 3000,
        "tags": ["видео"],
        "photos": 2,
    },
    {
        "author": "pavel_video",
        "title": "Сделаю Reels / Shorts из ваших материалов",
        "description": "Вертикальные ролики с трендовыми переходами и подписями. 3 ролика в пакете.",
        "price": 1800,
        "tags": ["видео", "маркетинг"],
        "photos": 1,
    },
    {
        "author": "olga_study",
        "title": "Решу задачи по высшей математике",
        "description": "Пределы, производные, интегралы, матрицы. С подробным решением и пояснениями.",
        "price": 800,
        "tags": ["учёба"],
        "photos": 1,
    },
    {
        "author": "olga_study",
        "title": "Оформлю презентацию для защиты",
        "description": "Аккуратный дизайн слайдов под вашу тему, инфографика и единый стиль. До 15 слайдов.",
        "price": 1500,
        "tags": ["учёба", "дизайн"],
        "photos": 2,
    },
    {
        "author": "sergey_3d",
        "title": "3D-модель предмета для печати или рендера",
        "description": "Смоделирую в Blender по референсу, подготовлю к 3D-печати или сделаю красивый рендер.",
        "price": 3200,
        "tags": ["3d", "дизайн"],
        "photos": 3,
    },
    {
        "author": "sergey_3d",
        "title": "Рекламный 3D-ролик товара",
        "description": "Короткая анимация вашего продукта с приятным освещением и материалами. 5–10 секунд.",
        "price": 7000,
        "tags": ["3d", "видео", "реклама"],
        "photos": 2,
    },
    {
        "author": "ivan_dev",
        "title": "Исправлю баги в вашем React-проекте",
        "description": "Найду и починю ошибки, отрефакторю код, подскажу по архитектуре. Оплата по объёму.",
        "price": 2200,
        "tags": ["разработка"],
        "photos": 1,
    },
    {
        "author": "anna_design",
        "title": "Оформлю шапку и аватар для соцсетей",
        "description": "Единый стиль для профиля: обложка, аватар, шаблоны постов. Под любую платформу.",
        "price": 1300,
        "tags": ["дизайн", "маркетинг"],
        "photos": 2,
    },
]

# Портфолио: username -> список (title, photo_seed)
PORTFOLIO = {
    "anna_design": ["Лендинг для кофейни", "Айдентика для стартапа"],
    "ivan_dev": ["Интернет-магазин на React", "Дашборд аналитики"],
    "sergey_3d": ["Игровой персонаж", "Визуализация интерьера"],
    "pavel_video": ["Промо-ролик для бренда"],
}

# Отзывы: (author_username, target_username, status, text)
REVIEWS = [
    ("ivan_dev", "anna_design", "positive", "Анна сделала шикарный логотип, всё чётко и быстро. Рекомендую!"),
    ("maria_text", "anna_design", "positive", "Очень приятно работать, учла все пожелания по дизайну."),
    ("dmitry_code", "ivan_dev", "positive", "Иван помог с вёрсткой, код чистый, сроки соблюдены."),
    ("elena_smm", "ivan_dev", "positive", "Отличный разработчик, всё работает как часы."),
    ("anna_design", "dmitry_code", "positive", "Бот работает отлично, Дмитрий всё подробно объяснил."),
    ("pavel_video", "maria_text", "positive", "Тексты огонь, конверсия выросла."),
    ("olga_study", "elena_smm", "positive", "Таргет настроен грамотно, заявки пошли сразу."),
    ("sergey_3d", "pavel_video", "positive", "Монтаж на высоте, ролик получился динамичным."),
    ("ivan_dev", "sergey_3d", "positive", "Крутая 3D-модель, всё по референсу."),
    ("maria_text", "olga_study", "negative", "Задачу решили, но пришлось немного подождать сверх срока."),
    ("dmitry_code", "elena_smm", "positive", "Контент-план структурный и понятный, спасибо!"),
]


def avatar_url(user):
    return user["avatar"]


def kwork_photos(slug, count):
    return [
        f"https://picsum.photos/seed/{slug}-{i}/800/600" for i in range(count)
    ]


def slugify(text, idx):
    base = "".join(ch if ch.isalnum() else "-" for ch in text.lower())
    base = base.strip("-")[:24] or "kwork"
    return f"{base}-{idx}"


async def get_or_create_user(db, data):
    res = await db.execute(
        select(models.User).where(models.User.username == data["username"])
    )
    user = res.scalar_one_or_none()
    if user:
        return user, False

    salt = generate_salt()
    user = models.User(
        username=data["username"],
        name=data["name"],
        email=data["email"],
        specialization=data["specialization"],
        description=data["description"],
        avatar_id=avatar_url(data),
        password_hash=get_password_hash(DEFAULT_PASSWORD, salt),
        password_salt=salt,
    )
    db.add(user)
    await db.flush()
    return user, True


async def get_or_create_named(db, model, name):
    res = await db.execute(select(model).where(model.name == name))
    obj = res.scalar_one_or_none()
    if obj:
        return obj
    obj = model(name=name)
    db.add(obj)
    await db.flush()
    return obj


async def link_user_skill(db, user_id, skill_id):
    res = await db.execute(
        models.user_skill.select().where(
            models.user_skill.c.user_id == user_id,
            models.user_skill.c.skill_id == skill_id,
        )
    )
    if not res.first():
        await db.execute(
            models.user_skill.insert().values(
                user_id=user_id, skill_id=skill_id
            )
        )


async def main():
    random.seed(42)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # --- Навыки и теги ---
        skill_map = {}
        for name in SKILLS:
            skill_map[name] = await get_or_create_named(db, models.Skill, name)

        tag_map = {}
        for name in TAGS:
            tag_map[name] = await get_or_create_named(db, models.Tag, name)

        # --- Пользователи ---
        user_map = {}
        created_users = 0
        for data in USERS:
            user, created = await get_or_create_user(db, data)
            user_map[data["username"]] = user
            created_users += int(created)
            for skill_name in data["skills"]:
                skill = skill_map.get(skill_name)
                if skill:
                    await link_user_skill(db, user.id, skill.id)

        await db.commit()

        # --- Проверяем, есть ли уже объявления (чтобы не плодить дубликаты) ---
        existing_kworks = (
            await db.execute(select(func.count(models.Kwork.id)))
        ).scalar() or 0

        if existing_kworks > 0:
            print(
                f"В базе уже есть объявления ({existing_kworks}). "
                "Пропускаю создание kworks/портфолио/отзывов/чатов."
            )
            print(f"Пользователей создано в этом запуске: {created_users}")
            print("Готово.")
            return

        # --- Объявления ---
        created_kworks = []
        for idx, k in enumerate(KWORKS):
            author = user_map[k["author"]]
            slug = slugify(k["title"], idx)
            photos = kwork_photos(slug, k.get("photos", 1))

            kwork = models.Kwork(
                title=k["title"],
                description=k["description"],
                price=k["price"],
                user_id=author.id,
                photo_ids=json.dumps(photos),
                status=KworkStatus.NOT_COMPLETED,
            )
            db.add(kwork)
            await db.flush()

            for tag_name in k.get("tags", []):
                tag = tag_map.get(tag_name)
                if tag:
                    await db.execute(
                        models.kwork_tag.insert().values(
                            kwork_id=kwork.id, tag_id=tag.id
                        )
                    )

            created_kworks.append(kwork)

        await db.commit()

        # --- Несколько сделок: заказы (in_process) + чаты с сообщениями ---
        deals = [
            # (индекс объявления, username заказчика)
            (0, "ivan_dev"),
            (4, "anna_design"),
            (8, "dmitry_code"),
        ]
        for kwork_idx, client_username in deals:
            kwork = created_kworks[kwork_idx]
            client = user_map[client_username]
            if client.id == kwork.user_id:
                continue

            kwork.client_id = client.id
            kwork.status = KworkStatus.IN_PROCESS

            chat = models.Chat(
                initiator_id=kwork.user_id,
                receiver_id=client.id,
                kwork_id=kwork.id,
            )
            db.add(chat)
            await db.flush()

            dialog = [
                (client.id, "Здравствуйте! Заинтересовало ваше объявление, можем обсудить?"),
                (kwork.user_id, "Привет! Да, конечно. Расскажите подробнее, что нужно."),
                (client.id, "Нужно примерно как в описании, сроки — неделя. Бюджет ок?"),
                (kwork.user_id, "Да, всё подходит. Давайте начнём, скину детали в течение дня."),
            ]
            for sender_id, text in dialog:
                db.add(
                    models.Message(
                        chat_id=chat.id, sender_id=sender_id, text=text
                    )
                )

        # Одну сделку отметим выполненной
        done_kwork = created_kworks[6]
        done_client = user_map["maria_text"]
        if done_client.id != done_kwork.user_id:
            done_kwork.client_id = done_client.id
            done_kwork.status = KworkStatus.COMPLETED
            done_chat = models.Chat(
                initiator_id=done_kwork.user_id,
                receiver_id=done_client.id,
                kwork_id=done_kwork.id,
            )
            db.add(done_chat)
            await db.flush()
            db.add(
                models.Message(
                    chat_id=done_chat.id,
                    sender_id=done_client.id,
                    text="Спасибо, всё получил, работа отличная!",
                )
            )

        await db.commit()

        # --- Портфолио ---
        for username, items in PORTFOLIO.items():
            user = user_map[username]
            for i, title in enumerate(items):
                db.add(
                    models.Portfolio(
                        user_id=user.id,
                        title=title,
                        photo_id=f"https://picsum.photos/seed/pf-{user.id}-{i}/600/600",
                    )
                )
        await db.commit()

        # --- Отзывы ---
        for author_username, target_username, status, text in REVIEWS:
            author = user_map[author_username]
            target = user_map[target_username]
            if author.id == target.id:
                continue
            db.add(
                models.Review(
                    author_id=author.id,
                    target_id=target.id,
                    text=text,
                    status=(
                        ReviewStatus.POSITIVE
                        if status == "positive"
                        else ReviewStatus.NEGATIVE
                    ),
                )
            )
        await db.commit()

        print("=== Сидирование завершено ===")
        print(f"Пользователей:   {len(USERS)} (новых: {created_users})")
        print(f"Навыков:         {len(SKILLS)}")
        print(f"Тегов:           {len(TAGS)}")
        print(f"Объявлений:      {len(KWORKS)}")
        print(f"Портфолио:       {sum(len(v) for v in PORTFOLIO.values())}")
        print(f"Отзывов:         {len(REVIEWS)}")
        print(f"Чатов (сделок):  {len(deals) + 1}")
        print()
        print(f"Пароль для всех аккаунтов: {DEFAULT_PASSWORD}")
        print("Например, логин: anna_design / ivan_dev / dmitry_code")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
