-- ============================================================================
-- FinMark Enterprise Microservices - 4 Dedicated Database Demo Seed Script
-- ============================================================================
-- Purpose:
--   Seeds demo roles, permissions, users, products, sample orders, outbox events,
--   and notifications across the four dedicated microservice databases:
--     1. finmark_auth_db
--     2. finmark_inventory_db
--     3. finmark_order_db
--     4. finmark_notification_db
--
-- How to use in MySQL Workbench:
--   1. Make sure MySQL Server is running.
--   2. Make sure Alembic migrations were already run, so the tables exist.
--      Required tables include auth_users, inventory_products, order_orders,
--      notification_messages, etc.
--   3. Open this file in MySQL Workbench.
--   4. Execute the whole script.
--   5. Refresh SCHEMAS and inspect the four finmark_* databases.
--
-- Safe to rerun:
--   Uses INSERT ... ON DUPLICATE KEY UPDATE and NOT EXISTS checks.
--
-- Demo login accounts:
--   admin@example.com              / Admin@12345
--   manager@example.com            / Demo@12345
--   product.manager@example.com    / Demo@12345
--   inventory.manager@example.com  / Demo@12345
--   order.manager@example.com      / Demo@12345
--   notification.manager@example.com / Demo@12345
--   report.analyst@example.com     / Demo@12345
--   planning.officer@example.com   / Demo@12345
--   auditor@example.com            / Demo@12345
--   staff@example.com              / Demo@12345
--   viewer@example.com             / Demo@12345
--   user@example.com               / Demo@12345
--   customer@example.com           / Demo@12345
-- ============================================================================

SET NAMES utf8mb4;
SET time_zone = '+08:00';
SET @now := NOW(6);

CREATE DATABASE IF NOT EXISTS finmark_auth_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS finmark_inventory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS finmark_order_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS finmark_notification_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- These hashes were generated using the same bcrypt/passlib style used by the FastAPI backend.
-- The seeder intentionally resets demo user passwords so classroom/demo login is predictable.
SET @admin_hash := '$2b$12$Y2QSEgfU90VlmsPNUDJ2quNwecxyghyYuprJbg7wnsmoapUd3UruO'; -- Admin@12345
SET @demo_hash  := '$2b$12$xd/xJ5RIWnats6tnQwqTnO9YrkYE37j6HvKYFwbIYX0V8QsKcLy6u'; -- Demo@12345

-- ============================================================================
-- 1) AUTH DATABASE: permissions, roles, users, mappings
-- ============================================================================
USE finmark_auth_db;

