import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.otp import OtpCode
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user_auth import TokenResponse, UserResponse
from app.utils.jwt import create_access_token, create_refresh_token
from app.utils.otp import generate_otp, hash_otp, otp_expiry
from app.utils.password import hash_password, validate_password_strength, verify_password


async def register(db: AsyncSession, email: str, password: str, full_name: str | None) -> UserResponse:
    try:
        validate_password_strength(password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=email, hashed_password=hash_password(password), full_name=full_name)
    db.add(user)
    await db.flush()
    return UserResponse.model_validate(user)


async def login(db: AsyncSession, email: str, password: str) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    return await _issue_tokens(db, user)


async def logout(db: AsyncSession, refresh_token_str: str) -> None:
    token_hash = _hash_token(refresh_token_str)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    token = result.scalar_one_or_none()
    if token:
        token.revoked = True
        await db.flush()


async def verify_otp(db: AsyncSession, email: str, otp_code: str) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")
    await _consume_otp(db, user.id, "user", otp_code, "login_otp")
    return await _issue_tokens(db, user)


async def request_password_recovery(db: AsyncSession, email: str) -> None:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return
    code = generate_otp()
    db.add(OtpCode(
        code_hash=hash_otp(code),
        user_id=user.id,
        user_type="user",
        purpose="password_recovery",
        expires_at=otp_expiry(),
    ))
    await db.flush()
    # TODO: integrate email provider to send `code` to user.email


async def confirm_password_recovery(db: AsyncSession, email: str, otp_code: str, new_password: str) -> None:
    try:
        validate_password_strength(new_password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")
    await _consume_otp(db, user.id, "user", otp_code, "password_recovery")
    user.hashed_password = hash_password(new_password)
    await db.flush()


async def refresh_tokens(db: AsyncSession, refresh_token_str: str) -> TokenResponse:
    token_hash = _hash_token(refresh_token_str)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_type == "user",
            RefreshToken.revoked == False,  # noqa: E712
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    token = result.scalar_one_or_none()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    user = await db.get(User, token.user_id)
    if not user or not user.enabled:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not available")
    token.revoked = True
    await db.flush()
    return await _issue_tokens(db, user)


async def _issue_tokens(db: AsyncSession, user: User) -> TokenResponse:
    access = create_access_token(str(user.id), {"type": "user"})
    refresh = create_refresh_token(str(user.id))
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(
        token_hash=_hash_token(refresh),
        user_id=user.id,
        user_type="user",
        expires_at=expires_at,
    ))
    await db.flush()
    return TokenResponse(access_token=access, refresh_token=refresh)


async def _consume_otp(
    db: AsyncSession,
    user_id: uuid.UUID,
    user_type: str,
    code: str,
    purpose: str,
) -> OtpCode:
    result = await db.execute(
        select(OtpCode).where(
            OtpCode.code_hash == hash_otp(code),
            OtpCode.user_id == user_id,
            OtpCode.user_type == user_type,
            OtpCode.purpose == purpose,
            OtpCode.used == False,  # noqa: E712
            OtpCode.expires_at > datetime.now(timezone.utc),
        )
    )
    otp = result.scalar_one_or_none()
    if not otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
    otp.used = True
    await db.flush()
    return otp


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
