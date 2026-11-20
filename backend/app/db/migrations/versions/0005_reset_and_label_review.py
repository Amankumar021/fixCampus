"""Store password reset tokens and human reviewed category labels."""
from alembic import op
import sqlalchemy as sa

revision = "0005_reset_and_label_review"
down_revision = "0004_auth_token_version"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("password_reset_tokens"):
        op.create_table(
            "password_reset_tokens",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False, unique=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"])
        op.create_index("ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"], unique=True)
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("complaints")}
    if "category_reviewed_at" not in columns:
        op.add_column("complaints", sa.Column("category_reviewed_at", sa.DateTime(), nullable=True))
    if "category_reviewed_by_id" not in columns:
        with op.batch_alter_table("complaints") as batch_op:
            batch_op.add_column(sa.Column("category_reviewed_by_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_complaints_category_reviewed_by_id_users",
                "users",
                ["category_reviewed_by_id"],
                ["id"],
            )
    if "ix_password_reset_tokens_user_id" not in {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("password_reset_tokens")}:
        op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"])
    if "ix_password_reset_tokens_token_hash" not in {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("password_reset_tokens")}:
        op.create_index("ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"], unique=True)


def downgrade():
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("password_reset_tokens"):
        op.drop_index("ix_password_reset_tokens_token_hash", table_name="password_reset_tokens")
        op.drop_index("ix_password_reset_tokens_user_id", table_name="password_reset_tokens")
        op.drop_table("password_reset_tokens")
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("complaints")}
    if "category_reviewed_by_id" in columns:
        op.drop_column("complaints", "category_reviewed_by_id")
    if "category_reviewed_at" in columns:
        op.drop_column("complaints", "category_reviewed_at")
