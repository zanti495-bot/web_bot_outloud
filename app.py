from flask import Flask, request, jsonify, render_template, redirect, url_for, session, Response, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import os
import json
import asyncio
from datetime import datetime
import pandas as pd
from io import StringIO
from database import SessionLocal, init_db, User, Block, Question, View, Purchase, Design, AuditLog
from config import (
    BOT_TOKEN, ADMIN_TELEGRAM_ID, ADMIN_PASSWORD, FLASK_SECRET_KEY,
    WEBHOOK_URL, WEBHOOK_PATH
)
from bot import bot, dp, process_update  # импортируем из bot.py

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# Ограничение запросов (защита от DDoS/брута)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

init_db()

# ─── Декораторы ──────────────────────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def log_admin_action(action: str, details: str = ""):
    with SessionLocal() as db:
        log = AuditLog(
            admin_id=ADMIN_TELEGRAM_ID,
            action=action,
            details=details[:1000],
            created_at=datetime.utcnow()
        )
        db.add(log)
        db.commit()


# ─── Health & Webhook ────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return "OK", 200


@app.route(WEBHOOK_PATH, methods=["POST"])
@limiter.limit("100 per minute")
async def webhook():
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != "your-secret-token-very-long-random":  # ← задай в Timeweb
        abort(403)

    update = await request.get_json()
    asyncio.create_task(process_update(update))  # не блокируем flask
    return "", 200


# ─── Admin Auth ──────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            session.permanent = True
            log_admin_action("login_success")
            return redirect(url_for("dashboard"))
        log_admin_action("login_failed", request.remote_addr)
    return render_template("login.html")


@app.route("/logout")
@admin_required
def logout():
    session.pop("admin_logged_in", None)
    log_admin_action("logout")
    return redirect(url_for("login"))


# ─── Dashboard ───────────────────────────────────────────────────────────────

@app.route("/")
@admin_required
def dashboard():
    with SessionLocal() as db:
        stats = {
            "users_total": db.query(User).count(),
            "users_blocked": db.query(User).filter(User.is_blocked == True).count(),
            "views_total": db.query(View).count(),
            "purchases_total": db.query(Purchase).count(),
            "top_blocks": db.query(Block.title, db.func.count(View.id).label("views"))
                .join(Question).join(View).group_by(Block.id, Block.title)
                .order_by(db.func.count(View.id).desc()).limit(5).all(),
        }
    return render_template("dashboard.html", stats=stats)


# ─── Blocks CRUD ─────────────────────────────────────────────────────────────

@app.route("/blocks")
@admin_required
def blocks_list():
    with SessionLocal() as db:
        blocks = db.query(Block).order_by(Block.id.desc()).all()
    return render_template("blocks.html", blocks=blocks)


@app.route("/api/blocks", methods=["POST"])
@admin_required
@limiter.limit("20 per minute")
def api_block_create():
    data = request.json
    required = {"title"}
    if not all(k in data for k in required):
        return jsonify({"error": "missing fields"}), 400

    with SessionLocal() as db:
        block = Block(
            title=data["title"],
            description=data.get("description", ""),
            is_paid=bool(data.get("is_paid", False)),
            price=float(data.get("price", 0.0))
        )
        db.add(block)
        db.commit()
        db.refresh(block)

    log_admin_action("block_created", f"id={block.id} title={block.title}")
    return jsonify({"id": block.id, "title": block.title})


@app.route("/api/blocks/<int:block_id>", methods=["PUT", "DELETE"])
@admin_required
def api_block_update_delete(block_id):
    with SessionLocal() as db:
        block = db.query(Block).get(block_id)
        if not block:
            return jsonify({"error": "not found"}), 404

        if request.method == "DELETE":
            db.delete(block)
            db.commit()
            log_admin_action("block_deleted", f"id={block_id}")
            return jsonify({"success": True})

        # PUT — update
        data = request.json
        block.title = data.get("title", block.title)
        block.description = data.get("description", block.description)
        block.is_paid = bool(data.get("is_paid", block.is_paid))
        block.price = float(data.get("price", block.price))
        db.commit()
        log_admin_action("block_updated", f"id={block_id}")
        return jsonify({"success": True})


# ─── Broadcast (рассылка) ────────────────────────────────────────────────────

@app.route("/broadcast", methods=["GET", "POST"])
@admin_required
async def broadcast():
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        photo = request.files.get("photo")

        if not text and not photo:
            return render_template("broadcast.html", error="Нужен хотя бы текст или фото")

        with SessionLocal() as db:
            users = db.query(User.telegram_id).filter(User.is_blocked == False).all()

        success = 0
        failed = 0
        delay = 0.033  # ~30 сообщений в секунду — безопасно

        for (user_id,) in users:
            try:
                if photo:
                    await bot.send_photo(
                        chat_id=user_id,
                        photo=photo.read(),
                        caption=text,
                        parse_mode="HTML"
                    )
                else:
                    await bot.send_message(
                        chat_id=user_id,
                        text=text,
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )
                success += 1
            except Exception as e:
                failed += 1
                if "blocked" in str(e) or "deactivated" in str(e):
                    with SessionLocal() as db:
                        u = db.query(User).filter(User.telegram_id == user_id).first()
                        if u:
                            u.is_blocked = True
                            db.commit()

            await asyncio.sleep(delay)

        log_admin_action("broadcast_sent", f"success={success}, failed={failed}, text_len={len(text)}")
        return render_template("broadcast.html", success=f"Отправлено: {success}, ошибок: {failed}")

    return render_template("broadcast.html")


# ─── Export CSV ──────────────────────────────────────────────────────────────

@app.route("/users/export")
@admin_required
def export_users():
    with SessionLocal() as db:
        query = db.query(
            User.telegram_id,
            User.username,
            User.first_name,
            User.last_name,
            User.is_blocked,
            User.created_at
        ).all()

    output = StringIO()
    df = pd.DataFrame(query, columns=["id", "username", "first", "last", "blocked", "registered"])
    df.to_csv(output, index=False, encoding="utf-8-sig")
    output.seek(0)

    return Response(
        output,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=users_export.csv"}
    )


if __name__ == "__main__":
    # только для локальной отладки
    app.run(host="0.0.0.0", port=8080, debug=True)
