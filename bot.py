import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import F
import asyncio
import config
from database import get_session, Block, Question, User, AuditLog
from utils import get_user, get_blocks, get_questions, user_has_block, add_purchase, get_all_blocks_price, buy_all_blocks, log_view, add_audit_log

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class Broadcast(StatesGroup):
    message = State()

@dp.message(Command("start"))
async def start(message: types.Message):
    get_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть вопросы", web_app=types.WebAppInfo(url="https://zanti495-bot-web-bot-outloud-3d66.twc1.net/webapp/"))]
    ])
    await message.reply("Добро пожаловать! Нажмите кнопку ниже, чтобы открыть Mini App.", reply_markup=keyboard)

@dp.message(Command("myblocks"))
async def my_blocks(message: types.Message):
    user = get_user(message.from_user.id)
    blocks = get_blocks()
    purchased = [b for b in blocks if b.id in user.purchased_blocks or not b.is_paid]
    text = "Ваши блоки:\n" + "\n".join([f"- {b.name}" for b in purchased])
    await message.reply(text)

@dp.message(Command("admin"))
async def admin_menu(message: types.Message):
    if message.from_user.id != config.ADMIN_TELEGRAM_ID:
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Рассылка", "Статистика", "Выгрузка CSV")
    await message.reply("Админ-меню", reply_markup=keyboard)

@dp.message(F.text == "Рассылка")
async def broadcast_start(message: types.Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_TELEGRAM_ID:
        return
    await message.reply("Введите сообщение для рассылки (текст, фото, видео и т.д.)")
    await Broadcast.message.set()

@dp.message(Broadcast.message)
async def broadcast_send(message: types.Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_TELEGRAM_ID:
        return
    session = get_session()
    users = session.query(User).all()
    for user in users:
        try:
            if message.photo:
                await bot.send_photo(user.user_id, message.photo[-1].file_id, caption=message.caption, parse_mode='Markdown')
            elif message.video:
                await bot.send_video(user.user_id, message.video.file_id, caption=message.caption, parse_mode='Markdown')
            elif message.document:
                await bot.send_document(user.user_id, message.document.file_id, caption=message.caption, parse_mode='Markdown')
            else:
                await bot.send_message(user.user_id, message.text, parse_mode='Markdown')
        except Exception as e:
            logging.error(f"Error sending to {user.user_id}: {e}")
    await state.finish()
    await message.reply("Рассылка завершена")
    add_audit_log('broadcast', message.text or 'media')

@dp.message(F.text == "Статистика")
async def stats(message: types.Message):
    if message.from_user.id != config.ADMIN_TELEGRAM_ID:
        return
    session = get_session()
    users_count = session.query(User).count()
    purchases = sum(len(u.purchased_blocks) for u in session.query(User).all())
    views_count = session.query(View).count()
    text = f"Пользователи: {users_count}\nПокупки: {purchases}\nПросмотры: {views_count}"
    await message.reply(text)

@dp.message(F.text == "Выгрузка CSV")
async def csv_export(message: types.Message):
    if message.from_user.id != config.ADMIN_TELEGRAM_ID:
        return
    import pandas as pd
    session = get_session()
    users = session.query(User).all()
    data = [{'user_id': u.user_id, 'username': u.username, 'first_name': u.first_name, 'purchased': u.purchased_blocks} for u in users]
    df = pd.DataFrame(data)
    path = '/tmp/export.csv'
    df.to_csv(path, index=False)
    await bot.send_document(message.chat.id, types.InputFile(path))

# Заглушка для платежей (условные покупки)
@dp.pre_checkout_query()
async def pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)  # Заглушка

@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    await message.reply("Покупка успешна! (Условно)")  # Заглушка

# Webhook setup (если нужно, но для простоты используем polling)
async def on_startup():
    print("Bot started")

async def main():
    dp.startup.register(on_startup)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
