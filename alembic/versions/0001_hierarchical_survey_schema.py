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


def upgrade() -> None:
    # Add 'date' value to the questiontype enum.
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction in PostgreSQL.
    conn = op.get_bind()
    conn.execution_options(isolation_level="AUTOCOMMIT").execute(
        sa.text("ALTER TYPE questiontype ADD VALUE IF NOT EXISTS 'date'")
    )

    # Remove old columns from questions (survey_id, required, order)
    with op.batch_alter_table("questions") as batch_op:
        batch_op.drop_constraint("fk_questions_survey_id_surveys", type_="foreignkey")
        batch_op.drop_column("survey_id")
        batch_op.drop_column("required")
        batch_op.drop_column("order")

    # Create sections
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

    # Create survey_groups
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

    # Create group_questions
    op.create_table(
        "group_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("survey_groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("is_required", sa.Boolean, default=True, nullable=False),
        sa.Column("order", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("group_id", "question_id", name="uq_group_questions_group_id_question_id"),
    )
    op.create_index("ix_group_questions_group_id", "group_questions", ["group_id"])
    op.create_index("ix_group_questions_question_id", "group_questions", ["question_id"])

    # Alter answers: drop question_id, add group_question_id and date_value
    with op.batch_alter_table("answers") as batch_op:
        batch_op.drop_constraint("fk_answers_question_id_questions", type_="foreignkey")
        batch_op.drop_column("question_id")
        batch_op.add_column(sa.Column("group_question_id", postgresql.UUID(as_uuid=True), nullable=False))
        batch_op.add_column(sa.Column("date_value", sa.Date, nullable=True))
        batch_op.create_foreign_key(
            "fk_answers_group_question_id_group_questions",
            "group_questions", ["group_question_id"], ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_unique_constraint(
            "uq_answers_response_id_group_question_id",
            ["response_id", "group_question_id"],
        )
    op.create_index("ix_answers_group_question_id", "answers", ["group_question_id"])


def downgrade() -> None:
    op.drop_index("ix_answers_group_question_id", "answers")
    with op.batch_alter_table("answers") as batch_op:
        batch_op.drop_constraint("uq_answers_response_id_group_question_id", type_="unique")
        batch_op.drop_constraint("fk_answers_group_question_id_group_questions", type_="foreignkey")
        batch_op.drop_column("group_question_id")
        batch_op.drop_column("date_value")
        batch_op.add_column(sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False))
        batch_op.create_foreign_key(
            "fk_answers_question_id_questions",
            "questions", ["question_id"], ["id"],
            ondelete="CASCADE",
        )

    op.drop_index("ix_group_questions_question_id", "group_questions")
    op.drop_index("ix_group_questions_group_id", "group_questions")
    op.drop_table("group_questions")
    op.drop_index("ix_survey_groups_section_id", "survey_groups")
    op.drop_table("survey_groups")
    op.drop_index("ix_sections_survey_id", "sections")
    op.drop_table("sections")

    with op.batch_alter_table("questions") as batch_op:
        batch_op.add_column(sa.Column("survey_id", postgresql.UUID(as_uuid=True), nullable=False))
        batch_op.add_column(sa.Column("required", sa.Boolean, nullable=False, server_default="true"))
        batch_op.add_column(sa.Column("order", sa.Integer, nullable=False, server_default="0"))
        batch_op.create_foreign_key(
            "fk_questions_survey_id_surveys",
            "surveys", ["survey_id"], ["id"],
            ondelete="CASCADE",
        )
