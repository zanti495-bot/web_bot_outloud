import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, Message
from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH
from database import SessionLocal, User, Purchase, Block

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    with SessionLocal() as db:
        u = db.query(User).filter(User.telegram_id == user.id).first()
        if not u:
            u = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            db.add(u)
            db.commit()

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [
                types.KeyboardButton(
                    text="Открыть приложение",
                    web_app=WebAppInfo(url=WEBHOOK_URL.replace(WEBHOOK_PATH, "/"))
                )
            ]
        ]
    )

    await message.answer(
        "Привет! Это приложение с вопросами и тестами.\nНажми кнопку ниже.",
        reply_markup=markup
    )


@dp.message()
async def echo_or_other(message: Message):
    # Можно добавить обработку других команд, кнопок и т.д.
    pass


async def process_update(update_dict: dict):
    """Вызывается из Flask webhook"""
    from aiogram.types import Update
    update = Update.model_validate(update_dict, context={"bot": bot})
    await dp.feed_update(bot, update)


async def on_startup():
    await bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token="your-secret-token-very-long-random",  # должен совпадать с проверкой в app.py
        drop_pending_updates=True
    )
    print("Webhook установлен")


async def on_shutdown():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.session.close()


# Для локального запуска (отладка)
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
