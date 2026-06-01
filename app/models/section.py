import uuid
from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.mixins import TimestampMixin


class Section(Base, TimestampMixin):
    __tablename__ = "sections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    survey: Mapped["Survey"] = relationship("Survey", back_populates="sections")
    groups: Mapped[list["SurveyGroup"]] = relationship(
        "SurveyGroup",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="SurveyGroup.order",
    )
