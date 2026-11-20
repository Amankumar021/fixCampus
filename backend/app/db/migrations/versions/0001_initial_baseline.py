"""Initial CampusFix schema baseline.

Revision ID: 0001_baseline
Revises:
"""
from alembic import op
from app.db.base import Base
from app import models  # noqa: F401

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    Base.metadata.create_all(bind=op.get_bind())


def downgrade():
    # Preserve existing user and complaint records on downgrade.
    pass
