import uuid
import enum
from sqlalchemy import String, Text, Enum as PgEnum, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.mixins import TimestampMixin


class QuestionType(str, enum.Enum):
    text = "text"
    single_choice = "single_choice"
    multiple_choice = "multiple_choice"
    rating = "rating"


class Question(Base, TimestampMixin):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(PgEnum(QuestionType), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    survey: Mapped["Survey"] = relationship("Survey", back_populates="questions")
    options: Mapped[list["Option"]] = relationship(
        "Option",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="Option.order",
    )
