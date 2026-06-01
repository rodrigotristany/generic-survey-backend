import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_admin, get_db, get_optional_user
from app.models.admin_user import AdminUser
from app.models.user import User
from app.schemas.response import SubmitResponseRequest, SurveyResponseOut
from app.services import response as svc

router = APIRouter(prefix="/responses", tags=["Responses"])


@router.post("/surveys/{survey_id}/start", response_model=SurveyResponseOut, status_code=201)
async def start_response(
    survey_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    user_id = current_user.id if current_user else None
    return await svc.start_response(db, survey_id, user_id)


@router.post("/{response_id}/submit", response_model=SurveyResponseOut)
async def submit_response(
    response_id: uuid.UUID,
    data: SubmitResponseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    user_id = current_user.id if current_user else None
    return await svc.submit_response(db, response_id, data, user_id)


@router.get("/{response_id}", response_model=SurveyResponseOut)
async def get_response(
    response_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    return await svc.get_response(db, response_id)


@router.get("/surveys/{survey_id}", response_model=list[SurveyResponseOut])
async def list_survey_responses(
    survey_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    return await svc.list_survey_responses(db, survey_id)
