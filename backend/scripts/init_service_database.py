"""One-shot database initializer for replicated microservice deployments.

Run this once before starting service replicas. It avoids the race condition that
can happen when 12 containers all try to create/alter/seed the same database at
startup.
"""

from backend.database import init_db, session_scope
from backend.services.seed_service import seed_database


def main() -> None:
    init_db()
    with session_scope() as db:
        seed_database(db)
    print("FinMark database schema and demo seed data are ready.")


if __name__ == "__main__":
    main()
