from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify, abort
import pandas as pd
import config
from database import get_session, Block, Question, User, View, Design, AuditLog, add_audit_log
from utils import update_design, get_design, get_blocks, get_questions, user_has_block, get_all_blocks_price, log_view, add_purchase, buy_all_blocks, get_user
from functools import wraps
import asyncio
from aiogram import Bot
import os
import logging

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = config.FLASK_SECRET_KEY
bot = Bot(token=config.BOT_TOKEN)  # Для рассылок из админки

# ====================== Аутентификация ======================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == config.ADMIN_PASSWORD:  # В продакшене — хэширование!
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return render_template('login.html')

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ====================== Основные страницы ======================
@app.route('/dashboard')
@login_required
def dashboard():
    session_db = get_session()
    users_count = session_db.query(User).count()
    purchases = sum(len(u.purchased_blocks) for u in session_db.query(User).all())
    views_count = session_db.query(View).count()
    design = get_design()
    session_db.close()
    return render_template('dashboard.html', users=users_count, purchases=purchases, views=views_count, design=design)

# ====================== Дизайн ======================
@app.route('/design', methods=['GET', 'POST'])
@login_required
def design():
    if request.method == 'POST':
        new_settings = {
            'background_color': request.form['background_color'],
            'text_color': request.form['text_color'],
            'font_family': request.form['font_family'],
        }
        update_design(new_settings)
        return redirect(url_for('dashboard'))
    design = get_design()
    return render_template('design.html', design=design)

# ====================== Блоки ======================
@app.route('/blocks', methods=['GET', 'POST'])
@login_required
def blocks():
    session_db = get_session()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        is_paid = 'is_paid' in request.form
        price = int(request.form.get('price', 0))
        sort_order = int(request.form.get('sort_order', 0))
        block = Block(name=name, description=description, is_paid=is_paid, price=price, sort_order=sort_order)
        session_db.add(block)
        session_db.commit()
        add_audit_log('add_block', name)
        return redirect(url_for('blocks'))
    blocks = session_db.query(Block).order_by(Block.sort_order).all()
    session_db.close()
    return render_template('blocks.html', blocks=blocks)

@app.route('/edit_block/<int:block_id>', methods=['GET', 'POST'])
@login_required
def edit_block(block_id):
    session_db = get_session()
    block = session_db.query(Block).get(block_id)
    if not block:
        abort(404)
    if request.method == 'POST':
        block.name = request.form['name']
        block.description = request.form.get('description', '')
        block.is_paid = 'is_paid' in request.form
        block.price = int(request.form.get('price', 0))
        block.sort_order = int(request.form.get('sort_order', 0))
        session_db.commit()
        add_audit_log('edit_block', block.name)
        return redirect(url_for('blocks'))
    session_db.close()
    return render_template('edit_block.html', block=block)

@app.route('/delete_block/<int:block_id>')
@login_required
def delete_block(block_id):
    session_db = get_session()
    block = session_db.query(Block).get(block_id)
    if block:
        session_db.delete(block)
        session_db.commit()
        add_audit_log('delete_block', str(block_id))
    session_db.close()
    return redirect(url_for('blocks'))

# ====================== Вопросы ======================
@app.route('/questions/<int:block_id>', methods=['GET', 'POST'])
@login_required
def questions(block_id):
    session_db = get_session()
    block = session_db.query(Block).get(block_id)
    if not block:
        abort(404)
    if request.method == 'POST':
        text = request.form['text']
        sort_order = int(request.form.get('sort_order', 0))
        question = Question(block_id=block_id, text=text, sort_order=sort_order)
        session_db.add(question)
        session_db.commit()
        add_audit_log('add_question', text[:50])
        return redirect(url_for('questions', block_id=block_id))
    questions = session_db.query(Question).filter_by(block_id=block_id).order_by(Question.sort_order).all()
    session_db.close()
    return render_template('questions.html', questions=questions, block=block)

@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    session_db = get_session()
    question = session_db.query(Question).get(question_id)
    if not question:
        abort(404)
    if request.method == 'POST':
        question.text = request.form['text']
        question.sort_order = int(request.form.get('sort_order', 0))
        session_db.commit()
        add_audit_log('edit_question', question.text[:50])
        return redirect(url_for('questions', block_id=question.block_id))
    session_db.close()
    return render_template('edit_question.html', question=question)

