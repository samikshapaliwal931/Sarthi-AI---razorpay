from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = structlog.get_logger()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:  # type: ignore[misc]
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _apply_incremental_column_additions(conn)
    logger.info("database_initialized")


async def _apply_incremental_column_additions(conn: Any) -> None:
    """Best-effort column backfill for tables created before a model gained a column.

    There is no Alembic migration history for this project (schema is bootstrapped via
    ``create_all``), so newly added nullable columns need to be added to already-existing
    tables by hand. This only runs `ADD COLUMN IF NOT EXISTS`, which is safe to repeat.
    """
    from sqlalchemy import text

    if not engine.url.get_backend_name().startswith("postgresql"):
        return

    statements = [
        "ALTER TABLE merchants ADD COLUMN IF NOT EXISTS ai_buyer_api_key_hash VARCHAR(64)",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_merchants_ai_buyer_api_key_hash "
        "ON merchants (ai_buyer_api_key_hash)",
    ]
    for stmt in statements:
        await conn.execute(text(stmt))


async def close_db() -> None:
    await engine.dispose()
    logger.info("database_closed")
