import uuid
import enum
from sqlalchemy import String, Boolean, Enum as PgEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.mixins import TimestampMixin


class AdminRole(str, enum.Enum):
    superadmin = "superadmin"
    staff = "staff"


class AdminUser(Base, TimestampMixin):
    __tablename__ = "admin_users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[AdminRole] = mapped_column(PgEnum(AdminRole), default=AdminRole.staff, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
