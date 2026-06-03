import uuid
from slugify import slugify
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.admin_user import AdminUser
from app.models.survey import Survey, SurveyStatus
from app.models.section import Section
from app.models.survey_group import SurveyGroup
from app.models.group_question import GroupQuestion
from app.models.question import Question
from app.models.option import Option
from app.schemas.survey import (
    SurveyCreate, SurveyUpdate, SurveyOut, SurveyListItem,
    SectionCreate, SectionUpdate, SectionOut,
    SurveyGroupCreate, SurveyGroupUpdate, SurveyGroupOut,
    GroupQuestionCreate, GroupQuestionLink, GroupQuestionUpdate, GroupQuestionOut,
    QuestionCreate, QuestionUpdate, QuestionOut,
    OptionCreate,
)


# ── Survey ──────────────────────────────────────────────────────────────────

async def create_survey(db: AsyncSession, data: SurveyCreate, admin: AdminUser) -> SurveyOut:
    slug = await _unique_slug(db, data.title)
    survey = Survey(title=data.title, slug=slug, description=data.description, created_by=admin.id)
    db.add(survey)
    await db.flush()
    await db.refresh(survey, ["sections"])
    return SurveyOut.model_validate(survey)


async def list_surveys(db: AsyncSession, status_filter: SurveyStatus | None = None) -> list[SurveyListItem]:
    stmt = (
        select(
            Survey.id,
            Survey.title,
            Survey.slug,
            Survey.status,
            func.count(GroupQuestion.id).label("question_count"),
        )
        .outerjoin(Section, Section.survey_id == Survey.id)
        .outerjoin(SurveyGroup, SurveyGroup.section_id == Section.id)
        .outerjoin(GroupQuestion, GroupQuestion.group_id == SurveyGroup.id)
        .group_by(Survey.id)
    )
    if status_filter:
        stmt = stmt.where(Survey.status == status_filter)
    rows = (await db.execute(stmt)).all()
    return [
        SurveyListItem(id=r.id, title=r.title, slug=r.slug, status=r.status, question_count=r.question_count)
        for r in rows
    ]


async def get_survey(db: AsyncSession, survey_id: uuid.UUID) -> SurveyOut:
    async with AsyncSessionLocal() as fresh_db:
        result = await fresh_db.execute(select(Survey).options(_full_load()).where(Survey.id == survey_id))
        survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    return SurveyOut.model_validate(survey)


