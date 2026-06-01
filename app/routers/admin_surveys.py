import uuid
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_admin, get_db
from app.models.admin_user import AdminUser
from app.models.survey import SurveyStatus
from app.schemas.survey import (
    SurveyCreate, SurveyListItem, SurveyOut, SurveyUpdate,
    SectionCreate, SectionUpdate,
    SurveyGroupCreate, SurveyGroupUpdate,
    GroupQuestionCreate, GroupQuestionLink, GroupQuestionUpdate,
)
from app.services import survey as svc

router = APIRouter(prefix="/admin/surveys", tags=["Admin Surveys"])


# ── Survey ────────────────────────────────────────────────────────────────────

@router.post("", response_model=SurveyOut, status_code=201)
async def create_survey(data: SurveyCreate, db: AsyncSession = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    return await svc.create_survey(db, data, admin)


@router.get("", response_model=list[SurveyListItem])
async def list_surveys(status: Optional[SurveyStatus] = None, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return await svc.list_surveys(db, status)


@router.get("/{survey_id}", response_model=SurveyOut)
async def get_survey(survey_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return await svc.get_survey(db, survey_id)


@router.patch("/{survey_id}", response_model=SurveyOut)
async def update_survey(survey_id: uuid.UUID, data: SurveyUpdate, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return await svc.update_survey(db, survey_id, data)


@router.delete("/{survey_id}", status_code=204)
async def delete_survey(survey_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    await svc.delete_survey(db, survey_id)


# ── Section ───────────────────────────────────────────────────────────────────

@router.post("/{survey_id}/sections", response_model=SurveyOut, status_code=201)
async def create_section(survey_id: uuid.UUID, data: SectionCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return await svc.create_section(db, survey_id, data)


@router.patch("/{survey_id}/sections/{section_id}", response_model=SurveyOut)
async def update_section(survey_id: uuid.UUID, section_id: uuid.UUID, data: SectionUpdate, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return await svc.update_section(db, survey_id, section_id, data)


@router.delete("/{survey_id}/sections/{section_id}", status_code=204)
async def delete_section(survey_id: uuid.UUID, section_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    await svc.delete_section(db, survey_id, section_id)


# ── SurveyGroup ───────────────────────────────────────────────────────────────

@router.post("/{survey_id}/sections/{section_id}/groups", response_model=SurveyOut, status_code=201)
async def create_group(survey_id: uuid.UUID, section_id: uuid.UUID, data: SurveyGroupCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return await svc.create_group(db, survey_id, section_id, data)


@router.patch("/{survey_id}/sections/{section_id}/groups/{group_id}", response_model=SurveyOut)
async def update_group(survey_id: uuid.UUID, section_id: uuid.UUID, group_id: uuid.UUID, data: SurveyGroupUpdate, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return await svc.update_group(db, survey_id, section_id, group_id, data)


@router.delete("/{survey_id}/sections/{section_id}/groups/{group_id}", status_code=204)
async def delete_group(survey_id: uuid.UUID, section_id: uuid.UUID, group_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    await svc.delete_group(db, survey_id, section_id, group_id)


# ── GroupQuestion (placements) ────────────────────────────────────────────────

@router.post("/{survey_id}/sections/{section_id}/groups/{group_id}/questions", response_model=SurveyOut, status_code=201)
async def add_question_inline(survey_id: uuid.UUID, section_id: uuid.UUID, group_id: uuid.UUID, data: GroupQuestionCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return await svc.add_question_inline(db, survey_id, section_id, group_id, data)


@router.post("/{survey_id}/sections/{section_id}/groups/{group_id}/questions/link", response_model=SurveyOut, status_code=201)
async def link_question(survey_id: uuid.UUID, section_id: uuid.UUID, group_id: uuid.UUID, data: GroupQuestionLink, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return await svc.link_question(db, survey_id, section_id, group_id, data)


@router.patch("/{survey_id}/sections/{section_id}/groups/{group_id}/questions/{gq_id}", response_model=SurveyOut)
async def update_group_question(survey_id: uuid.UUID, section_id: uuid.UUID, group_id: uuid.UUID, gq_id: uuid.UUID, data: GroupQuestionUpdate, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return await svc.update_group_question(db, survey_id, section_id, group_id, gq_id, data)


@router.delete("/{survey_id}/sections/{section_id}/groups/{group_id}/questions/{gq_id}", response_model=SurveyOut)
async def delete_group_question(survey_id: uuid.UUID, section_id: uuid.UUID, group_id: uuid.UUID, gq_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return await svc.delete_group_question(db, survey_id, section_id, group_id, gq_id)
