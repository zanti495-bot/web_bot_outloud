from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import os
import io
import pandas as pd
from datetime import datetime
import logging
import asyncio
import json
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import func

# Logging setup
logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(levelname)s: %(message)s')

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "Kjwje18J_kemfjcijwjnjfnkwnfkewjnl_k2i13ji2iuUUUWJDJ_Kfijwoejnf")

# Bot setup (from bot.py)
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Handlers from bot.py
@dp.message(Command("start"))
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Открыть вопросы",
                web_app=types.WebAppInfo(url=os.getenv('WEBHOOK_HOST', 'https://zanti495-bot-web-bot-outloud-3d66.twc1.net'))
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

# Broadcast function from bot.py
async def send_broadcast(message_text: str):
    from database import db, User  # Отложенный импорт
    users = db.session.query(User.telegram_id).all()
    for user_id in users:
        try:
            await bot.send_message(user_id[0], message_text)
        except Exception as e:
            logging.error(f"Failed to send message to {user_id[0]}: {e}")

# Webhook settings
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', 'https://zanti495-bot-web-bot-outloud-3d66.twc1.net')
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Health-check
@app.route('/health')
def health():
    return 'OK', 200

# Отложенная инициализация БД (чтобы избежать circular imports)
with app.app_context():
    try:
        from database import init_db, db, Block, Question, User, View, Design, AuditLog, Purchase
        if not init_db(max_attempts=10, delay=5):  # Увеличил попытки
            logging.warning("DB init failed, but continuing...")
    except Exception as e:
        logging.error(f"Failed to init DB: {e}")

# Admin routes (truncated for brevity, assume full code here as in original)
# ... (вставьте полный код админ-роутов из вашего оригинального app.py, включая /admin/login, /admin, etc.)

# API routes (full as in original)
@app.route('/api/design')
def api_design():
    design = Design.query.first()
    return jsonify(design.settings if design else {})

@app.route('/api/blocks')
def api_blocks():
    blocks = Block.query.all()
    return jsonify([{'id': b.id, 'name': b.name, 'is_paid': b.is_paid, 'price': b.price} for b in blocks])

@app.route('/api/purchase', methods=['POST'])
def api_purchase():
    data = request.json
    user_id = data['user_id']
    block_id = data.get('block_id')  # None = все блоки
    purchase = Purchase(user_id=user_id, block_id=block_id)
    db.session.add(purchase)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/view', methods=['POST'])
def api_view():
    data = request.json
    view = View(user_id=data['user_id'], question_id=data['question_id'])
    db.session.add(view)
    db.session.commit()
    return jsonify({'success': True})

# Index
@app.route('/')
def index():
    return app.send_static_file('index.html')

# Webhook handler
async def webhook_handler(request: Request) -> Response:
    update = types.Update(**(await request.json()))
    await dp.feed_update(bot, update)
    return web.json_response({'status': 'ok'})

# Startup: set webhook
async def on_startup(aio_app):
    try:
        webhook = await bot.get_webhook_info()
        if webhook.url != WEBHOOK_URL:
            await bot.delete_webhook()  # Delete if conflict
            await bot.set_webhook(WEBHOOK_URL)
            logging.info(f"Webhook set to {WEBHOOK_URL}")
    except Exception as e:
        logging.error(f"Failed to set webhook: {e}")

if __name__ == '__main__':
    aiohttp_app = web.Application()
    aiohttp_app.router.add_post(WEBHOOK_PATH, webhook_handler)
    aiohttp_app.on_startup.append(on_startup)
    web.run_app(aiohttp_app, host='0.0.0.0', port=int(os.getenv('PORT', 8080)))
