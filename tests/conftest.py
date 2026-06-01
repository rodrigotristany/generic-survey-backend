import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import settings

_engine = create_async_engine(settings.DATABASE_URL)


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    """
    Yields an AsyncSession whose changes are always rolled back after the test.
    Uses join_transaction_mode="create_savepoint" so any session.flush() /
    session.commit() inside the test operates on a SAVEPOINT, leaving the
    outer transaction uncommitted. The outer rollback at teardown undoes
    everything.
    """
    conn = await _engine.connect()
    await conn.begin()
    session = AsyncSession(bind=conn, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        await session.close()
        await conn.rollback()
        await conn.close()
