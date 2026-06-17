/*
  FinMark Refactor + Seed Script
  Purpose:
  1. Fix MySQL Workbench Safe Update Mode errors.
  2. Remove deprecated ON DUPLICATE KEY UPDATE VALUES(column) usage.
  3. Seed roles, permissions, dummy users, user_roles, and role_permissions.
  4. Add Customer role for Product Dashboard-only access.
  5. Normalize enum/status values used by the FastAPI + SQLAlchemy backend.

  Run in MySQL Workbench connected to localhost:3306.
*/

CREATE DATABASE IF NOT EXISTS finmark_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE finmark_db;

-- Preserve the current Workbench setting, then disable Safe Update Mode for migration updates.
SET @OLD_SQL_SAFE_UPDATES = @@SQL_SAFE_UPDATES;
SET SQL_SAFE_UPDATES = 0;

START TRANSACTION;

/* =========================================================
   1. ROLES
   ========================================================= */
DROP TEMPORARY TABLE IF EXISTS tmp_seed_roles;
CREATE TEMPORARY TABLE tmp_seed_roles (
  name VARCHAR(80) NOT NULL PRIMARY KEY,
  description VARCHAR(255) NULL
);

INSERT INTO tmp_seed_roles (name, description) VALUES
  ('Admin', 'Full system administrator with access to all modules.'),
  ('Manager', 'Can manage orders, reports, and planning requests.'),
  ('Staff', 'Can use the product dashboard and manage assigned operational records.'),
  ('Viewer', 'Read-only user with product dashboard access.'),
  ('Customer', 'Customer account. Product dashboard only. No admin CRUD access.'),
  ('User', 'Standard application user with product dashboard access.'),
  ('Planner', 'Can manage planning requests and planning-related reports.'),
  ('Analyst', 'Can view and generate reports.'),
  ('Auditor', 'Can view audit logs and compliance records.');

-- Insert missing roles.
INSERT IGNORE INTO roles (name, description, created_at)
SELECT name, description, NOW()
FROM tmp_seed_roles;

-- Update existing role descriptions without using deprecated VALUES().
UPDATE roles r
JOIN tmp_seed_roles s ON s.name = r.name
SET r.description = s.description
WHERE r.id > 0;

/* =========================================================
   2. PERMISSIONS
   ========================================================= */
DROP TEMPORARY TABLE IF EXISTS tmp_seed_permissions;
CREATE TEMPORARY TABLE tmp_seed_permissions (
  code VARCHAR(120) NOT NULL PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  module VARCHAR(80) NOT NULL,
  description VARCHAR(255) NULL
);

