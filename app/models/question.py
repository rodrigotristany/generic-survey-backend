import uuid
import enum
from sqlalchemy import Text, Enum as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.mixins import TimestampMixin


class QuestionType(str, enum.Enum):
    text = "text"
    single_choice = "single_choice"
    multiple_choice = "multiple_choice"
    rating = "rating"
    date = "date"


class Question(Base, TimestampMixin):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(PgEnum(QuestionType), nullable=False)

    options: Mapped[list["Option"]] = relationship(
        "Option",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="Option.order",
    )
    group_questions: Mapped[list["GroupQuestion"]] = relationship(
        "GroupQuestion",
        back_populates="question",
    )
