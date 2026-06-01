import uuid
from slugify import slugify
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_user import AdminUser
from app.models.survey import Survey, SurveyStatus
from app.models.question import Question
from app.models.option import Option
from app.schemas.survey import SurveyCreate, SurveyUpdate, SurveyOut, SurveyListItem, QuestionCreate, QuestionUpdate


async def create_survey(db: AsyncSession, data: SurveyCreate, admin: AdminUser) -> SurveyOut:
    slug = await _unique_slug(db, data.title)
    survey = Survey(
        title=data.title,
        slug=slug,
        description=data.description,
        created_by=admin.id,
    )
    db.add(survey)
    await db.flush()

    for q_data in data.questions:
        await _add_question(db, survey.id, q_data)

    await db.refresh(survey, ["questions"])
    return SurveyOut.model_validate(survey)


async def list_surveys(db: AsyncSession, status_filter: SurveyStatus | None = None) -> list[SurveyListItem]:
    stmt = select(
        Survey.id,
        Survey.title,
        Survey.slug,
        Survey.status,
        func.count(Question.id).label("question_count"),
    ).outerjoin(Question, Question.survey_id == Survey.id).group_by(Survey.id)

    if status_filter:
        stmt = stmt.where(Survey.status == status_filter)

    result = await db.execute(stmt)
    rows = result.all()
    return [
        SurveyListItem(
            id=row.id,
            title=row.title,
            slug=row.slug,
            status=row.status,
            question_count=row.question_count,
        )
        for row in rows
    ]


async def get_survey(db: AsyncSession, survey_id: uuid.UUID) -> SurveyOut:
    survey = await _load_survey(db, survey_id)
    return SurveyOut.model_validate(survey)


async def get_survey_by_slug(db: AsyncSession, slug: str) -> SurveyOut:
    result = await db.execute(
        select(Survey)
        .options(selectinload(Survey.questions).selectinload(Question.options))
        .where(Survey.slug == slug)
    )
    survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    return SurveyOut.model_validate(survey)


async def update_survey(db: AsyncSession, survey_id: uuid.UUID, data: SurveyUpdate) -> SurveyOut:
    survey = await _load_survey(db, survey_id)
    if data.title is not None:
        survey.title = data.title
    if data.description is not None:
        survey.description = data.description
    if data.status is not None:
        survey.status = data.status
    await db.flush()
    await db.refresh(survey, ["questions"])
    return SurveyOut.model_validate(survey)


async def delete_survey(db: AsyncSession, survey_id: uuid.UUID) -> None:
    survey = await _load_survey(db, survey_id)
    await db.delete(survey)
    await db.flush()


async def add_question(db: AsyncSession, survey_id: uuid.UUID, data: QuestionCreate) -> SurveyOut:
    await _load_survey(db, survey_id)
    await _add_question(db, survey_id, data)
    return await get_survey(db, survey_id)


async def update_question(db: AsyncSession, survey_id: uuid.UUID, question_id: uuid.UUID, data: QuestionUpdate) -> SurveyOut:
    question = await _get_question(db, survey_id, question_id)
    if data.text is not None:
        question.text = data.text
    if data.question_type is not None:
        question.question_type = data.question_type
    if data.required is not None:
        question.required = data.required
    if data.order is not None:
        question.order = data.order
    await db.flush()
    return await get_survey(db, survey_id)


async def delete_question(db: AsyncSession, survey_id: uuid.UUID, question_id: uuid.UUID) -> SurveyOut:
    question = await _get_question(db, survey_id, question_id)
    await db.delete(question)
    await db.flush()
    return await get_survey(db, survey_id)


async def _add_question(db: AsyncSession, survey_id: uuid.UUID, data: QuestionCreate) -> Question:
    question = Question(
        survey_id=survey_id,
        text=data.text,
        question_type=data.question_type,
        required=data.required,
        order=data.order,
    )
    db.add(question)
    await db.flush()

    for opt_data in data.options:
        db.add(Option(question_id=question.id, text=opt_data.text, order=opt_data.order))
    await db.flush()
    return question


async def _load_survey(db: AsyncSession, survey_id: uuid.UUID) -> Survey:
    result = await db.execute(
        select(Survey)
        .options(selectinload(Survey.questions).selectinload(Question.options))
        .where(Survey.id == survey_id)
    )
    survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    return survey


async def _get_question(db: AsyncSession, survey_id: uuid.UUID, question_id: uuid.UUID) -> Question:
    result = await db.execute(
        select(Question)
        .options(selectinload(Question.options))
        .where(Question.id == question_id, Question.survey_id == survey_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return question


async def _unique_slug(db: AsyncSession, title: str) -> str:
    base = slugify(title)
    slug = base
    counter = 1
    while True:
        result = await db.execute(select(Survey).where(Survey.slug == slug))
        if not result.scalar_one_or_none():
            return slug
        slug = f"{base}-{counter}"
        counter += 1
