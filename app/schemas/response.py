from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.survey_response import ResponseStatus


class AnswerInput(BaseModel):
    question_id: UUID
    text_value: Optional[str] = None
    rating_value: Optional[int] = None
    selected_option_ids: list[UUID] = []


class SubmitResponseRequest(BaseModel):
    answers: list[AnswerInput]


class AnswerOut(BaseModel):
    id: UUID
    question_id: UUID
    text_value: Optional[str]
    rating_value: Optional[int]
    selected_option_ids: list[UUID]

    model_config = {"from_attributes": True}


class SurveyResponseOut(BaseModel):
    id: UUID
    survey_id: UUID
    user_id: Optional[UUID]
    status: ResponseStatus
    submitted_at: Optional[datetime]
    answers: list[AnswerOut]

    model_config = {"from_attributes": True}
