"""Invalidate access tokens after credential changes.

Revision ID: 0004_auth_token_version
Revises: 0003_student_rewards
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_auth_token_version"
down_revision = "0003_student_rewards"
branch_labels = None
depends_on = None


def upgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "token_version" not in columns:
        op.add_column("users", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))


def downgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "token_version" in columns:
        op.drop_column("users", "token_version")
