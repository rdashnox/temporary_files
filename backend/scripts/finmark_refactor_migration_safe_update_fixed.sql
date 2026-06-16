-- ============================================================
-- FINMARK / PlatformTech SD1-MS2
-- MySQL Refactor + Migration + Seed Script
-- Target: MySQL Workbench localhost:3306
-- Database: finmark_db
--
-- Purpose:
-- 1. Create/refactor the required tables.
-- 2. Add missing columns safely.
-- 3. Normalize enum/status values to the format expected by SQLAlchemy.
-- 4. Fix MySQL Workbench Safe Update Mode error 1175.
-- 5. Seed users, roles, permissions, user_roles, role_permissions,
--    orders, order_items, reports, planning_requests, and audit_logs.
--
-- Safe to rerun: YES. It uses CREATE IF NOT EXISTS, ADD COLUMN IF MISSING,
-- INSERT ... ON DUPLICATE KEY UPDATE, and INSERT IGNORE.
-- ============================================================

CREATE DATABASE IF NOT EXISTS finmark_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE finmark_db;

-- Workbench Safe Update Mode fix.
-- This allows migration UPDATE statements to run even when SQL_SAFE_UPDATES is enabled.
SET @OLD_SQL_SAFE_UPDATES = @@SQL_SAFE_UPDATES;
SET SQL_SAFE_UPDATES = 0;

SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- HELPER PROCEDURES
-- ============================================================

DELIMITER $$

DROP PROCEDURE IF EXISTS add_column_if_missing $$
CREATE PROCEDURE add_column_if_missing(
  IN p_table_name VARCHAR(64),
  IN p_column_name VARCHAR(64),
  IN p_column_definition TEXT
)
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = p_table_name
      AND COLUMN_NAME = p_column_name
  ) THEN
    SET @sql = CONCAT(
      'ALTER TABLE `', p_table_name, '` ADD COLUMN `', p_column_name, '` ', p_column_definition
    );
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END $$

DROP PROCEDURE IF EXISTS add_index_if_missing $$
CREATE PROCEDURE add_index_if_missing(
  IN p_table_name VARCHAR(64),
  IN p_index_name VARCHAR(64),
  IN p_index_definition TEXT
)
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = p_table_name
      AND INDEX_NAME = p_index_name
  ) THEN
    SET @sql = CONCAT('ALTER TABLE `', p_table_name, '` ADD ', p_index_definition);
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END $$

