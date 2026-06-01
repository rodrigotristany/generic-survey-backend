"""hierarchical survey schema

Revision ID: 0001
Revises:
Create Date: 2026-06-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def _create_enum(name: str, *values: str) -> None:
    vals = ", ".join(f"'{v}'" for v in values)
    op.execute(sa.text(f"""
        DO $$ BEGIN
            CREATE TYPE {name} AS ENUM ({vals});
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """))


def _drop_enum(name: str) -> None:
    op.execute(sa.text(f"DROP TYPE IF EXISTS {name}"))


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("superadmin", "staff", name="adminrole", create_type=False), nullable=False, server_default="staff"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_admin_users_email", "admin_users", ["email"])

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_type", sa.String(20), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean, nullable=False, server_default="false"),
    )
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    op.create_table(
        "otp_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code_hash", sa.String(255), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_type", sa.String(20), nullable=False),
        sa.Column("purpose", sa.String(50), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean, nullable=False, server_default="false"),
    )
    op.create_index("ix_otp_codes_code_hash", "otp_codes", ["code_hash"])

    op.create_table(
        "surveys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.Enum("draft", "published", "closed", name="surveystatus", create_type=False), nullable=False, server_default="draft"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("admin_users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_surveys_slug", "surveys", ["slug"])

    op.create_table(
        "sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("order", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sections_survey_id", "sections", ["survey_id"])

    op.create_table(
        "survey_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("section_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("order", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_survey_groups_section_id", "survey_groups", ["section_id"])

    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("question_type", sa.Enum("text", "single_choice", "multiple_choice", "rating", "date", name="questiontype", create_type=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.String(500), nullable=False),
        sa.Column("order", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "group_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("survey_groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("is_required", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("order", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("group_id", "question_id", name="uq_group_questions_group_id_question_id"),
    )
    op.create_index("ix_group_questions_group_id", "group_questions", ["group_id"])
    op.create_index("ix_group_questions_question_id", "group_questions", ["question_id"])

    op.create_table(
        "survey_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Enum("in_progress", "submitted", name="responsestatus", create_type=False), nullable=False, server_default="in_progress"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("response_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("survey_responses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("group_question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("group_questions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("text_value", sa.Text, nullable=True),
        sa.Column("rating_value", sa.Integer, nullable=True),
        sa.Column("date_value", sa.Date, nullable=True),
        sa.UniqueConstraint("response_id", "group_question_id", name="uq_answers_response_id_group_question_id"),
    )
    op.create_index("ix_answers_response_id", "answers", ["response_id"])
    op.create_index("ix_answers_group_question_id", "answers", ["group_question_id"])

    op.create_table(
        "answer_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("answer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("answers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("option_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("options.id", ondelete="CASCADE"), nullable=False),
    )

    _create_enum("adminrole", "superadmin", "staff")
    _create_enum("surveystatus", "draft", "published", "closed")
    _create_enum("questiontype", "text", "single_choice", "multiple_choice", "rating", "date")
    _create_enum("responsestatus", "in_progress", "submitted")


def downgrade() -> None:
    op.drop_table("answer_options")
    op.drop_index("ix_answers_group_question_id", "answers")
    op.drop_index("ix_answers_response_id", "answers")
    op.drop_table("answers")
    op.drop_table("survey_responses")
    op.drop_index("ix_group_questions_question_id", "group_questions")
    op.drop_index("ix_group_questions_group_id", "group_questions")
    op.drop_table("group_questions")
    op.drop_table("options")
    op.drop_table("questions")
    op.drop_index("ix_survey_groups_section_id", "survey_groups")
    op.drop_table("survey_groups")
    op.drop_index("ix_sections_survey_id", "sections")
    op.drop_table("sections")
    op.drop_index("ix_surveys_slug", "surveys")
    op.drop_table("surveys")
    op.drop_index("ix_otp_codes_code_hash", "otp_codes")
    op.drop_table("otp_codes")
    op.drop_index("ix_refresh_tokens_token_hash", "refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_users_email", "users")
    op.drop_table("users")
    op.drop_index("ix_admin_users_email", "admin_users")
    op.drop_table("admin_users")

    _drop_enum("adminrole")
    _drop_enum("surveystatus")
    _drop_enum("questiontype")
    _drop_enum("responsestatus")
