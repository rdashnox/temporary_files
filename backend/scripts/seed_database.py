"""Seed roles, permissions, and the demo user manually.

Run from the project root after configuring DATABASE_URL:
    python -m backend.scripts.seed_database
"""
from backend.database import init_db, session_scope
from backend.services.seed_service import seed_database


def main() -> None:
    init_db()
    with session_scope() as db:
        seed_database(db)
    print("Database seeded successfully.")


if __name__ == "__main__":
    main()
