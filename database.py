import json
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import config
from sqlalchemy.exc import ArgumentError, OperationalError
# SAImportError не нужен — используйте встроенный ImportError 

engine = None
Session = None
Base = declarative_base()

# Пытаемся создать engine с отловом ошибок
try:
    print(f"Попытка подключения к БД с URL: {config.DATABASE_URL}")
    engine = create_engine(config.DATABASE_URL, echo=False)  # echo=True для отладки логов БД
    Session = sessionmaker(bind=engine)
    print("Engine успешно создан")
except ArgumentError as e:
    print(f"Ошибка парсинга DATABASE_URL: {e}")
    print("Проверьте формат URL в настройках Timeweb (должен начинаться с postgresql+psycopg://)")
    raise
except OperationalError as e:
    print(f"Ошибка подключения к базе данных: {e}")
    print("Возможные причины: неверный пароль, хост недоступен, БД не существует, или нужен/ненужен sslmode")
    raise
except SAImportError as e:
    print(f"Ошибка импорта драйвера БД (psycopg или psycopg2 не установлен или не найден): {e}")
    print("Убедитесь, что в requirements.txt есть psycopg и URL использует +psycopg")
    raise
except Exception as e:
    print(f"Неизвестная ошибка при создании engine: {e}")
    raise

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
try:
    Base.metadata.create_all(engine)
    print("Таблицы успешно созданы или уже существуют")
except Exception as e:
    print(f"Ошибка при создании таблиц: {e}")

# Функции для работы с БД
def get_session():
    return Session()

def add_audit_log(action, details):
    session = get_session()
    log = AuditLog(action=action, details=details)
    session.add(log)
    session.commit()
    session.close()
