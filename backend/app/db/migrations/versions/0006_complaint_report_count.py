"""Track repeat reports against an existing complaint."""
from alembic import op
import sqlalchemy as sa

revision = "0006_complaint_report_count"
down_revision = "0005_reset_and_label_review"
branch_labels = None
depends_on = None


def upgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("complaints")}
    if "report_count" not in columns:
        op.add_column("complaints", sa.Column("report_count", sa.Integer(), nullable=False, server_default="1"))


def downgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("complaints")}
    if "report_count" in columns:
        op.drop_column("complaints", "report_count")
