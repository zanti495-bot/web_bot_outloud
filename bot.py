import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import BOT_TOKEN
from database import db, User

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Открыть вопросы",
                web_app=types.WebAppInfo(url="https://zanti495-bot-web-bot-outloud-3d66.twc1.net/")
            )
        ]
    ])
    await message.answer(
        "Добро пожаловать! Нажмите кнопку ниже, чтобы открыть Mini App.",
        reply_markup=keyboard
    )

@dp.message()
async def echo(message: Message):
    await message.reply("Привет! Это бот для рассылок. Используй /start.")

async def send_broadcast(message_text: str):
    users = db.session.query(User.telegram_id).all()
    for user_id in users:
        try:
            await bot.send_message(user_id[0], message_text)
        except:
            pass
