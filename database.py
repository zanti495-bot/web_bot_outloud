from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import OperationalError, DatabaseError
from datetime import datetime
import os
import time
import logging

logging.basicConfig(level=logging.DEBUG)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    blocked = Column(Boolean, default=False)

class Block(Base):
    __tablename__ = 'blocks'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    is_paid = Column(Boolean, default=False)
    price = Column(Float, default=0.0)
    questions = relationship('Question', backref='block')

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    text = Column(String)
    block_id = Column(Integer, ForeignKey('blocks.id'))

class View(Base):
    __tablename__ = 'views'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    question_id = Column(Integer, ForeignKey('questions.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)

class Design(Base):
    __tablename__ = 'design'
    id = Column(Integer, primary_key=True)
    settings = Column(JSON)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    action = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    @staticmethod
    def log(action):
        log = AuditLog(action=action)
        db.session.add(log)
        db.session.commit()

class Purchase(Base):
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    block_id = Column(Integer, ForeignKey('blocks.id'), nullable=True)  # None для всех блоков

# ENGINE из ENV
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не установлен в переменных окружения!")

# Добавляем sslmode=require (упростил, если verify-full не работает; верните если нужно)
if "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10,
    connect_args={'sslmode': 'require'}
)

Session = sessionmaker(bind=engine)
db = Session()

def init_db(max_attempts=10, delay=5):
    attempt = 1
    while attempt <= max_attempts:
        try:
            Base.metadata.create_all(engine, checkfirst=True)
            logging.info(f"[{datetime.now()}] Таблицы успешно созданы или уже существуют")
            return True
        except (OperationalError, DatabaseError) as e:
            logging.error(f"[{datetime.now()}] Попытка {attempt}/{max_attempts} — ошибка БД: {str(e)}")
            if attempt < max_attempts:
                time.sleep(delay)
            attempt += 1
        except Exception as e:
            logging.error(f"[{datetime.now()}] Неожиданная ошибка: {str(e)}")
            break
    logging.error(f"[{datetime.now()}] Не удалось инициализировать БД после {max_attempts} попыток")
    return False
