-- =========================================================
-- FinMark Admin Seed Script
-- Users + Roles + Permissions + User Roles + Role Permissions
-- MySQL Workbench Ready
-- =========================================================
-- Notes:
-- 1. Run this AFTER your tables are created.
-- 2. Passwords are bcrypt-hashed and compatible with passlib[bcrypt].
-- 3. This script is idempotent: safe to run more than once.
-- 4. It does not delete existing users/roles/permissions.
-- =========================================================

USE finmark_db;

START TRANSACTION;

-- =========================================================
-- 1. ROLES
-- =========================================================
INSERT INTO roles (name, description, is_active, created_at, updated_at)
VALUES
  ('Admin', 'Full system administrator with complete access.', 1, NOW(), NOW()),
  ('Manager', 'Manages orders, reports, planning requests, and operational records.', 1, NOW(), NOW()),
  ('Staff', 'Handles daily order and planning request operations.', 1, NOW(), NOW()),
  ('Planner', 'Creates and manages planning requests.', 1, NOW(), NOW()),
  ('Analyst', 'Views and generates reports.', 1, NOW(), NOW()),
  ('Auditor', 'Reviews audit logs and system activity.', 1, NOW(), NOW()),
  ('Viewer', 'Read-only user for basic dashboard access.', 1, NOW(), NOW())
ON DUPLICATE KEY UPDATE
  description = VALUES(description),
  is_active = VALUES(is_active),
  updated_at = NOW();

-- =========================================================
-- 2. PERMISSIONS
-- Format: module.action
-- =========================================================
INSERT INTO permissions (code, name, module, description, created_at)
VALUES
  -- Dashboard
  ('dashboard.read', 'View Dashboard', 'dashboard', 'Can view dashboard summary and statistics.', NOW()),

  -- Users
  ('users.read', 'View Users', 'users', 'Can view users.', NOW()),
  ('users.create', 'Create Users', 'users', 'Can create new users.', NOW()),
  ('users.update', 'Update Users', 'users', 'Can update existing users.', NOW()),
  ('users.delete', 'Delete Users', 'users', 'Can deactivate/delete users.', NOW()),

  -- Roles
  ('roles.read', 'View Roles', 'roles', 'Can view roles.', NOW()),
  ('roles.create', 'Create Roles', 'roles', 'Can create new roles.', NOW()),
  ('roles.update', 'Update Roles', 'roles', 'Can update existing roles.', NOW()),
  ('roles.delete', 'Delete Roles', 'roles', 'Can deactivate/delete roles.', NOW()),

  -- Permissions
  ('permissions.read', 'View Permissions', 'permissions', 'Can view permissions.', NOW()),
  ('permissions.create', 'Create Permissions', 'permissions', 'Can create permissions.', NOW()),
  ('permissions.update', 'Update Permissions', 'permissions', 'Can update permissions.', NOW()),
  ('permissions.delete', 'Delete Permissions', 'permissions', 'Can delete permissions.', NOW()),

  -- Orders
  ('orders.read', 'View Orders', 'orders', 'Can view orders.', NOW()),
  ('orders.create', 'Create Orders', 'orders', 'Can create orders.', NOW()),
  ('orders.update', 'Update Orders', 'orders', 'Can update orders.', NOW()),
  ('orders.delete', 'Delete Orders', 'orders', 'Can delete orders.', NOW()),

  -- Reports
  ('reports.read', 'View Reports', 'reports', 'Can view reports.', NOW()),
  ('reports.create', 'Create Reports', 'reports', 'Can create reports.', NOW()),
  ('reports.update', 'Update Reports', 'reports', 'Can update reports.', NOW()),
  ('reports.delete', 'Delete Reports', 'reports', 'Can delete reports.', NOW()),
  ('reports.generate', 'Generate Reports', 'reports', 'Can generate reports.', NOW()),
  ('reports.download', 'Download Reports', 'reports', 'Can download report files.', NOW()),

  -- Planning Requests
  ('planning_requests.read', 'View Planning Requests', 'planning_requests', 'Can view planning requests.', NOW()),
  ('planning_requests.create', 'Create Planning Requests', 'planning_requests', 'Can create planning requests.', NOW()),
  ('planning_requests.update', 'Update Planning Requests', 'planning_requests', 'Can update planning requests.', NOW()),
  ('planning_requests.delete', 'Delete Planning Requests', 'planning_requests', 'Can delete planning requests.', NOW()),
  ('planning_requests.approve', 'Approve Planning Requests', 'planning_requests', 'Can approve planning requests.', NOW()),
  ('planning_requests.reject', 'Reject Planning Requests', 'planning_requests', 'Can reject planning requests.', NOW()),

  -- Audit Logs
  ('audit_logs.read', 'View Audit Logs', 'audit_logs', 'Can view audit logs.', NOW()),
  ('audit_logs.create', 'Create Audit Logs', 'audit_logs', 'Can manually create audit log records.', NOW()),
  ('audit_logs.update', 'Update Audit Logs', 'audit_logs', 'Can update audit log records.', NOW()),
  ('audit_logs.delete', 'Delete Audit Logs', 'audit_logs', 'Can delete audit log records.', NOW())
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  module = VALUES(module),
  description = VALUES(description);

