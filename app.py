import os
import logging
import asyncio
import json
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic._migration")

print("=== APP.PY VERSION 2026-02-01-v7 LOADED ===")
print(f"Current commit: {os.environ.get('COMMIT_SHA', 'unknown')}")
print(f"APP_URL = {os.environ.get('APP_URL')}")
print(f"BOT_TOKEN exists = {bool(os.environ.get('BOT_TOKEN'))}")
print(f"DATABASE_URL exists = {bool(os.environ.get('DATABASE_URL'))}")
print(f"Working directory files: {os.listdir('.')}")

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Update, WebAppInfo
from aiogram.filters import Command

from fastapi_amis_admin.admin import admin
from fastapi_amis_admin.site import AdminSite
from sqlmodel import SQLModel, Field, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from database import get_dsn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Telegram Quiz Bot + Admin")

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
    difficulty: int = Field(default=1, ge=1, le=5)
    explanation: str | None = None
    image_url: str | None = None
    is_active: bool = Field(default=True)

class BotSettings(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    welcome_message: str = Field(default="Добро пожаловать в квиз-бот!")
    questions_per_day_limit: int = Field(default=10)
    answer_timeout_seconds: int = Field(default=60)

@app.on_event("startup")
async def startup_event():
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
                await session.refresh()
            print("Настройки проверены")
            logger.info("Настройки проверены")

        webhook_url = f"{app_url.rstrip('/')}/webhook"
        await bot.set_webhook(webhook_url)
        print(f"Webhook установлен: {webhook_url}")
        logger.info(f"Webhook установлен: {webhook_url}")
    except Exception as e:
        print(f"Startup error: {str(e)}")
        logger.exception("Startup error")
    print("=== STARTUP FINISHED ===")

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

@app.post("/webhook")
async def webhook_handler(request: Request):
    try:
        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot=bot, update=update)
        logger.info("Webhook обработан")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Webhook ошибка: {e}", exc_info=True)
        return {"ok": False}, 500

@app.get("/miniapp", response_class=HTMLResponse)
async def miniapp_page():
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Mini App</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
</head>
<body>
    <h1>Привет из Mini App!</h1>
    <p id="user-id">User ID: ...</p>
    <script>
        const user = Telegram.WebApp.initDataUnsafe.user;
        document.getElementById('user-id').innerText = 'User ID: ' + (user ? user.id : 'Not available');
    </script>
</body>
</html>
    """

site = AdminSite(engine=engine, title="Админ-панель Квиза")

class QuestionAdmin(admin.ModelAdmin):
    page_schema = 'Вопросы'
    model = Question
    list_display = ['id', 'text', 'difficulty', 'is_active', 'correct_index']
    search_fields = ['text']
    form_include_pk = False

    form = [
        {"type": "input-text", "name": "text", "label": "Текст вопроса", "required": True},
        {"type": "input-json", "name": "options_json", "label": "Варианты ответа (JSON массив)", "required": True},
        {"type": "input-number", "name": "correct_index", "label": "Индекс правильного ответа (с 0)", "required": True, "min": 0},
        {"type": "input-number", "name": "difficulty", "label": "Сложность (1–5)", "min": 1, "max": 5},
        {"type": "input-textarea", "name": "explanation", "label": "Объяснение / комментарий"},
        {"type": "input-text", "name": "image_url", "label": "Ссылка на картинку (опционально)"},
        {"type": "switch", "name": "is_active", "label": "Активен", "value": True}
    ]

site.register_admin(QuestionAdmin)
site.register_admin(admin.ModelAdmin(model=Category, page_schema='Категории'))
site.register_admin(admin.ModelAdmin(model=BotSettings, page_schema='Настройки бота', list_display=['welcome_message', 'questions_per_day_limit', 'answer_timeout_seconds']))

app.mount("/admin", site.router)

@app.get("/")
async def root():
    return RedirectResponse("/admin")