import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

load_dotenv()

# Конфигурация подключения к БД
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
ASYNC_DB_URL = DB_URL.replace("postgresql://", "postgresql+asyncpg://")

# Базовый класс моделей
Base = declarative_base()

# Синхронное подключение
engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_sync_session():
    """Dependency для FastAPI (sync)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Асинхронное подключение
async_engine = create_async_engine(ASYNC_DB_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_session():
    """Dependency для FastAPI (async)."""
    async with AsyncSessionLocal() as session:
        yield session

async def init_models():
    """Создание всех таблиц в БД (async)."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
