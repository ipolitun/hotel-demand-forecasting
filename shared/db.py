from datetime import datetime
from sqlalchemy import create_engine, DateTime, func
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from shared.db_config import database_config


# === Синхронное подключение ===
sync_engine = create_engine(database_config.sync_url, echo=False)
SessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)


def get_sync_session():
    """Dependency для FastAPI (sync)."""
    with SessionLocal() as session:
        yield session


# === Асинхронное подключение ===
async_engine = create_async_engine(database_config.async_url, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session():
    """Dependency для FastAPI (async)."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_models():
    """Создание всех таблиц в БД (async)."""
    async with async_engine.begin() as session:
        await session.run_sync(Base.metadata.create_all)


# === Базовый класс для всех моделей ===
class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

