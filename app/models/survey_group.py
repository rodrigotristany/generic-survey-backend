import uuid
from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.mixins import TimestampMixin


class SurveyGroup(Base, TimestampMixin):
    __tablename__ = "survey_groups"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    section_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    section: Mapped["Section"] = relationship("Section", back_populates="groups")
    group_questions: Mapped[list["GroupQuestion"]] = relationship(
        "GroupQuestion",
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="GroupQuestion.order",
    )