DROP PROCEDURE IF EXISTS copy_column_if_exists $$
CREATE PROCEDURE copy_column_if_exists(
  IN p_table_name VARCHAR(64),
  IN p_source_column VARCHAR(64),
  IN p_target_column VARCHAR(64)
)
BEGIN
  IF EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = p_table_name
      AND COLUMN_NAME = p_source_column
  ) AND EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = p_table_name
      AND COLUMN_NAME = p_target_column
  ) THEN
    SET @sql = CONCAT(
      'UPDATE `', p_table_name, '` SET `', p_target_column, '` = `', p_source_column, '` ',
      'WHERE (`', p_target_column, '` IS NULL OR `', p_target_column, '` = '''')'
    );
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END $$

DELIMITER ;

-- ============================================================
-- TABLES
-- ============================================================

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
  KEY ix_user_roles_user_id (user_id),
  KEY ix_user_roles_role_id (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS role_permissions (
  role_id INT NOT NULL,
  permission_id INT NOT NULL,
  assigned_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (role_id, permission_id),
  KEY ix_role_permissions_role_id (role_id),
  KEY ix_role_permissions_permission_id (permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS orders (
  id INT NOT NULL AUTO_INCREMENT,
  order_number VARCHAR(40) NOT NULL,
  user_id INT NULL,
  customer_name VARCHAR(120) NOT NULL,
  delivery_address VARCHAR(255) NOT NULL,
  payment_method VARCHAR(60) NOT NULL DEFAULT 'Cash on Delivery',
  status VARCHAR(20) NOT NULL DEFAULT 'NEW',
  subtotal DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  discount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  shipping_fee DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  tax DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  total DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_orders_order_number (order_number),
  KEY ix_orders_id (id),
  KEY ix_orders_order_number (order_number),
  KEY ix_orders_status (status),
  KEY ix_orders_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS order_items (
  id INT NOT NULL AUTO_INCREMENT,
  order_id INT NOT NULL,
  product_id INT NOT NULL,
  product_name VARCHAR(120) NOT NULL,
  quantity INT NOT NULL,
  unit_price DECIMAL(12,2) NOT NULL,
  line_total DECIMAL(12,2) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_order_item_product (order_id, product_id),
  KEY ix_order_items_id (id),
  KEY ix_order_items_order_id (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS reports (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(160) NOT NULL,
  report_type VARCHAR(80) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'QUEUED',
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
  KEY ix_reports_created_by_user_id (created_by_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS planning_requests (
  id INT NOT NULL AUTO_INCREMENT,
  request_number VARCHAR(40) NOT NULL,
  title VARCHAR(160) NOT NULL,
  description TEXT NULL,
  priority VARCHAR(30) NOT NULL DEFAULT 'normal',
  status VARCHAR(20) NOT NULL DEFAULT 'SUBMITTED',
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
  KEY ix_planning_requests_requested_by_user_id (requested_by_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
  KEY ix_audit_logs_entity (entity_type, entity_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- ADD MISSING COLUMNS FOR OLD/PARTIAL TABLES
-- ============================================================

CALL add_column_if_missing('roles', 'description', 'VARCHAR(255) NULL');
CALL add_column_if_missing('roles', 'is_active', 'BOOLEAN NOT NULL DEFAULT TRUE');
CALL add_column_if_missing('roles', 'created_at', 'DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)');
CALL add_column_if_missing('roles', 'updated_at', 'DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)');

CALL add_column_if_missing('permissions', 'name', 'VARCHAR(120) NOT NULL DEFAULT ''''');
CALL add_column_if_missing('permissions', 'module', 'VARCHAR(80) NOT NULL DEFAULT ''general''');
CALL add_column_if_missing('permissions', 'description', 'VARCHAR(255) NULL');
CALL add_column_if_missing('permissions', 'created_at', 'DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)');

CALL add_column_if_missing('users', 'username', 'VARCHAR(255) NULL');
CALL add_column_if_missing('users', 'email', 'VARCHAR(255) NULL');
CALL add_column_if_missing('users', 'hashed_password', 'VARCHAR(255) NULL');
CALL add_column_if_missing('users', 'full_name', 'VARCHAR(120) NULL');
CALL add_column_if_missing('users', 'is_active', 'BOOLEAN NOT NULL DEFAULT TRUE');
CALL add_column_if_missing('users', 'is_verified', 'BOOLEAN NOT NULL DEFAULT FALSE');
CALL add_column_if_missing('users', 'verification_token', 'VARCHAR(255) NULL');
CALL add_column_if_missing('users', 'verification_token_expires_at', 'DATETIME(6) NULL');
CALL add_column_if_missing('users', 'password_reset_token', 'VARCHAR(255) NULL');
CALL add_column_if_missing('users', 'password_reset_token_expires_at', 'DATETIME(6) NULL');
CALL add_column_if_missing('users', 'last_login_at', 'DATETIME(6) NULL');
CALL add_column_if_missing('users', 'created_at', 'DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)');
CALL add_column_if_missing('users', 'updated_at', 'DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)');

CALL add_column_if_missing('orders', 'order_number', 'VARCHAR(40) NULL');
CALL add_column_if_missing('orders', 'user_id', 'INT NULL');
CALL add_column_if_missing('orders', 'customer_name', 'VARCHAR(120) NOT NULL DEFAULT ''Customer''');
CALL add_column_if_missing('orders', 'delivery_address', 'VARCHAR(255) NOT NULL DEFAULT ''N/A''');
CALL add_column_if_missing('orders', 'payment_method', 'VARCHAR(60) NOT NULL DEFAULT ''Cash on Delivery''');
CALL add_column_if_missing('orders', 'status', 'VARCHAR(20) NOT NULL DEFAULT ''NEW''');
CALL add_column_if_missing('orders', 'subtotal', 'DECIMAL(12,2) NOT NULL DEFAULT 0.00');
CALL add_column_if_missing('orders', 'discount', 'DECIMAL(12,2) NOT NULL DEFAULT 0.00');
CALL add_column_if_missing('orders', 'shipping_fee', 'DECIMAL(12,2) NOT NULL DEFAULT 0.00');
CALL add_column_if_missing('orders', 'tax', 'DECIMAL(12,2) NOT NULL DEFAULT 0.00');
CALL add_column_if_missing('orders', 'total', 'DECIMAL(12,2) NOT NULL DEFAULT 0.00');
CALL add_column_if_missing('orders', 'created_at', 'DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)');
CALL add_column_if_missing('orders', 'updated_at', 'DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)');

