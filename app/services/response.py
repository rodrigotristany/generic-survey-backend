import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.survey import Survey, SurveyStatus
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

    answers_out: list[AnswerOut] = []
    for ans_data in data.answers:
        answer = Answer(
            response_id=response.id,
            question_id=ans_data.question_id,
            text_value=ans_data.text_value,
            rating_value=ans_data.rating_value,
        )
        db.add(answer)
        await db.flush()

        for opt_id in ans_data.selected_option_ids:
            db.add(AnswerOption(answer_id=answer.id, option_id=opt_id))
        await db.flush()

        answers_out.append(AnswerOut(
            id=answer.id,
            question_id=answer.question_id,
            text_value=answer.text_value,
            rating_value=answer.rating_value,
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
            question_id=a.question_id,
            text_value=a.text_value,
            rating_value=a.rating_value,
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
