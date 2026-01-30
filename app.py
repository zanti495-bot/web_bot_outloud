from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import os
import io
import pandas as pd
from datetime import datetime
from database import db, Block, Question, User, View, Design, AuditLog, Purchase, Base, engine
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "Kjwje18J_kemfjcijwjnjfnkwnfkewjnl_k2i13ji2iuUUUWJDJ_Kfijwoejnf")

# Безопасная инициализация таблиц БД
with app.app_context():
    from database import init_db
    if not init_db(max_attempts=5, delay=3):
        print(f"[{datetime.now()}] Критическая ошибка: БД не инициализирована. Приложение может работать некорректно.")
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
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error="Неверный пароль")
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

# Дашборд
@app.route('/admin')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
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
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        name = request.form['name']
        is_paid = 'is_paid' in request.form
        price = float(request.form.get('price', 0))
        block = Block(name=name, is_paid=is_paid, price=price)
        db.session.add(block)
        db.session.commit()
        AuditLog.log(f'Добавлен блок: {name}')
    blocks = db.session.query(Block).all()
    return render_template('blocks.html', blocks=blocks)

# Вопросы в блоке
@app.route('/admin/questions/<int:block_id>', methods=['GET', 'POST'])
def admin_questions(block_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    block = db.session.get(Block, block_id)
    if not block:
        return "Блок не найден", 404
    if request.method == 'POST':
        text = request.form['text']
        question = Question(text=text, block_id=block_id)
        db.session.add(question)
        db.session.commit()
        AuditLog.log(f'Добавлен вопрос в блок {block_id}')
    questions = db.session.query(Question).filter_by(block_id=block_id).all()
    return render_template('questions.html', block=block, questions=questions)

# Дизайн Mini App
@app.route('/admin/design', methods=['GET', 'POST'])
def admin_design():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    design = db.session.query(Design).first() or Design()
    if request.method == 'POST':
        design.settings = {
            'background_color': request.form['background_color'],
            'text_color': request.form['text_color'],
            'font_family': request.form['font_family']
        }
        db.session.add(design)
        db.session.commit()
        AuditLog.log('Обновлён дизайн')
    settings = design.settings if design else {}
    return render_template('design.html', design=settings)

# Рассылка
@app.route('/admin/broadcast', methods=['GET', 'POST'])
def admin_broadcast():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        message = request.form['message']
        from bot import send_broadcast
        send_broadcast(message)
        AuditLog.log('Отправлена рассылка')
    return render_template('broadcast.html')

# Аналитика
@app.route('/admin/analytics')
def admin_analytics():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    top_blocks = db.session.query(Block.name, func.count(View.id))\
        .join(View, Block.id == Question.block_id, View.question_id == Question.id)\
        .group_by(Block.id)\
        .order_by(func.count(View.id).desc())\
        .limit(5).all()
    return render_template('analytics.html', top_blocks=top_blocks)

# Пользователи
@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    query = request.form.get('query', '') if request.method == 'POST' else ''
    if query:
        users = db.session.query(User).filter(
            (User.username.ilike(f'%{query}%')) | (User.telegram_id == query)
        ).all()
    else:
        users = db.session.query(User).all()
    return render_template('users.html', users=users)

@app.route('/admin/block_user/<int:user_id>', methods=['POST'])
def block_user(user_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    user = db.session.get(User, user_id)
    if user:
        user.blocked = True
        db.session.commit()
        AuditLog.log(f'Заблокирован пользователь {user_id}')
    return redirect(url_for('admin_users'))

@app.route('/admin/unblock_user/<int:user_id>', methods=['POST'])
def unblock_user(user_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    user = db.session.get(User, user_id)
    if user:
        user.blocked = False
        db.session.commit()
        AuditLog.log(f'Разблокирован пользователь {user_id}')
    return redirect(url_for('admin_users'))

@app.route('/admin/user_views/<int:user_id>')
def user_views(user_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    views = db.session.query(View).filter_by(user_id=user_id)\
        .order_by(View.timestamp.desc()).limit(10).all()
    return render_template('user_views.html', views=views)

# Логи аудита
@app.route('/admin/logs')
def admin_logs():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    logs = db.session.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
    return render_template('logs.html', logs=logs)

@app.route('/admin/clear_logs', methods=['POST'])
def clear_logs():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    db.session.query(AuditLog).delete()
    db.session.commit()
    return redirect(url_for('admin_logs'))

# Экспорт пользователей в CSV
@app.route('/admin/export_users')
def export_users():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    users = db.session.query(User).all()
    df = pd.DataFrame([{
        'id': u.id,
        'username': u.username,
        'telegram_id': u.telegram_id,
        'blocked': u.blocked
    } for u in users])
    output = io.BytesIO()
    df.to_csv(output, index=False, encoding='utf-8')
    output.seek(0)
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='users.csv'
    )

# API для Mini App
@app.route('/api/blocks')
def api_blocks():
    blocks = db.session.query(Block).all()
    return jsonify([{'id': b.id, 'name': b.name, 'is_paid': b.is_paid, 'price': b.price} for b in blocks])

@app.route('/api/questions/<int:block_id>')
def api_questions(block_id):
    questions = db.session.query(Question).filter_by(block_id=block_id).all()
    return jsonify([{'id': q.id, 'text': q.text} for q in questions])

@app.route('/api/design')
def api_design():
    design = db.session.query(Design).first()
    return jsonify(design.settings if design else {})

@app.route('/api/purchase', methods=['POST'])
def api_purchase():
    data = request.json
    user_id = data['user_id']
    block_id = data.get('block_id')  # None = все блоки
    purchase = Purchase(user_id=user_id, block_id=block_id)
    db.session.add(purchase)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/check_purchase/<int:user_id>/<int:block_id>')
def api_check_purchase(user_id, block_id):
    purchased = db.session.query(Purchase).filter_by(user_id=user_id, block_id=block_id).first() is not None
    return jsonify({'purchased': purchased})

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), debug=True)
