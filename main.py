import os
import logging
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from datetime import datetime
from werkzeug.security import check_password_hash
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_change_me")

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', 'https://zanti495-bot-web-bot-outloud-3d66.twc1.net')
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Открыть вопросы", web_app=types.WebAppInfo(url=WEBHOOK_HOST))
    ]])
    await message.answer("Добро пожаловать! Нажми ниже.", reply_markup=keyboard)

@dp.message()
async def echo(message: types.Message):
    await message.reply("Используй /start")

async def send_broadcast(message_text: str):
    from database import db, User  # отложенный импорт
    users = db.session.query(User.telegram_id).all()
    for uid in users:
        try:
            await bot.send_message(uid[0], message_text)
        except Exception as e:
            logging.error(f"Не удалось отправить {uid[0]}: {e}")

# Webhook endpoint (async)
@app.route(WEBHOOK_PATH, methods=['POST'])
async def telegram_webhook():
    update = types.Update.de_json(request.get_json(force=True))
    await dp.feed_update(bot, update)
    return jsonify(status="ok")

# Установка webhook (вызови после деплоя: https://твой-домен/admin/set_webhook)
@app.route('/admin/set_webhook')
def admin_set_webhook():
    if 'logged_in' not in session:
        return redirect(url_for('admin_login'))
    try:
        import asyncio
        asyncio.run(bot.delete_webhook(drop_pending_updates=True))
        asyncio.run(bot.set_webhook(WEBHOOK_URL))
        return "Webhook установлен: " + WEBHOOK_URL
    except Exception as e:
        return f"Ошибка: {str(e)}"

# Отложенная инициализация БД
try:
    from database import init_db, db, Block, Question, User, View, Design, AuditLog, Purchase
    init_db(max_attempts=15, delay=4)
    logging.info("БД инициализирована")
except Exception as e:
    logging.error(f"Ошибка инициализации БД: {e}")

# Твои остальные маршруты (admin, api и т.д.) — вставь сюда из предыдущих версий
# Пример минимального admin login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    from config import ADMIN_PASSWORD
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect('/admin')
        return render_template('login.html', error='Неверный пароль')
    return render_template('login.html')

@app.route('/admin')
def admin():
    if 'logged_in' not in session:
        return redirect(url_for('admin_login'))
    return "Админ-панель (добавь свои шаблоны и логику)"

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
