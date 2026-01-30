import asyncio
import os
from flask import Flask, request, render_template
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Update, WebAppInfo
from asgiref.wsgi import WsgiToAsgi
from database import init_db

app = Flask(__name__, template_folder='templates')
bot_token = os.environ.get('BOT_TOKEN', 'your_fallback_token_for_local_test')
bot = Bot(token=bot_token)
dp = Dispatcher()

# Флаг для инициализации только один раз
setup_done = False

@app.before_request
def setup_once():
    global setup_done
    if not setup_done:
        setup_done = True
        asyncio.run(init_db())
        asyncio.run(set_webhook())

async def set_webhook():
    app_url = os.environ.get('APP_URL', 'https://your-local-url-for-test')
    webhook_url = f"{app_url}/webhook"
    await bot.set_webhook(webhook_url)

@dp.message(commands=['start'])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    app_url = os.environ.get('APP_URL', 'https://your-local-url-for-test')
    web_app = WebAppInfo(url=f"{app_url}/miniapp")
    button = InlineKeyboardButton("Открыть вопросы", web_app=web_app)
    keyboard.add(button)
    await message.answer("Добро пожаловать!", reply_markup=keyboard)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    update = Update.de_json(data, bot)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(dp.process_update(update))
    return 'ok', 200

@app.route('/miniapp')
def miniapp():
    return render_template('index.html')

# Для локального запуска (не в production)
if __name__ == '__main__':
    asyncio.run(init_db())
    asyncio.run(set_webhook())
    app.run(debug=True)

# Преобразование в ASGI для uvicorn
app = WsgiToAsgi(app)