INSERT INTO auth_permissions (code, name, module, description, created_at) VALUES
('users.read', 'Read users', 'auth', 'View user accounts.', @now),
('users.manage', 'Manage users', 'auth', 'Create, update, disable, and assign user accounts.', @now),
('users.create', 'Create users', 'auth', 'Create user accounts.', @now),
('users.update', 'Update users', 'auth', 'Update user accounts.', @now),
('users.delete', 'Delete users', 'auth', 'Delete or deactivate user accounts.', @now),
('roles.read', 'Read roles', 'auth', 'View roles.', @now),
('roles.manage', 'Manage roles', 'auth', 'Create and update roles.', @now),
('roles.create', 'Create roles', 'auth', 'Create roles.', @now),
('roles.update', 'Update roles', 'auth', 'Update roles.', @now),
('roles.delete', 'Delete roles', 'auth', 'Delete or deactivate roles.', @now),
('permissions.read', 'Read permissions', 'auth', 'View permissions.', @now),
('permissions.manage', 'Manage permissions', 'auth', 'Create and update permissions.', @now),
('permissions.create', 'Create permissions', 'auth', 'Create permissions.', @now),
('permissions.update', 'Update permissions', 'auth', 'Update permissions.', @now),
('permissions.delete', 'Delete permissions', 'auth', 'Delete permissions.', @now),
('orders.read', 'Read orders', 'order', 'View orders.', @now),
('orders.manage', 'Manage orders', 'order', 'Create, update, and process orders.', @now),
('orders.create', 'Create orders', 'order', 'Create orders.', @now),
('orders.update', 'Update orders', 'order', 'Update orders.', @now),
('orders.delete', 'Delete orders', 'order', 'Delete/cancel orders.', @now),
('inventory.read', 'Read inventory', 'inventory', 'View inventory.', @now),
('inventory.manage', 'Manage inventory', 'inventory', 'Manage stock and inventory records.', @now),
('inventory.create', 'Create inventory records', 'inventory', 'Create inventory records.', @now),
('inventory.update', 'Update inventory records', 'inventory', 'Update inventory records.', @now),
('inventory.delete', 'Delete inventory records', 'inventory', 'Delete inventory records.', @now),
('products.read', 'Read products', 'inventory', 'View products.', @now),
('products.manage', 'Manage products', 'inventory', 'Manage product catalog.', @now),
('products.create', 'Create products', 'inventory', 'Create products.', @now),
('products.update', 'Update products', 'inventory', 'Update products.', @now),
('products.delete', 'Delete products', 'inventory', 'Delete/deactivate products.', @now),
('dashboard.admin', 'Open Admin Dashboard', 'dashboard', 'Access the Admin Dashboard.', @now),
('dashboard.products', 'Open Product Dashboard', 'dashboard', 'Access the Product Dashboard.', @now),
('product_dashboard.access', 'Access Product Dashboard', 'dashboard', 'Legacy-compatible Product Dashboard access flag.', @now),
('notifications.read', 'Read notifications', 'notification', 'View notifications.', @now),
('notifications.manage', 'Manage notifications', 'notification', 'Manage notifications.', @now),
('notifications.create', 'Create notifications', 'notification', 'Create notifications.', @now),
('notifications.update', 'Update notifications', 'notification', 'Update notifications.', @now),
('notifications.delete', 'Delete notifications', 'notification', 'Delete notifications.', @now),
('reports.read', 'Read reports', 'report', 'View reports.', @now),
('reports.manage', 'Manage reports', 'report', 'Manage reports.', @now),
('reports.create', 'Create reports', 'report', 'Create reports.', @now),
('reports.update', 'Update reports', 'report', 'Update reports.', @now),
('reports.delete', 'Delete reports', 'report', 'Delete reports.', @now),
('reports.generate', 'Generate reports', 'report', 'Generate reports.', @now),
('planning.read', 'Read planning requests', 'planning', 'View planning requests.', @now),
('planning.manage', 'Manage planning requests', 'planning', 'Manage planning requests.', @now),
('planning.create', 'Create planning requests', 'planning', 'Create planning requests.', @now),
('planning.update', 'Update planning requests', 'planning', 'Update planning requests.', @now),
('planning.delete', 'Delete planning requests', 'planning', 'Delete planning requests.', @now),
('planning.approve', 'Approve planning requests', 'planning', 'Approve planning requests.', @now),
('planning.reject', 'Reject planning requests', 'planning', 'Reject planning requests.', @now),
('planning_requests.read', 'Read planning requests alias', 'planning', 'Compatibility alias for planning.read.', @now),
('planning_requests.create', 'Create planning requests alias', 'planning', 'Compatibility alias for planning.create.', @now),
('planning_requests.update', 'Update planning requests alias', 'planning', 'Compatibility alias for planning.update.', @now),
('planning_requests.delete', 'Delete planning requests alias', 'planning', 'Compatibility alias for planning.delete.', @now),
('planning_requests.approve', 'Approve planning requests alias', 'planning', 'Compatibility alias for planning.approve.', @now),
('planning_requests.reject', 'Reject planning requests alias', 'planning', 'Compatibility alias for planning.reject.', @now),
('audit.read', 'Read audit logs', 'audit', 'View audit logs.', @now),
('audit.manage', 'Manage audit logs', 'audit', 'Manage audit logs.', @now),
('audit_logs.read', 'Read audit logs alias', 'audit', 'Compatibility alias for audit.read.', @now),
('audit_logs.create', 'Create audit logs alias', 'audit', 'Compatibility alias for audit create.', @now),
('audit_logs.update', 'Update audit logs alias', 'audit', 'Compatibility alias for audit update.', @now),
('audit_logs.delete', 'Delete audit logs alias', 'audit', 'Compatibility alias for audit delete.', @now)
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  module = VALUES(module),
  description = VALUES(description);

