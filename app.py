from flask import Flask, render_template, request, redirect, url_for, jsonify, session, Response
from functools import wraps
import os
from database import SessionLocal, User, Block, Question, View, Purchase, Design, AuditLog, init_db
from config import ADMIN_TELEGRAM_ID, ADMIN_PASSWORD, FLASK_SECRET_KEY
import pandas as pd
from io import StringIO

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

init_db()

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/health")
def health():
    return "OK", 200


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("login"))


@app.route("/")
@admin_required
def dashboard():
    with SessionLocal() as db:
        users_count = db.query(User).count()
        views_count = db.query(View).count()
        purchases_count = db.query(Purchase).count()
        top_blocks = db.query(Block.title, func.count(View.id).label("views"))\
            .join(Question).join(View).group_by(Block.id).order_by(func.count(View.id).desc()).limit(5).all()
    return render_template("dashboard.html", users=users_count, views=views_count,
                           purchases=purchases_count, top_blocks=top_blocks)


@app.route("/blocks")
@admin_required
def blocks():
    with SessionLocal() as db:
        blocks = db.query(Block).all()
    return render_template("blocks.html", blocks=blocks)


@app.route("/api/blocks", methods=["POST"])
@admin_required
def api_create_block():
    data = request.json
    with SessionLocal() as db:
        block = Block(
            title=data["title"],
            description=data.get("description"),
            is_paid=data.get("is_paid", False),
            price=data.get("price", 0.0)
        )
        db.add(block)
        db.commit()
        db.refresh(block)
        log_action("create_block", f"Создан блок {block.id} — {block.title}")
    return jsonify({"id": block.id})


# Другие API-эндпоинты (update/delete block, questions, design, broadcast и т.д.)
# опущены для краткости — реализуются аналогично


@app.route("/users/export")
@admin_required
def export_users():
    with SessionLocal() as db:
        users = db.query(User.telegram_id, User.username, User.first_name, User.last_name, User.created_at).all()
    output = StringIO()
    df = pd.DataFrame(users, columns=["id", "username", "first_name", "last_name", "registered"])
    df.to_csv(output, index=False)
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=users.csv"}
    )


def log_action(action, details):
    with SessionLocal() as db:
        log = AuditLog(admin_id=ADMIN_TELEGRAM_ID, action=action, details=details)
        db.add(log)
        db.commit()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