INSERT INTO tmp_seed_permissions (code, name, module, description) VALUES
  ('dashboard.read', 'View Dashboard', 'dashboard', 'Can view the main dashboard.'),

  ('products.read', 'View Products', 'products', 'Can view the product dashboard and product catalog.'),
  ('products.checkout', 'Checkout Products', 'products', 'Can add products to cart and checkout.'),

  ('users.read', 'View Users', 'users', 'Can view users in the admin dashboard.'),
  ('users.create', 'Create Users', 'users', 'Can create users.'),
  ('users.update', 'Update Users', 'users', 'Can update users.'),
  ('users.delete', 'Delete Users', 'users', 'Can deactivate users.'),

  ('roles.read', 'View Roles', 'roles', 'Can view roles in the admin dashboard.'),
  ('roles.create', 'Create Roles', 'roles', 'Can create roles.'),
  ('roles.update', 'Update Roles', 'roles', 'Can update roles.'),
  ('roles.delete', 'Delete Roles', 'roles', 'Can delete or deactivate roles.'),

  ('permissions.read', 'View Permissions', 'permissions', 'Can view permission codes in the admin dashboard.'),
  ('permissions.create', 'Create Permissions', 'permissions', 'Can create permission codes.'),
  ('permissions.update', 'Update Permissions', 'permissions', 'Can update permission codes.'),
  ('permissions.delete', 'Delete Permissions', 'permissions', 'Can delete permission codes.'),

  ('orders.read', 'View Orders', 'orders', 'Can view orders.'),
  ('orders.create', 'Create Orders', 'orders', 'Can create orders.'),
  ('orders.update', 'Update Orders', 'orders', 'Can update orders.'),
  ('orders.delete', 'Delete Orders', 'orders', 'Can delete orders.'),

  ('reports.read', 'View Reports', 'reports', 'Can view reports.'),
  ('reports.create', 'Create Reports', 'reports', 'Can create reports.'),
  ('reports.update', 'Update Reports', 'reports', 'Can update reports.'),
  ('reports.delete', 'Delete Reports', 'reports', 'Can delete reports.'),
  ('reports.generate', 'Generate Reports', 'reports', 'Can generate reports.'),
  ('reports.download', 'Download Reports', 'reports', 'Can download reports.'),

  ('planning_requests.read', 'View Planning Requests', 'planning_requests', 'Can view planning requests.'),
  ('planning_requests.create', 'Create Planning Requests', 'planning_requests', 'Can create planning requests.'),
  ('planning_requests.update', 'Update Planning Requests', 'planning_requests', 'Can update planning requests.'),
  ('planning_requests.delete', 'Delete Planning Requests', 'planning_requests', 'Can delete planning requests.'),
  ('planning_requests.approve', 'Approve Planning Requests', 'planning_requests', 'Can approve planning requests.'),
  ('planning_requests.reject', 'Reject Planning Requests', 'planning_requests', 'Can reject planning requests.'),

  ('audit_logs.read', 'View Audit Logs', 'audit_logs', 'Can view audit logs.'),
  ('audit_logs.create', 'Create Audit Logs', 'audit_logs', 'Can manually create audit log records.'),
  ('audit_logs.update', 'Update Audit Logs', 'audit_logs', 'Can update audit log records.'),
  ('audit_logs.delete', 'Delete Audit Logs', 'audit_logs', 'Can delete audit log records.');

-- Insert missing permissions.
INSERT IGNORE INTO permissions (code, name, module, description, created_at)
SELECT code, name, module, description, NOW()
FROM tmp_seed_permissions;

-- Update existing permissions without deprecated VALUES().
UPDATE permissions p
JOIN tmp_seed_permissions s ON s.code = p.code
SET
  p.name = s.name,
  p.module = s.module,
  p.description = s.description
WHERE p.id > 0;

/* =========================================================
   3. USERS WITH BCRYPT-HASHED DUMMY PASSWORDS
   Plaintext passwords are listed in comments for testing only.
   ========================================================= */
DROP TEMPORARY TABLE IF EXISTS tmp_seed_users;
CREATE TEMPORARY TABLE tmp_seed_users (
  email VARCHAR(255) NOT NULL PRIMARY KEY,
  full_name VARCHAR(120) NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  is_active TINYINT(1) NOT NULL,
  is_verified TINYINT(1) NOT NULL
);

INSERT INTO tmp_seed_users (email, full_name, hashed_password, is_active, is_verified) VALUES
  -- admin@example.com / Admin123!
  ('admin@example.com', 'Admin User', '$2b$12$R.bkgyDvOlhuptVHQH7AKeeXWFWc3//tBdLri5bH7o5JdxNKp.j1K', 1, 1),

  -- manager@example.com / Manager123!
  ('manager@example.com', 'Manager User', '$2b$12$SK/LhRLpMW7xy0xzXHbNZuF9PK/8MJWjn8e7u6OoYfMOV4qIpDujG', 1, 1),

  -- staff@example.com / Staff123!
  ('staff@example.com', 'Staff User', '$2b$12$3HFQCWQTuyHFXSjiAbUKeOnP0wqu1C7SewwMg7K4r78QKVg0L5hs.', 1, 1),

  -- viewer@example.com / Viewer123!
  ('viewer@example.com', 'Viewer User', '$2b$12$4.KSqJa/Vl5kFymqbirz8eZNEDeueZNMWtafcYtOVNnA6TQU9NA0u', 1, 1),

  -- customer@example.com / Customer123!
  ('customer@example.com', 'Customer User', '$2b$12$vF0pAaGoIodf8KJh7vdZkuLAFV5ZqhIwWEkbGu3WpGmI3Cjeu6i7u', 1, 1),

  -- user@example.com / Password123!
  ('user@example.com', 'Demo User', '$2b$12$MC6B8Fu82WGvB67rMuUKSOfK.iC6zTajOA.o2mXb90V5dsLyeKupq', 1, 1);