INSERT INTO auth_roles (name, description, is_active, created_at, updated_at) VALUES
('Super Admin', 'Highest-level full access role for enterprise demo.', 1, @now, @now),
('Administrator', 'Full system administrator with access to Admin and Product dashboards.', 1, @now, @now),
('Admin', 'Admin alias role with full system access.', 1, @now, @now),
('Superuser', 'Superuser alias role with full system access.', 1, @now, @now),
('Manager', 'General manager with operational dashboard access.', 1, @now, @now),
('Product Manager', 'Manages Product Dashboard and product catalog.', 1, @now, @now),
('Inventory Manager', 'Manages product stock and inventory.', 1, @now, @now),
('Order Manager', 'Manages customer orders and checkout operations.', 1, @now, @now),
('Notification Manager', 'Manages notifications and internal event messages.', 1, @now, @now),
('Report Analyst', 'Reads and manages reports.', 1, @now, @now),
('Planning Officer', 'Reads and manages planning requests.', 1, @now, @now),
('Auditor', 'Reads audit logs and compliance records.', 1, @now, @now),
('Staff', 'Daily operations staff with product and order access.', 1, @now, @now),
('Viewer', 'Read-only demo user.', 1, @now, @now),
('User', 'General authenticated user.', 1, @now, @now),
('Customer', 'Product-only customer role.', 1, @now, @now)
ON DUPLICATE KEY UPDATE
  description = VALUES(description),
  is_active = VALUES(is_active),
  updated_at = VALUES(updated_at);

-- Full-access roles: admin accounts must see every dashboard, including Product Dashboard.
INSERT INTO auth_role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, @now
FROM auth_roles r
CROSS JOIN auth_permissions p
WHERE r.name IN ('Super Admin', 'Administrator', 'Admin', 'Superuser')
ON DUPLICATE KEY UPDATE assigned_at = auth_role_permissions.assigned_at;

-- Manager role: broad operational access, but not low-level auth administration.
INSERT INTO auth_role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, @now
FROM auth_roles r
JOIN auth_permissions p ON p.code IN (
  'dashboard.admin','dashboard.products','product_dashboard.access',
  'orders.read','orders.manage','orders.create','orders.update',
  'inventory.read','inventory.manage','inventory.update',
  'products.read','products.manage','products.create','products.update',
  'notifications.read','notifications.manage',
  'reports.read','reports.manage','reports.generate',
  'planning.read','planning.manage','planning.approve','planning.reject',
  'audit.read'
)
WHERE r.name = 'Manager'
ON DUPLICATE KEY UPDATE assigned_at = auth_role_permissions.assigned_at;

-- Product Manager
INSERT INTO auth_role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, @now
FROM auth_roles r
JOIN auth_permissions p ON p.code IN (
  'dashboard.products','product_dashboard.access',
  'inventory.read','products.read','products.manage','products.create','products.update','products.delete',
  'notifications.read','reports.read'
)
WHERE r.name = 'Product Manager'
ON DUPLICATE KEY UPDATE assigned_at = auth_role_permissions.assigned_at;

-- Inventory Manager
INSERT INTO auth_role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, @now
FROM auth_roles r
JOIN auth_permissions p ON p.code IN (
  'dashboard.products','product_dashboard.access',
  'inventory.read','inventory.manage','inventory.create','inventory.update','inventory.delete',
  'products.read','products.manage','products.update',
  'notifications.read','reports.read'
)
WHERE r.name = 'Inventory Manager'
ON DUPLICATE KEY UPDATE assigned_at = auth_role_permissions.assigned_at;

-- Order Manager
INSERT INTO auth_role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, @now
FROM auth_roles r
JOIN auth_permissions p ON p.code IN (
  'dashboard.products','product_dashboard.access',
  'orders.read','orders.manage','orders.create','orders.update','orders.delete',
  'inventory.read','products.read','notifications.read','reports.read'
)
WHERE r.name = 'Order Manager'
ON DUPLICATE KEY UPDATE assigned_at = auth_role_permissions.assigned_at;

-- Notification Manager
INSERT INTO auth_role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, @now
FROM auth_roles r
JOIN auth_permissions p ON p.code IN (
  'dashboard.products','product_dashboard.access',
  'notifications.read','notifications.manage','notifications.create','notifications.update','notifications.delete',
  'orders.read','inventory.read','products.read'
)
WHERE r.name = 'Notification Manager'
ON DUPLICATE KEY UPDATE assigned_at = auth_role_permissions.assigned_at;

