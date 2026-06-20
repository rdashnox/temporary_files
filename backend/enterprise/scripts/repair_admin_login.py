from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import OperationalError, ProgrammingError

from backend.core.security import verify_password
from backend.enterprise.databases import AuthSessionLocal, safe_url
from backend.enterprise.config import enterprise_settings
from backend.enterprise.models import AuthUser
from backend.enterprise.services.auth_enterprise_service import seed_auth_database


def main() -> None:
    print("FinMark Enterprise Auth Login Repair")
    print("=" * 58)
    print(f"Auth DB: {safe_url(enterprise_settings.auth_database_url)}")
    try:
        with AuthSessionLocal() as db:
            seed_auth_database(db)
            admin = db.scalar(select(AuthUser).where(AuthUser.email == "admin@example.com"))
            if admin is None:
                raise RuntimeError("Admin account was not created.")
            password_ok = verify_password("Admin@12345", admin.hashed_password)
            print(f"Admin ID       : {admin.id}")
            print(f"Admin email    : {admin.email}")
            print(f"Active         : {admin.is_active}")
            print(f"Verified       : {admin.is_verified}")
            print(f"Password check : {'OK' if password_ok else 'FAILED'}")
            print(f"Roles          : {[role.name for role in admin.roles]}")
            print(f"Permissions    : {sorted({permission.code for role in admin.roles for permission in role.permissions})}")
            if not password_ok:
                raise RuntimeError("Admin password hash still does not match Admin@12345.")
    except (OperationalError, ProgrammingError) as exc:
        print("\nCould not connect to the Auth DB or tables are missing.")
        print("Run these first:")
        print(r"  .\repair-mysql-connection.ps1 -StartIfStopped")
        print(r"  .\setup-enterprise-mysql.ps1")
        print(r"  .\run-enterprise-migrations-mysql.ps1")
        raise exc
    print("=" * 58)
    print("Login repair complete. Demo login: admin@example.com / Admin@12345")


if __name__ == "__main__":
    main()
