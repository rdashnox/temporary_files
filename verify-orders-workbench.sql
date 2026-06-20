-- FinMark dedicated Order DB verification
-- Run this in MySQL Workbench after checkout.
USE finmark_order_db;

SELECT COUNT(*) AS total_orders FROM order_orders;

SELECT
  id,
  order_number,
  user_id,
  customer_name,
  status,
  total,
  created_at
FROM order_orders
ORDER BY created_at DESC, id DESC
LIMIT 25;

SELECT
  oi.id,
  oi.order_id,
  oo.order_number,
  oi.product_id,
  oi.product_name,
  oi.quantity,
  oi.unit_price,
  oi.line_total
FROM order_items oi
JOIN order_orders oo ON oo.id = oi.order_id
ORDER BY oi.id DESC
LIMIT 50;