-- Report Analyst
INSERT INTO auth_role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, @now
FROM auth_roles r
JOIN auth_permissions p ON p.code IN (
  'dashboard.products','product_dashboard.access',
  'reports.read','reports.manage','reports.generate','orders.read','inventory.read','products.read'
)
WHERE r.name = 'Report Analyst'
ON DUPLICATE KEY UPDATE assigned_at = auth_role_permissions.assigned_at;

-- Planning Officer
INSERT INTO auth_role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, @now
FROM auth_roles r
JOIN auth_permissions p ON p.code IN (
  'dashboard.products','product_dashboard.access',
  'planning.read','planning.manage','planning.create','planning.update','planning.approve','planning.reject',
  'planning_requests.read','planning_requests.create','planning_requests.update','planning_requests.approve','planning_requests.reject',
  'orders.read','products.read'
)
WHERE r.name = 'Planning Officer'
ON DUPLICATE KEY UPDATE assigned_at = auth_role_permissions.assigned_at;

-- Auditor
INSERT INTO auth_role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, @now
FROM auth_roles r
JOIN auth_permissions p ON p.code IN (
  'dashboard.admin','dashboard.products','product_dashboard.access',
  'audit.read','audit.manage','audit_logs.read','users.read','roles.read','permissions.read','orders.read','reports.read','planning.read'
)
WHERE r.name = 'Auditor'
ON DUPLICATE KEY UPDATE assigned_at = auth_role_permissions.assigned_at;

-- Staff
INSERT INTO auth_role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, @now
FROM auth_roles r
JOIN auth_permissions p ON p.code IN (
  'dashboard.products','product_dashboard.access',
  'orders.read','orders.create','inventory.read','products.read','notifications.read'
)
WHERE r.name = 'Staff'
ON DUPLICATE KEY UPDATE assigned_at = auth_role_permissions.assigned_at;

-- Viewer and User: read-only/product dashboard access.
INSERT INTO auth_role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, @now
FROM auth_roles r
JOIN auth_permissions p ON p.code IN (
  'dashboard.products','product_dashboard.access','orders.read','inventory.read','products.read','notifications.read','reports.read','planning.read'
)
WHERE r.name IN ('Viewer', 'User')
ON DUPLICATE KEY UPDATE assigned_at = auth_role_permissions.assigned_at;

-- Customer: product-only, intentionally no Admin Dashboard permission.
INSERT INTO auth_role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, @now
FROM auth_roles r
JOIN auth_permissions p ON p.code IN ('dashboard.products','product_dashboard.access','inventory.read','products.read','notifications.read')
WHERE r.name = 'Customer'
ON DUPLICATE KEY UPDATE assigned_at = auth_role_permissions.assigned_at;

-- Demo users. All are verified and active.
INSERT INTO auth_users (username, email, hashed_password, full_name, is_active, is_verified, verification_token, verification_token_expires_at, password_reset_token, password_reset_token_expires_at, last_login_at, created_at, updated_at) VALUES
('admin@example.com', 'admin@example.com', @admin_hash, 'System Administrator', 1, 1, NULL, NULL, NULL, NULL, NULL, @now, @now),
('manager@example.com', 'manager@example.com', @demo_hash, 'Demo General Manager', 1, 1, NULL, NULL, NULL, NULL, NULL, @now, @now),
('product.manager@example.com', 'product.manager@example.com', @demo_hash, 'Demo Product Manager', 1, 1, NULL, NULL, NULL, NULL, NULL, @now, @now),
('inventory.manager@example.com', 'inventory.manager@example.com', @demo_hash, 'Demo Inventory Manager', 1, 1, NULL, NULL, NULL, NULL, NULL, @now, @now),
('order.manager@example.com', 'order.manager@example.com', @demo_hash, 'Demo Order Manager', 1, 1, NULL, NULL, NULL, NULL, NULL, @now, @now),
('notification.manager@example.com', 'notification.manager@example.com', @demo_hash, 'Demo Notification Manager', 1, 1, NULL, NULL, NULL, NULL, NULL, @now, @now),
('report.analyst@example.com', 'report.analyst@example.com', @demo_hash, 'Demo Report Analyst', 1, 1, NULL, NULL, NULL, NULL, NULL, @now, @now),
('planning.officer@example.com', 'planning.officer@example.com', @demo_hash, 'Demo Planning Officer', 1, 1, NULL, NULL, NULL, NULL, NULL, @now, @now),
('auditor@example.com', 'auditor@example.com', @demo_hash, 'Demo Auditor', 1, 1, NULL, NULL, NULL, NULL, NULL, @now, @now),
('staff@example.com', 'staff@example.com', @demo_hash, 'Demo Staff User', 1, 1, NULL, NULL, NULL, NULL, NULL, @now, @now),
('viewer@example.com', 'viewer@example.com', @demo_hash, 'Demo Viewer User', 1, 1, NULL, NULL, NULL, NULL, NULL, @now, @now),
('user@example.com', 'user@example.com', @demo_hash, 'Demo General User', 1, 1, NULL, NULL, NULL, NULL, NULL, @now, @now),
('customer@example.com', 'customer@example.com', @demo_hash, 'Demo Customer User', 1, 1, NULL, NULL, NULL, NULL, NULL, @now, @now)
ON DUPLICATE KEY UPDATE
  email = VALUES(email),
  hashed_password = VALUES(hashed_password),
  full_name = VALUES(full_name),
  is_active = 1,
  is_verified = 1,
  verification_token = NULL,
  verification_token_expires_at = NULL,
  password_reset_token = NULL,
  password_reset_token_expires_at = NULL,
  updated_at = VALUES(updated_at);