-- Insert missing users.
INSERT IGNORE INTO users (email, full_name, hashed_password, is_active, is_verified, created_at)
SELECT email, full_name, hashed_password, is_active, is_verified, NOW()
FROM tmp_seed_users;

-- Update dummy users safely without deprecated VALUES().
UPDATE users u
JOIN tmp_seed_users s ON s.email = u.email
SET
  u.full_name = s.full_name,
  u.hashed_password = s.hashed_password,
  u.is_active = s.is_active,
  u.is_verified = s.is_verified
WHERE u.id > 0;

/* =========================================================
   4. USER -> ROLE ASSIGNMENTS
   ========================================================= */
DROP TEMPORARY TABLE IF EXISTS tmp_seed_user_roles;
CREATE TEMPORARY TABLE tmp_seed_user_roles (
  email VARCHAR(255) NOT NULL,
  role_name VARCHAR(80) NOT NULL,
  PRIMARY KEY (email, role_name)
);

INSERT INTO tmp_seed_user_roles (email, role_name) VALUES
  ('admin@example.com', 'Admin'),
  ('manager@example.com', 'Manager'),
  ('staff@example.com', 'Staff'),
  ('viewer@example.com', 'Viewer'),
  ('customer@example.com', 'Customer'),
  ('user@example.com', 'User');

INSERT IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM tmp_seed_user_roles s
JOIN users u ON u.email = s.email
JOIN roles r ON r.name = s.role_name;

/* =========================================================
   5. ROLE -> PERMISSION ASSIGNMENTS
   ========================================================= */
DROP TEMPORARY TABLE IF EXISTS tmp_seed_role_permissions;
CREATE TEMPORARY TABLE tmp_seed_role_permissions (
  role_name VARCHAR(80) NOT NULL,
  permission_code VARCHAR(120) NOT NULL,
  PRIMARY KEY (role_name, permission_code)
);

-- Admin gets all permissions.
INSERT INTO tmp_seed_role_permissions (role_name, permission_code)
SELECT 'Admin', code FROM tmp_seed_permissions;

-- Manager gets operational/admin read + update permissions, but not full user deletion or permission deletion.
INSERT IGNORE INTO tmp_seed_role_permissions (role_name, permission_code) VALUES
  ('Manager', 'dashboard.read'),
  ('Manager', 'products.read'),
  ('Manager', 'products.checkout'),
  ('Manager', 'users.read'),
  ('Manager', 'roles.read'),
  ('Manager', 'permissions.read'),
  ('Manager', 'orders.read'),
  ('Manager', 'orders.create'),
  ('Manager', 'orders.update'),
  ('Manager', 'reports.read'),
  ('Manager', 'reports.create'),
  ('Manager', 'reports.update'),
  ('Manager', 'reports.generate'),
  ('Manager', 'reports.download'),
  ('Manager', 'planning_requests.read'),
  ('Manager', 'planning_requests.create'),
  ('Manager', 'planning_requests.update'),
  ('Manager', 'planning_requests.approve'),
  ('Manager', 'planning_requests.reject'),
  ('Manager', 'audit_logs.read');

-- Staff can use the product dashboard and operational records.
INSERT IGNORE INTO tmp_seed_role_permissions (role_name, permission_code) VALUES
  ('Staff', 'dashboard.read'),
  ('Staff', 'products.read'),
  ('Staff', 'products.checkout'),
  ('Staff', 'orders.read'),
  ('Staff', 'orders.create'),
  ('Staff', 'orders.update'),
  ('Staff', 'planning_requests.read'),
  ('Staff', 'planning_requests.create'),
  ('Staff', 'reports.read');

-- Viewer is read-only and product dashboard-visible.
INSERT IGNORE INTO tmp_seed_role_permissions (role_name, permission_code) VALUES
  ('Viewer', 'dashboard.read'),
  ('Viewer', 'products.read'),
  ('Viewer', 'orders.read'),
  ('Viewer', 'reports.read'),
  ('Viewer', 'planning_requests.read');

