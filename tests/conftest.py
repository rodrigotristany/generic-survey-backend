import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings

# NullPool avoids connection reuse between tests, which prevents asyncpg
# from seeing a "operation in progress" state from a previous test.
_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    """
    Yields an AsyncSession bound to an explicit connection whose transaction
    is always rolled back after the test. Tests must use flush() instead of
    commit() — flush() sends SQL to the DB within the open transaction without
    committing it, so the teardown rollback undoes everything cleanly.
    """
    conn = await _engine.connect()
    trans = await conn.begin()
    session = AsyncSession(bind=conn, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()
        if trans.is_active:
            await trans.rollback()
        await conn.close()