-- User-to-role assignments.
INSERT INTO auth_user_roles (user_id, role_id, assigned_at)
SELECT u.id, r.id, @now FROM auth_users u JOIN auth_roles r
WHERE u.username = 'admin@example.com' AND r.name IN ('Super Admin', 'Administrator', 'Admin', 'Superuser')
ON DUPLICATE KEY UPDATE assigned_at = auth_user_roles.assigned_at;

INSERT INTO auth_user_roles (user_id, role_id, assigned_at)
SELECT u.id, r.id, @now FROM auth_users u JOIN auth_roles r
WHERE (u.username = 'manager@example.com' AND r.name = 'Manager')
   OR (u.username = 'product.manager@example.com' AND r.name = 'Product Manager')
   OR (u.username = 'inventory.manager@example.com' AND r.name = 'Inventory Manager')
   OR (u.username = 'order.manager@example.com' AND r.name = 'Order Manager')
   OR (u.username = 'notification.manager@example.com' AND r.name = 'Notification Manager')
   OR (u.username = 'report.analyst@example.com' AND r.name = 'Report Analyst')
   OR (u.username = 'planning.officer@example.com' AND r.name = 'Planning Officer')
   OR (u.username = 'auditor@example.com' AND r.name = 'Auditor')
   OR (u.username = 'staff@example.com' AND r.name = 'Staff')
   OR (u.username = 'viewer@example.com' AND r.name = 'Viewer')
   OR (u.username = 'user@example.com' AND r.name = 'User')
   OR (u.username = 'customer@example.com' AND r.name = 'Customer')
ON DUPLICATE KEY UPDATE assigned_at = auth_user_roles.assigned_at;

-- Keep useful user id variables for cross-service demo rows.
SELECT @admin_id := id FROM auth_users WHERE username = 'admin@example.com' LIMIT 1;
SELECT @customer_id := id FROM auth_users WHERE username = 'customer@example.com' LIMIT 1;
SELECT @manager_id := id FROM auth_users WHERE username = 'manager@example.com' LIMIT 1;

INSERT INTO auth_audit_logs (actor_user_id, action, entity_type, entity_id, detail, created_at)
SELECT @admin_id, 'create', 'seed', 'four-dedicated-databases', 'Workbench demo seed executed for all four dedicated databases.', @now
WHERE NOT EXISTS (
  SELECT 1 FROM auth_audit_logs
  WHERE entity_type = 'seed' AND entity_id = 'four-dedicated-databases'
);

-- ============================================================================
-- 2) INVENTORY DATABASE: product catalog and sample outbox event
-- ============================================================================
USE finmark_inventory_db;

