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


# --- Question (reusable library) ---

class QuestionCreate(BaseModel):
    text: str
    question_type: QuestionType
    options: list[OptionCreate] = []


class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    question_type: Optional[QuestionType] = None


class QuestionOut(BaseModel):
    id: UUID
    text: str
    question_type: QuestionType
    options: list[OptionOut]

    model_config = {"from_attributes": True}


# --- GroupQuestion (placement) ---

class GroupQuestionCreate(BaseModel):
    """Flow A: create a new question inline and place it in this group."""
    text: str
    question_type: QuestionType
    options: list[OptionCreate] = []
    is_required: bool = True
    order: int


class GroupQuestionLink(BaseModel):
    """Flow B: link an existing question from the library into this group."""
    question_id: UUID
    is_required: bool = True
    order: int


class GroupQuestionUpdate(BaseModel):
    is_required: Optional[bool] = None
    order: Optional[int] = None


class GroupQuestionOut(BaseModel):
    id: UUID
    question_id: UUID
    is_required: bool
    order: int
    question: QuestionOut

    model_config = {"from_attributes": True}


# --- SurveyGroup ---

class SurveyGroupCreate(BaseModel):
    title: str
    order: int


class SurveyGroupUpdate(BaseModel):
    title: Optional[str] = None
    order: Optional[int] = None


class SurveyGroupOut(BaseModel):
    id: UUID
    title: str
    order: int
    group_questions: list[GroupQuestionOut]

    model_config = {"from_attributes": True}


# --- Section ---

class SectionCreate(BaseModel):
    title: str
    order: int


class SectionUpdate(BaseModel):
    title: Optional[str] = None
    order: Optional[int] = None


class SectionOut(BaseModel):
    id: UUID
    title: str
    order: int
    groups: list[SurveyGroupOut]

    model_config = {"from_attributes": True}


# --- Survey ---

class SurveyCreate(BaseModel):
    title: str
    description: Optional[str] = None


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
    sections: list[SectionOut]

    model_config = {"from_attributes": True}


class SurveyListItem(BaseModel):
    id: UUID
    title: str
    slug: str
    status: SurveyStatus
    question_count: int
