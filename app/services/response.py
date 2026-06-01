import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.survey import Survey, SurveyStatus
from app.models.section import Section
from app.models.survey_group import SurveyGroup
from app.models.group_question import GroupQuestion
from app.models.question import QuestionType
from app.models.survey_response import SurveyResponse, ResponseStatus
from app.models.answer import Answer
from app.models.answer_option import AnswerOption
from app.schemas.response import SubmitResponseRequest, SurveyResponseOut, AnswerOut


async def start_response(
    db: AsyncSession,
    survey_id: uuid.UUID,
    user_id: uuid.UUID | None,
) -> SurveyResponseOut:
    survey = await db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    if survey.status != SurveyStatus.published:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Survey is not open for responses")
    response = SurveyResponse(survey_id=survey_id, user_id=user_id)
    db.add(response)
    await db.flush()
    return _to_out(response, [])


async def submit_response(
    db: AsyncSession,
    response_id: uuid.UUID,
    data: SubmitResponseRequest,
    user_id: uuid.UUID | None,
) -> SurveyResponseOut:
    response = await _load_response(db, response_id)

    if response.status == ResponseStatus.submitted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Response already submitted")
    if user_id and response.user_id and response.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    valid_gq_ids = await _get_valid_group_question_ids(db, response.survey_id)

    answers_out: list[AnswerOut] = []
    for ans_data in data.answers:
        if ans_data.group_question_id not in valid_gq_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"group_question_id {ans_data.group_question_id} does not belong to this survey",
            )

        gq_info = valid_gq_ids[ans_data.group_question_id]
        q_type = gq_info["question_type"]
        is_required = gq_info["is_required"]

        _validate_answer(ans_data, q_type, is_required)

        answer = Answer(
            response_id=response.id,
            group_question_id=ans_data.group_question_id,
            text_value=ans_data.text_value,
            rating_value=ans_data.rating_value,
            date_value=ans_data.date_value,
        )
        db.add(answer)
        await db.flush()

        for opt_id in ans_data.selected_option_ids:
            db.add(AnswerOption(answer_id=answer.id, option_id=opt_id))
        await db.flush()

        answers_out.append(AnswerOut(
            id=answer.id,
            group_question_id=answer.group_question_id,
            text_value=answer.text_value,
            rating_value=answer.rating_value,
            date_value=answer.date_value,
            selected_option_ids=ans_data.selected_option_ids,
        ))

    response.status = ResponseStatus.submitted
    response.submitted_at = datetime.now(timezone.utc)
    await db.flush()
    return _to_out(response, answers_out)


async def get_response(db: AsyncSession, response_id: uuid.UUID) -> SurveyResponseOut:
    response = await _load_response(db, response_id)
    answers_out = await _build_answers_out(db, response)
    return _to_out(response, answers_out)


async def list_survey_responses(db: AsyncSession, survey_id: uuid.UUID) -> list[SurveyResponseOut]:
    result = await db.execute(
        select(SurveyResponse).where(SurveyResponse.survey_id == survey_id)
    )
    responses = result.scalars().all()
    out = []
    for r in responses:
        answers_out = await _build_answers_out(db, r)
        out.append(_to_out(r, answers_out))
    return out


def _validate_answer(ans_data, q_type: QuestionType, is_required: bool) -> None:
    choice_types = {QuestionType.single_choice, QuestionType.multiple_choice}
    is_empty = (
        ans_data.text_value is None
        and ans_data.rating_value is None
        and ans_data.date_value is None
        and not ans_data.selected_option_ids
    )
    if is_required and is_empty:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"group_question_id {ans_data.group_question_id} is required",
        )
    if ans_data.date_value is not None and q_type != QuestionType.date:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="date_value only allowed for date questions")
    if ans_data.selected_option_ids and q_type not in choice_types:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="selected_option_ids only allowed for choice questions")
    if q_type == QuestionType.single_choice and len(ans_data.selected_option_ids) > 1:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="single_choice allows at most one selected option")


async def _get_valid_group_question_ids(db: AsyncSession, survey_id: uuid.UUID) -> dict:
    """Returns {gq_id: {question_type, is_required}} for all GroupQuestions in the survey."""
    result = await db.execute(
        select(GroupQuestion, GroupQuestion.question).join(GroupQuestion.question)
        .join(SurveyGroup, GroupQuestion.group_id == SurveyGroup.id)
        .join(Section, SurveyGroup.section_id == Section.id)
        .where(Section.survey_id == survey_id)
    )
    return {
        row.GroupQuestion.id: {
            "question_type": row.GroupQuestion.question.question_type,
            "is_required": row.GroupQuestion.is_required,
        }
        for row in result.all()
    }


async def _load_response(db: AsyncSession, response_id: uuid.UUID) -> SurveyResponse:
    response = await db.get(SurveyResponse, response_id)
    if not response:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response not found")
    return response


async def _build_answers_out(db: AsyncSession, response: SurveyResponse) -> list[AnswerOut]:
    result = await db.execute(
        select(Answer)
        .options(selectinload(Answer.selected_options))
        .where(Answer.response_id == response.id)
    )
    answers = result.scalars().all()
    return [
        AnswerOut(
            id=a.id,
            group_question_id=a.group_question_id,
            text_value=a.text_value,
            rating_value=a.rating_value,
            date_value=a.date_value,
            selected_option_ids=[ao.option_id for ao in a.selected_options],
        )
        for a in answers
    ]


def _to_out(response: SurveyResponse, answers: list[AnswerOut]) -> SurveyResponseOut:
    return SurveyResponseOut(
        id=response.id,
        survey_id=response.survey_id,
        user_id=response.user_id,
        status=response.status,
        submitted_at=response.submitted_at,
        answers=answers,
    )
