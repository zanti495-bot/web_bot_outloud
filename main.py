import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from werkzeug.security import check_password_hash
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from sqlalchemy import func

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "Kjwje18J_kemfjcijwjnjfnkwnfkewjnl_k2i13ji2iuUUUWJDJ_Kfijwoejnf")

# Telegram Bot
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Домен берём из переменной окружения или fallback
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', 'https://zanti495-bot-web-bot-outloud-3d66.twc1.net')
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST.rstrip('/')}{WEBHOOK_PATH}"

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="Открыть вопросы",
            web_app=types.WebAppInfo(url=WEBHOOK_HOST)
        )
    ]])
    await message.answer(
        "Добро пожаловать! Нажми кнопку ниже, чтобы открыть Mini App.",
        reply_markup=keyboard
    )

@dp.message()
async def echo(message: types.Message):
    await message.reply("Привет! Используй /start для открытия приложения.")

async def send_broadcast(message_text: str):
    from database import db, User  # отложенный импорт
    users = db.session.query(User.telegram_id).all()
    success_count = 0
    for uid in users:
        try:
            await bot.send_message(uid[0], message_text)
            success_count += 1
        except Exception as e:
            logging.error(f"Не удалось отправить пользователю {uid[0]}: {e}")
    logging.info(f"Рассылка завершена. Отправлено: {success_count} из {len(users)}")

# Telegram Webhook
@app.route(WEBHOOK_PATH, methods=['POST'])
async def telegram_webhook():
    try:
        update = types.Update.de_json(request.get_json(force=True))
        await dp.feed_update(bot, update)
        return jsonify(status="ok")
    except Exception as e:
        logging.error(f"Ошибка в webhook: {e}")
        return jsonify(status="error"), 500

# Установка webhook (вызвать после деплоя)
@app.route('/admin/set_webhook')
def admin_set_webhook():
    if 'logged_in' not in session:
        return redirect(url_for('admin_login'))
    try:
        asyncio.run(bot.delete_webhook(drop_pending_updates=True))
        asyncio.run(bot.set_webhook(url=WEBHOOK_URL))
        return f"Webhook успешно установлен: {WEBHOOK_URL}"
    except Exception as e:
        return f"Ошибка установки webhook: {str(e)}", 500

# Отложенная инициализация БД
try:
    from database import init_db, db, Block, Question, User, View, Design, AuditLog, Purchase
    init_db(max_attempts=15, delay=4)
    logging.info("База данных инициализирована")
except Exception as e:
    logging.error(f"Не удалось инициализировать БД при старте: {e}")

# Админ — авторизация
from config import ADMIN_PASSWORD

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('login.html', error='Неверный пароль')
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

