import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from app.models.survey_response import ResponseStatus


class AnswerInput(BaseModel):
    group_question_id: UUID
    text_value: Optional[str] = None
    rating_value: Optional[int] = None
    date_value: Optional[datetime.date] = None
    selected_option_ids: list[UUID] = []


class SubmitResponseRequest(BaseModel):
    answers: list[AnswerInput]


class AnswerOut(BaseModel):
    id: UUID
    group_question_id: UUID
    text_value: Optional[str]
    rating_value: Optional[int]
    date_value: Optional[datetime.date]
    selected_option_ids: list[UUID]

    model_config = {"from_attributes": True}


class SurveyResponseOut(BaseModel):
    id: UUID
    survey_id: UUID
    user_id: Optional[UUID]
    status: ResponseStatus
    submitted_at: Optional[datetime.datetime]
    answers: list[AnswerOut]

    model_config = {"from_attributes": True}
