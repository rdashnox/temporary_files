"""Migrate legacy monolith Auth data into the enterprise Auth database.

Source database: legacy monolith DB, normally finmark_db.
Target database: dedicated enterprise Auth DB, normally finmark_auth_db.

The migration is idempotent. It upserts users, roles, permissions, role-permission
mappings, and user-role mappings. It also guarantees that the Administrator role
and admin@example.com account can access every dashboard.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import OperationalError, ProgrammingError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.core.security import hash_password
from backend.enterprise.config import enterprise_settings
from backend.enterprise.databases import AuthSessionLocal, safe_url, session_scope
from backend.enterprise.models import AuthAuditLog, AuthPermission, AuthRole, AuthUser, AuditAction
from backend.enterprise.services.auth_enterprise_service import seed_auth_database


ADMIN_ROLE_NAMES = {"admin", "administrator", "super admin", "superadmin", "super user", "superuser"}
ADMIN_EMAILS = {"admin@example.com", "admin@finmark.local", "administrator@example.com"}
DEFAULT_ADMIN_PASSWORD = "Admin@12345"

ENTERPRISE_EXTRA_PERMISSIONS = [
    ("dashboard.admin", "Open Admin Dashboard", "dashboard", "Allows opening the admin dashboard."),
    ("dashboard.products", "Open Product Dashboard", "dashboard", "Allows opening the product/cart dashboard."),
    ("product_dashboard.access", "Access Product Dashboard", "dashboard", "Backward-compatible product dashboard access permission."),
    ("products.read", "Read products", "inventory", "Backward-compatible product catalog read permission."),
    ("products.manage", "Manage products", "inventory", "Backward-compatible product catalog management permission."),
    ("inventory.read", "Read inventory", "inventory", "Allows reading inventory and product data."),
    ("inventory.manage", "Manage inventory", "inventory", "Allows managing inventory and product data."),
]


@dataclass
class MigrationStats:
    legacy_permissions_found: int = 0
    legacy_roles_found: int = 0
    legacy_users_found: int = 0
    permissions_upserted: int = 0
    roles_upserted: int = 0
    users_upserted: int = 0
    role_permissions_linked: int = 0
    user_roles_linked: int = 0
    admin_users_repaired: int = 0


def _mask_url(url: str) -> str:
    try:
        return str(make_url(url).render_as_string(hide_password=True))
    except Exception:
        return "<invalid url>"


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    return value if value not in (None, "") else default


def _build_url(*, user: str, password: str, host: str, port: int, database: str) -> str:
    return f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{database}"


def resolve_legacy_url(args: argparse.Namespace) -> str:
    if args.legacy_url:
        return args.legacy_url
    if _env("LEGACY_DATABASE_URL"):
        return _env("LEGACY_DATABASE_URL") or ""

    # DATABASE_URL may have been removed in enterprise mode, but if it still
    # points to the legacy finmark_db, allow it as a source.
    database_url = _env("DATABASE_URL")
    if database_url and args.legacy_database in database_url:
        return database_url

    legacy_user = args.legacy_user or _env("LEGACY_DB_USER") or _env("DB_USER") or "root"
    legacy_password = args.legacy_password
    if legacy_password is None:
        legacy_password = _env("LEGACY_DB_PASSWORD")
    if legacy_password is None:
        legacy_password = _env("DB_PASSWORD", "") or ""
    legacy_host = args.legacy_host or _env("LEGACY_DB_HOST") or _env("DB_HOST") or "127.0.0.1"
    legacy_port = int(args.legacy_port or _env("LEGACY_DB_PORT") or _env("DB_PORT") or "3306")
    legacy_database = args.legacy_database or _env("LEGACY_DB_NAME") or _env("DB_NAME") or "finmark_db"
    return _build_url(user=legacy_user, password=legacy_password, host=legacy_host, port=legacy_port, database=legacy_database)


def _engine(url: str) -> Engine:
    kwargs = {"future": True, "pool_pre_ping": True}
    if not url.startswith("sqlite"):
        kwargs["connect_args"] = {"connect_timeout": 10}
    return create_engine(url, **kwargs)


def _table_exists(inspector, table_name: str) -> bool:  # noqa: ANN001
    return table_name in set(inspector.get_table_names())


def _columns(inspector, table_name: str) -> set[str]:  # noqa: ANN001
    if not _table_exists(inspector, table_name):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _read_table(connection, inspector, table_name: str, wanted_columns: list[str]) -> list[dict[str, Any]]:  # noqa: ANN001
    available = _columns(inspector, table_name)
    if not available:
        return []
    selected = [column for column in wanted_columns if column in available]
    if not selected:
        return []
    column_sql = ", ".join(f"`{column}`" for column in selected)
    rows = connection.execute(text(f"SELECT {column_sql} FROM `{table_name}`")).mappings().all()
    return [dict(row) for row in rows]


def _normalize(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    return str(value).strip()


def _normalize_email(username: str, email: str | None, legacy_id: Any) -> str:
    email_value = _normalize(email).lower()
    if email_value:
        return email_value
    username_value = _normalize(username).lower()
    if "@" in username_value:
        return username_value
    return f"legacy-user-{legacy_id}@finmark.local"


def _normalize_username(username: str | None, email: str, legacy_id: Any) -> str:
    username_value = _normalize(username).lower()
    if username_value:
        return username_value
    return email or f"legacy-user-{legacy_id}@finmark.local"


def _find_user(db: Session, username: str, email: str) -> AuthUser | None:
    return db.scalar(select(AuthUser).where((AuthUser.email == email) | (AuthUser.username == username)))


def _id_is_available(db: Session, model, item_id: Any) -> bool:  # noqa: ANN001
    if item_id in (None, ""):
        return False
    try:
        item_id_int = int(item_id)
    except (TypeError, ValueError):
        return False
    return db.get(model, item_id_int) is None


def _ensure_extra_permissions(db: Session) -> None:
    for code, name, module, description in ENTERPRISE_EXTRA_PERMISSIONS:
        permission = db.scalar(select(AuthPermission).where(AuthPermission.code == code))
        if permission is None:
            db.add(AuthPermission(code=code, name=name, module=module, description=description))
        else:
            permission.name = permission.name or name
            permission.module = permission.module or module
            permission.description = permission.description or description
    db.flush()


def _upsert_permission(db: Session, row: dict[str, Any]) -> AuthPermission:
    legacy_id = row.get("id")
    code = _normalize(row.get("code")).lower()
    if not code:
        code = _normalize(row.get("name"), f"legacy.permission.{legacy_id}").lower().replace(" ", ".")
    name = _normalize(row.get("name"), code)
    module = _normalize(row.get("module"), "legacy") or "legacy"
    description = _normalize(row.get("description"), "Imported from legacy finmark_db permissions.")

    permission = db.scalar(select(AuthPermission).where(AuthPermission.code == code))
    if permission is None:
        kwargs = {"code": code, "name": name, "module": module, "description": description}
        if _id_is_available(db, AuthPermission, legacy_id):
            kwargs["id"] = int(legacy_id)
        permission = AuthPermission(**kwargs)
        db.add(permission)
        db.flush()
    else:
        permission.name = name or permission.name
        permission.module = module or permission.module
        permission.description = description or permission.description
    return permission


def _upsert_role(db: Session, row: dict[str, Any]) -> AuthRole:
    legacy_id = row.get("id")
    name = _normalize(row.get("name"), f"Legacy Role {legacy_id}")
    description = _normalize(row.get("description"), "Imported from legacy finmark_db roles.")
    is_active = bool(row.get("is_active", True))

    role = db.scalar(select(AuthRole).where(AuthRole.name == name))
    if role is None:
        kwargs = {"name": name, "description": description, "is_active": is_active}
        if _id_is_available(db, AuthRole, legacy_id):
            kwargs["id"] = int(legacy_id)
        role = AuthRole(**kwargs)
        db.add(role)
        db.flush()
    else:
        role.description = description or role.description
        role.is_active = is_active
    return role


def _upsert_user(db: Session, row: dict[str, Any], *, verify_imported_users: bool) -> AuthUser:
    legacy_id = row.get("id")
    email = _normalize_email(_normalize(row.get("username")), row.get("email"), legacy_id)
    username = _normalize_username(row.get("username"), email, legacy_id)
    hashed_password = _normalize(row.get("hashed_password")) or hash_password("ChangeMe@12345")
    full_name = _normalize(row.get("full_name")) or None
    is_active = bool(row.get("is_active", True))
    is_verified = bool(row.get("is_verified", True)) or verify_imported_users

    user = _find_user(db, username, email)
    if user is None:
        kwargs = {
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "full_name": full_name,
            "is_active": is_active,
            "is_verified": is_verified,
            "verification_token": None,
            "verification_token_expires_at": None,
            "password_reset_token": None,
            "password_reset_token_expires_at": None,
            "last_login_at": row.get("last_login_at"),
        }
        if _id_is_available(db, AuthUser, legacy_id):
            kwargs["id"] = int(legacy_id)
        user = AuthUser(**kwargs)
        db.add(user)
        db.flush()
    else:
        user.username = username
        user.email = email
        user.hashed_password = hashed_password
        user.full_name = full_name or user.full_name
        user.is_active = is_active
        user.is_verified = is_verified
        user.verification_token = None
        user.verification_token_expires_at = None
        user.password_reset_token = None
        user.password_reset_token_expires_at = None
        user.last_login_at = row.get("last_login_at") or user.last_login_at
    return user


def _link_role_permission(role: AuthRole, permission: AuthPermission) -> bool:
    if permission not in role.permissions:
        role.permissions.append(permission)
        return True
    return False


def _link_user_role(user: AuthUser, role: AuthRole) -> bool:
    if role not in user.roles:
        user.roles.append(role)
        return True
    return False


def _ensure_admin_access(db: Session, *, reset_admin_password: bool = True) -> int:
    _ensure_extra_permissions(db)
    all_permissions = list(db.scalars(select(AuthPermission)).all())

    administrator = db.scalar(select(AuthRole).where(AuthRole.name == "Administrator"))
    if administrator is None:
        administrator = AuthRole(name="Administrator", description="Full system administrator", is_active=True)
        db.add(administrator)
        db.flush()
    administrator.description = "Full system administrator with access to all dashboards"
    administrator.is_active = True
    administrator.permissions = all_permissions

    admin_like_roles = [
        role for role in db.scalars(select(AuthRole)).all()
        if role.name.strip().lower() in ADMIN_ROLE_NAMES
    ]
    for role in admin_like_roles:
        role.is_active = True
        for permission in all_permissions:
            _link_role_permission(role, permission)

    admin_users = []
    documented_admin = db.scalar(select(AuthUser).where(AuthUser.email == "admin@example.com"))
    if documented_admin is None:
        documented_admin = AuthUser(
            username="admin@example.com",
            email="admin@example.com",
            full_name="System Administrator",
            hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
            is_active=True,
            is_verified=True,
            roles=[administrator],
        )
        db.add(documented_admin)
        db.flush()
    admin_users.append(documented_admin)

    for user in db.scalars(select(AuthUser)).all():
        role_names = {role.name.strip().lower() for role in user.roles}
        if user.email.lower() in ADMIN_EMAILS or user.username.lower() in ADMIN_EMAILS or role_names.intersection(ADMIN_ROLE_NAMES):
            admin_users.append(user)

    repaired = 0
    for user in set(admin_users):
        user.is_active = True
        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires_at = None
        if reset_admin_password and (user.email.lower() == "admin@example.com" or user.username.lower() == "admin@example.com"):
            user.hashed_password = hash_password(DEFAULT_ADMIN_PASSWORD)
        if _link_user_role(user, administrator):
            repaired += 1
        repaired += 1
    return repaired


def migrate(legacy_url: str, *, verify_imported_users: bool, reset_admin_password: bool, dry_run: bool = False) -> MigrationStats:
    stats = MigrationStats()
    legacy_engine = _engine(legacy_url)
    print("FinMark legacy Auth migration")
    print("=" * 72)
    print(f"Source legacy DB : {_mask_url(legacy_url)}")
    print(f"Target Auth DB   : {safe_url(enterprise_settings.auth_database_url)}")
    print("=" * 72)

    with legacy_engine.connect() as legacy_conn:
        inspector = inspect(legacy_conn)
        required_tables = ["users", "roles", "permissions", "user_roles", "role_permissions"]
        available = set(inspector.get_table_names())
        missing = [table for table in required_tables if table not in available]
        if missing:
            raise RuntimeError(
                "Legacy database is reachable, but required Auth tables are missing: "
                + ", ".join(missing)
                + ". Confirm that the old database is finmark_db and not one of the new enterprise databases."
            )

        legacy_permissions = _read_table(
            legacy_conn,
            inspector,
            "permissions",
            ["id", "code", "name", "module", "description", "created_at"],
        )
        legacy_roles = _read_table(
            legacy_conn,
            inspector,
            "roles",
            ["id", "name", "description", "is_active", "created_at", "updated_at"],
        )
        legacy_users = _read_table(
            legacy_conn,
            inspector,
            "users",
            [
                "id",
                "username",
                "email",
                "hashed_password",
                "full_name",
                "is_active",
                "is_verified",
                "last_login_at",
                "created_at",
                "updated_at",
            ],
        )
        legacy_role_permissions = _read_table(legacy_conn, inspector, "role_permissions", ["role_id", "permission_id"])
        legacy_user_roles = _read_table(legacy_conn, inspector, "user_roles", ["user_id", "role_id"])

    stats.legacy_permissions_found = len(legacy_permissions)
    stats.legacy_roles_found = len(legacy_roles)
    stats.legacy_users_found = len(legacy_users)

    with session_scope(AuthSessionLocal) as auth_db:
        # Start with required enterprise roles/permissions, then import legacy values.
        seed_auth_database(auth_db)
        _ensure_extra_permissions(auth_db)

        permission_map: dict[int, AuthPermission] = {}
        for row in legacy_permissions:
            permission = _upsert_permission(auth_db, row)
            if row.get("id") is not None:
                permission_map[int(row["id"])] = permission
            stats.permissions_upserted += 1

        role_map: dict[int, AuthRole] = {}
        for row in legacy_roles:
            role = _upsert_role(auth_db, row)
            if row.get("id") is not None:
                role_map[int(row["id"])] = role
            stats.roles_upserted += 1

        for row in legacy_role_permissions:
            role = role_map.get(int(row["role_id"])) if row.get("role_id") is not None else None
            permission = permission_map.get(int(row["permission_id"])) if row.get("permission_id") is not None else None
            if role is not None and permission is not None and _link_role_permission(role, permission):
                stats.role_permissions_linked += 1

        user_map: dict[int, AuthUser] = {}
        for row in legacy_users:
            user = _upsert_user(auth_db, row, verify_imported_users=verify_imported_users)
            if row.get("id") is not None:
                user_map[int(row["id"])] = user
            stats.users_upserted += 1

        staff_role = auth_db.scalar(select(AuthRole).where(AuthRole.name == "Staff"))
        for row in legacy_user_roles:
            user = user_map.get(int(row["user_id"])) if row.get("user_id") is not None else None
            role = role_map.get(int(row["role_id"])) if row.get("role_id") is not None else None
            if user is not None and role is not None and _link_user_role(user, role):
                stats.user_roles_linked += 1

        # Any imported user without a role still receives Staff so Auth tokens are usable.
        if staff_role is not None:
            for user in user_map.values():
                if not user.roles:
                    _link_user_role(user, staff_role)

        stats.admin_users_repaired = _ensure_admin_access(auth_db, reset_admin_password=reset_admin_password)

        auth_db.add(
            AuthAuditLog(
                actor_user_id=None,
                action=AuditAction.CREATE,
                entity_type="auth_migration",
                entity_id="legacy-finmark-db",
                detail=(
                    f"Migrated {stats.legacy_users_found} users, {stats.legacy_roles_found} roles, "
                    f"and {stats.legacy_permissions_found} permissions from legacy database."
                ),
            )
        )

        if dry_run:
            auth_db.rollback()
            print("Dry run complete. No target Auth DB changes were committed.")

    return stats


def _print_stats(stats: MigrationStats) -> None:
    print("\nMigration summary")
    print("-" * 72)
    print(f"Legacy permissions found : {stats.legacy_permissions_found}")
    print(f"Legacy roles found       : {stats.legacy_roles_found}")
    print(f"Legacy users found       : {stats.legacy_users_found}")
    print(f"Permissions upserted     : {stats.permissions_upserted}")
    print(f"Roles upserted           : {stats.roles_upserted}")
    print(f"Users upserted           : {stats.users_upserted}")
    print(f"Role permissions linked  : {stats.role_permissions_linked}")
    print(f"User roles linked        : {stats.user_roles_linked}")
    print(f"Admin accounts repaired  : {stats.admin_users_repaired}")
    print("-" * 72)
    print("Admin access guaranteed: Admin dashboard + Product dashboard")
    print(f"Documented admin login  : admin@example.com / {DEFAULT_ADMIN_PASSWORD}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate legacy FinMark users/roles/permissions into the dedicated enterprise Auth DB.")
    parser.add_argument("--legacy-url", default=None, help="Full SQLAlchemy URL for the old finmark_db database.")
    parser.add_argument("--legacy-host", default="127.0.0.1")
    parser.add_argument("--legacy-port", default="3306")
    parser.add_argument("--legacy-database", default="finmark_db")
    parser.add_argument("--legacy-user", default=None)
    parser.add_argument("--legacy-password", default=None)
    parser.add_argument("--preserve-verification", action="store_true", help="Keep old is_verified values instead of making imported users verified.")
    parser.add_argument("--preserve-admin-password", action="store_true", help="Do not reset admin@example.com to Admin@12345.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    legacy_url = resolve_legacy_url(args)
    try:
        stats = migrate(
            legacy_url,
            verify_imported_users=not args.preserve_verification,
            reset_admin_password=not args.preserve_admin_password,
            dry_run=args.dry_run,
        )
        _print_stats(stats)
    except OperationalError as exc:
        print("\nLegacy Auth migration failed because the old MySQL database could not be opened.")
        print("Common fixes:")
        print("  1. Start MySQL Server / XAMPP MySQL.")
        print("  2. Confirm the old database name is finmark_db in MySQL Workbench.")
        print("  3. Use a MySQL account that can SELECT from finmark_db, for example:")
        print(r"     .\migrate-legacy-auth-to-enterprise.ps1 -LegacyUser root -LegacyPassword \"your-root-password\"")
        print("  4. Or run grant-legacy-auth-read-workbench.sql in MySQL Workbench as root, then run:")
        print(r"     .\migrate-legacy-auth-to-enterprise.ps1 -LegacyUser finmark_app -LegacyPassword \"FinmarkApp@2026!\"")
        raise exc
    except (ProgrammingError, SQLAlchemyError, RuntimeError) as exc:
        print("\nLegacy Auth migration failed.")
        print(str(exc))
        raise exc


if __name__ == "__main__":
    main()
