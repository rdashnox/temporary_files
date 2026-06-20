from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Permission, Role, User
from ..core.security import hash_password


DEFAULT_PERMISSIONS = [
    ("users.read", "View Users", "users", "Read user profiles and account status."),
    ("users.manage", "Manage Users", "users", "Create, update, and deactivate users."),
    ("roles.manage", "Manage Roles", "access", "Manage roles and permissions."),
    ("orders.read", "View Orders", "orders", "View order lists and order details."),
    ("orders.manage", "Manage Orders", "orders", "Create and update orders."),
    ("inventory.read", "View Inventory", "inventory", "View product catalog and stock summaries."),
    ("notifications.read", "View Notifications", "notifications", "View in-app order and stock notifications."),
    ("reports.read", "View Reports", "reports", "View generated reports."),
    ("reports.manage", "Manage Reports", "reports", "Create and update report jobs."),
    ("planning.read", "View Planning Requests", "planning", "View planning requests."),
    ("planning.manage", "Manage Planning Requests", "planning", "Create and approve planning requests."),
    ("audit.read", "View Audit Logs", "audit", "Review audit activity."),
]


DEFAULT_ROLES = {
    "Admin": [code for code, *_ in DEFAULT_PERMISSIONS],
    "Manager": [
        "orders.read",
        "orders.manage",
        "inventory.read",
        "notifications.read",
        "reports.read",
        "reports.manage",
        "planning.read",
        "planning.manage",
    ],
    "Staff": ["orders.read", "orders.manage", "inventory.read", "notifications.read", "reports.read", "planning.read"],
    "Viewer": ["orders.read", "inventory.read", "notifications.read", "reports.read", "planning.read"],
    "Customer": ["inventory.read", "notifications.read"],
}


def seed_database(db: Session) -> None:
    """Seed roles, permissions, and a verified demo account for local development."""
    permissions_by_code: dict[str, Permission] = {}

    for code, name, module, description in DEFAULT_PERMISSIONS:
        permission = db.scalar(select(Permission).where(Permission.code == code))
        if permission is None:
            permission = Permission(
                code=code,
                name=name,
                module=module,
                description=description,
            )
            db.add(permission)
            db.flush()
        permissions_by_code[code] = permission

    roles_by_name: dict[str, Role] = {}
    for role_name, permission_codes in DEFAULT_ROLES.items():
        role = db.scalar(select(Role).where(Role.name == role_name))
        if role is None:
            role = Role(name=role_name, description=f"Default {role_name} role")
            db.add(role)
            db.flush()
        role.permissions = [permissions_by_code[code] for code in permission_codes]
        roles_by_name[role_name] = role

    seeded_users = [
        ("user@example.com", "Password123!", "Admin"),
        ("customer@example.com", "Customer123!", "Customer"),
    ]

    for email, password, role_name in seeded_users:
        demo_user = db.scalar(select(User).where(User.email == email))
        if demo_user is None:
            demo_user = User(
                username=email,
                email=email,
                hashed_password=hash_password(password),
                is_verified=True,
                is_active=True,
                roles=[roles_by_name[role_name]],
            )
            db.add(demo_user)
        elif not demo_user.roles:
            demo_user.roles = [roles_by_name[role_name]]

    db.commit()
