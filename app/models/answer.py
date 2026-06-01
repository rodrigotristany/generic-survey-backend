import uuid
from sqlalchemy import ForeignKey, Text, Integer, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import datetime


class Answer(Base):
    __tablename__ = "answers"
    __table_args__ = (
        UniqueConstraint("response_id", "group_question_id", name="uq_answers_response_id_group_question_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    response_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("survey_responses.id", ondelete="CASCADE"), nullable=False, index=True)
    group_question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("group_questions.id", ondelete="RESTRICT"), nullable=False, index=True)
    text_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    date_value: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)

    response: Mapped["SurveyResponse"] = relationship("SurveyResponse", back_populates="answers")
    group_question: Mapped["GroupQuestion"] = relationship("GroupQuestion", back_populates="answers")
    selected_options: Mapped[list["AnswerOption"]] = relationship(
        "AnswerOption",
        back_populates="answer",
        cascade="all, delete-orphan",
    )
