"""Database session management"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from app.config import settings

# --- SQLite UUID compatibility -------------------------------------------------
# When using SQLite, the PostgreSQL UUID type isn't natively supported. We
# monkeypatch the SQLite type compiler to render UUID columns as CHAR(36),
# allowing us to keep using UUID columns in models across backends.
try:
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler  # type: ignore

    def _visit_UUID(self, type_, **kw):
        return "CHAR(36)"

    # Add handler if not already present
    if not hasattr(SQLiteTypeCompiler, "visit_UUID"):
        SQLiteTypeCompiler.visit_UUID = _visit_UUID  # type: ignore[attr-defined]
except Exception:
    # Safe to ignore if dialect/module isn't present
    pass
# ------------------------------------------------------------------------------

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections"""
    await engine.dispose()
