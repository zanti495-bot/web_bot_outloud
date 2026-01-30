import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH
from database import SessionLocal, User

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first = message.from_user.first_name
    last = message.from_user.last_name

    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            user = User(
                telegram_id=user_id,
                username=username,
                first_name=first,
                last_name=last
            )
            db.add(user)
            db.commit()

    await message.answer(
        "Добро пожаловать!\nНажми ниже, чтобы открыть приложение",
        reply_markup=types.ReplyKeyboardMarkup(
            resize_keyboard=True,
            keyboard=[
                [types.KeyboardButton(
                    text="Открыть Mini App",
                    web_app=WebAppInfo(url=WEBHOOK_URL.replace(WEBHOOK_PATH, "/"))
                )]
            ]
        )
    )


async def on_startup():
    await bot.set_webhook(url=WEBHOOK_URL)


async def on_shutdown():
    await bot.delete_webhook(drop_pending_updates=True)


async def main():
    await on_startup()
    await dp.start_polling(bot)  # на время отладки polling
    # для продакшена заменить на webhook-обработчик в app.py


if __name__ == "__main__":
    asyncio.run(main())