INSERT INTO inventory_products (id, sku, name, category, description, price, compare_at_price, stock_quantity, rating, badge, image, is_active, created_at, updated_at) VALUES
(1, 'FM-0001', 'FinMark Smart Ledger', 'Finance Tools', 'A lightweight ledger kit for tracking small-business sales, expenses, and cash flow.', 1499.00, 1899.00, 18, 4.80, 'Best Seller', '📒', 1, @now, @now),
(2, 'FM-0002', 'Marketing Launch Pack', 'Marketing', 'Ready-to-use campaign templates for product launches, retargeting, and weekly reporting.', 2199.00, 2599.00, 11, 4.70, 'Popular', '🚀', 1, @now, @now),
(3, 'FM-0003', 'Inventory Starter Bundle', 'Operations', 'Barcode labels, reorder trackers, and stock movement templates for growing stores.', 1799.00, NULL, 25, 4.60, 'New', '📦', 1, @now, @now),
(4, 'FM-0004', 'Business Analytics Board', 'Analytics', 'Dashboard widgets for revenue trends, product performance, and conversion monitoring.', 2999.00, 3499.00, 8, 4.90, 'Premium', '📊', 1, @now, @now),
(5, 'FM-0005', 'Checkout Optimization Kit', 'E-Commerce', 'A UX checklist and reporting pack for reducing abandoned carts and improving checkout flow.', 1299.00, 1599.00, 16, 4.50, 'Sale', '🛒', 1, @now, @now),
(6, 'FM-0006', 'Customer Care Script Set', 'Support', 'Reusable response templates for order issues, refunds, shipping delays, and client follow-ups.', 899.00, NULL, 31, 4.40, 'Starter', '💬', 1, @now, @now)
ON DUPLICATE KEY UPDATE
  sku = VALUES(sku),
  name = VALUES(name),
  category = VALUES(category),
  description = VALUES(description),
  price = VALUES(price),
  compare_at_price = VALUES(compare_at_price),
  stock_quantity = VALUES(stock_quantity),
  rating = VALUES(rating),
  badge = VALUES(badge),
  image = VALUES(image),
  is_active = VALUES(is_active),
  updated_at = VALUES(updated_at);

INSERT INTO inventory_outbox_events (event_id, event_type, aggregate_type, aggregate_id, payload_json, status, attempts, created_at, published_at) VALUES
('demo-inventory-low-stock-0001', 'inventory.low_stock', 'inventory_product', '2',
 JSON_OBJECT('event_id','demo-inventory-low-stock-0001','event_type','inventory.low_stock','aggregate_type','inventory_product','aggregate_id','2','payload', JSON_OBJECT('product_id', 2, 'product_name', 'Marketing Launch Pack', 'stock', 11)),
 'PUBLISHED', 0, @now, @now)
ON DUPLICATE KEY UPDATE
  payload_json = VALUES(payload_json),
  status = VALUES(status),
  attempts = VALUES(attempts),
  published_at = VALUES(published_at);

-- ============================================================================
-- 3) ORDER DATABASE: sample orders, order items, outbox events
-- ============================================================================
USE finmark_order_db;

INSERT INTO order_orders (order_number, user_id, idempotency_key, customer_name, delivery_address, payment_method, status, subtotal, discount, shipping_fee, tax, total, created_at, updated_at) VALUES
('FM-DEMO-0001', @customer_id, 'seed-demo-order-0001', 'Demo Customer User', 'FinMark Demo Address, Quezon City', 'Cash on Delivery', 'PAID', 5897.00, 0.00, 50.00, 0.00, 5947.00, @now, @now),
('FM-DEMO-0002', @manager_id, 'seed-demo-order-0002', 'Demo General Manager', 'FinMark Office Demo Address', 'Bank Transfer', 'COMPLETED', 3098.00, 100.00, 0.00, 0.00, 2998.00, @now, @now)
ON DUPLICATE KEY UPDATE
  user_id = VALUES(user_id),
  customer_name = VALUES(customer_name),
  delivery_address = VALUES(delivery_address),
  payment_method = VALUES(payment_method),
  status = VALUES(status),
  subtotal = VALUES(subtotal),
  discount = VALUES(discount),
  shipping_fee = VALUES(shipping_fee),
  tax = VALUES(tax),
  total = VALUES(total),
  updated_at = VALUES(updated_at);

SELECT @order1_id := id FROM order_orders WHERE order_number = 'FM-DEMO-0001' LIMIT 1;
SELECT @order2_id := id FROM order_orders WHERE order_number = 'FM-DEMO-0002' LIMIT 1;

INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price, line_total)
SELECT @order1_id, 1, 'FinMark Smart Ledger', 1, 1499.00, 1499.00 WHERE @order1_id IS NOT NULL
ON DUPLICATE KEY UPDATE product_name = VALUES(product_name), quantity = VALUES(quantity), unit_price = VALUES(unit_price), line_total = VALUES(line_total);

INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price, line_total)
SELECT @order1_id, 2, 'Marketing Launch Pack', 2, 2199.00, 4398.00 WHERE @order1_id IS NOT NULL
ON DUPLICATE KEY UPDATE product_name = VALUES(product_name), quantity = VALUES(quantity), unit_price = VALUES(unit_price), line_total = VALUES(line_total);

INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price, line_total)
SELECT @order2_id, 5, 'Checkout Optimization Kit', 1, 1299.00, 1299.00 WHERE @order2_id IS NOT NULL
ON DUPLICATE KEY UPDATE product_name = VALUES(product_name), quantity = VALUES(quantity), unit_price = VALUES(unit_price), line_total = VALUES(line_total);

INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price, line_total)
SELECT @order2_id, 3, 'Inventory Starter Bundle', 1, 1799.00, 1799.00 WHERE @order2_id IS NOT NULL
ON DUPLICATE KEY UPDATE product_name = VALUES(product_name), quantity = VALUES(quantity), unit_price = VALUES(unit_price), line_total = VALUES(line_total);

INSERT INTO order_outbox_events (event_id, event_type, aggregate_type, aggregate_id, payload_json, status, attempts, created_at, published_at) VALUES
('demo-order-created-0001', 'order.created', 'order', 'FM-DEMO-0001',
 JSON_OBJECT('event_id','demo-order-created-0001','event_type','order.created','aggregate_type','order','aggregate_id','FM-DEMO-0001','payload', JSON_OBJECT('order_number','FM-DEMO-0001','order_id',@order1_id,'user_id',@customer_id,'customer_name','Demo Customer User','total',5947.00,'status','PAID','source','workbench-seed')),
 'PUBLISHED', 0, @now, @now),
('demo-order-created-0002', 'order.created', 'order', 'FM-DEMO-0002',
 JSON_OBJECT('event_id','demo-order-created-0002','event_type','order.created','aggregate_type','order','aggregate_id','FM-DEMO-0002','payload', JSON_OBJECT('order_number','FM-DEMO-0002','order_id',@order2_id,'user_id',@manager_id,'customer_name','Demo General Manager','total',2998.00,'status','COMPLETED','source','workbench-seed')),
 'PUBLISHED', 0, @now, @now)
ON DUPLICATE KEY UPDATE
  payload_json = VALUES(payload_json),
  status = VALUES(status),
  attempts = VALUES(attempts),
  published_at = VALUES(published_at);

-- ============================================================================
-- 4) NOTIFICATION DATABASE: sample notifications and inbox events
-- ============================================================================
USE finmark_notification_db;

INSERT INTO notification_messages (user_id, title, message, channel, entity_type, entity_id, is_read, created_at)
SELECT NULL, 'Enterprise notification service ready', 'Notification DB is separated and ready to consume events.', 'in_app', 'system', 'notification-service', 0, @now
WHERE NOT EXISTS (SELECT 1 FROM notification_messages WHERE entity_type = 'system' AND entity_id = 'notification-service');

INSERT INTO notification_messages (user_id, title, message, channel, entity_type, entity_id, is_read, created_at)
SELECT @admin_id, 'Admin full access ready', 'The admin account has full access to Admin Dashboard and Product Dashboard.', 'in_app', 'auth', 'admin-full-access', 0, @now
WHERE NOT EXISTS (SELECT 1 FROM notification_messages WHERE entity_type = 'auth' AND entity_id = 'admin-full-access');

INSERT INTO notification_messages (user_id, title, message, channel, entity_type, entity_id, is_read, created_at)
SELECT @customer_id, 'Demo order created', 'Sample order FM-DEMO-0001 was seeded successfully.', 'in_app', 'order', 'FM-DEMO-0001', 0, @now
WHERE NOT EXISTS (SELECT 1 FROM notification_messages WHERE entity_type = 'order' AND entity_id = 'FM-DEMO-0001');