@app.route('/delete_question/<int:question_id>')
@login_required
def delete_question(question_id):
    session_db = get_session()
    question = session_db.query(Question).get(question_id)
    if question:
        block_id = question.block_id
        session_db.delete(question)
        session_db.commit()
        add_audit_log('delete_question', str(question_id))
    session_db.close()
    return redirect(url_for('questions', block_id=block_id))

# ====================== Аналитика ======================
@app.route('/analytics')
@login_required
def analytics():
    session_db = get_session()
    logs = session_db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()
    session_db.close()
    return render_template('analytics.html', logs=logs)

# ====================== Экспорт пользователей ======================
@app.route('/export/users')
@login_required
def export_users():
    session_db = get_session()
    users = session_db.query(User).all()
    data = [{
        'user_id': u.user_id,
        'username': u.username or '',
        'first_name': u.first_name or '',
        'purchased_blocks': ','.join(map(str, u.purchased_blocks)),
        'created_at': u.created_at
    } for u in users]
    df = pd.DataFrame(data)
    path = '/tmp/users_export.csv'
    df.to_csv(path, index=False)
    session_db.close()
    return send_file(path, as_attachment=True, download_name='users.csv')

# ====================== Рассылка из админки ======================
@app.route('/broadcast', methods=['GET', 'POST'])
@login_required
def broadcast():
    if request.method == 'POST':
        text = request.form.get('text', '')
        media = request.files.get('media')
        media_path = None
        if media:
            media_path = f'/tmp/{media.filename}'
            media.save(media_path)
        
        async def send_broadcast():
            session_db = get_session()
            users = session_db.query(User).all()
            for user in users:
                try:
                    if media_path:
                        if media.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                            await bot.send_photo(user.user_id, open(media_path, 'rb'), caption=text, parse_mode='Markdown')
                        elif media.filename.lower().endswith(('.mp4', '.avi')):
                            await bot.send_video(user.user_id, open(media_path, 'rb'), caption=text, parse_mode='Markdown')
                        else:
                            await bot.send_document(user.user_id, open(media_path, 'rb'), caption=text, parse_mode='Markdown')
                    else:
                        await bot.send_message(user.user_id, text, parse_mode='Markdown')
                except Exception as e:
                    logging.error(f"Broadcast error to {user.user_id}: {e}")
            session_db.close()
            if media_path and os.path.exists(media_path):
                os.remove(media_path)
        
        asyncio.run(send_broadcast())
        add_audit_log('broadcast_from_admin', text[:50])
        return redirect(url_for('dashboard'))
    
    return render_template('broadcast.html')

# ====================== API для Mini App ======================
@app.route('/api/design')
def api_design():
    return jsonify(get_design())

@app.route('/api/blocks')
def api_blocks():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        abort(400)
    blocks = get_blocks()
    result = []
    for b in blocks:
        accessible = (not b.is_paid) or user_has_block(user_id, b.id)
        result.append({
            'id': b.id,
            'name': b.name,
            'price': b.price,
            'accessible': accessible
        })
    return jsonify(result)

@app.route('/api/questions')
def api_questions():
    block_id = request.args.get('block_id', type=int)
    if not block_id:
        abort(400)
    questions = get_questions(block_id)
    return jsonify([{'id': q.id, 'text': q.text} for q in questions])

@app.route('/api/log_view', methods=['POST'])
def api_log_view():
    data = request.get_json()
    if not data or 'user_id' not in data or 'question_id' not in data:
        abort(400)
    log_view(data['user_id'], data['question_id'])
    return jsonify({'ok': True})

@app.route('/api/all_blocks_price')
def api_all_blocks_price():
    return jsonify({'price': get_all_blocks_price()})

@app.route('/api/create_invoice', methods=['POST'])
def api_create_invoice():
    data = request.get_json()
    if not data or 'user_id' not in data:
        abort(400)
    user_id = data['user_id']
    if 'block_id' in data:
        add_purchase(user_id, data['block_id'])
    elif 'all_blocks' in data and data['all_blocks']:
        buy_all_blocks(user_id)
    return jsonify({'ok': True, 'message': 'Покупка успешна (условно)'})  # Условная покупка

# ====================== Запуск ======================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)