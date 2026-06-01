from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_admin, get_db
from app.schemas.admin_auth import (
    AdminLoginRequest,
    LogoutRequest,
    MessageResponse,
    OtpVerifyRequest,
    PasswordRecoveryConfirm,
    PasswordRecoveryRequest,
    RefreshRequest,
    TokenResponse,
)
from app.services import admin_auth as svc

router = APIRouter(prefix="/admin/auth", tags=["Admin Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(data: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    return await svc.login(db, data.email, data.password)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    await svc.logout(db, data.refresh_token)
    return MessageResponse(message="logged out")


@router.post("/otp/verify", response_model=TokenResponse)
async def otp_verify(data: OtpVerifyRequest, db: AsyncSession = Depends(get_db)):
    return await svc.verify_otp(db, data.email, data.otp_code)


@router.post("/password-recovery/request", response_model=MessageResponse)
async def password_recovery_request(data: PasswordRecoveryRequest, db: AsyncSession = Depends(get_db)):
    await svc.request_password_recovery(db, data.email)
    return MessageResponse(message="If the email exists, an OTP has been sent")


@router.post("/password-recovery/confirm", response_model=MessageResponse)
async def password_recovery_confirm(data: PasswordRecoveryConfirm, db: AsyncSession = Depends(get_db)):
    await svc.confirm_password_recovery(db, data.email, data.otp_code, data.new_password)
    return MessageResponse(message="password updated")


@router.post("/token/refresh", response_model=TokenResponse)
async def token_refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await svc.refresh_tokens(db, data.refresh_token)
