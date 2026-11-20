"""Add refresh token tracking and ensure complaint query index.

Revision ID: 0002_refresh_sessions
Revises: 0001_baseline
"""
from alembic import op
from app.db.base import Base
from app import models  # noqa: F401

revision = "0002_refresh_sessions"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)
    from sqlalchemy import inspect
    inspector = inspect(bind)
    if inspector.has_table("complaints"):
        indexes = {item["name"] for item in inspector.get_indexes("complaints")}
        if "ix_complaints_status_created" not in indexes:
            op.create_index("ix_complaints_status_created", "complaints", ["status", "created_at"])


def downgrade():
    # Keep token/session history and preserve existing CampusFix records.
    pass