CALL add_column_if_missing('order_items', 'order_id', 'INT NULL');
CALL add_column_if_missing('order_items', 'product_id', 'INT NOT NULL DEFAULT 0');
CALL add_column_if_missing('order_items', 'product_name', 'VARCHAR(120) NOT NULL DEFAULT ''Product''');
CALL add_column_if_missing('order_items', 'quantity', 'INT NOT NULL DEFAULT 1');
CALL add_column_if_missing('order_items', 'unit_price', 'DECIMAL(12,2) NOT NULL DEFAULT 0.00');
CALL add_column_if_missing('order_items', 'line_total', 'DECIMAL(12,2) NOT NULL DEFAULT 0.00');

CALL add_column_if_missing('reports', 'name', 'VARCHAR(160) NULL');
CALL add_column_if_missing('reports', 'report_type', 'VARCHAR(80) NOT NULL DEFAULT ''general''');
CALL add_column_if_missing('reports', 'status', 'VARCHAR(20) NOT NULL DEFAULT ''QUEUED''');
CALL add_column_if_missing('reports', 'parameters_json', 'TEXT NULL');
CALL add_column_if_missing('reports', 'file_path', 'VARCHAR(255) NULL');
CALL add_column_if_missing('reports', 'created_by_user_id', 'INT NULL');
CALL add_column_if_missing('reports', 'created_at', 'DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)');
CALL add_column_if_missing('reports', 'completed_at', 'DATETIME(6) NULL');
CALL copy_column_if_exists('reports', 'title', 'name');
CALL copy_column_if_exists('reports', 'generated_by_id', 'created_by_user_id');

CALL add_column_if_missing('planning_requests', 'request_number', 'VARCHAR(40) NULL');
CALL add_column_if_missing('planning_requests', 'title', 'VARCHAR(160) NOT NULL DEFAULT ''Planning Request''');
CALL add_column_if_missing('planning_requests', 'description', 'TEXT NULL');
CALL add_column_if_missing('planning_requests', 'priority', 'VARCHAR(30) NOT NULL DEFAULT ''normal''');
CALL add_column_if_missing('planning_requests', 'status', 'VARCHAR(20) NOT NULL DEFAULT ''SUBMITTED''');
CALL add_column_if_missing('planning_requests', 'requested_by_user_id', 'INT NULL');
CALL add_column_if_missing('planning_requests', 'due_date', 'DATETIME(6) NULL');
CALL add_column_if_missing('planning_requests', 'created_at', 'DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)');
CALL add_column_if_missing('planning_requests', 'updated_at', 'DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)');

CALL add_column_if_missing('audit_logs', 'actor_user_id', 'INT NULL');
CALL add_column_if_missing('audit_logs', 'action', 'VARCHAR(30) NOT NULL DEFAULT ''CREATE''');
CALL add_column_if_missing('audit_logs', 'entity_type', 'VARCHAR(80) NOT NULL DEFAULT ''system''');
CALL add_column_if_missing('audit_logs', 'entity_id', 'VARCHAR(80) NULL');
CALL add_column_if_missing('audit_logs', 'detail', 'TEXT NULL');
CALL add_column_if_missing('audit_logs', 'ip_address', 'VARCHAR(80) NULL');
CALL add_column_if_missing('audit_logs', 'user_agent', 'VARCHAR(255) NULL');
CALL add_column_if_missing('audit_logs', 'created_at', 'DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)');

-- ============================================================
-- NORMALIZE COLUMN TYPES AND DEFAULTS
-- SQLAlchemy Enum currently expects UPPERCASE enum names.
-- This is the fix for: 'ready' is not among defined enum values.
-- ============================================================

