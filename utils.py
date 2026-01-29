import json
from database import get_session, User, Block, Question, View, Design, add_audit_log
import config

def get_user(user_id, username=None, first_name=None):
    session = get_session()
    user = session.query(User).filter_by(user_id=user_id).first()
    if not user:
        user = User(user_id=user_id, username=username, first_name=first_name)
        session.add(user)
        session.commit()
    else:
        if username:
            user.username = username
        if first_name:
            user.first_name = first_name
        session.commit()
    session.close()
    return user

def get_blocks():
    session = get_session()
    blocks = session.query(Block).order_by(Block.sort_order).all()
    session.close()
    return blocks

def get_questions(block_id):
    session = get_session()
    questions = session.query(Question).filter_by(block_id=block_id).order_by(Question.sort_order).all()
    session.close()
    return questions

def user_has_block(user_id, block_id):
    user = get_user(user_id)
    return block_id in user.purchased_blocks

def add_purchase(user_id, block_id):
    session = get_session()
    user = session.query(User).filter_by(user_id=user_id).first()
    if block_id not in user.purchased_blocks:
        user.purchased_blocks.append(block_id)
        session.commit()
        add_audit_log('add_purchase', f"user {user_id} block {block_id}")
    session.close()

def get_all_blocks_price():
    session = get_session()
    paid_blocks = session.query(Block).filter_by(is_paid=True).all()
    total = sum(block.price for block in paid_blocks)
    session.close()
    return total * 0.8  # Скидка 20% для "все блоки"

def buy_all_blocks(user_id):
    session = get_session()
    user = session.query(User).filter_by(user_id=user_id).first()
    paid_blocks = session.query(Block).filter_by(is_paid=True).all()
    for block in paid_blocks:
        if block.id not in user.purchased_blocks:
            user.purchased_blocks.append(block.id)
    session.commit()
    add_audit_log('buy_all', f"user {user_id}")
    session.close()

def log_view(user_id, question_id):
    session = get_session()
    view = View(user_id=user_id, question_id=question_id)
    session.add(view)
    session.commit()
    session.close()

def get_design():
    session = get_session()
    design = session.query(Design).first()
    if not design:
        design = Design(settings=config.DEFAULT_DESIGN)
        session.add(design)
        session.commit()
    session.close()
    return design.settings

def update_design(new_settings):
    session = get_session()
    design = session.query(Design).first()
    if not design:
        design = Design()
        session.add(design)
    design.settings = new_settings
    session.commit()
    session.close()
    add_audit_log('update_design', json.dumps(new_settings))