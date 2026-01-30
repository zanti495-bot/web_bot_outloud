import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.webhook import aiohttp_server
from database import db, User
from config import BOT_TOKEN, ADMIN_TELEGRAM_ID
from aiohttp import web
import os

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: Message):
    # Кнопка для открытия Mini App
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Открыть вопросы",
                web_app=types.WebAppInfo(url="zanti495-bot-web-bot-outloud-3d66.twc1.net")  # Замените на ваш реальный домен из timeweb.cloud App Platform
            )
        ]
    ])
    await message.answer(
        "Добро пожаловать! Это бот для рассылок и доступа к Mini App. Нажмите кнопку ниже, чтобы открыть вопросы.",
        reply_markup=keyboard
    )

@dp.message()
async def echo(message: Message):
    await message.reply("Привет! Это бот для рассылок. Используйте /start для начала.")

async def send_broadcast(message_text: str):
    # Рассылка всем пользователям из БД
    users = db.session.query(User.telegram_id).all()
    for user_id in users:
        try:
            await bot.send_message(user_id[0], message_text)
        except Exception as e:
            print(f"Ошибка отправки пользователю {user_id[0]}: {str(e)}")

# Webhook setup (как в исходном файле)
WEBHOOK_HOST = 'https://zanti495-bot-web-bot-outloud-3d66.twc1.net'  # Ваш домен из timeweb.cloud App Platform
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

async def on_startup(app):
    webhook = await bot.get_webhook_info()
    if webhook.url != WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)

def run_bot():
    app = web.Application()
    aiohttp_server.setup_webhook(dp, app, path=WEBHOOK_PATH)
    app.on_startup.append(on_startup)
    web.run_app(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == '__main__':
    run_bot()