-- =========================================================
-- 3. USERS
-- Passwords:
-- admin@example.com    / Admin123!
-- manager@example.com  / Manager123!
-- staff@example.com    / Staff123!
-- planner@example.com  / Planner123!
-- analyst@example.com  / Analyst123!
-- auditor@example.com  / Auditor123!
-- viewer@example.com   / Viewer123!
-- user@example.com     / Password123!
-- =========================================================
INSERT INTO users (
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
  last_login_at,
  created_at,
  updated_at
)
VALUES
  (
    'admin@example.com',
    'admin@example.com',
    '$2b$12$i4pY/RtXoUmVnMKJ7BRcW.gGywu9MQ1NLTSZwTZV9/tRECdUsHfTG',
    'System Administrator',
    1,
    1,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NOW(),
    NOW()
  ),
  (
    'manager@example.com',
    'manager@example.com',
    '$2b$12$5I807om1wNoERo4LYqoIAekRTsg.VN73gUZN8VqFRnL/KX1NlnzgG',
    'Operations Manager',
    1,
    1,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NOW(),
    NOW()
  ),
  (
    'staff@example.com',
    'staff@example.com',
    '$2b$12$v0aztEGn7TVxZE4bLZEL2u0ep0jXaKKCuX8.cvW9YUrOVjmZJrOp2',
    'Operations Staff',
    1,
    1,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NOW(),
    NOW()
  ),
  (
    'planner@example.com',
    'planner@example.com',
    '$2b$12$timbK4FkE7puPasVaJQU3.qj4NvdI.xLaKuhvwDIDpVjPityKX6hK',
    'Planning Officer',
    1,
    1,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NOW(),
    NOW()
  ),
  (
    'analyst@example.com',
    'analyst@example.com',
    '$2b$12$BuADUis0OyUsXAByiKnMd.fcLuN24frMW3VIqDyt8cmUb3M4MGgWy',
    'Report Analyst',
    1,
    1,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NOW(),
    NOW()
  ),
  (
    'auditor@example.com',
    'auditor@example.com',
    '$2b$12$S3p.5FC58eRDnGJDsYtwAOCHLWE3kFvk.Sj3CRDcc2U.PzPWhduxe',
    'System Auditor',
    1,
    1,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NOW(),
    NOW()
  ),
  (
    'viewer@example.com',
    'viewer@example.com',
    '$2b$12$AaXZG6YcJXs8M13Z4TG3TunGjKR7hc8ODuXdY1UTGnLQEgp0zIiUC',
    'Read Only Viewer',
    1,
    1,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NOW(),
    NOW()
  ),
  (
    'user@example.com',
    'user@example.com',
    '$2b$12$suC5nPiUABpY697wailkkeukWCB9uJ/pdyPwcj0z2rxK0AHkm.x16',
    'Demo User',
    1,
    1,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NOW(),
    NOW()
  )
ON DUPLICATE KEY UPDATE
  hashed_password = VALUES(hashed_password),
  full_name = VALUES(full_name),
  is_active = VALUES(is_active),
  is_verified = VALUES(is_verified),
  verification_token = NULL,
  verification_token_expires_at = NULL,
  password_reset_token = NULL,
  password_reset_token_expires_at = NULL,
  updated_at = NOW();

-- =========================================================
-- 4. USER ROLE ASSIGNMENTS
-- =========================================================
INSERT IGNORE INTO user_roles (user_id, role_id, assigned_at)
SELECT u.id, r.id, NOW()
FROM users u
JOIN roles r ON r.name = 'Admin'
WHERE u.email IN ('admin@example.com', 'user@example.com');

INSERT IGNORE INTO user_roles (user_id, role_id, assigned_at)
SELECT u.id, r.id, NOW()
FROM users u
JOIN roles r ON r.name = 'Manager'
WHERE u.email = 'manager@example.com';

INSERT IGNORE INTO user_roles (user_id, role_id, assigned_at)
SELECT u.id, r.id, NOW()
FROM users u
JOIN roles r ON r.name = 'Staff'
WHERE u.email = 'staff@example.com';

