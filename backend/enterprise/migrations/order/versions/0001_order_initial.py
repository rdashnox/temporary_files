"""order initial schema"""
from alembic import op
import sqlalchemy as sa

revision = "0001_order_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("order_orders", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("order_number", sa.String(40), nullable=False), sa.Column("user_id", sa.Integer()), sa.Column("idempotency_key", sa.String(120)), sa.Column("customer_name", sa.String(120), nullable=False), sa.Column("delivery_address", sa.String(255), nullable=False), sa.Column("payment_method", sa.String(60), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("subtotal", sa.Numeric(12,2), nullable=False), sa.Column("discount", sa.Numeric(12,2), nullable=False), sa.Column("shipping_fee", sa.Numeric(12,2), nullable=False), sa.Column("tax", sa.Numeric(12,2), nullable=False), sa.Column("total", sa.Numeric(12,2), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_order_orders_order_number", "order_orders", ["order_number"], unique=True)
    op.create_index("ix_order_orders_user_id", "order_orders", ["user_id"])
    op.create_index("ix_order_orders_idempotency_key", "order_orders", ["idempotency_key"], unique=True)
    op.create_index("ix_order_orders_status_created_at", "order_orders", ["status", "created_at"])
    op.create_index("ix_order_orders_user_created_at", "order_orders", ["user_id", "created_at"])
    op.create_table("order_items", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("order_id", sa.Integer(), sa.ForeignKey("order_orders.id", ondelete="CASCADE"), nullable=False), sa.Column("product_id", sa.Integer(), nullable=False), sa.Column("product_name", sa.String(120), nullable=False), sa.Column("quantity", sa.Integer(), nullable=False), sa.Column("unit_price", sa.Numeric(12,2), nullable=False), sa.Column("line_total", sa.Numeric(12,2), nullable=False), sa.UniqueConstraint("order_id", "product_id", name="uq_order_item_product"))
    op.create_index("ix_order_items_product_id", "order_items", ["product_id"])
    op.create_table("order_outbox_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("event_id", sa.String(80), nullable=False), sa.Column("event_type", sa.String(120), nullable=False), sa.Column("aggregate_type", sa.String(80), nullable=False), sa.Column("aggregate_id", sa.String(80), nullable=False), sa.Column("payload_json", sa.Text(), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("published_at", sa.DateTime(timezone=True)))
    op.create_index("ix_order_outbox_event_id", "order_outbox_events", ["event_id"], unique=True)
    op.create_index("ix_order_outbox_status", "order_outbox_events", ["status"])


def downgrade() -> None:
    op.drop_table("order_outbox_events")
    op.drop_table("order_items")
    op.drop_table("order_orders")
