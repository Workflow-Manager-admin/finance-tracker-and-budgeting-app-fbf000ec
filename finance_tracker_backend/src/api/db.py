"""
Database configuration and models for the Finance Tracker backend.
Implements SQLAlchemy ORM models, session management, and DB initialization/migration logic.
"""

import os
from typing import Generator
from sqlalchemy import create_engine, Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# Parse database URL from .env (examples: "sqlite:///./test.db" or PostgreSQL/MySQL URLs)
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./finance_tracker.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# -------------------------------
# ORM MODELS
# -------------------------------

class UserORM(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    transactions = relationship("TransactionORM", back_populates="user", cascade="all, delete-orphan")

class TransactionORM(Base):
    __tablename__ = "transactions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    category = Column(String, nullable=False)
    type = Column(String, nullable=False)  # "income" or "expense"
    date = Column(DateTime, nullable=False)
    description = Column(String, nullable=True)
    user = relationship("UserORM", back_populates="transactions")


# -------------------------------
# SESSION UTILS
# -------------------------------

# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """
    Dependency to provide a SQLAlchemy session to FastAPI endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------
# DB INIT & MIGRATION
# -------------------------------

# PUBLIC_INTERFACE
def init_db():
    """
    Create all DB tables if they do not exist.
    """
    Base.metadata.create_all(bind=engine)
