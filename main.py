import os
from flask import Flask, request, render_template_string
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.webhook import send_message
from database import init_db, get_db_session, User

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'Kjwje18J_kemfjcijwjnjfnkwnfkewjnl_k2i13ji2iuUUUWJDJ_Kfijwoejnf')

BOT_TOKEN = os.getenv('BOT_TOKEN', '8200746971:AAGkBS64Mn5LJtIlrMMPTZTfCdHdOdUb6Pc')
ADMIN_TELEGRAM_ID = int(os.getenv('ADMIN_TELEGRAM_ID', 393628087))
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'aasdJI2j12309LL')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализация БД
init_db()

# Шаблон для Mini App (простая заглушка)
INDEX_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Mini App</title>
</head>
<body>
    <h1>Привет из Mini App!</h1>
    <p>User ID: {{ user_id }}</p>
</body>
</html>
"""

# Обработчик команды /start
@dp.message(commands=['start'])
async def start_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть приложение", web_app=WebAppInfo(url=f"https://{os.getenv('APP_DOMAIN', 'localhost:8000')}/miniapp/{message.from_user.id}"))]
    ])
    await message.answer("Добро пожаловать! Нажмите кнопку, чтобы открыть Mini App.", reply_markup=keyboard)

    # Добавляем пользователя в БД, если его нет
    with get_db_session() as session:
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            new_user = User(telegram_id=message.from_user.id, username=message.from_user.username)
            session.add(new_user)
            session.commit()

# Flask роут для Mini App
@app.route('/miniapp/<int:user_id>')
def miniapp(user_id):
    return render_template_string(INDEX_HTML, user_id=user_id)

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
async def webhook():
    update = types.Update(**request.json)
    await dp.process_update(update)
    return {'ok': True}

# Установка webhook (вызывается при запуске)
async def set_webhook():
    webhook_url = f"https://{os.getenv('APP_DOMAIN', 'localhost:8000')}/webhook"
    await bot.set_webhook(webhook_url)

if __name__ == '__main__':
    import asyncio
    asyncio.run(set_webhook())
    app.run(host='0.0.0.0', port=8000)