INSERT INTO notification_messages (user_id, title, message, channel, entity_type, entity_id, is_read, created_at)
SELECT NULL, 'Low stock alert', 'Marketing Launch Pack is down to 11 unit(s). Consider restocking.', 'in_app', 'inventory', '2', 0, @now
WHERE NOT EXISTS (SELECT 1 FROM notification_messages WHERE entity_type = 'inventory' AND entity_id = '2');

INSERT INTO notification_inbox_events (event_id, event_type, payload_json, processed_at) VALUES
('demo-order-created-0001', 'order.created', JSON_OBJECT('event_id','demo-order-created-0001','event_type','order.created','aggregate_type','order','aggregate_id','FM-DEMO-0001','payload', JSON_OBJECT('order_number','FM-DEMO-0001','user_id',@customer_id)), @now),
('demo-order-created-0002', 'order.created', JSON_OBJECT('event_id','demo-order-created-0002','event_type','order.created','aggregate_type','order','aggregate_id','FM-DEMO-0002','payload', JSON_OBJECT('order_number','FM-DEMO-0002','user_id',@manager_id)), @now),
('demo-inventory-low-stock-0001', 'inventory.low_stock', JSON_OBJECT('event_id','demo-inventory-low-stock-0001','event_type','inventory.low_stock','aggregate_type','inventory_product','aggregate_id','2','payload', JSON_OBJECT('product_id', 2, 'product_name', 'Marketing Launch Pack', 'stock', 11)), @now)
ON DUPLICATE KEY UPDATE
  event_type = VALUES(event_type),
  payload_json = VALUES(payload_json),
  processed_at = VALUES(processed_at);

-- ============================================================================
-- 5) VERIFICATION QUERIES FOR MYSQL WORKBENCH
-- ============================================================================
SELECT 'AUTH USERS' AS section;
SELECT u.id, u.username, u.email, u.full_name, u.is_active, u.is_verified,
       GROUP_CONCAT(r.name ORDER BY r.name SEPARATOR ', ') AS roles
FROM finmark_auth_db.auth_users u
LEFT JOIN finmark_auth_db.auth_user_roles ur ON ur.user_id = u.id
LEFT JOIN finmark_auth_db.auth_roles r ON r.id = ur.role_id
GROUP BY u.id, u.username, u.email, u.full_name, u.is_active, u.is_verified
ORDER BY u.id;

SELECT 'AUTH ROLES AND PERMISSION COUNTS' AS section;
SELECT r.name AS role_name, COUNT(rp.permission_id) AS permission_count
FROM finmark_auth_db.auth_roles r
LEFT JOIN finmark_auth_db.auth_role_permissions rp ON rp.role_id = r.id
GROUP BY r.id, r.name
ORDER BY r.name;

SELECT 'ADMIN DASHBOARD ACCESS CHECK' AS section;
SELECT u.username, r.name AS role_name, p.code AS permission_code
FROM finmark_auth_db.auth_users u
JOIN finmark_auth_db.auth_user_roles ur ON ur.user_id = u.id
JOIN finmark_auth_db.auth_roles r ON r.id = ur.role_id
JOIN finmark_auth_db.auth_role_permissions rp ON rp.role_id = r.id
JOIN finmark_auth_db.auth_permissions p ON p.id = rp.permission_id
WHERE u.username = 'admin@example.com'
  AND p.code IN ('dashboard.admin', 'dashboard.products', 'product_dashboard.access', 'users.manage', 'products.manage')
ORDER BY r.name, p.code;

SELECT 'INVENTORY PRODUCTS' AS section;
SELECT id, sku, name, category, price, stock_quantity, badge, is_active
FROM finmark_inventory_db.inventory_products
ORDER BY id;

SELECT 'ORDERS' AS section;
SELECT o.id, o.order_number, o.user_id, o.customer_name, o.status, o.total, COUNT(i.id) AS item_count
FROM finmark_order_db.order_orders o
LEFT JOIN finmark_order_db.order_items i ON i.order_id = o.id
GROUP BY o.id, o.order_number, o.user_id, o.customer_name, o.status, o.total
ORDER BY o.id;

SELECT 'NOTIFICATIONS' AS section;
SELECT id, user_id, title, entity_type, entity_id, is_read, created_at
FROM finmark_notification_db.notification_messages
ORDER BY id;

SELECT 'SEED COMPLETE' AS result,
       'admin@example.com / Admin@12345' AS admin_login,
       'All other demo users / Demo@12345' AS demo_login;
