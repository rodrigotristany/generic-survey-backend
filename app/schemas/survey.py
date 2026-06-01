from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from app.models.survey import SurveyStatus
from app.models.question import QuestionType


class OptionCreate(BaseModel):
    text: str
    order: int


class OptionUpdate(BaseModel):
    text: Optional[str] = None
    order: Optional[int] = None


class OptionOut(BaseModel):
    id: UUID
    text: str
    order: int

    model_config = {"from_attributes": True}


class QuestionCreate(BaseModel):
    text: str
    question_type: QuestionType
    required: bool = True
    order: int
    options: list[OptionCreate] = []


class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    question_type: Optional[QuestionType] = None
    required: Optional[bool] = None
    order: Optional[int] = None


class QuestionOut(BaseModel):
    id: UUID
    text: str
    question_type: QuestionType
    required: bool
    order: int
    options: list[OptionOut]

    model_config = {"from_attributes": True}


class SurveyCreate(BaseModel):
    title: str
    description: Optional[str] = None
    questions: list[QuestionCreate] = []


class SurveyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[SurveyStatus] = None


class SurveyOut(BaseModel):
    id: UUID
    title: str
    slug: str
    description: Optional[str]
    status: SurveyStatus
    created_by: UUID
    questions: list[QuestionOut]

    model_config = {"from_attributes": True}


class SurveyListItem(BaseModel):
    id: UUID
    title: str
    slug: str
    status: SurveyStatus
    question_count: int

    model_config = {"from_attributes": True}
