from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
from config import DATABASE_URL
import datetime

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(64))
    first_name = Column(String(128))
    last_name = Column(String(128))
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class Block(Base):
    __tablename__ = "blocks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    is_paid = Column(Boolean, default=False)
    price = Column(Float, default=0.0)
    questions = relationship("Question", back_populates="block", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(Integer, ForeignKey("blocks.id"), nullable=False)
    text = Column(Text, nullable=False)
    order = Column(Integer, default=0)
    block = relationship("Block", back_populates="questions")


class View(Base):
    __tablename__ = "views"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    viewed_at = Column(DateTime, server_default=func.now())


class Purchase(Base):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    block_id = Column(Integer, ForeignKey("blocks.id"), nullable=False)
    purchased_at = Column(DateTime, server_default=func.now())


class Design(Base):
    __tablename__ = "design"
    id = Column(Integer, primary_key=True)
    settings = Column(JSON, default=dict)  # {"bg": "#121212", "text": "#e0e0e0", "font": "system-ui"}


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer)  # telegram id
    action = Column(String(255))
    details = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


def init_db():
    Base.metadata.create_all(bind=engine)
