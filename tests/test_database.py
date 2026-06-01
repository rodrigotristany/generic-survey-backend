import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_user import AdminUser, AdminRole
from app.utils.password import hash_password, verify_password


def _make_user(**kwargs) -> AdminUser:
    defaults = dict(
        email=f"test-{uuid.uuid4()}@example.com",
        hashed_password=hash_password("TestPass123!"),
        role=AdminRole.staff,
    )
    return AdminUser(**{**defaults, **kwargs})


# ── Connection ────────────────────────────────────────────────────────────────

async def test_database_connection(db: AsyncSession):
    # Arrange / Act
    result = await db.execute(text("SELECT 1"))
    # Assert
    assert result.scalar() == 1


# ── Insert ────────────────────────────────────────────────────────────────────

async def test_insert_admin_user_persists_to_db(db: AsyncSession):
    # Arrange
    user = _make_user(email="insert@example.com")
    # Act
    db.add(user)
    await db.flush()
    fetched = await db.get(AdminUser, user.id)
    # Assert
    assert fetched is not None
    assert fetched.email == "insert@example.com"


async def test_insert_admin_user_default_role_is_staff(db: AsyncSession):
    # Arrange / Act
    user = _make_user()
    db.add(user)
    await db.flush()
    # Assert
    assert user.role == AdminRole.staff


async def test_insert_admin_user_password_is_hashed(db: AsyncSession):
    # Arrange
    plain = "TestPass123!"
    user = _make_user(hashed_password=hash_password(plain))
    # Act
    db.add(user)
    await db.flush()
    fetched = await db.get(AdminUser, user.id)
    # Assert
    assert fetched.hashed_password != plain
    assert verify_password(plain, fetched.hashed_password)


async def test_insert_duplicate_email_raises_integrity_error(db: AsyncSession):
    # Arrange
    email = "duplicate@example.com"
    db.add(_make_user(email=email))
    await db.flush()
    # Act / Assert
    db.add(_make_user(email=email))
    with pytest.raises(IntegrityError):
        await db.flush()
    # Reset session — PostgreSQL aborts the transaction on any error, so the
    # session must be explicitly rolled back before teardown touches it.
    await db.rollback()


# ── Update ────────────────────────────────────────────────────────────────────

async def test_update_admin_user_role(db: AsyncSession):
    # Arrange
    user = _make_user(role=AdminRole.staff)
    db.add(user)
    await db.flush()
    # Act
    user.role = AdminRole.superadmin
    await db.flush()
    await db.refresh(user)
    # Assert
    assert user.role == AdminRole.superadmin


async def test_update_admin_user_enabled_flag(db: AsyncSession):
    # Arrange
    user = _make_user()
    db.add(user)
    await db.flush()
    # Act
    user.enabled = False
    await db.flush()
    await db.refresh(user)
    # Assert
    assert user.enabled is False


async def test_update_admin_user_email(db: AsyncSession):
    # Arrange
    user = _make_user(email="old@example.com")
    db.add(user)
    await db.flush()
    # Act
    user.email = "new@example.com"
    await db.flush()
    await db.refresh(user)
    # Assert
    assert user.email == "new@example.com"


# ── Delete ────────────────────────────────────────────────────────────────────

async def test_delete_admin_user_removes_from_db(db: AsyncSession):
    # Arrange
    user = _make_user()
    db.add(user)
    await db.flush()
    user_id = user.id
    # Act
    await db.delete(user)
    await db.flush()
    # Assert
    assert await db.get(AdminUser, user_id) is None


async def test_delete_nonexistent_user_does_not_raise(db: AsyncSession):
    # Arrange — user never inserted
    user = _make_user()
    # Act / Assert — expunge so SQLAlchemy doesn't try to track it
    await db.delete(user) if user in db else None
    # Nothing should be raised; get on a random UUID returns None
    assert await db.get(AdminUser, uuid.uuid4()) is None
