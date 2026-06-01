import uuid
from sqlalchemy import Boolean, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.mixins import TimestampMixin


class GroupQuestion(Base, TimestampMixin):
    __tablename__ = "group_questions"
    __table_args__ = (
        UniqueConstraint("group_id", "question_id", name="uq_group_questions_group_id_question_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("survey_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False, index=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    group: Mapped["SurveyGroup"] = relationship("SurveyGroup", back_populates="group_questions")
    question: Mapped["Question"] = relationship("Question", back_populates="group_questions")
    answers: Mapped[list["Answer"]] = relationship("Answer", back_populates="group_question")
