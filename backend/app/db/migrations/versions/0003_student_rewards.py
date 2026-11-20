"""Add student social-impact reward points.

Revision ID: 0003_student_rewards
Revises: 0002_refresh_sessions
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_student_rewards"
down_revision = "0002_refresh_sessions"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if "reward_points" not in {column["name"] for column in inspector.get_columns("users")}:
        op.add_column("users", sa.Column("reward_points", sa.Integer(), nullable=False, server_default="0"))
    if inspector.has_table("reward_transactions"):
        return
    op.create_table(
        "reward_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("complaint_id", sa.Integer(), sa.ForeignKey("complaints.id"), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=48), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("points > 0", name="ck_reward_points_positive"),
        sa.UniqueConstraint("student_id", "complaint_id", "reason", name="uq_reward_student_complaint_reason"),
    )
    op.create_index("ix_reward_transactions_student_id", "reward_transactions", ["student_id"])
    op.create_index("ix_reward_transactions_complaint_id", "reward_transactions", ["complaint_id"])


def downgrade():
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("reward_transactions"):
        op.drop_index("ix_reward_transactions_complaint_id", table_name="reward_transactions")
        op.drop_index("ix_reward_transactions_student_id", table_name="reward_transactions")
        op.drop_table("reward_transactions")
    if "reward_points" in {column["name"] for column in inspector.get_columns("users")}:
        op.drop_column("users", "reward_points")