-- Customer should only see/use the Product Dashboard, not Admin CRUD.
INSERT IGNORE INTO tmp_seed_role_permissions (role_name, permission_code) VALUES
  ('Customer', 'dashboard.read'),
  ('Customer', 'products.read'),
  ('Customer', 'products.checkout'),
  ('Customer', 'orders.create');

-- Standard User can use Product Dashboard and checkout.
INSERT IGNORE INTO tmp_seed_role_permissions (role_name, permission_code) VALUES
  ('User', 'dashboard.read'),
  ('User', 'products.read'),
  ('User', 'products.checkout'),
  ('User', 'orders.read'),
  ('User', 'orders.create');

-- Planner role.
INSERT IGNORE INTO tmp_seed_role_permissions (role_name, permission_code) VALUES
  ('Planner', 'dashboard.read'),
  ('Planner', 'products.read'),
  ('Planner', 'planning_requests.read'),
  ('Planner', 'planning_requests.create'),
  ('Planner', 'planning_requests.update'),
  ('Planner', 'planning_requests.approve'),
  ('Planner', 'planning_requests.reject'),
  ('Planner', 'reports.read');

-- Analyst role.
INSERT IGNORE INTO tmp_seed_role_permissions (role_name, permission_code) VALUES
  ('Analyst', 'dashboard.read'),
  ('Analyst', 'products.read'),
  ('Analyst', 'reports.read'),
  ('Analyst', 'reports.create'),
  ('Analyst', 'reports.generate'),
  ('Analyst', 'reports.download');

-- Auditor role.
INSERT IGNORE INTO tmp_seed_role_permissions (role_name, permission_code) VALUES
  ('Auditor', 'dashboard.read'),
  ('Auditor', 'products.read'),
  ('Auditor', 'audit_logs.read'),
  ('Auditor', 'users.read'),
  ('Auditor', 'roles.read'),
  ('Auditor', 'permissions.read'),
  ('Auditor', 'orders.read'),
  ('Auditor', 'reports.read'),
  ('Auditor', 'planning_requests.read');

INSERT IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM tmp_seed_role_permissions s
JOIN roles r ON r.name = s.role_name
JOIN permissions p ON p.code = s.permission_code;

/* =========================================================
   6. NORMALIZE ENUM VALUES FOR SQLALCHEMY
   SQLAlchemy Enum expects uppercase names by default.
   These WHERE clauses prevent MySQL Workbench Error Code 1175.
   ========================================================= */
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
  WHEN 'submitted' THEN 'SUBMITTED'
  WHEN 'in_review' THEN 'IN_REVIEW'
  WHEN 'approved' THEN 'APPROVED'
  WHEN 'rejected' THEN 'REJECTED'
  WHEN 'cancelled' THEN 'CANCELLED'
  WHEN 'canceled' THEN 'CANCELLED'
  ELSE UPPER(status)
END
WHERE id > 0;

UPDATE audit_logs
SET action = UPPER(action)
WHERE id > 0;

/* =========================================================
   7. VERIFICATION QUERIES
   ========================================================= */
SELECT 'ROLES' AS section, id, name, description
FROM roles
ORDER BY id;

SELECT 'PERMISSIONS' AS section, id, code, name, module
FROM permissions
ORDER BY module, code;

SELECT 'USERS_WITH_ROLES' AS section, u.id, u.email, u.full_name, r.name AS role_name
FROM users u
LEFT JOIN user_roles ur ON ur.user_id = u.id
LEFT JOIN roles r ON r.id = ur.role_id
ORDER BY u.id, r.name;

SELECT 'CUSTOMER_PERMISSIONS' AS section, r.name AS role_name, p.code AS permission_code
FROM roles r
JOIN role_permissions rp ON rp.role_id = r.id
JOIN permissions p ON p.id = rp.permission_id
WHERE r.name = 'Customer'
ORDER BY p.code;

COMMIT;

-- Restore the previous Workbench Safe Update Mode setting.
SET SQL_SAFE_UPDATES = @OLD_SQL_SAFE_UPDATES;
