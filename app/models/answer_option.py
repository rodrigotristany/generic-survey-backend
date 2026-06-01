import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AnswerOption(Base):
    __tablename__ = "answer_options"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    answer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("answers.id", ondelete="CASCADE"), nullable=False)
    option_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("options.id", ondelete="CASCADE"), nullable=False)

    answer: Mapped["Answer"] = relationship("Answer", back_populates="selected_options")
