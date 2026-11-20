"""Link complaint feedback to the staff member who completed the work."""
from alembic import op
import sqlalchemy as sa

revision = "0007_feedback_staff_link"
down_revision = "0006_complaint_report_count"
branch_labels = None
depends_on = None


def upgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("complaint_feedbacks")}
    if "staff_id" not in columns:
        op.add_column("complaint_feedbacks", sa.Column("staff_id", sa.Integer(), nullable=True))
        with op.batch_alter_table("complaint_feedbacks") as batch_op:
            batch_op.create_foreign_key("fk_complaint_feedbacks_staff_id_users", "users", ["staff_id"], ["id"])
        op.create_index("ix_complaint_feedbacks_staff_id", "complaint_feedbacks", ["staff_id"])
    # Backfill legacy feedback with the latest completed assignment when available.
    bind = op.get_bind()
    bind.execute(sa.text("""
        UPDATE complaint_feedbacks
        SET staff_id = (
            SELECT staff_id FROM staff_assignments
            WHERE staff_assignments.complaint_id = complaint_feedbacks.complaint_id
              AND staff_assignments.status = 'COMPLETED'
            ORDER BY completed_at DESC LIMIT 1
        )
        WHERE staff_id IS NULL
    """))


def downgrade():
    inspector = sa.inspect(op.get_bind())
    if "staff_id" in {column["name"] for column in inspector.get_columns("complaint_feedbacks")}:
        indexes = {index["name"] for index in inspector.get_indexes("complaint_feedbacks")}
        if "ix_complaint_feedbacks_staff_id" in indexes:
            op.drop_index("ix_complaint_feedbacks_staff_id", table_name="complaint_feedbacks")
        with op.batch_alter_table("complaint_feedbacks") as batch_op:
            batch_op.drop_constraint("fk_complaint_feedbacks_staff_id_users", type_="foreignkey")
            batch_op.drop_column("staff_id")