ALTER TABLE orders MODIFY status VARCHAR(20) NOT NULL DEFAULT 'NEW';
ALTER TABLE reports MODIFY status VARCHAR(20) NOT NULL DEFAULT 'QUEUED';
ALTER TABLE planning_requests MODIFY status VARCHAR(20) NOT NULL DEFAULT 'SUBMITTED';
ALTER TABLE audit_logs MODIFY action VARCHAR(30) NOT NULL DEFAULT 'CREATE';

UPDATE orders
SET status = CASE LOWER(status)
  WHEN 'new' THEN 'NEW'
  WHEN 'paid' THEN 'PAID'
  WHEN 'packed' THEN 'PACKED'
  WHEN 'shipped' THEN 'SHIPPED'
  WHEN 'completed' THEN 'COMPLETED'
  WHEN 'cancelled' THEN 'CANCELLED'
  WHEN 'canceled' THEN 'CANCELLED'
  WHEN 'exception' THEN 'EXCEPTION'
  ELSE UPPER(status)
END
WHERE id > 0;

UPDATE reports
SET status = CASE LOWER(status)
  WHEN 'queued' THEN 'QUEUED'
  WHEN 'running' THEN 'RUNNING'
  WHEN 'ready' THEN 'READY'
  WHEN 'failed' THEN 'FAILED'
  ELSE UPPER(status)
END
WHERE id > 0;

UPDATE planning_requests
SET status = CASE LOWER(status)
  WHEN 'draft' THEN 'DRAFT'
  WHEN 'submitted' THEN 'SUBMITTED'
  WHEN 'approved' THEN 'APPROVED'
  WHEN 'rejected' THEN 'REJECTED'
  WHEN 'cancelled' THEN 'CANCELLED'
  WHEN 'canceled' THEN 'CANCELLED'
  ELSE UPPER(status)
END
WHERE id > 0;

UPDATE audit_logs
SET action = CASE LOWER(action)
  WHEN 'create' THEN 'CREATE'
  WHEN 'update' THEN 'UPDATE'
  WHEN 'delete' THEN 'DELETE'
  WHEN 'login' THEN 'LOGIN'
  WHEN 'password_reset' THEN 'PASSWORD_RESET'
  WHEN 'verify_email' THEN 'VERIFY_EMAIL'
  WHEN 'checkout' THEN 'CHECKOUT'
  ELSE UPPER(action)
END
WHERE id > 0;

-- Fill nullable refactor columns after adding them.
UPDATE users SET username = email WHERE id > 0 AND (username IS NULL OR username = '') AND email IS NOT NULL;
UPDATE users SET email = username WHERE id > 0 AND (email IS NULL OR email = '') AND username IS NOT NULL;
UPDATE orders SET order_number = CONCAT('ORD-MIG-', LPAD(id, 6, '0')) WHERE id > 0 AND (order_number IS NULL OR order_number = '');
UPDATE reports SET name = CONCAT('Report #', id) WHERE id > 0 AND (name IS NULL OR name = '');
UPDATE planning_requests SET request_number = CONCAT('PR-MIG-', LPAD(id, 6, '0')) WHERE id > 0 AND (request_number IS NULL OR request_number = '');

-- ============================================================
-- INDEXES
-- ============================================================

CALL add_index_if_missing('roles', 'uq_roles_name', 'UNIQUE INDEX uq_roles_name (name)');
CALL add_index_if_missing('permissions', 'uq_permissions_code', 'UNIQUE INDEX uq_permissions_code (code)');
CALL add_index_if_missing('users', 'uq_users_username', 'UNIQUE INDEX uq_users_username (username)');
CALL add_index_if_missing('users', 'uq_users_email', 'UNIQUE INDEX uq_users_email (email)');
CALL add_index_if_missing('orders', 'uq_orders_order_number', 'UNIQUE INDEX uq_orders_order_number (order_number)');
CALL add_index_if_missing('orders', 'ix_orders_status', 'INDEX ix_orders_status (status)');
CALL add_index_if_missing('reports', 'ix_reports_name', 'INDEX ix_reports_name (name)');
CALL add_index_if_missing('reports', 'ix_reports_status', 'INDEX ix_reports_status (status)');
CALL add_index_if_missing('planning_requests', 'uq_planning_requests_request_number', 'UNIQUE INDEX uq_planning_requests_request_number (request_number)');
CALL add_index_if_missing('planning_requests', 'ix_planning_requests_status', 'INDEX ix_planning_requests_status (status)');
CALL add_index_if_missing('audit_logs', 'ix_audit_logs_action', 'INDEX ix_audit_logs_action (action)');
CALL add_index_if_missing('audit_logs', 'ix_audit_logs_entity', 'INDEX ix_audit_logs_entity (entity_type, entity_id)');

