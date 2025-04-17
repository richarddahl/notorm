"""
Setup for asynchronous SQLAlchemy sessions and engine initialization.
"""
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Database URL from environment variable, e.g., "postgresql+asyncpg://user:pass@host/db"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

_engine = None
_SessionLocal = None

def init_engine(database_url: str = None):
    """
    Initialize the async engine and session factory.
    """
    global _engine, _SessionLocal
    url = database_url or DATABASE_URL
    _engine = create_async_engine(url, echo=False, future=True)
    _SessionLocal = sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return _engine

async def get_session() -> AsyncSession:
    """
    Yield a database session for use with dependency injection.
    """
    global _SessionLocal
    if _SessionLocal is None:
        init_engine()
    async with _SessionLocal() as session:
        yield session