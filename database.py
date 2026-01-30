import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, DeclarativeBase, scoped_session

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/dbname?sslmode=verify-full&sslrootcert=/etc/ssl/certs/ca.crt')

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db_session():
    return SessionLocal()