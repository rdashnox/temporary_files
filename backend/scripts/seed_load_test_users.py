"""Create verified customer users for realistic concurrent-user load tests.

Usage from project root:
    python -m backend.scripts.seed_load_test_users --count 1000

Default credentials created:
    loadtest0001@example.com / LoadTest123!
    ...
    loadtest1000@example.com / LoadTest123!
"""

from __future__ import annotations

import argparse

from sqlalchemy import select

from backend.core.security import hash_password
from backend.database import session_scope
from backend.models import Role, User
from backend.services.seed_service import seed_database


def seed_users(count: int, password: str) -> int:
    created = 0
    with session_scope() as db:
        # Ensure Customer role exists even if this is a fresh local database.
        seed_database(db)
        customer_role = db.scalar(select(Role).where(Role.name == "Customer"))
        if customer_role is None:
            raise RuntimeError("Customer role was not found after seeding base data.")

        hashed_password = hash_password(password)
        for number in range(1, count + 1):
            email = f"loadtest{number:04d}@example.com"
            user = db.scalar(select(User).where(User.email == email))
            if user is not None:
                continue
            db.add(
                User(
                    username=email,
                    email=email,
                    hashed_password=hashed_password,
                    is_verified=True,
                    is_active=True,
                    roles=[customer_role],
                )
            )
            created += 1

    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed verified users for Locust load testing.")
    parser.add_argument("--count", type=int, default=1000, help="Number of users to seed.")
    parser.add_argument("--password", default="LoadTest123!", help="Password for all generated load-test users.")
    args = parser.parse_args()

    created = seed_users(args.count, args.password)
    print(f"Created {created} load-test user(s). Total requested: {args.count}.")


if __name__ == "__main__":
    main()
