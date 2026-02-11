"""
Database ORM models using SQLAlchemy with async support.
"""
from datetime import datetime, date
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from pathlib import Path

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool

Base = declarative_base()

# Global async engine and session maker
_engine = None
_async_session = None


class TopicProgress(Base):
    """Track student progress and confidence for each topic."""
    __tablename__ = "topic_progress"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(String, unique=True, nullable=False, index=True)
    confidence = Column(Float, default=0.5)
    times_reviewed = Column(Integer, default=0)
    last_studied = Column(DateTime, nullable=True)
    quiz_attempts = Column(Integer, default=0)
    quiz_correct = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QuizResult(Base):
    """Store quiz question results for tracking performance."""
    __tablename__ = "quiz_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(String, nullable=False, index=True)
    question = Column(Text, nullable=False)
    correct_answer = Column(String, nullable=True)  # For SBA questions
    user_answer = Column(String, nullable=True)
    # Note: Both boolean fields are kept for backward compatibility with different parts of the codebase
    # is_correct is used by quiz_service.py, correct is used by quiz router
    # TODO: Consolidate to single field in future refactor
    is_correct = Column(Boolean, nullable=True)  # Used by quiz_service
    correct = Column(Boolean, nullable=True)  # Used by quiz router - kept for compatibility
    difficulty = Column(String, default="medium")
    # Note: Both datetime fields are kept for backward compatibility
    # timestamp is used by quiz_service.py, quiz_date is used by quiz router
    # TODO: Consolidate to single field in future refactor
    timestamp = Column(DateTime, default=datetime.utcnow)  # Used by quiz_service
    quiz_date = Column(DateTime, default=datetime.utcnow)  # Used by quiz router


class StudySession(Base):
    """Track study sessions for retention/forgetting curve."""
    __tablename__ = "study_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(String, nullable=False, index=True)
    duration = Column(Integer, nullable=False)  # in seconds
    quality = Column(Integer, nullable=True)  # 1-5 rating
    notes = Column(Text, nullable=True)
    session_date = Column(DateTime, default=datetime.utcnow)


class AnkiCard(Base):
    """Store Anki flashcards imported from Anki decks."""
    __tablename__ = "anki_cards"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(String, nullable=True, index=True)
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    deck_name = Column(String, nullable=True)
    tags = Column(String, nullable=True)  # JSON string
    interval = Column(Integer, default=0)  # Current spaced repetition interval in days
    ease_factor = Column(Float, default=2.5)
    due_date = Column(DateTime, nullable=True)
    last_reviewed = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Note(Base):
    """Store student's personal notes."""
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String, nullable=True)  # e.g., "manual", "pdf_page_5", "lecture"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Exam(Base):
    """Track upcoming exams for study planning."""
    __tablename__ = "exams"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    topics_json = Column(Text, nullable=False)  # JSON array of topic IDs
    created_at = Column(DateTime, default=datetime.utcnow)


class StudyPlan(Base):
    """Store generated study plans for exam preparation."""
    __tablename__ = "study_plans"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=True)
    plan_json = Column(Text, nullable=False)  # JSON representation of the study plan
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    """Store chat conversation history with the AI tutor."""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, default="default", index=True)
    role = Column(String, nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


async def init_database(db_path: Path) -> None:
    """
    Initialize the SQLite database with async engine.
    
    Args:
        db_path: Path to SQLite database file
    """
    global _engine, _async_session
    
    # Create parent directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create async engine with SQLite
    database_url = f"sqlite+aiosqlite:///{db_path}"
    _engine = create_async_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    # Create all tables
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session maker
    _async_session = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False
    )


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session context manager.
    
    Usage:
        async with get_session() as db:
            result = await db.execute(...)
            await db.commit()
    """
    if _async_session is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    async with _async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