-- ============================================================
-- SEED ROLES
-- ============================================================

INSERT INTO roles (id, name, description, is_active)
VALUES
  (1, 'Admin', 'Default Admin role with full system access.', TRUE),
  (2, 'Manager', 'Default Manager role for operations, reports, and planning.', TRUE),
  (3, 'Staff', 'Default Staff role for day-to-day operational access.', TRUE)
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  description = VALUES(description),
  is_active = VALUES(is_active),
  updated_at = CURRENT_TIMESTAMP(6);

-- ============================================================
-- SEED PERMISSIONS
-- ============================================================

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

-- ============================================================
-- SEED ROLE PERMISSIONS
-- ============================================================

-- Admin: all permissions.
INSERT IGNORE INTO role_permissions (role_id, permission_id)
SELECT 1, id FROM permissions;

-- Manager: orders, reports, planning.
INSERT IGNORE INTO role_permissions (role_id, permission_id)
SELECT 2, id FROM permissions
WHERE code IN (
  'orders.read',
  'orders.manage',
  'reports.read',
  'reports.manage',
  'planning.read',
  'planning.manage'
);

-- Staff: basic operational permissions.
INSERT IGNORE INTO role_permissions (role_id, permission_id)
SELECT 3, id FROM permissions
WHERE code IN (
  'orders.read',
  'orders.manage',
  'reports.read',
  'planning.read'
);

-- ============================================================
-- SEED USERS
-- Demo passwords:
-- user@example.com    / Password123!
-- manager@example.com / Manager123!
-- staff@example.com   / Staff123!
-- ============================================================

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

INSERT IGNORE INTO user_roles (user_id, role_id)
VALUES
  (1, 1),
  (2, 2),
  (3, 3);

-- ============================================================
-- SEED ORDERS + ORDER ITEMS
-- ============================================================

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
  (1, 'ORD-2026-0001', 1, 'Demo Admin User', 'Quiapo, Manila, Philippines', 'Cash on Delivery', 'NEW', 2498.00, 100.00, 120.00, 0.00, 2518.00),
  (2, 'ORD-2026-0002', 2, 'Demo Manager User', 'Makati City, Philippines', 'GCash', 'PAID', 1899.00, 0.00, 120.00, 0.00, 2019.00),
  (3, 'ORD-2026-0003', 3, 'Demo Staff User', 'Quezon City, Philippines', 'Cash on Delivery', 'COMPLETED', 3199.00, 200.00, 0.00, 0.00, 2999.00)
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
  (1, 1, 101, 'Wireless Mouse', 2, 699.00, 1398.00),
  (2, 1, 102, 'Keyboard', 1, 1100.00, 1100.00),
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

-- ============================================================
-- SEED REPORTS
-- IMPORTANT: column is name, not title.
-- IMPORTANT: status values are UPPERCASE for SQLAlchemy enum compatibility.
-- ============================================================

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
  (1, 'Daily Sales Summary', 'sales', 'READY', '{"date":"2026-06-16","scope":"daily"}', '/reports/daily-sales-summary.pdf', 1, CURRENT_TIMESTAMP(6)),
  (2, 'Inventory Movement Report', 'inventory', 'QUEUED', '{"warehouse":"main","scope":"weekly"}', NULL, 2, NULL),
  (3, 'Planning Request Status Report', 'planning', 'READY', '{"status":"SUBMITTED"}', '/reports/planning-request-status.pdf', 2, CURRENT_TIMESTAMP(6))
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  report_type = VALUES(report_type),
  status = VALUES(status),
  parameters_json = VALUES(parameters_json),
  file_path = VALUES(file_path),
  created_by_user_id = VALUES(created_by_user_id),
  completed_at = VALUES(completed_at);

