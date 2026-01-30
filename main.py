import asyncio
import os
import logging
from flask import Flask, request, render_template_string
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Update, WebAppInfo
from aiogram.filters import Command
from asgiref.wsgi import WsgiToAsgi
from database import init_db, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

bot_token = os.environ.get('BOT_TOKEN')
if not bot_token:
    raise ValueError("BOT_TOKEN не установлен!")

bot = Bot(token=bot_token)
dp = Dispatcher()

setup_done = False

@app.before_request
def setup_once():
    global setup_done
    if not setup_done:
        setup_done = True
        asyncio.run(init_db())
        asyncio.run(set_webhook())

async def set_webhook():
    app_url = os.environ.get('APP_URL')
    if not app_url:
        logger.error("APP_URL не установлен!")
        return
    webhook_url = f"{app_url.rstrip('/')}/webhook"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook установлен: {webhook_url}")

@dp.message(Command("start"))
async def start_handler(message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Открыть вопросы",
            web_app=WebAppInfo(url=f"{os.environ.get('APP_URL')}/miniapp")
        )]
    ])
    await message.answer("Добро пожаловать!\nНажми кнопку ниже.", reply_markup=keyboard)

    # Добавляем пользователя в БД
    try:
        await User.create(message.from_user.id)
    except Exception as e:
        logger.error(f"Ошибка добавления пользователя: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.model_validate(data)
        asyncio.run(dp.feed_update(bot, update))
        return 'OK', 200
    except Exception as e:
        logger.error(f"Ошибка в webhook: {e}", exc_info=True)
        return 'Error', 500

@app.route('/miniapp')
def miniapp():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mini App</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
    </head>
    <body style="font-family:sans-serif; padding:20px; background:#f0f2f5;">
        <h1>Привет из Mini App!</h1>
        <p><strong>User ID:</strong> <span id="uid">загружается...</span></p>
        <script>
            const tg = window.Telegram.WebApp;
            tg.ready();
            tg.expand();
            const user = tg.initDataUnsafe.user || {};
            document.getElementById('uid').textContent = user.id || 'не получен';
        </script>
    </body>
    </html>
    ''')

if __name__ == '__main__':
    asyncio.run(init_db())
    asyncio.run(set_webhook())
    app.run(host='0.0.0.0', port=8000, debug=True)

app = WsgiToAsgi(app)