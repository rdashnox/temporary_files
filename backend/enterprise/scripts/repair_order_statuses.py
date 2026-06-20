"""Repair legacy order status values in the dedicated Order database.

Earlier Workbench demo seed scripts inserted lowercase status values such as
``paid`` and ``completed``. The enterprise Python app expects uppercase API
status names such as ``PAID`` and ``COMPLETED``. Mixed status values can make an
unfiltered Admin Manage Order List fail, while a search for a newly-created
order still works.

Run from the project root:
    python -m backend.enterprise.scripts.repair_order_statuses
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.enterprise.databases import order_engine, safe_url

VALID_STATUSES = ("NEW", "PAID", "PACKED", "SHIPPED", "COMPLETED", "CANCELLED", "EXCEPTION")


def main() -> None:
    print("FinMark Order DB status repair")
    print("=" * 56)
    print(f"Order DB URL: {safe_url(str(order_engine.url))}")

    try:
        with order_engine.begin() as connection:
            before = connection.execute(
                text("SELECT status, COUNT(*) AS total FROM order_orders GROUP BY status ORDER BY status")
            ).fetchall()
            print("\nBefore repair:")
            if before:
                for status, total in before:
                    print(f"  {status}: {total}")
            else:
                print("  No orders found yet.")

            normalized = connection.execute(
                text(
                    """
                    UPDATE order_orders
                    SET status = UPPER(TRIM(status))
                    WHERE status IS NOT NULL
                      AND status <> UPPER(TRIM(status))
                    """
                )
            ).rowcount

            invalid = connection.execute(
                text(
                    """
                    UPDATE order_orders
                    SET status = 'NEW'
                    WHERE status IS NULL
                       OR TRIM(status) = ''
                       OR UPPER(TRIM(status)) NOT IN ('NEW','PAID','PACKED','SHIPPED','COMPLETED','CANCELLED','EXCEPTION')
                    """
                )
            ).rowcount

            outbox_normalized = connection.execute(
                text(
                    """
                    UPDATE order_outbox_events
                    SET status = UPPER(TRIM(status))
                    WHERE status IS NOT NULL
                      AND status <> UPPER(TRIM(status))
                    """
                )
            ).rowcount

            connection.execute(
                text(
                    """
                    UPDATE order_outbox_events
                    SET status = 'PENDING'
                    WHERE status IS NULL
                       OR TRIM(status) = ''
                       OR UPPER(TRIM(status)) NOT IN ('PENDING','PUBLISHED','FAILED')
                    """
                )
            )

            after = connection.execute(
                text("SELECT status, COUNT(*) AS total FROM order_orders GROUP BY status ORDER BY status")
            ).fetchall()

            print("\nAfter repair:")
            if after:
                for status, total in after:
                    print(f"  {status}: {total}")
            else:
                print("  No orders found yet.")

            print("\nRows normalized:", normalized)
            print("Invalid/blank rows reset to NEW:", invalid)
            print("Outbox rows normalized:", outbox_normalized)
            print("\nPASS: Order statuses are now compatible with the Admin Manage Order List.")
    except SQLAlchemyError as exc:
        print("\nFAILED: Could not repair order statuses.")
        print(exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
