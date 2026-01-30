import asyncio
import os
import logging
from contextlib import asynccontextmanager

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

# --------------------------------------------------
# Инициализация один раз при старте приложения
# --------------------------------------------------
async def startup():
    logger.info("Запуск инициализации...")
    await init_db()
    await set_webhook()
    logger.info("Инициализация завершена")

async def set_webhook():
    app_url = os.environ.get('APP_URL')
    if not app_url:
        logger.error("APP_URL не установлен!")
        return
    
    webhook_url = f"{app_url.rstrip('/')}/webhook"
    try:
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook успешно установлен: {webhook_url}")
    except Exception as e:
        logger.error(f"Ошибка установки webhook: {e}")

# --------------------------------------------------
# Хэндлеры aiogram
# --------------------------------------------------
@dp.message(Command("start"))
async def start_handler(message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Открыть вопросы",
                web_app=WebAppInfo(url=f"{os.environ.get('APP_URL').rstrip('/')}/miniapp")
            )
        ]
    ])
    
    await message.answer(
        "Добро пожаловать!\nНажми кнопку ниже.",
        reply_markup=keyboard
    )

    try:
        created = await User.create(message.from_user.id)
        if created:
            logger.info(f"Новый пользователь добавлен: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка добавления пользователя в БД: {e}")

# --------------------------------------------------
# Вебхук — теперь асинхронный
# --------------------------------------------------
@app.route('/webhook', methods=['POST'])
async def webhook():
    try:
        data = await request.get_json()
        if not data:
            return 'Bad request', 400

        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
        return 'OK', 200
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}", exc_info=True)
        return 'Error', 500

# --------------------------------------------------
# Страница Mini App
# --------------------------------------------------
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
    <body style="font-family:sans-serif; padding:20px; background:#f0f2f5; text-align:center;">
        <h1>Привет из Mini App!</h1>
        <p><strong>User ID:</strong> <span id="uid">загружается...</span></p>
        
        <script>
            const tg = window.Telegram.WebApp;
            tg.ready();
            tg.expand();
            
            const user = tg.initDataUnsafe?.user || {};
            document.getElementById('uid').textContent = user.id || 'не удалось получить';
            
            // Для отладки можно вывести весь initData
            console.log('Telegram WebApp initData:', tg.initDataUnsafe);
        </script>
    </body>
    </html>
    ''')

# --------------------------------------------------
# Запуск (только для локальной отладки)
# --------------------------------------------------
if __name__ == '__main__':
    asyncio.run(startup())
    app.run(host='0.0.0.0', port=8000, debug=True)

# Для gunicorn + uvicorn
app = WsgiToAsgi(app)