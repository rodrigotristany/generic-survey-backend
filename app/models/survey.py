import uuid
import enum
from sqlalchemy import String, Text, Enum as PgEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.mixins import TimestampMixin


class SurveyStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    closed = "closed"


class Survey(Base, TimestampMixin):
    __tablename__ = "surveys"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SurveyStatus] = mapped_column(PgEnum(SurveyStatus), default=SurveyStatus.draft, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("admin_users.id"), nullable=False)

    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="survey",
        cascade="all, delete-orphan",
        order_by="Question.order",
    )
