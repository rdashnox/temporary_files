"""notification initial schema"""
from alembic import op
import sqlalchemy as sa

revision = "0001_notification_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("notification_messages", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer()), sa.Column("title", sa.String(160), nullable=False), sa.Column("message", sa.Text(), nullable=False), sa.Column("channel", sa.String(40), nullable=False), sa.Column("entity_type", sa.String(80)), sa.Column("entity_id", sa.String(80)), sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("0")), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_notification_messages_user_id", "notification_messages", ["user_id"])
    op.create_index("ix_notification_user_read", "notification_messages", ["user_id", "is_read"])
    op.create_index("ix_notification_user_created_at", "notification_messages", ["user_id", "created_at"])
    op.create_table("notification_inbox_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("event_id", sa.String(80), nullable=False), sa.Column("event_type", sa.String(120), nullable=False), sa.Column("payload_json", sa.Text(), nullable=False), sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_notification_inbox_event_id", "notification_inbox_events", ["event_id"], unique=True)


def downgrade() -> None:
    op.drop_table("notification_inbox_events")
    op.drop_table("notification_messages")
