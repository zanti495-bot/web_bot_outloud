from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import os
import io
import pandas as pd
from datetime import datetime
from database import db, Block, Question, User, View, Design, AuditLog, Purchase, Base, engine
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

# Импорты для aiogram и webhook
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
import asyncio
import json

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "Kjwje18J_kemfjcijwjnjfnkwnfkewjnl_k2i13ji2iuUUUWJDJ_Kfijwoejnf")

# Настройки бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Webhook настройки
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', 'https://zanti495-bot-web-bot-outloud-3d66.twc1.net')  # Замените на ваш реальный домен из timeweb.cloud
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Обработчик /start для бота
@dp.message(Command("start"))
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Открыть вопросы",
                web_app=types.WebAppInfo(url=WEBHOOK_HOST)  # URL Mini App — ваш домен
            )
        ]
    ])
    await message.answer(
        "Добро пожаловать! Это бот для рассылок и Mini App. Нажмите кнопку ниже.",
        reply_markup=keyboard
    )

@dp.message()
async def echo(message: Message):
    await message.reply("Привет! Это бот для рассылок. Используйте /start.")

# Безопасная инициализация таблиц БД
with app.app_context():
    from database import init_db
    if not init_db(max_attempts=5, delay=3):
        print(f"[{datetime.now()}] Предупреждение: БД не инициализирована (возможно, таблицы уже существуют). Приложение продолжает работу.")
    else:
        print(f"[{datetime.now()}] Инициализация БД прошла успешно")

# Health-check
@app.route('/health')
def health():
    return 'OK', 200

# Логин админа
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == os.getenv("ADMIN_PASSWORD", "aasdJI2j12309LL"):
            session['admin'] = True
            return redirect('/admin')
    return render_template('login.html')

# Дашборд
@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect('/admin/login')
    stats = {
        'users': db.session.query(User).count(),
        'views': db.session.query(View).count(),
        'purchases': db.session.query(Purchase).count()
    }
    return render_template('dashboard.html', stats=stats)

# Управление блоками
@app.route('/admin/blocks', methods=['GET', 'POST'])
def admin_blocks():
    if not session.get('admin'):
        return redirect('/admin/login')
    if request.method == 'POST':
        name = request.form.get('name')
        is_paid = 'is_paid' in request.form
        price = float(request.form.get('price', 0))
        block = Block(name=name, is_paid=is_paid, price=price)
        db.session.add(block)
        db.session.commit()
    blocks = Block.query.all()
    return render_template('blocks.html', blocks=blocks)

# Вопросы блока
@app.route('/admin/questions/<int:block_id>', methods=['GET', 'POST'])
def admin_questions(block_id):
    if not session.get('admin'):
        return redirect('/admin/login')
    block = Block.query.get_or_404(block_id)
    if request.method == 'POST':
        text = request.form.get('text')
        question = Question(text=text, block_id=block_id)
        db.session.add(question)
        db.session.commit()
    questions = Question.query.filter_by(block_id=block_id).all()
    return render_template('questions.html', block=block, questions=questions)

# Дизайн
@app.route('/admin/design', methods=['GET', 'POST'])
def admin_design():
    if not session.get('admin'):
        return redirect('/admin/login')
    design = Design.query.first()
    if request.method == 'POST':
        if not design:
            design = Design()
            db.session.add(design)
        design.settings = {
            'background_color': request.form.get('background_color', '#ffffff'),
            'text_color': request.form.get('text_color', '#000000'),
            'font_family': request.form.get('font_family', 'Arial, sans-serif')
        }
        db.session.commit()
    return render_template('design.html', design=design.settings if design else {})

# API для Mini App
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

# Главная страница Mini App
@app.route('/')
def index():
    return app.send_static_file('index.html')

# Асинхронный хендлер webhook для aiogram
async def webhook_handler(request: Request) -> Response:
    update = types.Update(**(await request.json()))
    await dp.feed_update(bot, update)
    return web.json_response({'status': 'ok'})

# Запуск aiohttp сервера с интеграцией Flask маршрутов
async def on_startup(aio_app):
    webhook = await bot.get_webhook_info()
    if webhook.url != WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)

if __name__ == '__main__':
    aiohttp_app = web.Application()
    aiohttp_app.router.add_post(WEBHOOK_PATH, webhook_handler)
    aiohttp_app.on_startup.append(on_startup)
    # Добавляем Flask маршруты в aiohttp (используем middlewares)
    async def flask_middleware(request, handler):
        with app.test_request_context():
            return await handler(request)

    aiohttp_app.middlewares.append(flask_middleware)

    web.run_app(aiohttp_app, host='0.0.0.0', port=int(os.getenv('PORT', 8080)))