async def get_survey_by_slug(db: AsyncSession, slug: str) -> SurveyOut:
    result = await db.execute(
        select(Survey).options(_full_load()).where(Survey.slug == slug)
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
    await db.commit()
    return SurveyOut.model_validate(survey)


async def delete_survey(db: AsyncSession, survey_id: uuid.UUID) -> None:
    survey = await _load_survey(db, survey_id)
    await db.delete(survey)
    await db.commit()


# ── Section ──────────────────────────────────────────────────────────────────

async def create_section(db: AsyncSession, survey_id: uuid.UUID, data: SectionCreate) -> SurveyOut:
    await _get_survey_or_404(db, survey_id)
    db.add(Section(survey_id=survey_id, title=data.title, order=data.order))
    await db.commit()
    return await get_survey(db, survey_id)


async def update_section(db: AsyncSession, survey_id: uuid.UUID, section_id: uuid.UUID, data: SectionUpdate) -> SurveyOut:
    section = await _get_section(db, survey_id, section_id)
    if data.title is not None:
        section.title = data.title
    if data.order is not None:
        section.order = data.order
    await db.commit()
    return await get_survey(db, survey_id)


async def delete_section(db: AsyncSession, survey_id: uuid.UUID, section_id: uuid.UUID) -> None:
    section = await _get_section(db, survey_id, section_id)
    await db.delete(section)
    await db.commit()


# ── SurveyGroup ───────────────────────────────────────────────────────────────

async def create_group(db: AsyncSession, survey_id: uuid.UUID, section_id: uuid.UUID, data: SurveyGroupCreate) -> SurveyOut:
    await _get_section(db, survey_id, section_id)
    db.add(SurveyGroup(section_id=section_id, title=data.title, order=data.order))
    await db.commit()
    return await get_survey(db, survey_id)


async def update_group(
    db: AsyncSession, survey_id: uuid.UUID, section_id: uuid.UUID, group_id: uuid.UUID, data: SurveyGroupUpdate
) -> SurveyOut:
    group = await _get_group(db, section_id, group_id)
    if data.title is not None:
        group.title = data.title
    if data.order is not None:
        group.order = data.order
    await db.commit()
    return await get_survey(db, survey_id)


async def delete_group(db: AsyncSession, survey_id: uuid.UUID, section_id: uuid.UUID, group_id: uuid.UUID) -> None:
    group = await _get_group(db, section_id, group_id)
    await db.delete(group)
    await db.commit()


# ── GroupQuestion ─────────────────────────────────────────────────────────────

async def add_question_inline(
    db: AsyncSession,
    survey_id: uuid.UUID,
    section_id: uuid.UUID,
    group_id: uuid.UUID,
    data: GroupQuestionCreate,
) -> SurveyOut:
    """Flow A: create a new Question in the library and place it in the group."""
    await _get_group(db, section_id, group_id)
    question = Question(text=data.text, question_type=data.question_type)
    db.add(question)
    await db.flush()
    for opt in data.options:
        db.add(Option(question_id=question.id, text=opt.text, order=opt.order))
    db.add(GroupQuestion(group_id=group_id, question_id=question.id, is_required=data.is_required, order=data.order))
    await db.commit()
    return await get_survey(db, survey_id)


async def link_question(
    db: AsyncSession,
    survey_id: uuid.UUID,
    section_id: uuid.UUID,
    group_id: uuid.UUID,
    data: GroupQuestionLink,
) -> SurveyOut:
    """Flow B: place an existing Question from the library into the group."""
    await _get_group(db, section_id, group_id)
    question = await db.get(Question, data.question_id)
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found in library")
    db.add(GroupQuestion(group_id=group_id, question_id=data.question_id, is_required=data.is_required, order=data.order))
    await db.commit()
    return await get_survey(db, survey_id)


async def update_group_question(
    db: AsyncSession,
    survey_id: uuid.UUID,
    section_id: uuid.UUID,
    group_id: uuid.UUID,
    group_question_id: uuid.UUID,
    data: GroupQuestionUpdate,
) -> SurveyOut:
    gq = await _get_group_question(db, group_id, group_question_id)
    if data.is_required is not None:
        gq.is_required = data.is_required
    if data.order is not None:
        gq.order = data.order
    await db.commit()
    return await get_survey(db, survey_id)


async def delete_group_question(
    db: AsyncSession,
    survey_id: uuid.UUID,
    section_id: uuid.UUID,
    group_id: uuid.UUID,
    group_question_id: uuid.UUID,
) -> SurveyOut:
    """Removes the placement only — the Question stays in the library."""
    gq = await _get_group_question(db, group_id, group_question_id)
    await db.delete(gq)
    await db.commit()
    return await get_survey(db, survey_id)


# ── Question library ──────────────────────────────────────────────────────────

async def list_questions(
    db: AsyncSession,
    question_type: str | None = None,
    search: str | None = None,
) -> list[QuestionOut]:
    stmt = select(Question).options(selectinload(Question.options))
    if question_type:
        stmt = stmt.where(Question.question_type == question_type)
    if search:
        stmt = stmt.where(Question.text.ilike(f"%{search}%"))
    questions = (await db.execute(stmt)).scalars().all()
    return [QuestionOut.model_validate(q) for q in questions]


async def create_question(db: AsyncSession, data: QuestionCreate) -> QuestionOut:
    question = Question(text=data.text, question_type=data.question_type)
    db.add(question)
    await db.flush()
    for opt in data.options:
        db.add(Option(question_id=question.id, text=opt.text, order=opt.order))
    await db.flush()
    await db.refresh(question, ["options"])
    return QuestionOut.model_validate(question)


async def get_question(db: AsyncSession, question_id: uuid.UUID) -> QuestionOut:
    result = await db.execute(
        select(Question).options(selectinload(Question.options)).where(Question.id == question_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return QuestionOut.model_validate(question)


async def update_question(db: AsyncSession, question_id: uuid.UUID, data: QuestionUpdate) -> QuestionOut:
    result = await db.execute(
        select(Question).options(selectinload(Question.options)).where(Question.id == question_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    if data.text is not None:
        question.text = data.text
    if data.question_type is not None:
        question.question_type = data.question_type
    await db.flush()
    return QuestionOut.model_validate(question)


async def delete_question(db: AsyncSession, question_id: uuid.UUID) -> None:
    result = await db.execute(
        select(GroupQuestion).where(GroupQuestion.question_id == question_id).limit(1)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Question is in use by one or more groups. Remove all placements before deleting.",
        )
    question = await db.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    await db.delete(question)
    await db.commit()


async def add_option(db: AsyncSession, question_id: uuid.UUID, data: OptionCreate) -> QuestionOut:
    question = await db.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    db.add(Option(question_id=question_id, text=data.text, order=data.order))
    await db.flush()
    await db.refresh(question, ["options"])
    return QuestionOut.model_validate(question)


async def update_option(db: AsyncSession, question_id: uuid.UUID, option_id: uuid.UUID, data) -> QuestionOut:
    option = await _get_option(db, question_id, option_id)
    if data.text is not None:
        option.text = data.text
    if data.order is not None:
        option.order = data.order
    await db.flush()
    result = await db.execute(
        select(Question).options(selectinload(Question.options)).where(Question.id == question_id)
    )
    return QuestionOut.model_validate(result.scalar_one())


async def delete_option(db: AsyncSession, question_id: uuid.UUID, option_id: uuid.UUID) -> QuestionOut:
    option = await _get_option(db, question_id, option_id)
    await db.delete(option)
    await db.flush()
    result = await db.execute(
        select(Question).options(selectinload(Question.options)).where(Question.id == question_id)
    )
    return QuestionOut.model_validate(result.scalar_one())


# ── Private helpers ────────────────────────────────────────────────────────────

def _full_load():
    return selectinload(Survey.sections).selectinload(Section.groups).selectinload(
        SurveyGroup.group_questions
    ).selectinload(GroupQuestion.question).selectinload(Question.options)


async def _load_survey(db: AsyncSession, survey_id: uuid.UUID) -> Survey:
    result = await db.execute(select(Survey).options(_full_load()).where(Survey.id == survey_id))
    survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    return survey


async def _get_survey_or_404(db: AsyncSession, survey_id: uuid.UUID) -> Survey:
    survey = await db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    return survey


async def _get_section(db: AsyncSession, survey_id: uuid.UUID, section_id: uuid.UUID) -> Section:
    result = await db.execute(
        select(Section).where(Section.id == section_id, Section.survey_id == survey_id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    return section


async def _get_group(db: AsyncSession, section_id: uuid.UUID, group_id: uuid.UUID) -> SurveyGroup:
    result = await db.execute(
        select(SurveyGroup).where(SurveyGroup.id == group_id, SurveyGroup.section_id == section_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group


async def _get_group_question(db: AsyncSession, group_id: uuid.UUID, gq_id: uuid.UUID) -> GroupQuestion:
    result = await db.execute(
        select(GroupQuestion).where(GroupQuestion.id == gq_id, GroupQuestion.group_id == group_id)
    )
    gq = result.scalar_one_or_none()
    if not gq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GroupQuestion not found")
    return gq


async def _get_option(db: AsyncSession, question_id: uuid.UUID, option_id: uuid.UUID) -> Option:
    result = await db.execute(
        select(Option).where(Option.id == option_id, Option.question_id == question_id)
    )
    option = result.scalar_one_or_none()
    if not option:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Option not found")
    return option


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
