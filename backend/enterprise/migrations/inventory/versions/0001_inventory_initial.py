"""inventory initial schema"""
from alembic import op
import sqlalchemy as sa

revision = "0001_inventory_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("inventory_products", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("sku", sa.String(80), nullable=False), sa.Column("name", sa.String(120), nullable=False), sa.Column("category", sa.String(80), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("price", sa.Numeric(12,2), nullable=False), sa.Column("compare_at_price", sa.Numeric(12,2)), sa.Column("stock_quantity", sa.Integer(), nullable=False, server_default="0"), sa.Column("rating", sa.Numeric(3,2), nullable=False, server_default="0"), sa.Column("badge", sa.String(80), nullable=False, server_default=""), sa.Column("image", sa.String(255), nullable=False, server_default=""), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_inventory_products_sku", "inventory_products", ["sku"], unique=True)
    op.create_index("ix_inventory_products_name", "inventory_products", ["name"])
    op.create_index("ix_inventory_products_category_active", "inventory_products", ["category", "is_active"])
    op.create_index("ix_inventory_products_stock", "inventory_products", ["stock_quantity"])
    op.create_table("inventory_outbox_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("event_id", sa.String(80), nullable=False), sa.Column("event_type", sa.String(120), nullable=False), sa.Column("aggregate_type", sa.String(80), nullable=False), sa.Column("aggregate_id", sa.String(80), nullable=False), sa.Column("payload_json", sa.Text(), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("published_at", sa.DateTime(timezone=True)))
    op.create_index("ix_inventory_outbox_event_id", "inventory_outbox_events", ["event_id"], unique=True)
    op.create_index("ix_inventory_outbox_status", "inventory_outbox_events", ["status"])


def downgrade() -> None:
    op.drop_table("inventory_outbox_events")
    op.drop_table("inventory_products")