INSERT IGNORE INTO user_roles (user_id, role_id, assigned_at)
SELECT u.id, r.id, NOW()
FROM users u
JOIN roles r ON r.name = 'Planner'
WHERE u.email = 'planner@example.com';

INSERT IGNORE INTO user_roles (user_id, role_id, assigned_at)
SELECT u.id, r.id, NOW()
FROM users u
JOIN roles r ON r.name = 'Analyst'
WHERE u.email = 'analyst@example.com';

INSERT IGNORE INTO user_roles (user_id, role_id, assigned_at)
SELECT u.id, r.id, NOW()
FROM users u
JOIN roles r ON r.name = 'Auditor'
WHERE u.email = 'auditor@example.com';

INSERT IGNORE INTO user_roles (user_id, role_id, assigned_at)
SELECT u.id, r.id, NOW()
FROM users u
JOIN roles r ON r.name = 'Viewer'
WHERE u.email = 'viewer@example.com';

-- =========================================================
-- 5. ROLE PERMISSION ASSIGNMENTS
-- =========================================================

-- Admin: all permissions
INSERT IGNORE INTO role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permissions p
WHERE r.name = 'Admin';

-- Manager: operations management, reports, planning, audit read
INSERT IGNORE INTO role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permissions p ON p.code IN (
  'dashboard.read',
  'orders.read', 'orders.create', 'orders.update',
  'reports.read', 'reports.create', 'reports.update', 'reports.generate', 'reports.download',
  'planning_requests.read', 'planning_requests.create', 'planning_requests.update',
  'planning_requests.approve', 'planning_requests.reject',
  'audit_logs.read'
)
WHERE r.name = 'Manager';

-- Staff: daily operational CRUD except delete/admin modules
INSERT IGNORE INTO role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permissions p ON p.code IN (
  'dashboard.read',
  'orders.read', 'orders.create', 'orders.update',
  'planning_requests.read', 'planning_requests.create', 'planning_requests.update',
  'reports.read'
)
WHERE r.name = 'Staff';

-- Planner: planning request focused
INSERT IGNORE INTO role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permissions p ON p.code IN (
  'dashboard.read',
  'planning_requests.read', 'planning_requests.create', 'planning_requests.update',
  'reports.read'
)
WHERE r.name = 'Planner';

-- Analyst: reporting focused
INSERT IGNORE INTO role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permissions p ON p.code IN (
  'dashboard.read',
  'reports.read', 'reports.create', 'reports.update', 'reports.generate', 'reports.download',
  'orders.read',
  'planning_requests.read'
)
WHERE r.name = 'Analyst';

-- Auditor: audit-focused read access
INSERT IGNORE INTO role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permissions p ON p.code IN (
  'dashboard.read',
  'audit_logs.read',
  'users.read',
  'roles.read',
  'permissions.read',
  'orders.read',
  'reports.read',
  'planning_requests.read'
)
WHERE r.name = 'Auditor';

-- Viewer: read-only basic access
INSERT IGNORE INTO role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permissions p ON p.code IN (
  'dashboard.read',
  'orders.read',
  'reports.read',
  'planning_requests.read'
)
WHERE r.name = 'Viewer';

-- =========================================================
-- 6. OPTIONAL AUDIT LOGS FOR SEED ACTION
-- =========================================================
INSERT INTO audit_logs (
  actor_user_id,
  action,
  entity_type,
  entity_id,
  detail,
  ip_address,
  user_agent,
  created_at
)
SELECT
  u.id,
  'CREATE',
  'seed',
  'users_roles_permissions',
  'Seeded users, roles, permissions, user_roles, and role_permissions from MySQL Workbench script.',
  '127.0.0.1',
  'MySQL Workbench',
  NOW()
FROM users u
WHERE u.email = 'admin@example.com'
LIMIT 1;

COMMIT;

-- =========================================================
-- 7. CHECK RESULTS
-- =========================================================
SELECT id, email, full_name, is_active, is_verified
FROM users
ORDER BY id;

SELECT r.name AS role_name, COUNT(rp.permission_id) AS permission_count
FROM roles r
LEFT JOIN role_permissions rp ON rp.role_id = r.id
GROUP BY r.id, r.name
ORDER BY r.id;

SELECT u.email, GROUP_CONCAT(r.name ORDER BY r.name SEPARATOR ', ') AS roles
FROM users u
LEFT JOIN user_roles ur ON ur.user_id = u.id
LEFT JOIN roles r ON r.id = ur.role_id
GROUP BY u.id, u.email
ORDER BY u.id;




