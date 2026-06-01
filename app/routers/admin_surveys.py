import uuid
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_admin, get_db
from app.models.admin_user import AdminUser
from app.models.survey import SurveyStatus
from app.schemas.survey import SurveyCreate, SurveyListItem, SurveyOut, SurveyUpdate, QuestionCreate, QuestionUpdate
from app.services import survey as svc

router = APIRouter(prefix="/admin/surveys", tags=["Admin Surveys"])


@router.post("", response_model=SurveyOut, status_code=201)
async def create_survey(
    data: SurveyCreate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
):
    return await svc.create_survey(db, data, admin)


@router.get("", response_model=list[SurveyListItem])
async def list_surveys(
    status: Optional[SurveyStatus] = None,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    return await svc.list_surveys(db, status)


@router.get("/{survey_id}", response_model=SurveyOut)
async def get_survey(
    survey_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    return await svc.get_survey(db, survey_id)


@router.patch("/{survey_id}", response_model=SurveyOut)
async def update_survey(
    survey_id: uuid.UUID,
    data: SurveyUpdate,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    return await svc.update_survey(db, survey_id, data)


@router.delete("/{survey_id}", status_code=204)
async def delete_survey(
    survey_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    await svc.delete_survey(db, survey_id)


@router.post("/{survey_id}/questions", response_model=SurveyOut, status_code=201)
async def add_question(
    survey_id: uuid.UUID,
    data: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    return await svc.add_question(db, survey_id, data)


@router.patch("/{survey_id}/questions/{question_id}", response_model=SurveyOut)
async def update_question(
    survey_id: uuid.UUID,
    question_id: uuid.UUID,
    data: QuestionUpdate,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    return await svc.update_question(db, survey_id, question_id, data)


@router.delete("/{survey_id}/questions/{question_id}", response_model=SurveyOut)
async def delete_question(
    survey_id: uuid.UUID,
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    return await svc.delete_question(db, survey_id, question_id)
