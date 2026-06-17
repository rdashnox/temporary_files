/*
  FinMark / PlatformTech MySQL Database Schema + Seed Data
  Target: MySQL Workbench localhost:3306

  Demo accounts seeded by this script:
    Admin   -> user@example.com     / Password123!
    Manager -> manager@example.com  / Manager123!
    Staff   -> staff@example.com    / Staff123!

  Passwords are bcrypt hashes compatible with the backend passlib bcrypt verifier.
*/

CREATE DATABASE IF NOT EXISTS finmark_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE finmark_db;

SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------
-- ACCESS CONTROL TABLES
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS roles (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(80) NOT NULL,
  description VARCHAR(255) NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_roles_name (name),
  KEY ix_roles_id (id),
  KEY ix_roles_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS permissions (
  id INT NOT NULL AUTO_INCREMENT,
  code VARCHAR(120) NOT NULL,
  name VARCHAR(120) NOT NULL,
  module VARCHAR(80) NOT NULL,
  description VARCHAR(255) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_permissions_code (code),
  KEY ix_permissions_id (id),
  KEY ix_permissions_code (code),
  KEY ix_permissions_module (module)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS role_permissions (
  role_id INT NOT NULL,
  permission_id INT NOT NULL,
  assigned_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (role_id, permission_id),
  CONSTRAINT fk_role_permissions_role_id
    FOREIGN KEY (role_id) REFERENCES roles(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_role_permissions_permission_id
    FOREIGN KEY (permission_id) REFERENCES permissions(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- USERS / AUTH TABLES
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
  id INT NOT NULL AUTO_INCREMENT,
  username VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  full_name VARCHAR(120) NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  is_verified BOOLEAN NOT NULL DEFAULT FALSE,
  verification_token VARCHAR(255) NULL,
  verification_token_expires_at DATETIME(6) NULL,
  password_reset_token VARCHAR(255) NULL,
  password_reset_token_expires_at DATETIME(6) NULL,
  last_login_at DATETIME(6) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_username (username),
  UNIQUE KEY uq_users_email (email),
  UNIQUE KEY uq_users_verification_token (verification_token),
  UNIQUE KEY uq_users_password_reset_token (password_reset_token),
  KEY ix_users_id (id),
  KEY ix_users_username (username),
  KEY ix_users_email (email),
  KEY ix_users_email_verified (email, is_verified)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_roles (
  user_id INT NOT NULL,
  role_id INT NOT NULL,
  assigned_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (user_id, role_id),
  CONSTRAINT fk_user_roles_user_id
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_user_roles_role_id
    FOREIGN KEY (role_id) REFERENCES roles(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- ORDERS TABLES
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS orders (
  id INT NOT NULL AUTO_INCREMENT,
  order_number VARCHAR(40) NOT NULL,
  user_id INT NULL,
  customer_name VARCHAR(120) NOT NULL,
  delivery_address VARCHAR(255) NOT NULL,
  payment_method VARCHAR(60) NOT NULL DEFAULT 'Cash on Delivery',
  status VARCHAR(20) NOT NULL DEFAULT 'new',
  subtotal DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
  discount DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
  shipping_fee DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
  tax DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
  total DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_orders_order_number (order_number),
  KEY ix_orders_id (id),
  KEY ix_orders_order_number (order_number),
  KEY ix_orders_status (status),
  KEY ix_orders_user_id (user_id),
  CONSTRAINT fk_orders_user_id
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS order_items (
  id INT NOT NULL AUTO_INCREMENT,
  order_id INT NOT NULL,
  product_id INT NOT NULL,
  product_name VARCHAR(120) NOT NULL,
  quantity INT NOT NULL,
  unit_price DECIMAL(12, 2) NOT NULL,
  line_total DECIMAL(12, 2) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_order_item_product (order_id, product_id),
  KEY ix_order_items_id (id),
  KEY ix_order_items_order_id (order_id),
  CONSTRAINT fk_order_items_order_id
    FOREIGN KEY (order_id) REFERENCES orders(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- REPORTS TABLES
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS reports (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(160) NOT NULL,
  report_type VARCHAR(80) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'queued',
  parameters_json TEXT NULL,
  file_path VARCHAR(255) NULL,
  created_by_user_id INT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  completed_at DATETIME(6) NULL,
  PRIMARY KEY (id),
  KEY ix_reports_id (id),
  KEY ix_reports_name (name),
  KEY ix_reports_report_type (report_type),
  KEY ix_reports_status (status),
  KEY ix_reports_created_by_user_id (created_by_user_id),
  CONSTRAINT fk_reports_created_by_user_id
    FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- PLANNING REQUEST TABLES
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS planning_requests (
  id INT NOT NULL AUTO_INCREMENT,
  request_number VARCHAR(40) NOT NULL,
  title VARCHAR(160) NOT NULL,
  description TEXT NULL,
  priority VARCHAR(30) NOT NULL DEFAULT 'normal',
  status VARCHAR(20) NOT NULL DEFAULT 'submitted',
  requested_by_user_id INT NULL,
  due_date DATETIME(6) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_planning_requests_request_number (request_number),
  KEY ix_planning_requests_id (id),
  KEY ix_planning_requests_request_number (request_number),
  KEY ix_planning_requests_priority (priority),
  KEY ix_planning_requests_status (status),
  KEY ix_planning_requests_requested_by_user_id (requested_by_user_id),
  CONSTRAINT fk_planning_requests_requested_by_user_id
    FOREIGN KEY (requested_by_user_id) REFERENCES users(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- AUDIT LOG TABLES
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS audit_logs (
  id INT NOT NULL AUTO_INCREMENT,
  actor_user_id INT NULL,
  action VARCHAR(30) NOT NULL,
  entity_type VARCHAR(80) NOT NULL,
  entity_id VARCHAR(80) NULL,
  detail TEXT NULL,
  ip_address VARCHAR(80) NULL,
  user_agent VARCHAR(255) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY ix_audit_logs_id (id),
  KEY ix_audit_logs_actor_user_id (actor_user_id),
  KEY ix_audit_logs_action (action),
  KEY ix_audit_logs_entity_type (entity_type),
  KEY ix_audit_logs_entity_id (entity_id),
  KEY ix_audit_logs_entity (entity_type, entity_id),
  CONSTRAINT fk_audit_logs_actor_user_id
    FOREIGN KEY (actor_user_id) REFERENCES users(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------
-- SEED: ROLES
-- ------------------------------------------------------------

INSERT INTO roles (id, name, description, is_active)
VALUES
  (1, 'Admin', 'Default Admin role', TRUE),
  (2, 'Manager', 'Default Manager role', TRUE),
  (3, 'Staff', 'Default Staff role', TRUE)
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  description = VALUES(description),
  is_active = VALUES(is_active),
  updated_at = CURRENT_TIMESTAMP(6);

-- ------------------------------------------------------------
-- SEED: PERMISSIONS
-- ------------------------------------------------------------

INSERT INTO permissions (id, code, name, module, description)
VALUES
  (1, 'users.read', 'View Users', 'users', 'Read user profiles and account status.'),
  (2, 'users.manage', 'Manage Users', 'users', 'Create, update, and deactivate users.'),
  (3, 'roles.manage', 'Manage Roles', 'access', 'Manage roles and permissions.'),
  (4, 'orders.read', 'View Orders', 'orders', 'View order lists and order details.'),
  (5, 'orders.manage', 'Manage Orders', 'orders', 'Create and update orders.'),
  (6, 'reports.read', 'View Reports', 'reports', 'View generated reports.'),
  (7, 'reports.manage', 'Manage Reports', 'reports', 'Create and update report jobs.'),
  (8, 'planning.read', 'View Planning Requests', 'planning', 'View planning requests.'),
  (9, 'planning.manage', 'Manage Planning Requests', 'planning', 'Create and approve planning requests.'),
  (10, 'audit.read', 'View Audit Logs', 'audit', 'Review audit activity.')
ON DUPLICATE KEY UPDATE
  code = VALUES(code),
  name = VALUES(name),
  module = VALUES(module),
  description = VALUES(description);

-- ------------------------------------------------------------
-- SEED: ROLE PERMISSIONS
-- Admin: all permissions
-- Manager: orders, reports, planning
-- Staff: read/basic operational permissions
-- ------------------------------------------------------------

INSERT IGNORE INTO role_permissions (role_id, permission_id)
VALUES
  (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
  (1, 6), (1, 7), (1, 8), (1, 9), (1, 10),
  (2, 4), (2, 5), (2, 6), (2, 7), (2, 8), (2, 9),
  (3, 4), (3, 5), (3, 6), (3, 8);

-- ------------------------------------------------------------
-- SEED: USERS
-- Passwords are bcrypt hashes. Do not store plain-text passwords.
-- ------------------------------------------------------------

INSERT INTO users (
  id,
  username,
  email,
  hashed_password,
  full_name,
  is_active,
  is_verified,
  verification_token,
  verification_token_expires_at,
  password_reset_token,
  password_reset_token_expires_at,
  last_login_at
)
VALUES
  (
    1,
    'user@example.com',
    'user@example.com',
    '$2b$12$9C16HaYLN8lE/x7/tkM4AOmaCXpUV8DljKgt2hw8KGl5dGXW9Ty0i',
    'Demo Admin User',
    TRUE,
    TRUE,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL
  ),
  (
    2,
    'manager@example.com',
    'manager@example.com',
    '$2b$12$XOnHheANgnfCBfNRjDBIS.iHrmAZlY7GeHbQtlf.wpfgrWzh4knwG',
    'Demo Manager User',
    TRUE,
    TRUE,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL
  ),
  (
    3,
    'staff@example.com',
    'staff@example.com',
    '$2b$12$f51Y/ppEgM8oGTVAQgx5qu2oxz.oxr08xK0/e.tHoLEMwkWd4csrq',
    'Demo Staff User',
    TRUE,
    TRUE,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL
  )
ON DUPLICATE KEY UPDATE
  username = VALUES(username),
  email = VALUES(email),
  hashed_password = VALUES(hashed_password),
  full_name = VALUES(full_name),
  is_active = VALUES(is_active),
  is_verified = VALUES(is_verified),
  updated_at = CURRENT_TIMESTAMP(6);

-- ------------------------------------------------------------
-- SEED: USER ROLES
-- ------------------------------------------------------------

INSERT IGNORE INTO user_roles (user_id, role_id)
VALUES
  (1, 1),
  (2, 2),
  (3, 3);

-- ------------------------------------------------------------
-- SEED: ORDERS
-- ------------------------------------------------------------

INSERT INTO orders (
  id,
  order_number,
  user_id,
  customer_name,
  delivery_address,
  payment_method,
  status,
  subtotal,
  discount,
  shipping_fee,
  tax,
  total
)
VALUES
  (1, 'ORD-2026-0001', 1, 'Demo Admin User', 'Quiapo, Manila, Philippines', 'Cash on Delivery', 'new', 2498.00, 100.00, 120.00, 0.00, 2518.00),
  (2, 'ORD-2026-0002', 2, 'Demo Manager User', 'Makati City, Philippines', 'GCash', 'paid', 1899.00, 0.00, 120.00, 0.00, 2019.00),
  (3, 'ORD-2026-0003', 3, 'Demo Staff User', 'Quezon City, Philippines', 'Cash on Delivery', 'completed', 3199.00, 200.00, 0.00, 0.00, 2999.00)
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
  updated_at = CURRENT_TIMESTAMP(6);

-- ------------------------------------------------------------
-- SEED: ORDER ITEMS
-- ------------------------------------------------------------

INSERT INTO order_items (
  id,
  order_id,
  product_id,
  product_name,
  quantity,
  unit_price,
  line_total
)
VALUES
  (1, 1, 101, 'Wireless Keyboard', 1, 1299.00, 1299.00),
  (2, 1, 102, 'Wireless Mouse', 1, 1199.00, 1199.00),
  (3, 2, 103, 'USB-C Hub', 1, 1899.00, 1899.00),
  (4, 3, 104, 'Laptop Stand', 1, 1499.00, 1499.00),
  (5, 3, 105, 'Desk Lamp', 1, 1700.00, 1700.00)
ON DUPLICATE KEY UPDATE
  order_id = VALUES(order_id),
  product_id = VALUES(product_id),
  product_name = VALUES(product_name),
  quantity = VALUES(quantity),
  unit_price = VALUES(unit_price),
  line_total = VALUES(line_total);

-- ------------------------------------------------------------
-- SEED: REPORTS
-- ------------------------------------------------------------

INSERT INTO reports (
  id,
  name,
  report_type,
  status,
  parameters_json,
  file_path,
  created_by_user_id,
  completed_at
)
VALUES
  (1, 'Daily Sales Summary', 'sales', 'ready', '{"date":"2026-06-16","scope":"daily"}', '/reports/daily-sales-summary.pdf', 1, CURRENT_TIMESTAMP(6)),
  (2, 'Inventory Movement Report', 'inventory', 'queued', '{"warehouse":"main","scope":"weekly"}', NULL, 2, NULL),
  (3, 'Planning Request Status Report', 'planning', 'ready', '{"status":"submitted"}', '/reports/planning-request-status.pdf', 2, CURRENT_TIMESTAMP(6))
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  report_type = VALUES(report_type),
  status = VALUES(status),
  parameters_json = VALUES(parameters_json),
  file_path = VALUES(file_path),
  created_by_user_id = VALUES(created_by_user_id),
  completed_at = VALUES(completed_at);

-- ------------------------------------------------------------
-- SEED: PLANNING REQUESTS
-- ------------------------------------------------------------

INSERT INTO planning_requests (
  id,
  request_number,
  title,
  description,
  priority,
  status,
  requested_by_user_id,
  due_date
)
VALUES
  (1, 'PR-2026-0001', 'Restock Fast-Moving Items', 'Request to restock top-selling accessories before the next campaign period.', 'high', 'submitted', 2, DATE_ADD(CURRENT_TIMESTAMP(6), INTERVAL 7 DAY)),
  (2, 'PR-2026-0002', 'Prepare July Sales Plan', 'Create sales plan and product bundle recommendations for July.', 'normal', 'approved', 1, DATE_ADD(CURRENT_TIMESTAMP(6), INTERVAL 14 DAY)),
  (3, 'PR-2026-0003', 'Audit Low Stock SKUs', 'Review SKUs with low stock and recommend reorder quantity.', 'normal', 'draft', 3, DATE_ADD(CURRENT_TIMESTAMP(6), INTERVAL 10 DAY))
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  description = VALUES(description),
  priority = VALUES(priority),
  status = VALUES(status),
  requested_by_user_id = VALUES(requested_by_user_id),
  due_date = VALUES(due_date),
  updated_at = CURRENT_TIMESTAMP(6);

-- ------------------------------------------------------------
-- SEED: AUDIT LOGS
-- ------------------------------------------------------------

INSERT INTO audit_logs (
  id,
  actor_user_id,
  action,
  entity_type,
  entity_id,
  detail,
  ip_address,
  user_agent
)
VALUES
  (1, 1, 'create', 'users', '1', 'Seeded demo admin user.', '127.0.0.1', 'MySQL Workbench Seed Script'),
  (2, 1, 'create', 'roles', '1', 'Seeded default roles and permissions.', '127.0.0.1', 'MySQL Workbench Seed Script'),
  (3, 2, 'create', 'orders', '2', 'Seeded demo paid order.', '127.0.0.1', 'MySQL Workbench Seed Script'),
  (4, 2, 'create', 'planning_requests', '1', 'Seeded planning request sample.', '127.0.0.1', 'MySQL Workbench Seed Script'),
  (5, 1, 'create', 'reports', '1', 'Seeded report sample.', '127.0.0.1', 'MySQL Workbench Seed Script')
ON DUPLICATE KEY UPDATE
  actor_user_id = VALUES(actor_user_id),
  action = VALUES(action),
  entity_type = VALUES(entity_type),
  entity_id = VALUES(entity_id),
  detail = VALUES(detail),
  ip_address = VALUES(ip_address),
  user_agent = VALUES(user_agent);

-- Keep AUTO_INCREMENT values ahead of seeded IDs.
ALTER TABLE roles AUTO_INCREMENT = 100;
ALTER TABLE permissions AUTO_INCREMENT = 100;
ALTER TABLE users AUTO_INCREMENT = 100;
ALTER TABLE orders AUTO_INCREMENT = 100;
ALTER TABLE order_items AUTO_INCREMENT = 100;
ALTER TABLE reports AUTO_INCREMENT = 100;
ALTER TABLE planning_requests AUTO_INCREMENT = 100;
ALTER TABLE audit_logs AUTO_INCREMENT = 100;

-- Quick verification queries.
SELECT 'roles' AS table_name, COUNT(*) AS total_rows FROM roles
UNION ALL SELECT 'permissions', COUNT(*) FROM permissions
UNION ALL SELECT 'role_permissions', COUNT(*) FROM role_permissions
UNION ALL SELECT 'users', COUNT(*) FROM users
UNION ALL SELECT 'user_roles', COUNT(*) FROM user_roles
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL SELECT 'reports', COUNT(*) FROM reports
UNION ALL SELECT 'planning_requests', COUNT(*) FROM planning_requests
UNION ALL SELECT 'audit_logs', COUNT(*) FROM audit_logs;