def login_required(f):
    def wrapper(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# Админ — дашборд
@app.route('/admin')
@login_required
def admin_dashboard():
    users_count = User.query.count()
    views_count = View.query.count()
    purchases_count = Purchase.query.count()
    stats = {
        'users': users_count,
        'views': views_count,
        'purchases': purchases_count
    }
    return render_template('dashboard.html', stats=stats)

# Блоки
@app.route('/admin/blocks', methods=['GET', 'POST'])
@login_required
def admin_blocks():
    if request.method == 'POST':
        name = request.form.get('name')
        is_paid = 'is_paid' in request.form
        price = float(request.form.get('price', 0))
        block = Block(name=name, is_paid=is_paid, price=price)
        db.session.add(block)
        db.session.commit()
        AuditLog.log(f"Добавлен блок: {name}")
        return redirect(url_for('admin_blocks'))
    blocks = Block.query.all()
    return render_template('blocks.html', blocks=blocks)

@app.route('/admin/questions/<int:block_id>', methods=['GET', 'POST'])
@login_required
def admin_questions(block_id):
    block = Block.query.get_or_404(block_id)
    if request.method == 'POST':
        text = request.form.get('text')
        question = Question(text=text, block_id=block_id)
        db.session.add(question)
        db.session.commit()
        AuditLog.log(f"Добавлен вопрос в блок {block.name}")
        return redirect(url_for('admin_questions', block_id=block_id))
    questions = Question.query.filter_by(block_id=block_id).all()
    return render_template('questions.html', block=block, questions=questions)

# Дизайн
@app.route('/admin/design', methods=['GET', 'POST'])
@login_required
def admin_design():
    design = Design.query.first()
    if request.method == 'POST':
        settings = {
            'background_color': request.form.get('background_color', '#ffffff'),
            'text_color': request.form.get('text_color', '#000000'),
            'font_family': request.form.get('font_family', 'Arial, sans-serif')
        }
        if design:
            design.settings = settings
        else:
            design = Design(settings=settings)
            db.session.add(design)
        db.session.commit()
        AuditLog.log("Изменён глобальный дизайн")
        return redirect(url_for('admin_design'))
    return render_template('design.html', design=design or {})

# Рассылка
@app.route('/admin/broadcast', methods=['GET', 'POST'])
@login_required
def admin_broadcast():
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            asyncio.run(send_broadcast(message))
            AuditLog.log(f"Выполнена рассылка: {message[:50]}...")
            return render_template('broadcast.html', success=True)
    return render_template('broadcast.html')

# Пользователи
@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    query = request.form.get('query') if request.method == 'POST' else ''
    if query:
        users = User.query.filter(
            (User.username.ilike(f"%{query}%")) | (User.telegram_id == query)
        ).all()
    else:
        users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/admin/block_user/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    user.blocked = True
    db.session.commit()
    AuditLog.log(f"Заблокирован пользователь {user.telegram_id}")
    return redirect(url_for('admin_users'))

@app.route('/admin/unblock_user/<int:user_id>', methods=['POST'])
@login_required
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.blocked = False
    db.session.commit()
    AuditLog.log(f"Разблокирован пользователь {user.telegram_id}")
    return redirect(url_for('admin_users'))

@app.route('/admin/user_views/<int:user_id>')
@login_required
def user_views(user_id):
    views = View.query.filter_by(user_id=user_id).order_by(View.timestamp.desc()).limit(10).all()
    return render_template('user_views.html', views=views)

# Логи аудита
@app.route('/admin/logs')
@login_required
def admin_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return render_template('logs.html', logs=logs)

@app.route('/admin/clear_logs', methods=['POST'])
@login_required
def clear_logs():
    AuditLog.query.delete()
    db.session.commit()
    AuditLog.log("Очищены все логи аудита")
    return redirect(url_for('admin_logs'))

# Аналитика
@app.route('/admin/analytics')
@login_required
def admin_analytics():
    top_blocks = db.session.query(
        Block.name, func.count(View.id).label('count')
    ).join(Question, View.question_id == Question.id)\
     .join(Block, Question.block_id == Block.id)\
     .group_by(Block.id)\
     .order_by(func.count(View.id).desc())\
     .limit(5).all()
    return render_template('analytics.html', top_blocks=top_blocks)

# API для Mini App
@app.route('/api/design')
def api_design():
    design = Design.query.first()
    return jsonify(design.settings if design else {})

@app.route('/api/blocks')
def api_blocks():
    blocks = Block.query.all()
    return jsonify([{
        'id': b.id,
        'name': b.name,
        'is_paid': b.is_paid,
        'price': b.price
    } for b in blocks])

@app.route('/api/check_purchase/<int:user_id>/<int:block_id>')
def api_check_purchase(user_id, block_id):
    purchased = Purchase.query.filter_by(user_id=user_id, block_id=block_id).first() is not None
    return jsonify({'purchased': purchased})

@app.route('/api/purchase', methods=['POST'])
def api_purchase():
    data = request.json
    user_id = data.get('user_id')
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

# Запуск только для локального тестирования
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), debug=False)
