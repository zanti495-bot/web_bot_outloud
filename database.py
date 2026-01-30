from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import os

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("Переменная окружения DATABASE_URL не установлена!")

engine = create_engine(
    DATABASE_URL,
    echo=False,                     # можно поставить True для отладки
    pool_pre_ping=True,             # проверяет соединение перед использованием
    pool_size=5,
    max_overflow=10,
    pool_timeout=30
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    """Генератор сессии для использования в зависимостях / with-блоках"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
