-- FinMark Enterprise Microservices - Verify Seeded Data in MySQL Workbench
-- Run this after .\seed-enterprise-mysql.ps1.

SELECT 'finmark_auth_db.auth_users' AS table_name, COUNT(*) AS row_count FROM finmark_auth_db.auth_users
UNION ALL
SELECT 'finmark_auth_db.auth_roles', COUNT(*) FROM finmark_auth_db.auth_roles
UNION ALL
SELECT 'finmark_auth_db.auth_permissions', COUNT(*) FROM finmark_auth_db.auth_permissions
UNION ALL
SELECT 'finmark_inventory_db.inventory_products', COUNT(*) FROM finmark_inventory_db.inventory_products
UNION ALL
SELECT 'finmark_order_db.order_orders', COUNT(*) FROM finmark_order_db.order_orders
UNION ALL
SELECT 'finmark_order_db.order_items', COUNT(*) FROM finmark_order_db.order_items
UNION ALL
SELECT 'finmark_order_db.order_outbox_events', COUNT(*) FROM finmark_order_db.order_outbox_events
UNION ALL
SELECT 'finmark_notification_db.notification_messages', COUNT(*) FROM finmark_notification_db.notification_messages
UNION ALL
SELECT 'finmark_notification_db.notification_inbox_events', COUNT(*) FROM finmark_notification_db.notification_inbox_events;

SELECT id, username, email, full_name, is_active, is_verified
FROM finmark_auth_db.auth_users
ORDER BY id;

SELECT id, sku, name, category, price, stock_quantity
FROM finmark_inventory_db.inventory_products
ORDER BY id
LIMIT 20;

SELECT id, order_number, user_id, customer_name, status, subtotal, shipping_fee, total, created_at
FROM finmark_order_db.order_orders
ORDER BY id DESC;

SELECT id, user_id, title, entity_type, entity_id, is_read, created_at
FROM finmark_notification_db.notification_messages
ORDER BY id DESC;


-- Auth migration checks
SELECT 'Auth migration users' AS item, COUNT(*) AS total FROM finmark_auth_db.auth_users;
SELECT 'Admin dashboard permissions' AS item, COUNT(*) AS total
FROM finmark_auth_db.auth_permissions
WHERE code IN ('users.manage','roles.manage','permissions.manage','dashboard.admin','dashboard.products','product_dashboard.access','inventory.read','products.read');
