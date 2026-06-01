import random
import hashlib
from datetime import datetime, timedelta, timezone
from app.config import settings


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def otp_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
