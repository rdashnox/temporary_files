-- ============================================================================
-- FinMark Enterprise - Repair Admin Order List status values
-- ============================================================================
-- Run this in MySQL Workbench if the Admin Dashboard Order List says
-- "No orders found" or the diagnostic shows /api/v1/orders returns 500 while
-- checkout-specific verification passes.
--
-- Cause:
--   Some earlier demo SQL seeds used lowercase statuses: paid, completed.
--   The Python backend expects uppercase statuses: PAID, COMPLETED.
-- ============================================================================

USE finmark_order_db;

SELECT 'Before repair' AS section, status, COUNT(*) AS total
FROM order_orders
GROUP BY status
ORDER BY status;

UPDATE order_orders
SET status = UPPER(TRIM(status))
WHERE status IS NOT NULL
  AND status <> UPPER(TRIM(status));

UPDATE order_orders
SET status = 'NEW'
WHERE status IS NULL
   OR TRIM(status) = ''
   OR UPPER(TRIM(status)) NOT IN ('NEW','PAID','PACKED','SHIPPED','COMPLETED','CANCELLED','EXCEPTION');


UPDATE order_outbox_events
SET status = UPPER(TRIM(status))
WHERE status IS NOT NULL
  AND status <> UPPER(TRIM(status));

UPDATE order_outbox_events
SET status = 'PENDING'
WHERE status IS NULL
   OR TRIM(status) = ''
   OR UPPER(TRIM(status)) NOT IN ('PENDING','PUBLISHED','FAILED');

SELECT 'After repair' AS section, status, COUNT(*) AS total
FROM order_orders
GROUP BY status
ORDER BY status;

SELECT id, order_number, customer_name, status, total, created_at
FROM order_orders
ORDER BY created_at DESC, id DESC
LIMIT 50;
