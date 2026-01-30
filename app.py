import os
import logging
import asyncio
import json

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Update, WebAppInfo
from aiogram.filters import Command

from sqlmodel import SQLModel, Field, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from database import get_dsn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Telegram Quiz Bot")

print("=== APP.PY VERSION 2026-02-01-v12 LOADED ===")
print(f"Current commit: {os.environ.get('COMMIT_SHA', 'unknown')}")
print(f"APP_URL = {os.environ.get('APP_URL')}")
print(f"BOT_TOKEN exists = {bool(os.environ.get('BOT_TOKEN'))}")
print(f"DATABASE_URL exists = {bool(os.environ.get('DATABASE_URL'))}")
print(f"Working directory files: {os.listdir('.')}")

bot_token = os.environ.get('BOT_TOKEN')
app_url = os.environ.get('APP_URL')

if not bot_token:
    raise ValueError("BOT_TOKEN не установлен!")
if not app_url:
    raise ValueError("APP_URL не установлен!")

bot = Bot(token=bot_token)
dp = Dispatcher()

engine = create_async_engine(get_dsn(), echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)

templates = Jinja2Templates(directory="templates")

# Модели
class Category(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    description: str | None = None

class Question(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    category_id: int | None = Field(default=None, foreign_key="category.id")
    text: str
    options_json: str = Field(default="[]")
    correct_index: int = Field(default=0)
    difficulty: int = Field(default=1)
    explanation: str | None = None
    image_url: str | None = None
    is_active: bool = Field(default=True)

class BotSettings(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    welcome_message: str = Field(default="Добро пожаловать в квиз!")

# Startup
@app.on_event("startup")
async def startup():
    print("=== STARTUP STARTED ===")
    logger.info("Startup started")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        print("Таблицы созданы")
        logger.info("Таблицы созданы")

        async with async_session() as session:
            result = await session.execute(select(BotSettings))
            if not result.scalar_one_or_none():
                session.add(BotSettings())
                await session.commit()
                print("Дефолтные настройки добавлены")
                logger.info("Дефолтные настройки добавлены")

        webhook_url = f"{app_url.rstrip('/')}/webhook"
        await bot.set_webhook(webhook_url)
        print(f"Webhook установлен: {webhook_url}")
        logger.info(f"Webhook установлен: {webhook_url}")
    except Exception as e:
        print(f"Startup error: {str(e)}")
        logger.exception("Startup error")
    print("=== STARTUP FINISHED ===")

# Aiogram /start
@dp.message(Command("start"))
async def start_handler(message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть вопросы", web_app=WebAppInfo(url=f"{app_url.rstrip('/')}/miniapp"))]
    ])

    async with async_session() as session:
        settings = (await session.execute(select(BotSettings))).scalar_one_or_none()
        welcome = settings.welcome_message if settings else "Добро пожаловать!"

    await message.answer(welcome, reply_markup=keyboard)
    print(f"/start обработан для {message.from_user.id}")
    logger.info(f"/start обработан для {message.from_user.id}")

# Webhook
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot=bot, update=update)
        logger.info("Webhook обработан")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Webhook ошибка: {e}", exc_info=True)
        return {"ok": False}, 500

# Mini App
@app.get("/miniapp", response_class=HTMLResponse)
async def miniapp(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Админка
@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    async with async_session() as session:
        questions = await session.execute(select(Question))
        questions = questions.scalars().all()
    return templates.TemplateResponse("admin.html", {"request": request, "questions": questions})

# Создание вопроса
@app.post("/admin/question")
async def create_question(
    request: Request,
    text: str = Form(...),
    options_json: str = Form(...),
    correct_index: int = Form(...),
    difficulty: int = Form(...),
    explanation: str = Form(None),
    image_url: str = Form(None),
    is_active: bool = Form(True),
    category_id: int = Form(None)
):
    async with async_session() as session:
        q = Question(
            text=text,
            options_json=options_json,
            correct_index=correct_index,
            difficulty=difficulty,
            explanation=explanation,
            image_url=image_url,
            is_active=is_active,
            category_id=category_id
        )
        session.add(q)
        await session.commit()
    return RedirectResponse("/admin", status_code=303)

# Health
@app.get("/health")
async def health():
    return {"status": "OK"}