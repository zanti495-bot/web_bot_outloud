import asyncio
import os
import logging
from flask import Flask, request, render_template_string
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Update, WebAppInfo
from aiogram.filters import Command
from asgiref.wsgi import WsgiToAsgi
from database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

bot_token = os.environ.get('BOT_TOKEN')
if not bot_token:
    raise ValueError("BOT_TOKEN не установлен в переменных окружения")

bot = Bot(token=bot_token)
dp = Dispatcher()

# Флаг однократной инициализации
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
        logger.error("APP_URL не установлен в переменных окружения")
        return

    webhook_url = f"{app_url.rstrip('/')}/webhook"
    try:
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook успешно установлен: {webhook_url}")
    except Exception as e:
        logger.error(f"Не удалось установить webhook: {e}")


@dp.message(Command("start"))
async def start_handler(message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Открыть вопросы",
                web_app=WebAppInfo(url=f"{os.environ.get('APP_URL', 'http://localhost:8000')}/miniapp")
            )
        ]
    ])
    await message.answer(
        "Добро пожаловать!\nНажми кнопку ниже, чтобы открыть Mini App.",
        reply_markup=keyboard
    )


@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, bot)
        if update:
            asyncio.run(dp.feed_update(bot, update))
        return 'OK', 200
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}", exc_info=True)
        return 'Error', 500


@app.route('/miniapp')
def miniapp():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mini App — Вопросы</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
                   background: #f0f2f5; margin: 0; padding: 20px; color: #333; }
            h1 { color: #0088cc; }
            .card { background: white; border-radius: 12px; padding: 20px; margin: 16px 0; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        </style>
    </head>
    <body>
        <h1>Привет из Mini App!</h1>
        <div class="card">
            <p><strong>User ID:</strong> <span id="user-id">загружается...</span></p>
            <p><strong>Имя:</strong> <span id="first-name">загружается...</span></p>
            <p><strong>Username:</strong> @<span id="username">загружается...</span></p>
        </div>

        <script>
            const tg = window.Telegram.WebApp;
            tg.ready();
            tg.expand();

            const user = tg.initDataUnsafe.user || {};
            document.getElementById('user-id').textContent = user.id || 'не удалось получить';
            document.getElementById('first-name').textContent = user.first_name || '—';
            document.getElementById('username').textContent = user.username || 'нет';
        </script>
    </body>
    </html>
    ''')


if __name__ == '__main__':
    # Локальный запуск для теста
    asyncio.run(init_db())
    asyncio.run(set_webhook())
    app.run(host='0.0.0.0', port=8000, debug=True)


# Для production (gunicorn + uvicorn)
app = WsgiToAsgi(app)