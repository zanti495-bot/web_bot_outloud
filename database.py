import json
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import config

engine = create_engine(config.DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class Block(Base):
    __tablename__ = 'blocks'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    is_paid = Column(Boolean, default=False)
    price = Column(Integer, default=0)
    sort_order = Column(Integer, default=0)
    questions = relationship('Question', backref='block')

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    block_id = Column(Integer, ForeignKey('blocks.id'), nullable=False)
    text = Column(String, nullable=False)
    sort_order = Column(Integer, default=0)

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    first_name = Column(String)
    purchased_blocks = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

class View(Base):
    __tablename__ = 'views'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    question_id = Column(Integer, ForeignKey('questions.id'))
    viewed_at = Column(DateTime, default=datetime.utcnow)

class Design(Base):
    __tablename__ = 'design'
    id = Column(Integer, primary_key=True)
    settings = Column(JSON, default=config.DEFAULT_DESIGN)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    action = Column(String)
    details = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Создание таблиц
Base.metadata.create_all(engine)

# Функции для работы с БД
def get_session():
    return Session()

def add_audit_log(action, details):
    session = get_session()
    log = AuditLog(action=action, details=details)
    session.add(log)
    session.commit()
    session.close()