-- ============================================================
-- SEED PLANNING REQUESTS
-- ============================================================

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
  (1, 'PR-2026-0001', 'Restock Fast-Moving Items', 'Request to restock top-selling accessories before the next campaign period.', 'high', 'SUBMITTED', 2, DATE_ADD(CURRENT_TIMESTAMP(6), INTERVAL 7 DAY)),
  (2, 'PR-2026-0002', 'Prepare July Sales Plan', 'Create sales plan and product bundle recommendations for July.', 'normal', 'APPROVED', 1, DATE_ADD(CURRENT_TIMESTAMP(6), INTERVAL 14 DAY)),
  (3, 'PR-2026-0003', 'Audit Low Stock SKUs', 'Review SKUs with low stock and recommend reorder quantity.', 'normal', 'DRAFT', 3, DATE_ADD(CURRENT_TIMESTAMP(6), INTERVAL 10 DAY))
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  description = VALUES(description),
  priority = VALUES(priority),
  status = VALUES(status),
  requested_by_user_id = VALUES(requested_by_user_id),
  due_date = VALUES(due_date),
  updated_at = CURRENT_TIMESTAMP(6);

-- ============================================================
-- SEED AUDIT LOGS
-- ============================================================

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
  (1, 1, 'CREATE', 'users', '1', 'Seeded demo admin user.', '127.0.0.1', 'MySQL Workbench Refactor Script'),
  (2, 1, 'CREATE', 'roles', '1', 'Seeded default roles and permissions.', '127.0.0.1', 'MySQL Workbench Refactor Script'),
  (3, 2, 'CREATE', 'orders', '2', 'Seeded demo paid order.', '127.0.0.1', 'MySQL Workbench Refactor Script'),
  (4, 2, 'CREATE', 'planning_requests', '1', 'Seeded planning request sample.', '127.0.0.1', 'MySQL Workbench Refactor Script'),
  (5, 1, 'CREATE', 'reports', '1', 'Seeded report sample.', '127.0.0.1', 'MySQL Workbench Refactor Script')
ON DUPLICATE KEY UPDATE
  actor_user_id = VALUES(actor_user_id),
  action = VALUES(action),
  entity_type = VALUES(entity_type),
  entity_id = VALUES(entity_id),
  detail = VALUES(detail),
  ip_address = VALUES(ip_address),
  user_agent = VALUES(user_agent);

-- ============================================================
-- FOREIGN KEYS
-- Add manually only if your database is clean. This script keeps FK creation
-- disabled during migration to prevent failure caused by old partial data.
-- Your SQLAlchemy app can still use relationships by IDs.
-- ============================================================

SET FOREIGN_KEY_CHECKS = 1;

-- Keep AUTO_INCREMENT values ahead of seeded IDs.
ALTER TABLE roles AUTO_INCREMENT = 100;
ALTER TABLE permissions AUTO_INCREMENT = 100;
ALTER TABLE users AUTO_INCREMENT = 100;
ALTER TABLE orders AUTO_INCREMENT = 100;
ALTER TABLE order_items AUTO_INCREMENT = 100;
ALTER TABLE reports AUTO_INCREMENT = 100;
ALTER TABLE planning_requests AUTO_INCREMENT = 100;
ALTER TABLE audit_logs AUTO_INCREMENT = 100;

-- Clean helper procedures.
DROP PROCEDURE IF EXISTS add_column_if_missing;
DROP PROCEDURE IF EXISTS add_index_if_missing;
DROP PROCEDURE IF EXISTS copy_column_if_exists;

-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================

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

SELECT id, name, status FROM reports LIMIT 1000;
SELECT id, order_number, status FROM orders LIMIT 1000;
SELECT id, request_number, title, status FROM planning_requests LIMIT 1000;
SELECT id, action, entity_type, entity_id FROM audit_logs LIMIT 1000;

-- Restore previous Workbench Safe Update setting.
SET SQL_SAFE_UPDATES = @OLD_SQL_SAFE_UPDATES;

-- ============================================================
-- AFTER RUNNING THIS SCRIPT
-- Restart backend:
-- python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
-- ============================================================
