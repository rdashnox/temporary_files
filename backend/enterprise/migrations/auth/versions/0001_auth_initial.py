"""auth initial schema"""
from alembic import op
import sqlalchemy as sa

revision = "0001_auth_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("auth_roles", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(80), nullable=False), sa.Column("description", sa.String(255)), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_auth_roles_name", "auth_roles", ["name"], unique=True)
    op.create_table("auth_permissions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("code", sa.String(120), nullable=False), sa.Column("name", sa.String(120), nullable=False), sa.Column("module", sa.String(80), nullable=False), sa.Column("description", sa.String(255)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_auth_permissions_code", "auth_permissions", ["code"], unique=True)
    op.create_index("ix_auth_permissions_module", "auth_permissions", ["module"])
    op.create_table("auth_users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("username", sa.String(255), nullable=False), sa.Column("email", sa.String(255), nullable=False), sa.Column("hashed_password", sa.String(255), nullable=False), sa.Column("full_name", sa.String(120)), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")), sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("0")), sa.Column("verification_token", sa.String(255)), sa.Column("verification_token_expires_at", sa.DateTime(timezone=True)), sa.Column("password_reset_token", sa.String(255)), sa.Column("password_reset_token_expires_at", sa.DateTime(timezone=True)), sa.Column("last_login_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_auth_users_username", "auth_users", ["username"], unique=True)
    op.create_index("ix_auth_users_email", "auth_users", ["email"], unique=True)
    op.create_index("ix_auth_users_email_verified", "auth_users", ["email", "is_verified"])
    op.create_index("ix_auth_users_verification_token", "auth_users", ["verification_token"], unique=True)
    op.create_index("ix_auth_users_password_reset_token", "auth_users", ["password_reset_token"], unique=True)
    op.create_table("auth_user_roles", sa.Column("user_id", sa.Integer(), sa.ForeignKey("auth_users.id", ondelete="CASCADE"), primary_key=True), sa.Column("role_id", sa.Integer(), sa.ForeignKey("auth_roles.id", ondelete="CASCADE"), primary_key=True), sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("auth_role_permissions", sa.Column("role_id", sa.Integer(), sa.ForeignKey("auth_roles.id", ondelete="CASCADE"), primary_key=True), sa.Column("permission_id", sa.Integer(), sa.ForeignKey("auth_permissions.id", ondelete="CASCADE"), primary_key=True), sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("auth_audit_logs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("actor_user_id", sa.Integer()), sa.Column("action", sa.String(30), nullable=False), sa.Column("entity_type", sa.String(80), nullable=False), sa.Column("entity_id", sa.String(80)), sa.Column("detail", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_auth_audit_logs_actor_user_id", "auth_audit_logs", ["actor_user_id"])
    op.create_index("ix_auth_audit_logs_action", "auth_audit_logs", ["action"])


def downgrade() -> None:
    for table in ["auth_audit_logs", "auth_role_permissions", "auth_user_roles", "auth_users", "auth_permissions", "auth_roles"]:
        op.drop_table(table)
