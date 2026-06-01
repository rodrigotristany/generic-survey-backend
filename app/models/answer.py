import uuid
from sqlalchemy import ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    response_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("survey_responses.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    text_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating_value: Mapped[int | None] = mapped_column(Integer, nullable=True)

    response: Mapped["SurveyResponse"] = relationship("SurveyResponse", back_populates="answers")
    selected_options: Mapped[list["AnswerOption"]] = relationship(
        "AnswerOption",
        back_populates="answer",
        cascade="all, delete-orphan",
    )
