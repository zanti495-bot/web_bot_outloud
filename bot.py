import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.webhook import aiohttp_server
from database import db, User
from config import BOT_TOKEN, ADMIN_TELEGRAM_ID
from aiohttp import web
import os

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message()
async def echo(message: Message):
    await message.reply("Привет! Это бот для рассылок.")

async def send_broadcast(message_text: str):
    users = db.session.query(User.telegram_id).all()
    for user_id in users:
        try:
            await bot.send_message(user_id[0], message_text)
        except:
            pass

# Webhook setup
WEBHOOK_HOST = 'https://zanti495-bot-web-bot-outloud-3d66.twc1.net'
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
