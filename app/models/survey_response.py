import uuid
import enum
from datetime import datetime
from sqlalchemy import ForeignKey, Enum as PgEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.mixins import TimestampMixin


class ResponseStatus(str, enum.Enum):
    in_progress = "in_progress"
    submitted = "submitted"


class SurveyResponse(Base, TimestampMixin):
    __tablename__ = "survey_responses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    survey_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)  # None = anonymous
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ResponseStatus] = mapped_column(PgEnum(ResponseStatus), default=ResponseStatus.in_progress)

    answers: Mapped[list["Answer"]] = relationship(
        "Answer",
        back_populates="response",
        cascade="all, delete-orphan",
    )
