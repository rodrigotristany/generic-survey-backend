import uuid
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_admin, get_db
from app.models.question import QuestionType
from app.schemas.survey import QuestionCreate, QuestionUpdate, QuestionOut, OptionCreate, OptionUpdate
from app.services import survey as svc

router = APIRouter(prefix="/admin/questions", tags=["Admin Questions"])


@router.get("", response_model=list[QuestionOut])
async def list_questions(
    type: Optional[QuestionType] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    return await svc.list_questions(db, question_type=type, search=search)


@router.post("", response_model=QuestionOut, status_code=201)
async def create_question(data: QuestionCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return await svc.create_question(db, data)


@router.get("/{question_id}", response_model=QuestionOut)
async def get_question(question_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return await svc.get_question(db, question_id)


@router.patch("/{question_id}", response_model=QuestionOut)
async def update_question(question_id: uuid.UUID, data: QuestionUpdate, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return await svc.update_question(db, question_id, data)


@router.delete("/{question_id}", status_code=204)
async def delete_question(question_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    await svc.delete_question(db, question_id)


@router.post("/{question_id}/options", response_model=QuestionOut, status_code=201)
async def add_option(question_id: uuid.UUID, data: OptionCreate, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return await svc.add_option(db, question_id, data)


@router.patch("/{question_id}/options/{option_id}", response_model=QuestionOut)
async def update_option(question_id: uuid.UUID, option_id: uuid.UUID, data: OptionUpdate, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return await svc.update_option(db, question_id, option_id, data)


@router.delete("/{question_id}/options/{option_id}", response_model=QuestionOut)
async def delete_option(question_id: uuid.UUID, option_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    return await svc.delete_option(db, question_id, option_id)
